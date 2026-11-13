"""Atlas-India v1.0: one Atlas for every Indian station network (the all-India league).

Data: INDIA_LONG.npz (tools/build_india_long.py): 453 CPCB / state-board stations, hourly, 2017-01-01 .. 2023-03-31.
Splits, as in the Delhi league: the last 182 days are TEST (2022-10-01 .. 2023-03-31), the 61 days before are
VALIDATION, everything earlier is TRAIN. A station is in the league if it reports PM2.5 on at least 50% of test
hours and 12.5% of training hours. Networks: every state with 6 or more such stations is one network; the rest
are pooled as "other states". In each network a fifth of the stations is never trained on (Track U; same seeded rule
as Delhi), the graph is built from how daily PM2.5 moves together, and every variable is scaled with that network's
training-period statistics. Pressure is centred on each station's own training median first (stations report it
in different units).

Model: the Delhi v1.1 Atlas unchanged (1M parameters, 72 h of 15 variables, next 24 h, PM2.5 carries the loss).
ONE set of weights for all networks: every training step draws a network (in proportion to its number of valid
training windows) and 16 windows from it. As in Delhi v1.2 the whole schedule is run and two models are kept: E, the
checkpoint an early-stopping rule on pooled validation keeps, and F, the weights after the last step.

One seed per run. It saves both models and their forecasts on the validation and test windows of every network
(every station: trained stations from the trained-station graph, unseen stations from the whole network).
Scoring, the E / F decision and the verdicts are in score_india.py.

  python tools/build_india_long.py && python run_atlas_india.py --seed 400
"""
import argparse, json, math, os, re, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import Delhi, SPD, TARGETS, DM, RAW, TEST_DAYS, VAL_DAYS
import run_atlas_delhi as R
from run_atlas_long import valid_origins

H, DEV, OUT = R.H, R.DEV, R.OUT
MIN_NET = 6
T0 = time.time()


def log(*a):
    print(*a, flush=True)


def networks(quick=False):
    """Split INDIA_LONG.npz into state networks and load each with the Delhi league's loader."""
    z = np.load(os.path.join(RAW, "INDIA_LONG.npz"), allow_pickle=False)
    X, names, state, city, vars_ = z["X"], [str(s) for s in z["stations"]], [str(s) for s in z["state"]], \
        [str(s) for s in z["city"]], [str(v) for v in z["vars"]]
    T = len(X)
    n_te, n_va = TEST_DAYS * SPD, VAL_DAYS * SPD
    b = T - n_te - n_va
    pm = np.isfinite(X[..., vars_.index("PM2.5")])
    ok = (pm[-n_te:].mean(0) >= 0.5) & (pm[:b].mean(0) >= 0.125)
    bp = vars_.index("BP")
    with np.errstate(all="ignore"):
        X[..., bp] = X[..., bp] - np.nanmedian(X[:b, :, bp], 0)[None] + 1000.0        # each station's own pressure level
    groups = {}
    for j in np.where(ok)[0]:
        groups.setdefault(state[j], []).append(j)
    nets = {k: v for k, v in groups.items() if len(v) >= MIN_NET}
    rest = sorted(j for k, v in groups.items() if len(v) < MIN_NET for j in v)
    if rest:
        nets["other states"] = rest
    out = []
    d = os.path.join(RAW, "india_nets"); os.makedirs(d, exist_ok=True)
    for k in sorted(nets, key=lambda k: -len(nets[k])):
        ix = np.array(nets[k])
        f = os.path.join(d, re.sub(r"[^a-z0-9]+", "_", k.lower()) + ".npz")
        np.savez(f, X=X[:, ix], vars=np.array(vars_), stations=np.array([names[j] for j in ix]), start=z["start"])
        D = Delhi(path=f, targets=TARGETS, backbone=False, wxfc=False, min_cov_train=0.125)
        assert D.N == len(ix), (k, D.N, len(ix))
        D.name, D.cities = k, [city[j] for j in ix]
        os.remove(f)
        out.append(D)
        if quick and len(out) == 3:
            break
    return out


def origins(D, quick=False):
    te, va = D.origins("test", R.TEST_STRIDE), D.origins("val", R.VAL_STRIDE)
    tr = D.origins("train", R.TRAIN_STRIDE)
    tr = valid_origins(D, tr[tr >= max(DM * SPD, 7 * SPD) + R.L], max(2, int(math.ceil(0.25 * len(D.seen)))))
    va4 = va[::4]
    if quick:
        va4, te = va4[:6], te[:8]
    return tr, va4, te


def pooled_val(m, nets, O):
    """Mean absolute error of the median forecast over every observed validation cell of every network's trained
    stations."""
    s = c = 0.0
    for D, (tr, va4, te) in zip(nets, O):
        e = np.abs(R.predict(m, D, va4, D.seen)[..., 1] - R.truth(D, va4, D.seen))
        ok = np.isfinite(e)
        s += float(e[ok].sum()); c += float(ok.sum())
    return s / max(c, 1)


def forecasts(m, nets, O):
    """Every station of every network: trained stations from the trained-station graph, unseen from the whole network."""
    out = {}
    for D, (tr, va4, te) in zip(nets, O):
        for nm, org in (("v4", va4), ("t", te)):
            f = np.zeros((len(org), D.N, H, 3), np.float32)
            f[:, D.seen] = R.predict(m, D, org, D.seen)
            if len(D.unseen):
                f[:, D.unseen] = R.predict(m, D, org, np.arange(D.N))[:, D.unseen]
            out[(D.name, nm)] = f
    return out


def test_mae(f, nets, O):
    sS = cS = sU = cU = 0.0
    for D, (tr, va4, te) in zip(nets, O):
        e = np.abs(f[(D.name, "t")][..., 1] - R.truth(D, te, np.arange(D.N)))
        x = e[:, D.seen]; ok = np.isfinite(x); sS += float(x[ok].sum()); cS += float(ok.sum())
        x = e[:, D.unseen]; ok = np.isfinite(x); sU += float(x[ok].sum()); cU += float(ok.sum())
    return sS / max(cS, 1), sU / max(cU, 1)


def reforecast(a):
    """Correction of 2026-11-13: forecasts again from the saved weights after the input fix in pw/ddata.py (a weather
    variable that no trained station of a network reports is no longer an input there). Nothing is retrained. The
    forecasts as first run are kept as asrun_<tag>_s<seed>.npz."""
    nets = networks(a.quick)
    O = [origins(D, a.quick) for D in nets]
    f_old = os.path.join(OUT, f"{a.tag}_s{a.seed}.npz")
    old = np.load(f_old)
    res = json.loads(str(old["meta"]))
    if "input_fix" in res or "loader" in res:                # already forecast with the fixed loader
        log(f"REFORECAST seed {a.seed}: not needed (forecasts already made with the fixed loader)")
        old.close(); return
    ck = torch.load(os.path.join(OUT, f"atlas_{a.tag}_s{a.seed}.pt"), map_location="cpu", weights_only=False)
    assert ck["networks"] == [D.name for D in nets], "networks differ from the saved model's"
    dropped = {D.name: D.aux_dropped for D in nets if D.aux_dropped}
    log(f"REFORECAST seed {a.seed}: variables no trained station reports, no longer inputs: {json.dumps(dropped)}")
    m = R.build(nets[0], a.size, 0)
    save, res["input_fix"] = {}, dict(dropped=dropped, as_run={}, trained_station_max_change={})
    for k in ("E", "F"):
        m.load_state_dict(ck[k])
        f = forecasts(m, nets, O)
        d = max(float(np.abs(f[(D.name, nm)][:, D.seen] - old[f"{D.name}|{k}_{nm}"][:, D.seen]).max()) for D in nets for nm in ("v4", "t"))
        res["input_fix"]["as_run"][k] = [res[k]["test_S"], res[k]["test_U"]]
        res["input_fix"]["trained_station_max_change"][k] = d
        res[k]["test_S"], res[k]["test_U"] = test_mae(f, nets, O)
        log(f"TEST {k} seed {a.seed} after the input fix (one model, uncalibrated, all networks pooled): trained stations "
            f"{res[k]['test_S']:.2f}, unseen {res[k]['test_U']:.2f}; as first run {res['input_fix']['as_run'][k][0]:.2f}, "
            f"{res['input_fix']['as_run'][k][1]:.2f}; largest change of any trained-station forecast {d:.4f} ug/m3")
        for (net, nm), arr in f.items():
            save[f"{net}|{k}_{nm}"] = arr
    old.close()
    os.replace(f_old, os.path.join(OUT, f"asrun_{a.tag}_s{a.seed}.npz"))
    np.savez_compressed(f_old, meta=np.array(json.dumps(res, default=float)), **save)
    log("INDIA-REFORECAST " + json.dumps(res, default=float))


def main(a):
    q = a.quick
    nets = networks(q)
    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    if skip:                                               # e.g. pretraining for another league: that city is left out
        assert skip <= {D.name for D in nets}, f"no such network: {skip - {D.name for D in nets}}"
        nets = [D for D in nets if D.name not in skip]
        log(f"left out, never trained on: {sorted(skip)}")
    if a.only:                                             # ICML L1: adapt to one network only
        assert a.only in {D.name for D in nets}, f"no such network: {a.only}"
        nets = [D for D in nets if D.name == a.only]
        log(f"adapting to one network only: {a.only}")
    O = [origins(D, q) for D in nets]
    for D, (tr, va4, te) in zip(nets, O):
        log(f"NET {D.name}: {D.N} stations ({len(D.seen)} trained on, {len(D.unseen)} unseen), {len(tr)} valid training windows, "
            f"{len(va4)} validation and {len(te)} test windows; PM2.5 missing {100 * np.isnan(D.Y[..., 0]).mean():.0f}%")
    w = np.array([len(o[0]) for o in O], float)
    assert (w > 0).all(), "a network has no valid training window"
    p = w / w.sum()
    log(f"{len(nets)} networks, {sum(D.N for D in nets)} stations, {int(w.sum())} valid training windows; test "
        f"{nets[0].dates[O[0][2][0]]} .. {nets[0].dates[O[0][2][-1] + H - 1]}; device {DEV}")
    torch.manual_seed(a.seed); rng = np.random.default_rng(a.seed)
    m = R.build(nets[0], a.size, 0)
    lr = (1e-3 if m.cfg["d"] <= 256 else 5e-4) * a.lr_scale
    fP = None
    if a.init:                                             # ICML L1: start from weights pre-trained without this network
        ck = torch.load(a.init, map_location="cpu", weights_only=False)
        assert all(ck["cfg"][k] == m.cfg[k] for k in m.cfg), "the saved model's configuration differs"
        assert not ({D.name for D in nets} & set(ck["networks"])), "the pre-trained weights saw this network"
        m.load_state_dict(ck["E"]); log(f"initialised from {a.init} (pre-trained on {len(ck['networks'])} networks)")
        if not a.pretrain_only:
            fP = forecasts(m, nets, O)                     # P: the pre-trained weights, before any training here
    steps, every = (60, 20) if q else (a.steps, a.every)
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / 100) * (0.1 + 0.45 * (1 + math.cos(math.pi * min(1, s / steps)))))
    D0 = nets[0]
    chw = torch.tensor([1.0] + [0.1] * (D0.K - 1) + [0.05] * D0.Ca, device=DEV)
    qs = torch.tensor([0.1, 0.5, 0.9], device=DEV)
    log(f"Atlas: {m.n_params():,} parameters, width {m.cfg['d']}; {steps} steps, a look at validation every {every}")
    v0 = pooled_val(m, nets, O)
    best, state, bad, frozen, v, t0, step = v0, {k: x.detach().clone() for k, x in m.state_dict().items()}, 0, None, v0, time.time(), 0
    log(f"  start pooled val MAE {v0:.3f}")
    for step in range(1, steps + 1):
        i = int(rng.choice(len(nets), p=p))
        D, tr = nets[i], O[i][0]
        b = R.make_batch(D, rng.choice(tr, min(16, len(tr)), replace=False), D.seen)
        rate = torch.rand(b["mc"].shape[0], 1, 1, 1, device=DEV) * 0.4
        mc = b["mc"] * (torch.rand(b["mc"].shape, device=DEV) >= rate).float()
        qq, rec, ex = R.forward(m, b, mc)
        e = b["yf"][..., None] - qq
        ww = b["of"] * chw
        loss = (torch.maximum(qs * e, (qs - 1) * e).mean(-1) * ww).sum() / ww.sum().clamp(min=1)
        hid = b["mc"] - mc
        loss = loss + 0.2 * (((rec - b["yc"]) ** 2) * hid * chw).sum() / (hid * chw).sum().clamp(min=1)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step(); sched.step()
        if step % every == 0 or step == steps:
            if frozen is not None and step % (3 * every) != 0 and step != steps:
                continue
            v = pooled_val(m, nets, O)
            if frozen is None:
                if v < best - 1e-4:
                    best, bad, state = v, 0, {k: x.detach().clone() for k, x in m.state_dict().items()}
                else:
                    bad += 1
                if bad >= a.patience:
                    frozen = step
            log(f"  step {step} pooled val MAE {v:.3f} (best {best:.3f}{', E fixed at step ' + str(frozen) if frozen else ''}) {time.time() - t0:.0f}s")
            if time.time() - t0 > a.cap * 60:
                break
    capped = bool(time.time() - t0 > a.cap * 60)
    if step % every != 0 and step != steps:
        v = pooled_val(m, nets, O)
    res = dict(seed=a.seed, loader="input fix of 2026-11-13", inputs_dropped={D.name: D.aux_dropped for D in nets if D.aux_dropped},
               params=m.n_params(), networks=[D.name for D in nets], stations=[D.N for D in nets],
               train_windows=[len(o[0]) for o in O], hit_time_cap=capped, minutes_train=round((time.time() - t0) / 60, 1),
               E=dict(val_MAE=best, steps=frozen or step), F=dict(val_MAE=v, steps=step))
    log("RUN " + json.dumps(res, default=float))
    if a.pretrain_only:                                    # only the weights are kept; no test window is touched
        os.makedirs(OUT, exist_ok=True)
        res.update(left_out=sorted(skip), minutes_total=round((time.time() - T0) / 60, 1))
        torch.save({"cfg": m.cfg, "E": {k: x.cpu() for k, x in state.items()}, "F": {k: x.detach().cpu() for k, x in m.state_dict().items()},
                    "networks": res["networks"], "meta": res}, os.path.join(OUT, f"atlas_{a.tag}_s{a.seed}.pt"))
        log("PRETRAIN " + json.dumps(res, default=float))
        return

    os.makedirs(OUT, exist_ok=True)
    sF = {k: x.detach().cpu().clone() for k, x in m.state_dict().items()}
    fF = forecasts(m, nets, O)
    m.load_state_dict(state); fE = forecasts(m, nets, O)
    save = {}
    if fP is not None:
        res["P"] = dict(zip(("test_S", "test_U"), test_mae(fP, nets, O)))
        log(f"TEST P seed {a.seed} (pre-trained only, never trained on {a.only or 'these networks'}): trained stations "
            f"{res['P']['test_S']:.2f}, unseen {res['P']['test_U']:.2f}")
        for (net, nm), arr in fP.items():
            save[f"{net}|P_{nm}"] = arr
    for k, f in (("E", fE), ("F", fF)):
        res[k]["test_S"], res[k]["test_U"] = test_mae(f, nets, O)
        log(f"TEST {k} seed {a.seed} (one model, uncalibrated, all networks pooled): trained stations {res[k]['test_S']:.2f}, unseen "
            f"{res[k]['test_U']:.2f}; validation {res[k]['val_MAE']:.3f}; steps {res[k]['steps']}")
        for (net, nm), arr in f.items():
            save[f"{net}|{k}_{nm}"] = arr
    res["minutes_total"] = round((time.time() - T0) / 60, 1)
    np.savez_compressed(os.path.join(OUT, f"{a.tag}_s{a.seed}.npz"), meta=np.array(json.dumps(res, default=float)), **save)
    torch.save({"cfg": m.cfg, "E": {k: x.cpu() for k, x in state.items()}, "F": sF, "networks": res["networks"]},
               os.path.join(OUT, f"atlas_{a.tag}_s{a.seed}.pt"))
    log("INDIA-RUN " + json.dumps(res, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=400)
    ap.add_argument("--size", type=int, default=1_000_000)
    ap.add_argument("--steps", type=int, default=60000)
    ap.add_argument("--every", type=int, default=2000)
    ap.add_argument("--patience", type=int, default=6)
    ap.add_argument("--cap", type=float, default=420, help="minutes of training")
    ap.add_argument("--skip", default="", help="networks to leave out, comma-separated (e.g. Delhi)")
    ap.add_argument("--tag", default="india", help="name of the output files")
    ap.add_argument("--pretrain-only", action="store_true", help="save the weights only: no forecasts, no test window")
    ap.add_argument("--reforecast", action="store_true", help="forecast again from the saved weights (input fix of 2026-11-13)")
    ap.add_argument("--only", default="", help="ICML L1: train (adapt) on this one network only")
    ap.add_argument("--init", default="", help="ICML L1: start from these pre-trained weights (.pt, checkpoint E)")
    ap.add_argument("--lr-scale", type=float, default=1.0, help="multiplies the learning rate (adaptation: 0.3)")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    reforecast(a) if a.reforecast else main(a)
