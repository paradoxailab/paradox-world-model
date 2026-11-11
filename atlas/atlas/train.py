"""Train one Atlas from random initialisation on N trajectories of one system and measure it.

Data budget: N trajectories in total; 80% train, 20% used only for early stopping (so model selection also pays
for its data). Test sets are fixed and never used for any choice: 2,000 fresh trajectories from the same parameter
ranges, 1,000 from parameter ranges the model never saw, and counterfactual forcings for intervention accuracy.
"""
import time

import numpy as np
import torch

from . import systems as S
from .model import QS, ring_geo, sized

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
def predict(m, d, geo, miss=0.0, seed=0, bs=500):
    m.eval(); out = []
    g = torch.Generator().manual_seed(seed)
    for i in range(0, len(d["yc"]), bs):
        yc = d["yc"][i:i + bs]
        mc = (torch.rand(yc.shape, generator=g) >= miss).float() if miss > 0 else torch.ones_like(yc)
        out.append(m(yc, mc, d["uc"][i:i + bs], d["uf"][i:i + bs], geo)[0])
    m.train()
    return torch.cat(out)


def _nmse(q, d):
    return float(((q[..., 1] - d["yf"]) ** 2).mean() / d["yf"].var())


def _auroc(pos, neg):
    r = np.argsort(np.argsort(np.concatenate([pos, neg]))) + 1
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def run(name, size, N, seed, noise=0.05, width=1.0, physics=False, max_steps=1200, batch=64, wd=1e-4, log=None):
    torch.manual_seed(seed); torch.set_num_threads(1)
    ring = S.is_ring(name)
    geo = ring_geo(S.M) if ring else None
    T = test_sets(name, noise)
    d = S.make(name, N, 10_000 + 1000 * seed + 7, noise, width=width)
    n_tr = max(1, int(round(0.8 * N)))
    tr = {k: v[:n_tr] for k, v in _t(d).items()}
    va = {k: v[n_tr:] for k, v in _t(d).items()}
    if len(va["yc"]) == 0: va = tr
    m = sized(int(size), spatial=ring, conserve=bool(physics and ring), dt=S.DT)
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
        q, rec = m(yc, mc, tr["uc"][i], tr["uf"][i], geo)
        hid = 1 - mc
        loss = pinball(q, tr["yfn"][i]) + 0.2 * (((rec - yc) ** 2) * hid).sum() / hid.sum().clamp(min=1)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step(); sched.step()
        if step % 50 == 0:
            v = float(pinball(predict(m, va, geo), va["yfn"]))
            if v < best - 1e-5:
                best, bad = v, 0
                best_state = {k: x.clone() for k, x in m.state_dict().items()}
            else:
                bad += 1
            if bad >= 6 and step >= 300:
                break
    secs = time.time() - t0
    m.load_state_dict(best_state)
    te, ood, cf = _t(T["te"]), _t(T["ood"]), _t(T["cf"])
    q, qo, qc = predict(m, te, geo), predict(m, ood, geo), predict(m, cf, geo)
    qtr = predict(m, tr, geo)
    wid = (q[..., 2] - q[..., 0]).mean((1, 2, 3)).numpy()
    wido = (qo[..., 2] - qo[..., 0]).mean((1, 2, 3)).numpy()
    err = ((q[..., 1] - te["yf"]) ** 2).mean((1, 2, 3)).sqrt().numpy()
    rk = lambda a: np.argsort(np.argsort(a)).astype(float)
    dy, dq = cf["yf"] - te["yf"], qc[..., 1] - q[..., 1]
    r = dict(system=name, size=int(size), params=m.n_params(), d=m.cfg["d"], N=int(N), n_train=n_tr, seed=seed,
             noise=noise, width=width, physics=int(bool(physics)), max_steps=max_steps, steps=step, secs=round(secs, 1),
             val=round(best, 5), nmse=_nmse(q, te), nmse_train=_nmse(qtr, tr), nmse_ood=_nmse(qo, ood),
             nmse_missing30=_nmse(predict(m, te, geo, miss=0.3), te),
             interv_nmse=float(((dq - dy) ** 2).mean() / (dy ** 2).mean()),
             cover80=float(((te["yfn"] >= q[..., 0]) & (te["yfn"] <= q[..., 2])).float().mean()),
             width_err_spearman=float(np.corrcoef(rk(wid), rk(err))[0, 1]),
             ood_auroc=_auroc(wido, wid),
             oracle=T["oracle"], oracle_ood=T["oracle_ood"], persistence=T["persistence"])
    if log:
        log(r)
    return r
