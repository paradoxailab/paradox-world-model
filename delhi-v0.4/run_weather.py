"""PWM-W v0.3: the Delhi weather league. Pure PWM-W (trained only on station observations) against the global
AI and physics weather models' real forecasts and the time-series foundation models, on the same stations, hours
and significance tests.

  python run_weather.py --league METAR      (needs data/raw/WX_METAR.npz; NWP_METAR.npz and E2_METAR.npz optional)
  python run_weather.py --league CPCB

Fixed rules (set before any test score was seen):
  * Model choice uses VALIDATION only: P0 (d=128, 3 layers) with seeds 0-2 gives the seed noise sigma; P1 (bigger),
    P2 (no graph), P3 (sparse experts) replace P0 only if their validation score is better by more than 2 sigma.
    The chosen setting is retrained with seeds 100-102; the entry "PWM-W" is the mean of the three.
  * Scored origins: every 6 hours of TEST (00/06/12/18 in the league's clock), all 24 hours ahead.
  * A global model is "beaten" on a variable only if PWM-W's MAE is significantly lower (Diebold-Mariano p<0.05
    AND day-block bootstrap 95% interval below zero) than BOTH its latest run (day0, generous to it) AND its latest
    run after a trailing 30-day local bias correction. Each comparison uses only hours where both have a value.
  * The hybrid (global forecasts issued >= 48 h earlier as extra inputs) is reported separately, never as PWM-W.
"""
import argparse, json, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from pw.leagues import TARGETS, SUFFIXES, HYBRID_INPUTS, DAY1_MAX_I
from pw.wdata import Wx, RAW, H
from pw import wtrain as WT
from pw import evaluate as EV

OUT = os.environ.get("PW_OUT", os.path.join(ROOT, "results"))
CACHE = os.environ.get("PW_CACHE", os.path.join(OUT, "cache"))
UNITS = {"AT": "deg C", "RH": "%", "WS": "m/s"}
BANDS = {"1-6h": slice(0, 6), "7-12h": slice(6, 12), "13-24h": slice(12, 24)}
VARIANTS = {
    "P0": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True),
    "P1": dict(d=192, layers=4, heads=6, ff=2, experts=0, use_graph=True),
    "P2": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=False),
    "P3": dict(d=128, layers=3, heads=4, ff=2, experts=4, use_graph=True),
    "P4": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, joint=True),   # + a second network
}
JOINT = {"METAR": "WMO", "WMO": "METAR"}       # same channels; the partner is used only before this league's VALIDATION
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def det(v):                                         # deterministic forecast -> degenerate quantiles
    return np.repeat(v[..., None], 3, -1)


def trailing_bias(F, Y, org, days=30, need=10):
    """F, Y [T, n, K]; bias for target hour o+i = mean over d=1..days of (F - Y)[o+i-24d] (all before o)."""
    E = F - Y
    W = len(org)
    i = np.arange(H)
    tt = org[:, None, None] + i[None, :, None] - 24 * np.arange(1, days + 1)[None, None]   # [W, H, days]
    tt = np.clip(tt, 0, len(E) - 1)
    e = E[tt]                                                                             # [W, H, days, n, K]
    with np.errstate(all="ignore"):
        cnt = np.isfinite(e).sum(2)
        b = np.where(cnt >= need, np.nanmean(e, 2), 0.0)                                  # [W, H, n, K]
    return b.transpose(0, 2, 3, 1)                                                        # [W, n, K, H]


def gather(F, org):
    """F [T, n, K] -> [W, n, K, H] at target hours o .. o+23."""
    tt = np.clip(org[:, None] + np.arange(H)[None], 0, len(F) - 1)
    return F[tt].transpose(0, 2, 3, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="WMO")
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--opponents", default="chronos2,tfm25,tfm3")
    ap.add_argument("--e2_only", action="store_true", help="re-score only the Earth-2 runs from saved predictions")
    a = ap.parse_args()
    if a.e2_only:
        return e2_only(a.league)
    os.makedirs(OUT, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
    tag = a.league.lower()
    t_all = time.time()
    D = Wx(a.league, hybrid=False)
    log(D.describe())
    tr = D.origins("train", 1)
    va = D.origins("val", 6)
    te = D.origins("test", 1)
    te = te[D.tod[te] % 6 == 0]
    log(f"origins: train {len(tr)}, validation {len(va)}, test {len(te)} (every 6 h); device {WT.DEV}")

    # ---------------- second network for joint training (P4) ----------------
    extra = None
    partner = JOINT.get(a.league)
    if partner and os.path.exists(os.path.join(RAW, f"WX_{partner}.npz")):
        D2 = Wx(partner)
        cut = int((D.dates[D.bounds["val"][0]] - D2.start).astype(int))         # partner hours before our VALIDATION
        o2 = np.concatenate([D2.origins(sp, 1) for sp in ("train", "val", "test")])
        o2 = o2[o2 + H <= cut]
        if len(o2) > 1000 and D2.Ca == D.Ca:
            extra = [(D2, o2)]
            log(f"joint-training partner {partner}: {D2.N} stations, {len(o2)} origins ending before {D.dates[D.bounds['val'][0]]}")

    # ---------------- pure PWM-W: validation-only choice ----------------
    res = {"league": a.league, "stations": D.stations, "variants": {}}
    vals = {}
    for name, cfg in VARIANTS.items():
        if cfg.get("joint") and not extra:
            continue
        seeds = (0, 1, 2) if name == "P0" else (0,)
        for s in seeds:
            log(f"variant {name} seed {s}: {cfg}")
            m, info = WT.train(dict(cfg), D, tr, None, va, a.steps, seed=s, log=log,
                               extra=extra if cfg.get("joint") else None)
            vals.setdefault(name, []).append(info["val_score"])
            res["variants"].setdefault(name, []).append(info)
    sig = float(np.std(vals["P0"], ddof=1))
    p0 = float(np.mean(vals["P0"]))
    others = [n for n in vals if n != "P0"]
    better = [n for n in others if p0 - vals[n][0] > 2 * sig]
    best = min(better, key=lambda n: vals[n][0]) if better else "P0"
    log(f"validation (MAE / spread): P0 {p0:.4f} +- {sig:.4f}; " +
        ", ".join(f"{k} {vals[k][0]:.4f}" for k in others) + f" -> chosen {best}")
    res["choice"] = {"sigma": sig, "P0_mean": p0, "chosen": best, "val": vals}
    cfg = dict(VARIANTS[best])
    finals, qv = [], []
    for s in (100, 101, 102):
        m, info = WT.train(dict(cfg), D, tr, None, va, a.steps, seed=s, log=log,
                           extra=extra if cfg.get("joint") else None)
        finals.append(m)
        res.setdefault("final", []).append(info)
    qs, ys = zip(*[WT.predict(m, D, te) for m in finals])
    q_pw, Y = np.mean(qs, 0), ys[0]                                       # [W, n, K, H, 3]
    qvs, yv = zip(*[WT.predict(m, D, va) for m in finals])
    q_v, yv = np.mean(qvs, 0), yv[0]
    cqr = [EV.fit_cqr(q_v[:, :, k], yv[:, :, k]) for k in range(D.K)]
    q_pw = np.stack([EV.apply_cqr(q_pw[:, :, k], cqr[k]) for k in range(D.K)], 2)
    torch.save({"cfg": cfg, "states": [m.state_dict() for m in finals], "stations": D.stations},
               os.path.join(OUT, f"pwm_w_weather_{tag}.pt"))

    entries = {"PWM-W (pure)": q_pw}
    kinds = {"PWM-W (pure)": "ours"}

    # ---------------- hybrid (reported separately) ----------------
    # H1: global forecasts (bias-corrected, newest run published before the origin) as extra inputs
    # H2: the same, and the base is their bias-corrected ensemble mean (MOS-style: the network learns a correction)
    Dh = Wx(a.league, hybrid=True)
    if Dh.NWP is not None:
        trh = Dh.origins("train", 1, need_nwp=True)
        log(f"hybrid: {Dh.Cn} global-forecast channels from {Dh.nwp_models}, {len(trh)} training origins from 2024")
        hcfg = dict(cfg, use_nwp=True)
        hcfg.pop("joint", None)
        hv = {}
        for hn, flag in (("H1", False), ("H2", True)):
            Dh.base_nwp = flag
            hv[hn] = WT.train(dict(hcfg), Dh, trh, None, va, a.steps, seed=0, log=log)[1]["val_score"]
        hbest = "H2" if hv["H1"] - hv["H2"] > 2 * sig else "H1"
        log(f"hybrid validation: H1 {hv['H1']:.4f}, H2 {hv['H2']:.4f} (2 sigma = {2 * sig:.4f}) -> {hbest}")
        res["hybrid_choice"] = {"val": hv, "chosen": hbest}
        Dh.base_nwp = hbest == "H2"
        hm = [WT.train(dict(hcfg), Dh, trh, None, va, a.steps, seed=s, log=log)[0] for s in (100, 101, 102)]
        qh = np.mean([WT.predict(m, Dh, te)[0] for m in hm], 0)
        qhv = np.mean([WT.predict(m, Dh, va)[0] for m in hm], 0)
        qh = np.stack([EV.apply_cqr(qh[:, :, k], EV.fit_cqr(qhv[:, :, k], yv[:, :, k])) for k in range(D.K)], 2)
        entries["PWM-W hybrid (uses global forecasts)"] = qh
        kinds["PWM-W hybrid (uses global forecasts)"] = "hybrid"

    # ---------------- baselines ----------------
    W = len(te)
    base_b, prof_b = [], []
    for i in range(0, W, 128):
        b = D.batch(te[i:i + 128], None, "cpu")
        base_b.append(b["base"].numpy()); prof_b.append((b["prof"] * D.sd[None, None, :, None] + b["m7"][..., None]).numpy())
    entries["Baseline: daily cycle + latest anomaly"] = det(np.concatenate(base_b))
    entries["Baseline: last 14 days' daily cycle"] = det(np.concatenate(prof_b))
    Yfull = D.Y
    entries["Baseline: same hour yesterday"] = det(gather(np.concatenate([np.full((24,) + Yfull.shape[1:], np.nan), Yfull])[:len(Yfull)], te))
    for k in list(entries):
        kinds.setdefault(k, "baseline")

    # ---------------- global weather models (archived real forecasts) ----------------
    nwp_meta = {}
    p = os.path.join(RAW, f"NWP_{a.league}.npz")
    if os.path.exists(p):
        z = np.load(p)
        if "score" in z.files:
            col = z["col"][D.keep]
            Fs, t0 = z["score"][:, col], int(z["score_t0"])                               # [Tw, n, M, S, K]
            nwp_meta = json.loads(str(z["meta"]))
            sfx = [str(s) for s in z["suffixes"]]
            sel = (np.arange(H) <= DAY1_MAX_I)[None, None, None, :]
            ens_v, ens_n = 0.0, 0
            for mi, nm in enumerate([str(s) for s in z["score_models"]]):
                Fm = {}
                for si, sname in enumerate(sfx):
                    F = np.full((D.T + 2 * H, D.N, D.K), np.nan, np.float32)
                    n_ = min(len(Fs), len(F) - t0)
                    F[t0:t0 + n_] = Fs[:n_, :, mi, si]
                    Fm[sname] = F
                if not np.isfinite(Fm["day0"]).any():
                    continue
                # latest run: often issued after the origin (generous to the global model)
                v0 = gather(Fm["day0"], te)
                b0 = trailing_bias(Fm["day0"][:D.T], Yfull, te)
                # newest run published before the origin: day1 for hours 0..16, day2 after (operationally fair)
                v1, v2 = gather(Fm["day1"], te), gather(Fm["day2"], te)
                b1, b2 = trailing_bias(Fm["day1"][:D.T], Yfull, te), trailing_bias(Fm["day2"][:D.T], Yfull, te)
                va_ = np.where(sel, v1, v2)
                ba_ = np.where(sel, b1, b2)
                for lab, v, b in ((f"{nm} [latest run]", v0, b0), (f"{nm} [issued before forecast start]", va_, ba_)):
                    if np.isfinite(v).mean() < 0.05:
                        continue
                    entries[lab], kinds[lab] = det(v), "global"
                    entries[lab + " + local bias correction"], kinds[lab + " + local bias correction"] = det(v - b), "global"
                if nm in HYBRID_INPUTS:
                    vb = va_ - ba_
                    ok_ = np.isfinite(vb)
                    ens_v = ens_v + np.where(ok_, vb, 0.0)
                    ens_n = ens_n + ok_
            if np.any(ens_n):
                ens = np.where(ens_n > 0, ens_v / np.maximum(ens_n, 1), np.nan).astype(np.float32)
                lab = "Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start)"
                entries[lab], kinds[lab] = det(ens), "global-ensemble"
    else:
        log("no archived global forecasts found (NWP file missing)")

    # ---------------- time-series foundation models ----------------
    from pw import opponents as OPP
    fm_meta = {}
    for m in finals:                                   # free the GPU for the foundation models
        m.cpu()
    if Dh.NWP is not None:
        for m in hm:
            m.cpu()
    torch.cuda.empty_cache()
    for key in [k for k in a.opponents.split(",") if k]:
        f = os.path.join(CACHE, f"wx_{tag}_{key}.npz")
        try:
            if os.path.exists(f):
                zz = np.load(f); q, meta = zz["q"], json.loads(str(zz["meta"]))
            else:
                qq = []
                for k in range(D.K):
                    y = np.concatenate([Yfull[:, :, k], np.full((H, D.N), np.nan, np.float32)])
                    for chunk in (4096, 1024, 256):
                        try:
                            qk, meta = OPP.run(key, y, te, np.arange(D.N), H, ctx=512, chunk=chunk, log=log)
                            break
                        except torch.cuda.OutOfMemoryError:
                            torch.cuda.empty_cache()
                            log(f"    {key}: out of GPU memory at chunk {chunk}, retrying smaller")
                    qq.append(qk)
                q = np.stack(qq, 2)                                                       # [W, n, K, H, 3]
                np.savez_compressed(f, q=q, meta=np.array(json.dumps(meta)))
            entries[meta["name"]] = q
            kinds[meta["name"]] = "tsfm"
            fm_meta[key] = meta
        except Exception as e:
            log(f"opponent {key}: NOT RUN ({str(e)[:200]})")
        torch.cuda.empty_cache()

    # ---------------- scoring ----------------
    obs = np.isfinite(Y)
    table, tests, verdicts = {}, {}, {}
    for name, q in entries.items():
        have = np.isfinite(q[..., 1])
        table[name] = {"kind": kinds[name]}
        for k, v in enumerate(TARGETS):
            m = obs[:, :, k] & have[:, :, k]
            cov = float(m.sum() / max(obs[:, :, k].sum(), 1))
            if cov < 0.05:
                continue
            yk = np.where(m, Y[:, :, k], np.nan)
            sc = EV.score(q[:, :, k], yk, horizons=(), floor=1e9, step_min=60)
            row = {"MAE": sc["MAE"], "RMSE": sc["RMSE"], "coverage": round(cov, 3)}
            if kinds[name] in ("ours", "hybrid", "tsfm"):
                row.update(QL=sc["QL"], COV80=sc["COV80"])
            for bn, sl in BANDS.items():
                mb = m[..., sl]
                row[f"MAE {bn}"] = float(np.abs(q[:, :, k, sl, 1] - np.nan_to_num(Y[:, :, k, sl]))[mb].mean()) if mb.any() else None
            table[name][v] = row
    per_day = 4
    for ours in [n for n in entries if kinds[n] in ("ours", "hybrid")]:
        for name, q in entries.items():
            if name == ours:
                continue
            for k, v in enumerate(TARGETS):
                m = obs[:, :, k] & np.isfinite(q[:, :, k, :, 1]) & np.isfinite(entries[ours][:, :, k, :, 1])
                if m.sum() / max(obs[:, :, k].sum(), 1) < 0.05:
                    continue
                yk = np.where(m, Y[:, :, k], np.nan)
                r = {"all": EV.compare(entries[ours][:, :, k], q[:, :, k], yk, per_day, "MAE")}
                if kinds[name] == "global" and "bias" not in name:
                    for bn, sl in BANDS.items():
                        yb = np.full_like(yk, np.nan); yb[..., sl] = yk[..., sl]
                        r[bn] = EV.compare(entries[ours][:, :, k], q[:, :, k], yb, per_day, "MAE")
                tests.setdefault(ours, {}).setdefault(name, {})[v] = r
    # headline verdicts against each global system, under two rules (both pre-set, both reported):
    #   STRICT: significantly better than its latest run AND its latest run + bias correction (latest runs are
    #           often issued after the origin, so this is generous to the global model)
    #   ISSUED-BEFORE-START: the same against the newest run published before the origin (+ bias correction)
    for ours in tests:
        for nm in sorted({n.split(" [")[0] for n in entries if kinds[n] == "global"}):
            for v in TARGETS:
                for rule, tag_ in (("STRICT", "latest run"), ("ISSUED-BEFORE-START", "issued before forecast start")):
                    a0 = tests[ours].get(f"{nm} [{tag_}]", {}).get(v, {}).get("all")
                    a1 = tests[ours].get(f"{nm} [{tag_}] + local bias correction", {}).get(v, {}).get("all")
                    if not a0 or not a1:
                        continue
                    vd = "BEATS" if a0["verdict"] == "WIN" and a1["verdict"] == "WIN" else \
                         ("LOSES TO" if "LOSS" in (a0["verdict"], a1["verdict"]) else "TIES / MIXED")
                    verdicts.setdefault(ours, {}).setdefault(rule, {}).setdefault(nm, {})[v] = {
                        "verdict": vd, "vs_raw_pct": round(a0["rel_diff_pct"], 1), "vs_bc_pct": round(a1["rel_diff_pct"], 1)}
                    log(f"RESULT {a.league} [{rule}] {ours} vs {nm} on {v}: {vd} (MAE {a0['rel_diff_pct']:+.1f}% vs raw, "
                        f"{a1['rel_diff_pct']:+.1f}% vs bias-corrected)")
        for opp, per in tests[ours].items():
            if kinds.get(opp) in ("tsfm", "global-ensemble", "baseline", "hybrid", "ours"):
                for v, r in per.items():
                    t = r.get("all")
                    if t:
                        log(f"RESULT {a.league} {ours} vs {opp} on {v}: {t['verdict']} (MAE {t['rel_diff_pct']:+.1f}%, "
                            f"p={t['p']:.2g}, 95% CI {t['ci95_pct'][0]:+.1f}..{t['ci95_pct'][1]:+.1f}%)")

    np.savez_compressed(os.path.join(OUT, f"wx_{tag}_preds.npz"), te=te, Y=Y, q_pw=q_pw, keep=D.keep)
    e2 = earth2(D, te, Y, q_pw, a.league)

    # ---------------- live forecast ----------------
    qlive = np.mean([WT.predict(m.to(WT.DEV), D, np.array([D.T]))[0] for m in finals], 0)[0]
    live = {"first_hour": str(D.dates[D.T]), "timezone": "UTC" if a.league in ("METAR", "WMO") else "Asia/Kolkata",
            "stations": D.stations, "targets": TARGETS,
            "q10_q50_q90": np.round(qlive, 2).tolist()}
    json.dump(live, open(os.path.join(OUT, f"wx_forecast_{tag}.json"), "w"))

    res.update(table=table, tests=tests, verdicts=verdicts, earth2=e2, nwp_identifiers=nwp_meta,
               foundation_models=fm_meta, minutes=round((time.time() - t_all) / 60, 1), log=LOG)
    json.dump(res, open(os.path.join(OUT, f"wx_{tag}_results.json"), "w"), indent=1, default=float)
    report(res, a.league, tag)
    log(f"done in {res['minutes']} min")


def earth2(D, te, Y, q_pw, league):
    """Models we ran ourselves: 00 UTC starts, read at +6/12/18 h. Each is also scored after removing its mean
    error per station, lead and variable computed on the TEST days themselves (generous to it)."""
    e2 = {}
    p2 = os.path.join(RAW, f"E2_{league}.npz")
    if not os.path.exists(p2):
        log("no Earth-2 runs found (E2 file missing)")
        return e2
    z2 = np.load(p2)
    meta2 = json.loads(str(z2["meta"])) if "meta" in z2.files else {}
    obs = np.isfinite(Y)
    pos = {int(o): i for i, o in enumerate(te)}
    for key in [f[:-2] for f in z2.files if f.endswith("_v")]:
        V = z2[f"{key}_v"][:, D.keep]
        o_e = [int((np.datetime64(str(d)).astype("datetime64[h]") - D.start).astype(int)) for d in z2[f"{key}_days"]]
        sel = [(j, pos[o]) for j, o in enumerate(o_e) if o in pos]
        if len(sel) < 10:
            continue
        jj, ww = map(np.array, zip(*sel))
        qe = np.full((len(ww), D.N, D.K, H), np.nan, np.float32)
        for li, ld in enumerate((6, 12, 18)):
            qe[:, :, :, ld] = V[jj, :, li, :]
        with np.errstate(all="ignore"):
            bias = np.nanmean(qe - np.where(obs[ww], Y[ww], np.nan), 0, keepdims=True)
        qb = qe - np.nan_to_num(bias)
        nm = meta2.get("models", {}).get(key, {}).get("name", key)
        for k, v in enumerate(TARGETS):
            m = obs[ww][:, :, k] & np.isfinite(qe[:, :, k])
            if m.sum() < 100:
                continue
            yk = np.where(m, Y[ww][:, :, k], np.nan)
            r0 = EV.compare(q_pw[ww][:, :, k], det(qe[:, :, k]), yk, 1, "MAE")
            r1 = EV.compare(q_pw[ww][:, :, k], det(qb[:, :, k]), yk, 1, "MAE")
            mae = lambda q: float(np.abs(q - np.nan_to_num(Y[ww][:, :, k]))[m].mean())
            vd = "BEATS" if r0 and r1 and r0["verdict"] == r1["verdict"] == "WIN" else \
                 ("LOSES TO" if r0 and r1 and "LOSS" in (r0["verdict"], r1["verdict"]) else "TIES / MIXED")
            e2.setdefault(nm, {})[v] = {"days": int(len(ww)), "MAE PWM-W": mae(q_pw[ww][:, :, k, :, 1]),
                                        "MAE model": mae(qe[:, :, k]), "MAE model bias-removed": mae(qb[:, :, k]),
                                        "test": r0, "test_bias_removed": r1, "verdict": vd}
            log(f"RESULT {league} PWM-W (pure) vs {nm} on {v} (+6/12/18 h, {len(ww)} days): {vd} (MAE "
                f"{mae(q_pw[ww][:, :, k, :, 1]):.3f} vs {mae(qe[:, :, k]):.3f}, bias-removed {mae(qb[:, :, k]):.3f} {UNITS[v]})")
    return e2


def e2_only(league):
    tag = league.lower()
    z = np.load(os.path.join(OUT, f"wx_{tag}_preds.npz"))
    D = Wx(league)
    assert np.array_equal(D.keep, z["keep"])
    res = json.load(open(os.path.join(OUT, f"wx_{tag}_results.json")))
    LOG.extend(res.get("log", []))
    res["earth2"] = earth2(D, z["te"], z["Y"], z["q_pw"], league)
    res["log"] = LOG
    json.dump(res, open(os.path.join(OUT, f"wx_{tag}_results.json"), "w"), indent=1, default=float)
    report(res, league, tag)


def report(res, league, tag):
    L = [f"# PWM-W v0.3 weather league: {league}", "", f"Stations: {len(res['stations'])}. "
         f"Chosen setting: {res['choice']['chosen']} (validation only). Test origins every 6 h, 24 h ahead.", ""]
    for v in TARGETS:
        L += [f"## {v} ({UNITS[v]})", "", "| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |",
              "|---|---|---|---|---|---|---|---|"]
        rows = [(n, r) for n, r in res["table"].items() if v in r]
        rows.sort(key=lambda x: x[1][v]["MAE"])
        f = lambda x: "-" if x is None else f"{x:.3f}"
        for n, r in rows:
            s = r[v]
            L.append(f"| {n} | {r['kind']} | {f(s['MAE'])} | {f(s['MAE 1-6h'])} | {f(s['MAE 7-12h'])} | "
                     f"{f(s['MAE 13-24h'])} | {f(s['RMSE'])} | {s['coverage']:.2f} |")
        L.append("")
    L += ["## Verdicts against the global weather models", "",
          "BEATS = significantly lower MAE than both the raw and the bias-corrected forecast. STRICT uses the latest run "
          "(often issued after our forecast start); ISSUED-BEFORE-START uses the newest run published before it.", ""]
    for ours, rules in res["verdicts"].items():
        for rule, d in rules.items():
            for nm, dv in d.items():
                L.append(f"- [{rule}] {ours} vs {nm}: " + "; ".join(
                    f"{v} {x['verdict']} ({x['vs_raw_pct']:+.1f}% / {x['vs_bc_pct']:+.1f}%)" for v, x in dv.items()))
    if res["earth2"]:
        L += ["", "## Models we ran ourselves (Earth2Studio, 00 UTC GFS start, +6/12/18 h)", ""]
        for nm, d in res["earth2"].items():
            for v, x in d.items():
                L.append(f"- {nm}, {v}: PWM-W {x['MAE PWM-W']:.3f} vs {x['MAE model']:.3f} (bias removed "
                         f"{x['MAE model bias-removed']:.3f}) {UNITS[v]} over {x['days']} days -> {x['verdict']}")
    L += ["", "Not tested: GenCast and WeatherNext (no public forecast archive; data needs a Google Cloud access "
          "request).", "", "## Log", "", "```", *LOG[-400:], "```"]
    open(os.path.join(OUT, f"wx_{tag}_report.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    main()
