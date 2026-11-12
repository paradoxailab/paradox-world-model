"""Atlas-Delhi Fusion v1.0: Atlas and the open-licence foundation models forecast together (Delhi PM2.5, next 24 h).

Members (each forecasts the 10/50/90% quantiles of every station's next 24 hourly values):
  * Atlas, the 3-seed 1M-parameter ensemble saved by run_atlas_delhi.py (observations only, trained on Delhi);
  * TimesFM 2.5 (Google, Apache-2.0), Chronos-2 and Chronos-Bolt (Amazon, Apache-2.0), zero-shot, 512 h of history.
TimesFM 3.0 is never a member (non-commercial licence: evaluation only).

The fused forecast is a weighted average of the members' quantiles; weights are non-negative and sum to 1, on a
0.05 grid, one set for each lead block (hours 1-6, 7-12, 13-24) unless stated. Two ways of choosing them:
  STATIC   chosen once on the validation period (2025-05-03 .. 2025-07-02). Three families are compared by 5-fold
           blocked cross-validation on validation (equal weights; one set; one set per lead block) and the family with
           the lowest cross-validated MAE is refitted on all validation windows.
  ONLINE   re-chosen at the start of every test day from the forecasts of the previous 30 days whose 24 target hours
           were all observed before that day began (validation-period forecasts fill the first month). Nothing from
           the future of a forecast is used. The 80% band is calibrated on the same trailing windows.
Weights are fitted on the training stations only; the never-trained stations (Track U) reuse them.

Controls, same procedure: the three foundation models fused without Atlas. Every entry is scored once on the test
windows (2025-07-03 .. 2025-12-31, every 6 h) with pw/evaluate.py; paired Diebold-Mariano + day-block bootstrap.

  python fuse.py            # needs DELHI.npz, atlas_delhi.pt and opponents/*.npz (output of the atlas-delhi run)
"""
import argparse, glob, itertools, json, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import Delhi, SPD, FLOOR, TARGETS
from pw import evaluate as E
from atlas.model import Atlas
import run_atlas_delhi as R

OUT = R.OUT
H = R.H
BLOCKS = [(0, 6), (6, 12), (12, 24)]
TRAIL_DAYS = 30
FM_KEYS = ["tfm25", "chronos2", "chronos-bolt"]
RES = {"tracks": {}, "weights": {}, "significance": {}, "claims": {}, "checks": {}}
T0 = time.time()


def log(*a):
    print(*a, flush=True)


def save():
    os.makedirs(OUT, exist_ok=True)
    json.dump(RES, open(os.path.join(OUT, "fusion_results.json"), "w"), indent=1, default=float)


def find(name):
    hits = sorted(glob.glob(os.path.join(OUT, "**", name), recursive=True)) + \
           sorted(glob.glob(os.path.join("/kaggle/input", "**", name), recursive=True))
    return hits[0] if hits else None


# ------------------------------------------------------------------------------------------------ weights
def simplex(k, step=0.05):
    n = int(round(1 / step))
    g = [c for c in itertools.product(range(n + 1), repeat=k - 1) if sum(c) <= n]
    G = np.array([list(c) + [n - sum(c)] for c in g], np.float32) / n
    return G


def best_w(F, y, G, chunk=256):
    """F [cells, k] member medians, y [cells] truth (no NaN). The grid point with the lowest mean absolute error."""
    best, arg = np.inf, 0
    for i in range(0, len(G), chunk):
        e = np.abs(F @ G[i:i + chunk].T - y[:, None]).mean(0)
        j = int(e.argmin())
        if e[j] < best:
            best, arg = float(e[j]), i + j
    return G[arg], best


def cells(M, Y, wins, blk):
    """Member medians and truth of the given windows and lead block, observed cells only. M [k, W, n, H]."""
    a, b = blk
    y = Y[wins][:, :, a:b].reshape(-1)
    F = M[:, wins][:, :, :, a:b].reshape(M.shape[0], -1).T
    ok = np.isfinite(y)
    return F[ok], y[ok]


def fit_family(M, Y, wins, fam, G):
    """Weights [n_blocks, k] for one family on the given windows."""
    k = M.shape[0]
    if fam == "equal":
        return np.full((len(BLOCKS), k), 1.0 / k, np.float32)
    if fam == "one set":
        w, _ = best_w(*cells(M, Y, wins, (0, H)), G)
        return np.repeat(w[None], len(BLOCKS), 0)
    return np.stack([best_w(*cells(M, Y, wins, blk), G)[0] for blk in BLOCKS])


def fuse(Q, W):
    """Q [k, W, n, H, 3] member quantiles, W [n_blocks, k] or [W, n_blocks, k] -> fused quantiles [W, n, H, 3]."""
    out = np.zeros(Q.shape[1:], np.float32)
    for bi, (a, b) in enumerate(BLOCKS):
        w = W[..., bi, :]
        if w.ndim == 1:
            out[:, :, a:b] = np.tensordot(w, Q[:, :, :, a:b], 1)
        else:
            out[:, :, a:b] = np.einsum("wk,kwnhq->wnhq", w, Q[:, :, :, a:b])
    return np.sort(out, -1)


def mae(q, y):
    return float(np.nanmean(np.abs(q[..., 1] - y)))


def static_weights(Qv, Yv, G, name):
    """Family chosen by 5-fold blocked cross-validation on the validation windows (training stations)."""
    M = Qv[..., 1]
    Wn = M.shape[1]
    folds = np.array_split(np.arange(Wn), 5)
    cv = {}
    for fam in ("equal", "one set", "one set per lead block"):
        errs, cnt = 0.0, 0
        for f in folds:
            tr = np.setdiff1d(np.arange(Wn), np.arange(f[0] - 2, f[-1] + 3))     # purge 2 windows (24 h) each side
            W = fit_family(M, Yv, tr, fam, G)
            q = fuse(Qv[:, f], W)
            ok = np.isfinite(Yv[f])
            errs += float(np.abs(q[..., 1] - Yv[f])[ok].sum()); cnt += int(ok.sum())
        cv[fam] = errs / cnt
    fam = min(cv, key=cv.get)
    W = fit_family(M, Yv, np.arange(Wn), fam, G)
    RES["weights"][name] = dict(cv_MAE=cv, family=fam, weights=W.tolist())
    log(f"STATIC {name}: cross-validated MAE {json.dumps({k: round(v, 3) for k, v in cv.items()})} -> {fam}")
    return W


def online_weights(Qh, Yh, oh, te, G, name, members):
    """One set of weights per lead block per test day, from the trailing TRAIL_DAYS of finished forecasts.
    Qh [k, Wh, n, H, 3] / Yh / oh: every cached forecast window (validation then test), training stations.
    Returns weights [len(te), n_blocks, k] and the trailing-window CQR widths [len(te), H]."""
    M = Qh[..., 1]
    k = M.shape[0]
    Wt = np.zeros((len(te), len(BLOCKS), k), np.float32)
    Dq = np.zeros((len(te), H), np.float32)
    day = (te - te[0]) // SPD
    for d in np.unique(day):
        t0 = te[day == d][0]
        hist = np.where((oh <= t0 - H) & (oh > t0 - H - TRAIL_DAYS * SPD))[0]
        W = np.stack([best_w(*cells(M, Yh, hist, blk), G)[0] for blk in BLOCKS])
        Wt[day == d] = W
        Dq[day == d] = E.fit_cqr(fuse(Qh[:, hist], W), Yh[hist])
    months = {}
    for i, o in enumerate(te):
        months.setdefault(int((o - te[0]) // (30.4 * SPD)), []).append(Wt[i].mean(0))
    RES["weights"][name] = dict(members=members, by_30_days={str(m): np.mean(v, 0).tolist() for m, v in months.items()},
                                mean=Wt.mean((0, 1)).tolist())
    log(f"ONLINE {name}: mean weights " + ", ".join(f"{m} {w:.2f}" for m, w in zip(members, Wt.mean((0, 1)))))
    for m, v in months.items():
        log(f"   test days {int(m * 30.4) + 1}-{int((m + 1) * 30.4)}: " + ", ".join(f"{mm} {w:.2f}" for mm, w in zip(members, np.mean(v, 0))))
    return Wt, Dq


def apply_cqr_w(q, Dq):
    """Per-window CQR widths Dq [W, H]."""
    q = q.copy()
    d = Dq[:, None, :]
    q[..., 0] = np.maximum(q[..., 0] - d, 0)
    q[..., 2] = q[..., 2] + d
    q[..., 1] = np.clip(q[..., 1], q[..., 0], q[..., 2])
    return q


# ------------------------------------------------------------------------------------------------ main
def main(a):
    D = Delhi(targets=TARGETS, backbone=False, wxfc=False)
    log(D.describe())
    te, va = D.origins("test", R.TEST_STRIDE), D.origins("val", R.VAL_STRIDE)
    va4 = va[::4]
    S, U, ALL = D.seen, D.unseen, np.arange(D.N)
    yv, yt = R.truth(D, va4, ALL), R.truth(D, te, ALL)
    sc = lambda qq, yy: E.score(qq, yy, horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)

    # members -------------------------------------------------------------------------------------------
    Q = {}                                                   # name -> (validation [Wv, N, H, 3], test [Wt, N, H, 3])
    ck = torch.load(find("atlas_delhi.pt"), map_location="cpu", weights_only=False)
    assert list(ck["stations"]) == list(D.stations), "station list differs from the saved model's"
    models = []
    for st in ck["states"]:
        m = Atlas(**ck["cfg"]).to(R.DEV); m.load_state_dict(st); models.append(m)
    log(f"Atlas: {len(models)} saved models of {models[0].n_params():,} parameters")

    def atlas(org):
        out = np.zeros((len(org), D.N, H, 3), np.float32)
        out[:, S] = np.mean([R.predict(m, D, org, S) for m in models], 0)
        out[:, U] = np.mean([R.predict(m, D, org, ALL) for m in models], 0)[:, U]      # unseen: whole network as input
        return np.sort(out, -1)

    Q["Atlas"] = (atlas(va4), atlas(te))
    log(f"Atlas forecasts done, {time.time() - T0:.0f}s")
    names = {"tfm25": "TimesFM 2.5", "chronos2": "Chronos-2", "chronos-bolt": "Chronos-Bolt"}
    for key in FM_KEYS:
        f = find(os.path.join("opponents", key + ".npz"))
        if not f:
            log(f"  {key}: cached forecasts not found, left out"); continue
        z = np.load(f)
        if z["qt"].shape[:2] != (len(te), D.N) or z["qv"].shape[:2] != (len(va4), D.N):
            log(f"  {key}: cached shapes {z['qt'].shape} / {z['qv'].shape} do not match the windows, left out"); continue
        Q[names[key]] = (z["qv"].astype(np.float32), z["qt"].astype(np.float32))
    members = list(Q)
    fms = [m for m in members if m != "Atlas"]
    log(f"members: {members}")
    np.savez_compressed(os.path.join(OUT, "fusion_members_atlas.npz"), qv=Q["Atlas"][0], qt=Q["Atlas"][1],
                        val_origins=va4, test_origins=te)

    preds = {"S": {}, "U": {}}

    def record(name, q, extra=None):
        RES["tracks"][name] = {"S": sc(q[:, S], yt[:, S]), "U": sc(q[:, U], yt[:, U]), **(extra or {})}
        preds["S"][name], preds["U"][name] = q[:, S], q[:, U]
        log(f"TEST {name}: Track S MAE {RES['tracks'][name]['S']['MAE']:.2f}, Track U MAE {RES['tracks'][name]['U']['MAE']:.2f}")
        save()

    for m in members:                                        # each member alone, calibrated on validation (as before)
        d = E.fit_cqr(Q[m][0][:, S], yv[:, S])
        record(m + " alone", E.apply_cqr(Q[m][1], d), {"val_MAE": mae(Q[m][0][:, S], yv[:, S])})
    RES["checks"] = {m: RES["tracks"][m + " alone"]["S"]["MAE"] for m in members}

    # history used by the online rule: every cached window (validation, then test), training stations
    oh = np.concatenate([va4, te])
    Yh = np.concatenate([yv, yt])[:, S]

    def run(tag, group):
        G = simplex(len(group))
        Qv = np.stack([Q[m][0] for m in group]); Qt = np.stack([Q[m][1] for m in group])
        W = static_weights(Qv[:, :, S], yv[:, S], G, tag + " (static)")
        qv_f = fuse(Qv, W)
        d = E.fit_cqr(qv_f[:, S], yv[:, S])
        record(tag + " (static)", E.apply_cqr(fuse(Qt, W), d), {"val_MAE": mae(qv_f[:, S], yv[:, S]), "members": group})
        Qh = np.concatenate([Qv, Qt], 1)[:, :, S]
        Wt, Dq = online_weights(Qh, Yh, oh, te, G, tag + " (online)", group)
        record(tag + " (online)", apply_cqr_w(fuse(Qt, Wt), Dq), {"members": group})

    run("Atlas-Delhi Fusion", members)
    if len(fms) >= 2:
        run("Foundation models only", fms)
    for m in fms:                                            # each foundation model with the same trailing calibration
        Qh = np.concatenate([Q[m][0], Q[m][1]])[:, S]
        day = (te - te[0]) // SPD
        Dq = np.zeros((len(te), H), np.float32)
        for dd in np.unique(day):
            t0 = te[day == dd][0]
            hist = np.where((oh <= t0 - H) & (oh > t0 - H - TRAIL_DAYS * SPD))[0]
            Dq[day == dd] = E.fit_cqr(Qh[hist], Yh[hist])
        record(m + " alone, trailing calibration", apply_cqr_w(Q[m][1], Dq))

    # significance --------------------------------------------------------------------------------------
    PRIMARY, SECOND = "Atlas-Delhi Fusion (online)", "Atlas-Delhi Fusion (static)"
    for final in (PRIMARY, SECOND):
        RES["significance"][final] = {}
        for t, cols in (("S", S), ("U", U)):
            RES["significance"][final][t] = {}
            for other, qo in preds[t].items():
                if other == final:
                    continue
                r = {mm: E.compare(preds[t][final], qo, yt[:, cols], R.PER_DAY, mm, reps=a.reps, floor=FLOOR["PM2.5"])
                     for mm in ("MAE", "RMSE", "QL")}
                RES["significance"][final][t][other] = r
                log(f"SIG {final} track {t} vs {other}: {r['MAE']['verdict']} {r['MAE']['rel_diff_pct']:+.2f}% p={r['MAE']['p']:.2g}"
                    f" | QL {r['QL']['verdict']} {r['QL']['rel_diff_pct']:+.2f}%")
    # the rules written before the run -------------------------------------------------------------------
    for final in (PRIMARY, SECOND):
        g = RES["significance"][final]
        c = {}
        for m in members:
            vS, vU = g["S"][m + " alone"]["MAE"]["verdict"], g["U"][m + " alone"]["MAE"]["verdict"]
            c[m] = "BEATS" if (vS, vU) == ("WIN", "WIN") else ("LOSES" if "LOSS" in (vS, vU) else
                                                               f"not beaten (training stations {vS}, unseen stations {vU})")
        ctrl = "Foundation models only " + ("(online)" if "online" in final else "(static)")
        if ctrl in g["S"]:
            v = g["S"][ctrl]["MAE"]
            c["Atlas adds information beyond the foundation models"] = (
                f"{'YES' if v['verdict'] == 'WIN' else 'NOT SHOWN'} (training stations {v['rel_diff_pct']:+.2f}%, p={v['p']:.2g}; "
                f"unseen stations {g['U'][ctrl]['MAE']['rel_diff_pct']:+.2f}%, p={g['U'][ctrl]['MAE']['p']:.2g})")
        RES["claims"][final] = c
        log("CLAIMS " + final + ": " + json.dumps(c))
    RES["primary"] = PRIMARY
    np.savez_compressed(os.path.join(OUT, "fusion_preds.npz"), qS_online=preds["S"][PRIMARY], qS_static=preds["S"][SECOND],
                        qU_online=preds["U"][PRIMARY], qU_static=preds["U"][SECOND], yS=yt[:, S], yU=yt[:, U],
                        test_origins=te, seen=S, unseen=U)
    RES["minutes_total"] = round((time.time() - T0) / 60, 1)
    save(); report()


def report():
    R_ = RES
    o = ["# Atlas-Delhi Fusion v1.0: results (generated from fusion_results.json)", ""]
    for t, title in (("S", "Track S: training stations"), ("U", "Track U: stations never trained on")):
        o += [f"## {title} (PM2.5, ug/m3, next 24 h)", "",
              "| Entry | MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | fusion (online) vs this | fusion (static) vs this |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for n, v in sorted(R_["tracks"].items(), key=lambda kv: kv[1][t]["MAE"]):
            s = v[t]
            cmp = []
            for final in ("Atlas-Delhi Fusion (online)", "Atlas-Delhi Fusion (static)"):
                g = R_["significance"].get(final, {}).get(t, {}).get(n, {}).get("MAE")
                cmp.append("–" if not g else f"{g['verdict']} {g['rel_diff_pct']:+.1f}% (p={g['p']:.2g})")
            o.append(f"| {n} | {s['MAE']:.2f} | {s['RMSE']:.2f} | {s['QL']:.2f} | {s['COV80']:.0f} | {s['MAE@1h']:.2f} | {s['MAE@6h']:.2f} | "
                     f"{s['MAE@12h']:.2f} | {s['MAE@24h']:.2f} | {cmp[0]} | {cmp[1]} |")
        o.append("")
    o += ["## Weights", ""]
    rd = lambda x: [rd(y) for y in x] if isinstance(x, (list, tuple)) else ({a: rd(b) for a, b in x.items()} if isinstance(x, dict)
                                                                            else (round(x, 3) if isinstance(x, float) else x))
    for k, v in R_["weights"].items():
        o.append(f"- {k}: " + json.dumps(rd(v), default=float))
    o += ["", "## Verdicts under the rules written before the run", ""]
    for k, v in R_["claims"].items():
        o += [f"**{k}**", ""] + [f"- {m}: {c}" for m, c in v.items()] + [""]
    open(os.path.join(OUT, "FUSION_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))
    log(f"done in {R_.get('minutes_total', 0)} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    main(ap.parse_args())
