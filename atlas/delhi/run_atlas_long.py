"""Atlas-Delhi v1.1 (stage 9): the same 1M-parameter Atlas, trained on all of Delhi's history.

One change from stage 7/8: the training data. DELHI_LONG.npz (tools/build_delhi_long.py) joins CPCB's earlier hourly
station measurements to the league file; training windows start in 2018, when most of Delhi's stations came online
(a window is used only if at least 8 training stations have 12 or more observed PM2.5 hours both in the last 24 h and
in the 24 target hours, which also skips the April-December 2023 gap). Stations, the seen / unseen split, inputs,
model, loss, validation and test windows are the league's, unchanged.

One seed per run (3 seeds = 3 notebooks in parallel). Each run makes two models:
  B  trained on every valid window since 2018; checkpoint = best validation MAE;
  C  B fine-tuned on the league's own 16 months at a fifth of the learning rate (drift: sensors and emissions change);
     if fine-tuning never improves validation, C is B.
It saves both models and their forecasts on the fusion's validation windows and on the test windows (every station:
training stations from the training-station graph, unseen stations from the whole network, as in stage 7).
Which of B / C is used, and whether it replaces the 16-month Atlas, is decided on validation in fuse.py.

  python tools/build_delhi_long.py && python run_atlas_long.py --seed 300
"""
import argparse, json, math, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import Delhi, SPD, FLOOR, TARGETS, DM, RAW
from pw import evaluate as E
import run_atlas_delhi as R

H, DEV, OUT = R.H, R.DEV, R.OUT
T0 = time.time()


def log(*a):
    print(*a, flush=True)


def valid_origins(D, org, min_st=8, min_h=12):
    obs = np.isfinite(D.Y[:, D.seen, 0])
    cs = np.concatenate([np.zeros((1, obs.shape[1])), np.cumsum(obs, 0)])
    fut, past = cs[org + H] - cs[org], cs[org] - cs[org - 24]
    return org[((fut >= min_h) & (past >= min_h)).sum(1) >= min_st]


def train(D, m, org, val_org, seed, max_steps, name, lr, cap_min, every, patience, bs=16, full=False):
    """R.train's loop (same loss, masking and optimiser) from a given model, with its own learning rate and caps.
    full=True (v1.2): the whole schedule is run. The checkpoint the early-stopping rule would have kept is remembered
    (recipe E) and returned; the model is left with the weights after the last step (recipe F), which validation never
    chose."""
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / 100) * (0.1 + 0.45 * (1 + math.cos(math.pi * min(1, s / max_steps)))))
    chw = torch.tensor([1.0] + [0.1] * (D.K - 1) + [0.05] * D.Ca, device=DEV)
    qs = torch.tensor([0.1, 0.5, 0.9], device=DEV)
    yv = R.truth(D, val_org, D.seen)
    v0 = float(np.nanmean(np.abs(R.predict(m, D, val_org, D.seen)[..., 1] - yv)))
    best, state, bad, t0, step = v0, {k: x.detach().clone() for k, x in m.state_dict().items()}, 0, time.time(), 0
    frozen, v = None, v0
    log(f"  {name} start val MAE {v0:.3f}; {len(org)} training windows, lr {lr}, up to {max_steps} steps")
    for step in range(1, max_steps + 1):
        b = R.make_batch(D, rng.choice(org, min(bs, len(org)), replace=False), D.seen)
        rate = torch.rand(b["mc"].shape[0], 1, 1, 1, device=DEV) * 0.4
        mc = b["mc"] * (torch.rand(b["mc"].shape, device=DEV) >= rate).float()
        q, rec, ex = R.forward(m, b, mc)
        e = b["yf"][..., None] - q
        w = b["of"] * chw
        loss = (torch.maximum(qs * e, (qs - 1) * e).mean(-1) * w).sum() / w.sum().clamp(min=1)
        hid = b["mc"] - mc
        loss = loss + 0.2 * (((rec - b["yc"]) ** 2) * hid * chw).sum() / (hid * chw).sum().clamp(min=1)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step(); sched.step()
        if step % every == 0 or step == max_steps:
            if frozen is not None and step % (5 * every) != 0 and step != max_steps:
                continue                                  # recipe E is fixed: look at validation less often
            v = float(np.nanmean(np.abs(R.predict(m, D, val_org, D.seen)[..., 1] - yv)))
            if frozen is None:
                if v < best - 1e-4:
                    best, bad, state = v, 0, {k: x.detach().clone() for k, x in m.state_dict().items()}
                else:
                    bad += 1
            log(f"  {name} step {step} val MAE {v:.3f} (best {best:.3f}{', E fixed at step ' + str(frozen) if frozen else ''}) {time.time() - t0:.0f}s")
            if frozen is None and bad >= patience:
                if not full:
                    break
                frozen = step
            if time.time() - t0 > cap_min * 60:
                break
    capped = bool(time.time() - t0 > cap_min * 60)
    if full:
        if step % every != 0 and step != max_steps:       # stopped by the time cap between two looks
            v = float(np.nanmean(np.abs(R.predict(m, D, val_org, D.seen)[..., 1] - yv)))
        info = dict(name=name, seed=seed, train_windows=len(org), minutes=round((time.time() - t0) / 60, 1), start_val_MAE=v0,
                    hit_time_cap=capped, E=dict(val_MAE=best, steps=frozen or step), F=dict(val_MAE=v, steps=step))
        log("RUN " + json.dumps(info, default=float))
        return info, state
    m.load_state_dict(state)
    info = dict(name=name, seed=seed, train_windows=len(org), steps=step, minutes=round((time.time() - t0) / 60, 1),
                start_val_MAE=v0, val_MAE=best, hit_time_cap=capped)
    log("RUN " + json.dumps(info, default=float))
    return info


def main(a):
    q = a.quick
    D = Delhi(path=os.path.join(RAW, "DELHI_LONG.npz"), targets=TARGETS, backbone=False, wxfc=False, first=a.first)
    log(D.describe()); log(f"device {DEV}; league hours start at index {D.league_offset}")
    te, va = D.origins("test", R.TEST_STRIDE), D.origins("val", R.VAL_STRIDE)
    va_fast, va4 = va[::2], va[::4]
    tr = D.origins("train", R.TRAIN_STRIDE)
    tr = valid_origins(D, tr[tr >= max(DM * SPD, 7 * SPD) + R.L], a.min_stations)
    tr_league = tr[tr >= D.league_offset + max(DM * SPD, 7 * SPD) + R.L]            # the league's own 16 months
    yr = D.dates[tr].astype("datetime64[Y]").astype(int) + 1970
    log(f"training windows: {len(tr)} valid since {a.first} ({len(tr_league)} of them in the league's 16 months); by year "
        + ", ".join(f"{y}: {int((yr == y).sum())}" for y in sorted(set(yr.tolist()))))
    S, U, ALL = D.seen, D.unseen, np.arange(D.N)
    if q:
        va, va_fast, va4, te = va[:24], va[:24:2], va[:24:4], te[:20]
    yv, yt = R.truth(D, va_fast, S), R.truth(D, te, ALL)
    res = dict(seed=a.seed, first=a.first, train_windows=int(len(tr)), league_windows=int(len(tr_league)), describe=D.describe())

    def forecasts(m):
        out = {}
        for nm, org in (("v4", va4), ("t", te)):
            f = np.zeros((len(org), D.N, H, 3), np.float32)
            f[:, S] = R.predict(m, D, org, S)
            f[:, U] = R.predict(m, D, org, ALL)[:, U]
            out[nm] = f
        return out

    def test_mae(f):
        e = np.abs(f["t"][..., 1] - yt)
        return float(np.nanmean(e[:, S])), float(np.nanmean(e[:, U]))

    torch.manual_seed(a.seed)
    m = R.build(D, a.size, 0)
    lr = 1e-3 if m.cfg["d"] <= 256 else 5e-4
    log(f"Atlas: {m.n_params():,} parameters, width {m.cfg['d']}")
    os.makedirs(OUT, exist_ok=True)
    save = {}
    if a.init:                                               # v1.3: start from weights trained on the rest of India
        import glob
        hits = sorted(glob.glob(a.init) + glob.glob(os.path.join("/kaggle/input", "**", os.path.basename(a.init)), recursive=True))
        assert hits, f"no checkpoint at {a.init}"
        ck = torch.load(hits[0], map_location="cpu", weights_only=False)
        assert all(ck["cfg"][k] == m.cfg[k] for k in m.cfg), "the pretrained model is not this model"
        assert "Delhi" not in ck["networks"], "the pretrained model has seen Delhi stations: Track U would not be clean"
        m.load_state_dict(ck[a.init_key])
        fP = forecasts(m)
        iP = dict(val_MAE=float(np.nanmean(np.abs(R.predict(m, D, va_fast, S)[..., 1] - yv))), steps=0)
        iP["test_S"], iP["test_U"] = test_mae(fP)
        log(f"TEST P seed {a.seed} (weights from the rest of India, no Delhi training; one model, uncalibrated): trained stations "
            f"{iP['test_S']:.2f}, unseen {iP['test_U']:.2f}; validation {iP['val_MAE']:.3f}")
        save.update(P_v4=fP["v4"], P_t=fP["t"])
        res.update(P=iP, pretrain=dict(file=os.path.basename(hits[0]), key=a.init_key, networks=ck["networks"],
                                       meta=ck.get("meta", {})), lr_b=a.lr_b)
    if a.full:                                               # v1.2: whole schedule; E = early-stopping rule, F = last step
        info, sE = train(D, m, tr, va_fast, a.seed, 80 if q else a.steps, f"F-s{a.seed}", lr, a.cap_b, 20 if q else a.every,
                         2 if q else a.patience, full=True)
        fF = forecasts(m); sF = {k: v.detach().cpu().clone() for k, v in m.state_dict().items()}
        m.load_state_dict(sE); fE = forecasts(m)
        for k, f in (("E", fE), ("F", fF)):
            info[k]["test_S"], info[k]["test_U"] = test_mae(f)
            log(f"TEST {k} seed {a.seed} (one model, uncalibrated): trained stations {info[k]['test_S']:.2f}, unseen {info[k]['test_U']:.2f}"
                f"; validation {info[k]['val_MAE']:.3f}; steps {info[k]['steps']}")
        res.update(E=info["E"], F=info["F"], params=m.n_params(), hit_time_cap=info["hit_time_cap"],
                   minutes_total=round((time.time() - T0) / 60, 1))
        np.savez_compressed(os.path.join(OUT, f"long2_s{a.seed}.npz"), meta=np.array(json.dumps(res, default=float)), val_origins=va4,
                            test_origins=te, E_v4=fE["v4"], E_t=fE["t"], F_v4=fF["v4"], F_t=fF["t"])
        torch.save({"cfg": m.cfg, "E": {k: v.cpu() for k, v in sE.items()}, "F": sF, "stations": D.stations, "first": a.first},
                   os.path.join(OUT, f"atlas_long2_s{a.seed}.pt"))
        log("LONG-RUN " + json.dumps(res, default=float))
        return
    iB = train(D, m, tr, va_fast, a.seed, 60 if q else a.steps, f"B-s{a.seed}", lr * a.lr_b, a.cap_b, 20 if q else a.every, a.patience)
    fB = forecasts(m); sB = {k: v.detach().cpu().clone() for k, v in m.state_dict().items()}
    iB["test_S"], iB["test_U"] = test_mae(fB)
    log(f"TEST B seed {a.seed} (one model, uncalibrated): trained stations {iB['test_S']:.2f}, unseen {iB['test_U']:.2f}")
    save.update(B_v4=fB["v4"], B_t=fB["t"])
    np.savez_compressed(os.path.join(OUT, f"{a.tag}_s{a.seed}.npz"), meta=np.array(json.dumps(dict(res, B=iB), default=float)), val_origins=va4,
                        test_origins=te, **save)
    iC = train(D, m, tr_league, va_fast, a.seed + 1000, 40 if q else a.ft_steps, f"C-s{a.seed}", lr * 0.2, a.cap_c, 20 if q else 100, 10)
    fC = forecasts(m)
    iC["test_S"], iC["test_U"] = test_mae(fC)
    log(f"TEST C seed {a.seed} (one model, uncalibrated): trained stations {iC['test_S']:.2f}, unseen {iC['test_U']:.2f}")
    save.update(C_v4=fC["v4"], C_t=fC["t"])
    res.update(B=iB, C=iC, params=m.n_params(), minutes_total=round((time.time() - T0) / 60, 1))
    np.savez_compressed(os.path.join(OUT, f"{a.tag}_s{a.seed}.npz"), meta=np.array(json.dumps(res, default=float)), val_origins=va4,
                        test_origins=te, **save)
    torch.save({"cfg": m.cfg, "B": sB, "C": {k: v.detach().cpu() for k, v in m.state_dict().items()}, "stations": D.stations,
                "first": a.first}, os.path.join(OUT, f"atlas_{a.tag}_s{a.seed}.pt"))
    log("LONG-RUN " + json.dumps(res, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=300)
    ap.add_argument("--first", default="2018-01-01")
    ap.add_argument("--size", type=int, default=1_000_000)
    ap.add_argument("--steps", type=int, default=24000)
    ap.add_argument("--every", type=int, default=400)
    ap.add_argument("--patience", type=int, default=10)
    ap.add_argument("--ft-steps", type=int, default=3000)
    ap.add_argument("--cap-b", type=float, default=330, help="minutes")
    ap.add_argument("--cap-c", type=float, default=60, help="minutes")
    ap.add_argument("--min-stations", type=int, default=8)
    ap.add_argument("--full", action="store_true", help="v1.2: whole schedule, recipes E and F")
    ap.add_argument("--init", default="", help="v1.3: start from this checkpoint (run_atlas_india.py --skip Delhi --pretrain-only)")
    ap.add_argument("--init-key", default="E")
    ap.add_argument("--lr-b", type=float, default=1.0, help="learning-rate factor for stage B (v1.3: 0.3)")
    ap.add_argument("--tag", default="long", help="name of the output files (v1.3: long3)")
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args())
