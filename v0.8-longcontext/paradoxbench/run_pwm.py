"""Score a PWM-Dyn v0.4 seed ensemble on ParadoxBench-1 (one task, one track), with validation-fitted
conformal calibration. Test data is touched exactly once, here.

  python paradoxbench/run_pwm.py --task PEMS08 --track B --versions v04-lc-s0 v04-lc-s1 v04-lc-s2
  python paradoxbench/run_pwm.py --task PEMS08 --track Z --source PEMS04 --versions v04-ind-s0 ...
"""
import argparse, json, os, sys
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from pwm.data import load, ROOT
from pwm.calibration import fit_cqr, apply_cqr
from paradoxbench.spec import TASKS, official_windows, validation_windows, hidden_sensors, replay_gaps, VAL_SEED
from paradoxbench.metrics import bench_score
from paradoxbench.score import record
from train import build, predict, DEV


def members(dsname, versions):
    out = []
    for v in versions:
        d = os.path.join(ROOT, "models", dsname, v)
        rep = json.load(open(f"{d}/report.json"))
        out.append((v, rep))
    return out


def ensemble(ds, mem, srcname, idx, drop=None, members_out=None, gaps=None):
    qs = []
    for v, rep in mem:
        m = build(ds, rep["config"])
        sd = torch.load(os.path.join(ROOT, "models", srcname, v, "weights.pt"), map_location="cpu")
        m.load_state_dict(sd)
        q10, q50, q90, y = predict(m.to(DEV).eval(), ds, idx, drop_nodes=drop, gaps=gaps)
        qs.append(np.stack([q10, q50, q90]))
        if members_out is not None:
            members_out[v] = q50
    q = np.sort(np.mean(qs, 0), axis=0)
    return q[0], q[1], q[2], y, sum(p.numel() for p in m.parameters())


def main(a):
    loader = TASKS[a.task][0]
    src = TASKS[a.source][0] if a.track == "Z" else loader
    mem = members(src, a.versions)
    cfg = mem[0][1]["config"]
    lc, prof = bool(cfg.get("lc")), bool(cfg.get("profile"))
    assert all(bool(r["config"].get("lc")) == lc for _, r in mem), "mixed ensemble"
    base = load(loader)                                   # lag-free: defines the official windows
    test_idx, val_idx = official_windows(base), validation_windows(base)
    if a.track == "Z":                                    # no target statistics, no target calibration
        sds = load(src, lc=lc, profile=prof)
        ds = load(loader, lc=lc, stats=(sds.mean, sds.std), profile=prof)
    else:
        sds = ds = load(loader, lc=lc, profile=prof)
    drop = hidden_sensors(ds.N) if a.track == "R" else None
    gt = gv = None
    if a.track == "G":                                    # 1.2: replayed real outages (validation: other draws)
        gt, aff_t = replay_gaps(base, test_idx)
        gv, aff_v = replay_gaps(base, val_idx, seed=VAL_SEED)

    # calibration on the validation split (source validation split for zero-shot transfer)
    cal_idx = validation_windows(load(src)) if a.track == "Z" else val_idx
    v10, v50, v90, vy, _ = ensemble(sds, mem, src, cal_idx, drop=None if a.track == "Z" else drop, gaps=gv)
    vvalid = sds.valid(vy)
    if a.track == "G":
        vvalid &= aff_v[:, None, :]
    if a.track == "R":
        keep = np.zeros(ds.N, bool); keep[drop] = True
        vvalid &= keep[None, None, :]
    delta = fit_cqr(sds, v10, v90, vy, vvalid)

    per = {}
    q10, q50, q90, y, nparam = ensemble(ds, mem, src, test_idx, drop=drop, members_out=per, gaps=gt)
    c10, c50, c90 = apply_cqr(ds, q10, q50, q90, delta)
    tag = f"PWM-Dyn {a.tag}{'-LC' if lc else ''}"
    name = {"A": tag, "B": tag, "R": tag, "G": tag,
            "Z": f"{tag} inductive (trained on {a.source} only)"}[a.track]
    name += f" ({len(mem)}-seed, CQR)"
    from paradoxbench.score import truth
    _, yt, valid = truth(a.task, a.track, base)
    raw = bench_score(q10, q50, q90, yt, valid)
    member_test = {v: {k: bench_score(None, p, None, yt, valid)[k] for k in ("MAE", "RMSE")} for v, p in per.items()}
    maes = np.array([m["MAE"] for m in member_test.values()])
    print(f"ParadoxBench-seeds {a.task}/{a.track} {a.tag}: single-model test MAE " +
          " ".join(f"{x:.3f}" for x in maes) + f" | mean {maes.mean():.3f} sd {maes.std(ddof=1) if len(maes) > 1 else 0:.3f}",
          flush=True)
    record(a.task, a.track, name, c10, c50, c90,
           {"type": "specialist (Paradox, trained from scratch)", "params": nparam,
            "context_steps": ds.context, "members": [v for v, _ in mem],
            "trained_on": f"{a.source if a.track == 'Z' else a.task} train split only",
            "calibration": {"method": "split-conformal CQR on validation", "delta_per_horizon": delta.tolist()},
            "member_test": member_test,
            "uncalibrated": {k: raw[k] for k in ("MAE", "IS80", "QL", "COV80", "WIDTH")}}, base)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=list(TASKS))
    ap.add_argument("--track", required=True, choices=list("ABRGZ"))
    ap.add_argument("--versions", nargs="+", required=True)
    ap.add_argument("--source", default="PEMS04")
    ap.add_argument("--tag", default="v0.4", help="model version label shown on the leaderboard")
    main(ap.parse_args())
