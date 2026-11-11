"""Train one Atlas from random initialisation on N trajectories of one system and measure it.

Data budget: N trajectories in total; 80% train, 20% used only for early stopping (so model selection also pays
for its data). Test sets are fixed and never used for any choice: 2,000 fresh trajectories from the same parameter
ranges, 1,000 from parameter ranges the model never saw, and counterfactual forcings for intervention accuracy.
"""
import time

import numpy as np
import torch

from . import systems as S
from .model import QS, ring_basis, ring_geo, sized
from .sysid import identify, smooth_forecast

_CACHE = {}


def _t(d, keys=("yc", "yf", "yfn", "uc", "uf")):
    return {k: torch.from_numpy(d[k]) for k in keys}


def test_sets(name, noise):
    key = (name, noise)
    if key not in _CACHE:
        te = S.make(name, 2000, 999, noise)
        ood = S.make(name, 1000, 998, noise, ood=True)
        # counterfactual: same trajectories, a different forcing over the forecast steps
        rng = np.random.default_rng(997)
        u2 = te["u"].copy()
        n, U = len(u2), u2.shape[2]
        node = rng.integers(0, U, n)
        amp = rng.normal(0, 1.0, n) if U == 1 else rng.uniform(0.3, 1.5, n)
        u2[:, S.L:] = 0.0
        u2[np.arange(n), S.L:, node] = amp[:, None]
        cf = S.make(name, 2000, 999, noise, theta=te["theta"], s0=te["s0"], u=u2)
        cf["yc"], cf["uc"] = te["yc"], te["uc"]                          # identical observed past
        k = 24 if len(S.SYSTEMS[name][0]) == 1 else 16
        _CACHE[key] = dict(te=te, ood=ood, cf=cf, oracle=S.nmse(S.oracle(name, te, k), te),
                           oracle_ood=S.nmse(S.oracle(name, ood, k, ood=True), ood),
                           persistence=S.nmse(S.persistence(te), te))
    return _CACHE[key]


def pinball(q, y):
    e = y[..., None] - q
    qs = torch.tensor(QS)
    return torch.maximum(qs * e, (qs - 1) * e).mean()


@torch.no_grad()
def predict(m, d, geo, miss=0.0, seed=0, bs=500, basis=None, extras=False):
    m.eval(); out, exs = [], []
    g = torch.Generator().manual_seed(seed)
    for i in range(0, len(d["yc"]), bs):
        yc = d["yc"][i:i + bs]
        mc = (torch.rand(yc.shape, generator=g) >= miss).float() if miss > 0 else torch.ones_like(yc)
        q, _, ex = m(yc, mc, d["uc"][i:i + bs], d["uf"][i:i + bs], geo, basis)
        out.append(q); exs.append(ex)
    m.train()
    q = torch.cat(out)
    return (q, {k: torch.cat([e[k] for e in exs]) for k in exs[0]}) if extras else q


def novelty(train_f, feats, k=5):
    """How far a case lies from everything seen in training: mean distance to its k nearest training cases,
    in standardised feature space. Returns one score per row of each array in feats."""
    mu, sd = train_f.mean(0, keepdim=True), train_f.std(0, keepdim=True).clamp(min=1e-6)
    tr = (train_f - mu) / sd
    k = min(k, len(tr))
    return [torch.cdist((f - mu) / sd, tr).topk(k, largest=False).values.mean(1).numpy() for f in feats]


def _nmse(q, d):
    return float(((q[..., 1] - d["yf"]) ** 2).mean() / d["yf"].var())


def _auroc(pos, neg):
    r = np.argsort(np.argsort(np.concatenate([pos, neg]))) + 1
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def run(name, size, N, seed, noise=0.05, width=1.0, physics=False, max_steps=1200, batch=64, wd=1e-4, log=None,
        sysid=False, patience=6, gate=False):
    torch.manual_seed(seed); torch.set_num_threads(1)
    ring = S.is_ring(name)
    geo = ring_geo(S.M) if ring else None
    basis = (ring_basis(S.M) if ring else None) if sysid else None
    T = test_sets(name, noise)
    d = S.make(name, N, 10_000 + 1000 * seed + 7, noise, width=width)
    n_tr = max(1, int(round(0.8 * N)))
    tr = {k: v[:n_tr] for k, v in _t(d).items()}
    va = {k: v[n_tr:] for k, v in _t(d).items()}
    if len(va["yc"]) == 0: va = tr
    m = sized(int(size), spatial=ring, conserve=bool(physics and ring), dt=S.DT, sysid=bool(sysid),
              K=S.M if (ring and sysid) else 1, lags=2 if ring else 3, gate=bool(gate))
    lr = 1e-3 if m.cfg["d"] <= 256 else 5e-4
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=wd)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / 50) * (0.1 + 0.45 * (1 + np.cos(np.pi * min(1, s / max_steps)))))
    rng = np.random.default_rng(seed)
    best, best_state, bad, t0, step = float("inf"), None, 0, time.time(), 0
    B = min(batch, n_tr)
    for step in range(1, max_steps + 1):
        i = torch.from_numpy(rng.integers(0, n_tr, B))
        yc = tr["yc"][i]
        mc = (torch.rand(yc.shape) >= 0.15).float()                       # hide 15% of the observed values
        q, rec, ex = m(yc, mc, tr["uc"][i], tr["uf"][i], geo, basis)
        hid = 1 - mc
        loss = pinball(q, tr["yfn"][i]) + 0.2 * (((rec - yc) ** 2) * hid).sum() / hid.sum().clamp(min=1)
        if sysid:                       # the identified dynamics alone must also forecast well
            loss = loss + 0.5 * (ex["base"] - tr["yfn"][i]).abs().mean()
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step(); sched.step()
        if step % 50 == 0:
            v = float(pinball(predict(m, va, geo, basis=basis), va["yfn"]))
            if v < best - 1e-5:
                best, bad = v, 0
                best_state = {k: x.clone() for k, x in m.state_dict().items()}
            else:
                bad += 1
            if bad >= patience and step >= 300:
                break
    secs = time.time() - t0
    m.load_state_dict(best_state)
    te, ood, cf = _t(T["te"]), _t(T["ood"]), _t(T["cf"])
    (q, ext), (qo, exo), (qv, exv), (_, extr) = [predict(m, x, geo, basis=basis, extras=True) for x in (te, ood, va, tr)]
    qc, qtr = predict(m, cf, geo, basis=basis), predict(m, tr, geo, basis=basis)
    nov = {}
    for key in (("z", "theta") if sysid else ("z",)):          # novelty flag: distance from the training cases
        a_te, a_ood, a_va = novelty(extr[key], [ext[key], exo[key], exv[key]])
        thr = float(np.percentile(a_va, 95))                    # 5% false alarms on the held-out training split
        nov[key] = dict(auroc=_auroc(a_ood, a_te), flagged_ood=float((a_ood > thr).mean()),
                        false_alarm=float((a_te > thr).mean()))
        flags = (torch.from_numpy(a_te > thr), torch.from_numpy(a_ood > thr))
    fb = {}
    if sysid:   # fallback: where the flag fires, forecast from the window alone (identification with no learned parts)
        bs_ = basis if basis is not None else torch.eye(1)[None]
        for nm_, d_, q_, fl in (("", te, q, flags[0]), ("_ood", ood, qo, flags[1])):
            th = identify(d_["yc"], d_["uc"], bs_, m.p, torch.full((m.p * bs_.shape[0] * 2,), 0.01))
            cl = smooth_forecast(th, d_["yc"], torch.ones_like(d_["yc"]), torch.cat([d_["uc"], d_["uf"]], 2), bs_, m.p, S.H)[1]
            mix = torch.where(fl[:, None, None, None], cl, q_[..., 1])
            e_ = lambda a, sel=slice(None): float(((a[sel] - d_["yf"][sel]) ** 2).mean() / d_["yf"].var())
            fb["nmse_fb" + nm_] = e_(mix)
            fb["flag_err" + nm_] = dict(flagged=e_(q_[..., 1], fl) if fl.any() else None,
                                        unflagged=e_(q_[..., 1], ~fl) if (~fl).any() else None)
    wid = (q[..., 2] - q[..., 0]).mean((1, 2, 3)).numpy()
    wido = (qo[..., 2] - qo[..., 0]).mean((1, 2, 3)).numpy()
    err = ((q[..., 1] - te["yf"]) ** 2).mean((1, 2, 3)).sqrt().numpy()
    rk = lambda a: np.argsort(np.argsort(a)).astype(float)
    dy, dq = cf["yf"] - te["yf"], qc[..., 1] - q[..., 1]
    r = dict(system=name, size=int(size), params=m.n_params(), d=m.cfg["d"], N=int(N), n_train=n_tr, seed=seed,
             noise=noise, width=width, physics=int(bool(physics)), max_steps=max_steps, steps=step, secs=round(secs, 1),
             val=round(best, 5), nmse=_nmse(q, te), nmse_train=_nmse(qtr, tr), nmse_ood=_nmse(qo, ood),
             nmse_missing30=_nmse(predict(m, te, geo, miss=0.3, basis=basis), te), sysid=int(bool(sysid)), gate=int(bool(gate)), patience=patience, alpha=(float(ext['alpha'].mean()) if sysid else None),
             alpha_ood=(float(exo['alpha'].mean()) if sysid else None),
             novelty=nov, **fb, nmse_base=(float(((ext['base'] - te['yf']) ** 2).mean() / te['yf'].var()) if sysid else None),
             nmse_ood_base=(float(((exo['base'] - ood['yf']) ** 2).mean() / ood['yf'].var()) if sysid else None),
             interv_nmse=float(((dq - dy) ** 2).mean() / (dy ** 2).mean()),
             cover80=float(((te["yfn"] >= q[..., 0]) & (te["yfn"] <= q[..., 2])).float().mean()),
             width_err_spearman=float(np.corrcoef(rk(wid), rk(err))[0, 1]),
             ood_auroc=_auroc(wido, wid),
             oracle=T["oracle"], oracle_ood=T["oracle_ood"], persistence=T["persistence"])
    if log:
        log(r)
    return r
