"""Atlas-Live: the continuously updating model, replayed on real data (rules: atlas/README.md, "Atlas-Live").

The Delhi test period is walked through in time order; at every step only measurements that had already arrived are
used. Layers: 1 frozen Atlas v1.3; 2 + a daily bias and band correction from the trailing 30 days; 3 + a weekly
fine-tune that is kept only if it does better on the most recent week.

  python run_live.py            # needs DELHI_LONG.npz, atlas_long3_s*.pt, fusion_members_atlas.npz, opponents/tfm25.npz
"""
import argparse, glob, json, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
import run_atlas_delhi as R
import run_atlas_long as RL
import league_v2 as LV
from pw.ddata import SPD, FLOOR, RAW, DM
from pw import evaluate as E
from atlas.model import Atlas

H, OUT = R.H, R.OUT
BLOCKS = [(0, 6), (6, 12), (12, 24)]
TRAIL, SHRINK = 30, 50
log = LV.log
T0 = time.time()


def daily_correction(q, y, org, S, first_test):
    """q [W, N, H, 3] forecasts at origins org (time order), y [W, N, H] truth. For each origin, the correction is
    fitted on earlier origins whose targets ended before that origin's day began. Returns the corrected forecasts."""
    out = q.copy()
    day = org // SPD
    for d in np.unique(day[org >= first_test]):
        now = d * SPD
        past = np.where((org + H <= now) & (org >= now - TRAIL * SPD))[0]
        cur = np.where(day == d)[0]
        if len(past) < 8:
            continue
        err = q[past][..., 1] - y[past]                                         # [P, N, H]
        qp = q[past].copy()
        for a, b in BLOCKS:
            e = err[:, :, a:b]
            n = np.isfinite(e).sum((0, 2))
            with np.errstate(all="ignore"):
                bias = np.nan_to_num(np.nanmean(e, (0, 2))) * n / (n + SHRINK)   # [N]
            out[cur, :, a:b] -= bias[None, :, None, None]
            qp[:, :, a:b] -= bias[None, :, None, None]
        out[cur] = E.apply_cqr(np.maximum(out[cur], 0), E.fit_cqr(np.maximum(qp[:, S], 0), y[past][:, S]))
    return out


def main(a):
    q = a.quick
    D, te, va, va4 = LV.league()
    log(D.describe())
    S, U, ALL = D.seen, D.unseen, np.arange(D.N)
    pre = np.arange(te[0] - TRAIL * SPD, te[0], R.TEST_STRIDE)                  # the month before the test: history for layer 2
    if q:
        te = te[:60]
    org = np.concatenate([pre, te])
    y = R.truth(D, org, ALL)
    yt = y[len(pre):]
    files = list({os.path.basename(f): f for f in sorted(glob.glob(os.path.join(OUT, "**", "atlas_long3_s*.pt"), recursive=True) +
                                                       glob.glob("/kaggle/input/**/atlas_long3_s*.pt", recursive=True))}.values())
    models = []
    for f in files:
        ck = torch.load(f, map_location="cpu", weights_only=False)
        assert list(ck["stations"]) == list(D.stations)
        m = Atlas(**ck["cfg"]).to(R.DEV); m.load_state_dict(ck["B"]); models.append(m)
    log(f"Atlas v1.3: {len(models)} saved models; {len(pre)} warm-up origins, {len(te)} test origins")

    def fc(ms, o):
        f = np.zeros((len(o), D.N, H, 3), np.float32)
        f[:, S] = np.mean([R.predict(m, D, o, S) for m in ms], 0)
        f[:, U] = np.mean([R.predict(m, D, o, ALL)[:, U] for m in ms], 0)
        return np.sort(f, -1)

    sc = lambda qq, c: E.score(qq[:, c], yt[:, c], horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)
    RES = {"tracks": {}, "significance": {}, "weekly": []}
    P = {}

    def record(name, qq):
        P[name] = qq
        RES["tracks"][name] = {"S": sc(qq, S), "U": sc(qq, U)}
        log(f"TEST {name}: Track S MAE {RES['tracks'][name]['S']['MAE']:.2f}, Track U MAE {RES['tracks'][name]['U']['MAE']:.2f}")

    # ---------------------------------------------------------------- layer 1: frozen
    f1 = fc(models, org)
    fz = LV.find("fusion_members_atlas.npz")
    if fz and not q:
        z = np.load(fz)
        d = E.fit_cqr(z["qv"][:, S], R.truth(D, va4, S))
        L1 = "1 Frozen Atlas v1.3 (validation calibration)"
        record(L1, E.apply_cqr(f1[len(pre):], d))
        chk = (RES["tracks"][L1]["S"]["MAE"], RES["tracks"][L1]["U"]["MAE"])
        log(f"CHECK frozen reproduced {chk[0]:.2f} / {chk[1]:.2f} (recorded 28.91 / 25.56); largest difference from the saved forecasts "
            f"{float(np.abs(f1[len(pre):] - z['qt']).max()):.4f}")
        assert abs(chk[0] - 28.91) < 0.02 and abs(chk[1] - 25.56) < 0.02, "frozen Atlas v1.3 not reproduced"
    else:
        L1 = "1 Frozen Atlas v1.3 (uncalibrated)"; record(L1, f1[len(pre):])
    # ---------------------------------------------------------------- layer 2: daily correction
    L2 = "2 + daily correction (trailing 30 days)"
    record(L2, daily_correction(f1, y, org, S, te[0])[len(pre):])
    # ---------------------------------------------------------------- layer 3: weekly gated fine-tune
    f3 = f1.copy()
    week = 7 * SPD
    starts = np.arange(te[0], te[-1] + 1, week)
    lo_ok = max(DM * SPD, 7 * SPD) + R.L
    for wi, now in enumerate(starts):
        cand = np.arange(max(lo_ok, now - 9 * week), now - H + 1, R.TRAIN_STRIDE)   # every target hour is before `now`
        gate = cand[cand >= now - week]
        tr = RL.valid_origins(D, cand[cand + H <= now - week], 8)
        kept = []
        for k, m in enumerate(models):
            if len(tr) < 32 or len(gate) < 8:
                kept.append(None); continue
            info = RL.train(D, m, tr, gate, 1000 * wi + k, 20 if q else a.steps, f"week{wi}-m{k}", a.lr, 20, 10 if q else 50, 10)
            kept.append(dict(start=info["start_val_MAE"], best=info["val_MAE"], changed=bool(info["val_MAE"] < info["start_val_MAE"] - 1e-4)))
        ix = np.where((org >= now) & (org < now + week))[0]
        f3[ix] = fc(models, org[ix])                                            # forecasts of the coming week, written before its truth
        RES["weekly"].append(dict(week=wi, date=str(D.dates[now])[:10], train_windows=int(len(tr)), gate_windows=int(len(gate)), models=kept))
        log("WEEK " + json.dumps(RES["weekly"][-1], default=float))
    L3 = "3 + weekly gated fine-tune"
    record(L3, daily_correction(f3, y, org, S, te[0])[len(pre):])
    np.savez_compressed(os.path.join(OUT, "live_ledger.npz"), origins=org, issue_time=D.dates[org].astype("datetime64[h]").astype(str),
                        frozen=f1, weekly=f3, stations=np.array(D.stations))
    os.makedirs(LV.L2, exist_ok=True)
    # ---------------------------------------------------------------- tests
    ft = LV.find(os.path.join("opponents", "tfm25.npz"))
    if ft and not q:
        o = np.load(ft)
        record("TimesFM 2.5 (Google, zero-shot)", E.apply_cqr(o["qt"], E.fit_cqr(o["qv"][:, S], R.truth(D, va4, S))))
    pairs = [(L2, L1), (L3, L1), (L3, L2)] + [(x, "TimesFM 2.5 (Google, zero-shot)") for x in (L1, L2, L3) if "TimesFM 2.5 (Google, zero-shot)" in P]
    for A_, B_ in pairs:
        r = {t: {mm: E.compare(P[A_][:, c], P[B_][:, c], yt[:, c], R.PER_DAY, mm, reps=200 if q else 2000, floor=FLOOR["PM2.5"]) for mm in ("MAE", "QL")}
             for t, c in (("S", S), ("U", U))}
        RES["significance"][f"{A_} vs {B_}"] = r
        v = [r[t]["MAE"]["verdict"] if r[t]["MAE"] else "–" for t in ("S", "U")]
        claim = "BEATS" if v == ["WIN", "WIN"] else ("LOSES" if "LOSS" in v else "level")
        log(f"SIG {A_} vs {B_}: " + "; ".join(f"{t} {r[t]['MAE']['verdict']} {r[t]['MAE']['rel_diff_pct']:+.2f}% p={r[t]['MAE']['p']:.2g}" for t in ("S", "U") if r[t]["MAE"]) + f" -> {claim}")
    # by month: where does updating matter
    mon = D.dates[te].astype("datetime64[M]").astype(str)
    RES["by_month"] = {mo: {n: float(np.nanmean(np.abs(P[n][mon == mo][:, S][..., 1] - yt[mon == mo][:, S]))) for n in P} for mo in sorted(set(mon))}
    log("BY-MONTH (trained stations MAE) " + json.dumps(RES["by_month"], default=float))
    RES["minutes"] = round((time.time() - T0) / 60, 1)
    json.dump(RES, open(os.path.join(OUT, "live_results.json"), "w"), indent=1, default=float)
    log(f"done in {RES['minutes']} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--lr", type=float, default=1e-4)
    main(ap.parse_args())
