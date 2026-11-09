"""PWM-W v1.0 adds two steps after the model choice, each adopted only if > 2 sigma better on VALIDATION:
  (E) a two-family ensemble: the chosen setting averaged with the best passing setting of the other architecture family
      (graph encoder P4-P8 vs 21-day patch transformer P9-P10);
  (S) self-correction: the trailing 30-day correction the global models get (mean error at that station, lead and hour
      over the last 30 days, at least 10), applied to PWM-W's own forecasts issued before the origin. Pure and hybrid
      decide separately.

PWM-W v0.7 adds rolling weekly updates of the pure model (fine-tuned on data observed before each test week;
adopted only if > 2 sigma better on validation, simulated the same way).

PWM-W v0.6 (v0.3 league, v0.4 hybrid and issued-before-start rule, v0.5 H3, v0.6 cross-network training):
v0.6 lets the small CPCB network (16 months of training data) also learn from the 20-station WMO network's 4 years,
using only WMO hours before CPCB's validation period and normalisation statistics from those hours alone.

The Delhi weather league. Pure PWM-W (trained only on station observations) against the global
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
import argparse
import gc, json, os, sys, time

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
    "P5": dict(d=192, layers=4, heads=6, ff=2, experts=0, use_graph=True, joint=True),   # v0.6: P1 size + partner
    # v0.8: same data, used better (adopted only if > 2 sigma better than P0 on validation, like every variant)
    "P6": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, joint=True, longctx=True),  # 14-day encoder
    "P7": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, joint=True, ema=True),     # weight averaging
    "P8": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, joint=True, longctx=True, ema=True),
    # v0.9 PWM-X: 21-day patch transformer with per-window normalisation (+ self-supervised patch reconstruction)
    "P9": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, joint=True, xarch=True, ema=True),
    "P10": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, joint=True, xarch=True, ssl=True, ema=True),
    # v2.0 PWM-India: the India-wide corpus (WX_INDIA, 2015-2024-11) as an extra joint-training partner.
    #   P11 = P10 + the corpus (same 1.26M model: isolates the effect of data)
    #   P12 = 10.1M model (width 288, 6 graph layers, 8 heads, 4 patch layers), started from India-wide pretraining
    #         (pretrain_india.py) and fine-tuned with the corpus as partner
    "P11": dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, joint=True, xarch=True, ssl=True, ema=True,
                india=True),
    "P12": dict(d=288, layers=6, heads=8, ff=2, experts=0, use_graph=True, joint=True, xarch=True, ssl=True, ema=True,
                xlayers=4, india=True, pretrained=True, lr=7e-4),
}
JOINT = {"METAR": ["WMO"], "WMO": ["METAR"], "CPCB": ["WMO"]}   # partners: used only before this league's VALIDATION,
#   with their own normalisation statistics also computed only from before it; other channels matched by name
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


def self_bias(models, D, org, days=30, need=10, lo=0):
    """v1.0 self-correction: the same trailing correction the global models get, applied to PWM-W's own errors.
    For origin o and lead i, the mean error of PWM-W's forecasts issued at o-24d (d = 1..days) for the same lead,
    whose target hours o+i-24d all lie before o. Needs >= `need` such days, else 0. Returns [W, n, K, H]."""
    from pw.wdata import PD, SPD, LH
    floor = max(PD * SPD + LH, int(lo))
    req = np.unique(np.concatenate([org - 24 * d for d in range(1, days + 1)]))
    req = req[req >= floor]
    if len(req) == 0:
        return np.zeros((len(org), D.N, D.K, H), np.float32)
    outs = [WT.predict(m, D, req) for m in models]
    err = np.mean([o[0] for o in outs], 0)[..., 1] - outs[0][1]                          # [R, n, K, H]
    pos = {int(o): j for j, o in enumerate(req)}
    W = len(org)
    E = np.full((days, W) + err.shape[1:], np.nan, np.float32)
    for d in range(1, days + 1):
        for w, o in enumerate(org):
            j = pos.get(int(o) - 24 * d)
            if j is not None:
                E[d - 1, w] = err[j]
    with np.errstate(all="ignore"):
        cnt = np.isfinite(E).sum(0)
        b = np.where(cnt >= need, np.nanmean(E, 0), 0.0)
    return np.nan_to_num(b).astype(np.float32)


def EV_val(q, y, sd):
    """Validation score of an ensemble forecast: MAE of the median in units of each target's spread, averaged."""
    v = ~np.isnan(y)
    return float(np.mean([np.abs(q[:, :, k, :, 1] - np.nan_to_num(y[:, :, k]))[v[:, :, k]].mean() / sd[k]
                          for k in range(q.shape[2])]))


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
    ap.add_argument("--fm_only", action="store_true", help="re-score saved predictions against the foundation models")
    ap.add_argument("--variants", default="", help="comma list to run (P0 always); default all")
    ap.add_argument("--init", default="", help="v2.0: India-wide pretrained weights (pretrain_india.py) for P12")
    ap.add_argument("--no_v10", action="store_true", help="skip the v1.0 ensemble and self-correction steps")
    ap.add_argument("--rolling", type=int, default=0, help="v0.7 rolling updates (rejected on CPCB validation; off)")
    a = ap.parse_args()
    if a.fm_only:
        os.makedirs(CACHE, exist_ok=True)
        return fm_only(a)
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
    extra = []
    v0 = D.dates[D.bounds["val"][0]]
    for partner in JOINT.get(a.league, []):
        if not os.path.exists(os.path.join(RAW, f"WX_{partner}.npz")):
            continue
        st = np.load(os.path.join(RAW, f"WX_{partner}.npz"))["start"]
        cut = int((v0 - np.datetime64(str(st)).astype("datetime64[h]")).astype(int))   # partner hours before our VALIDATION
        D2 = Wx(partner, stats_until=cut)
        shared, shift = D2.align_to(D)
        o2 = np.concatenate([D2.origins(sp, 1) for sp in ("train", "val", "test")])
        o2 = np.unique(o2[o2 + H <= cut])
        if len(o2) > 1000:
            extra.append((D2, o2))
            log(f"joint-training partner {partner}: {D2.N} stations, {len(o2)} origins ending before {v0}; "
                f"shared other channels {shared}; clock shift {shift:+d} h")
    extra = extra or None
    # v2.0: the India-wide corpus as one more partner, for the variants that ask for it
    extra_india = list(extra or [])
    if os.path.exists(os.path.join(RAW, "WX_INDIA.npz")):
        st = np.load(os.path.join(RAW, "WX_INDIA.npz"))["start"]
        cut = int((v0 - np.datetime64(str(st)).astype("datetime64[h]")).astype(int))
        DI = Wx("INDIA", stats_until=cut)
        shared, shift = DI.align_to(D)
        oi = np.concatenate([DI.origins(sp, 1) for sp in ("train", "val", "test")])
        oi = np.unique(oi[oi + H <= cut])
        extra_india.append((DI, oi))
        log(f"India-wide corpus: {DI.N} stations, {len(oi)} origins ending before {v0} "
            f"(corpus ends {DI.start + np.timedelta64(DI.T - 1, 'h')}); shared other channels {shared}; clock shift {shift:+d} h")
    extra_india = extra_india or None
    init_ok = bool(a.init) and os.path.exists(a.init)
    if a.init and not init_ok:
        log(f"pretrained weights {a.init} not found: P12 is skipped")

    def partners(c):
        if not c.get("joint"):
            return None
        return extra_india if c.get("india") else extra

    def with_init(c):
        c = dict(c)
        if c.pop("pretrained", False):
            c["init"] = a.init
        c.pop("india", None)
        return c

    # ---------------- pure PWM-W: validation-only choice ----------------
    res = {"league": a.league, "stations": D.stations, "variants": {}}
    vals = {}
    only = set(x for x in a.variants.split(",") if x) | {"P0"} if a.variants else None
    for name, cfg in VARIANTS.items():
        if cfg.get("joint") and not extra:
            continue
        if cfg.get("india") and (extra_india is None or len(extra_india) == len(extra or [])):
            continue
        if cfg.get("pretrained") and not init_ok:
            continue
        if only is not None and name not in only:
            continue
        seeds = (0, 1, 2) if name == "P0" else (0,)
        for s in seeds:
            log(f"variant {name} seed {s}: {cfg}")
            m, info = WT.train(with_init(cfg), D, tr, None, va, a.steps, seed=s, log=log,
                               extra=partners(cfg))
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
        m, info = WT.train(with_init(cfg), D, tr, None, va, a.steps, seed=s, log=log,
                           extra=partners(cfg))
        finals.append(m)
        res.setdefault("final", []).append(info)
    qs, ys = zip(*[WT.predict(m, D, te) for m in finals])
    q_pw, Y = np.mean(qs, 0), ys[0]                                       # [W, n, K, H, 3]
    qvs, yv = zip(*[WT.predict(m, D, va) for m in finals])
    q_v, yv = np.mean(qvs, 0), yv[0]

    # ---------------- v0.7: rolling weekly updates, adopted only if > 2 sigma better on VALIDATION ----------------
    all_org = np.unique(np.concatenate([D.origins(sp, 1) for sp in ("train", "val", "test")]))
    if a.rolling:
        qr_v, _ = WT.rolling_predict(finals, cfg, D, va, all_org, steps=max(a.steps // 12, 5), log=log)
        s_frozen = EV_val(q_v, yv, D.sd)
        s_roll = EV_val(qr_v, yv, D.sd)
        adopt = s_frozen - s_roll > 2 * sig
        log(f"rolling validation (ensemble MAE / spread): frozen {s_frozen:.4f}, weekly updates {s_roll:.4f} "
            f"(2 sigma = {2 * sig:.4f}) -> {'ADOPTED' if adopt else 'not adopted'}")
        res["rolling"] = {"frozen": s_frozen, "rolling": s_roll, "adopted": bool(adopt)}
        if adopt:
            q_pw, _ = WT.rolling_predict(finals, cfg, D, te, all_org, steps=max(a.steps // 12, 5), log=log)
            q_v = qr_v
    # ---------------- v1.0 (E): two-family ensemble, adopted only if > 2 sigma better on VALIDATION ----------------
    fam = lambda n: "x" if VARIANTS[n].get("xarch") else "g"
    rest = sorted([n for n in better if n != best and fam(n) != fam(best)], key=lambda n: vals[n][0])
    res["ensemble"] = {"partner": None, "adopted": False}
    if rest and not a.no_v10:
        n2 = rest[0]
        cfg2 = dict(VARIANTS[n2])
        fin2 = [WT.train(with_init(cfg2), D, tr, None, va, a.steps, seed=s, log=log,
                         extra=partners(cfg2))[0] for s in (100, 101, 102)]
        q_v2 = np.mean([WT.predict(m, D, va)[0] for m in fin2], 0)
        s1, s2 = EV_val(q_v, yv, D.sd), EV_val((q_v + q_v2) / 2, yv, D.sd)
        adopt = s1 - s2 > 2 * sig
        log(f"v1.0 ensemble validation: {best} alone {s1:.4f}, {best}+{n2} {s2:.4f} (2 sigma = {2 * sig:.4f}) -> "
            f"{'ADOPTED' if adopt else 'not adopted'}")
        res["ensemble"] = {"partner": n2, "single": s1, "ensemble": s2, "adopted": bool(adopt)}
        if adopt:
            q_pw = (q_pw + np.mean([WT.predict(m, D, te)[0] for m in fin2], 0)) / 2
            q_v = (q_v + q_v2) / 2
            finals = finals + fin2
        else:
            del fin2
    # ---------------- v1.0 (S): self-correction from PWM-W's own trailing errors, validation decides ----------------
    res["self_correction"] = {"adopted": False}
    if not a.no_v10:
        bv, bt = self_bias(finals, D, va), self_bias(finals, D, te)
        s1, s2 = EV_val(q_v, yv, D.sd), EV_val(q_v - bv[..., None], yv, D.sd)
        adopt = s1 - s2 > 2 * sig
        log(f"v1.0 self-correction validation: raw {s1:.4f}, corrected {s2:.4f} (2 sigma = {2 * sig:.4f}) -> "
            f"{'ADOPTED' if adopt else 'not adopted'}")
        res["self_correction"] = {"raw": s1, "corrected": s2, "adopted": bool(adopt)}
        if adopt:
            q_v, q_pw = q_v - bv[..., None], q_pw - bt[..., None]
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
        hcfg = dict(with_init(cfg), use_nwp=True)
        hcfg.pop("joint", None)
        hv = {}
        # H3 (v0.5): H2 + further predictors from the same runs (cloud, radiation, dew point, pressure, wind dir.)
        designs = {"H1": (False, False), "H2": (True, False)}
        if Dh.Cx:
            designs["H3"] = (True, True)
        for hn, (flag, extra_) in designs.items():
            Dh.base_nwp = flag
            hv[hn] = WT.train(dict(hcfg, nwp_extra=extra_), Dh, trh, None, va, a.steps, seed=0, log=log)[1]["val_score"]
        hbest = "H1"                                           # each step must beat the current choice by > 2 sigma
        for hn in ("H2", "H3"):
            if hn in hv and hv[hbest] - hv[hn] > 2 * sig:
                hbest = hn
        log("hybrid validation: " + ", ".join(f"{k} {v:.4f}" for k, v in hv.items()) +
            f" (2 sigma = {2 * sig:.4f}) -> {hbest}")
        res["hybrid_choice"] = {"val": hv, "chosen": hbest}
        Dh.base_nwp, hx_ = designs[hbest]
        hm = [WT.train(dict(hcfg, nwp_extra=hx_), Dh, trh, None, va, a.steps, seed=s, log=log)[0] for s in (100, 101, 102)]
        qh = np.mean([WT.predict(m, Dh, te)[0] for m in hm], 0)
        qhv = np.mean([WT.predict(m, Dh, va)[0] for m in hm], 0)
        res["hybrid_self_correction"] = {"adopted": False}
        if not a.no_v10:
            lo_h = (Dh.nwp_from + 1) if getattr(Dh, "nwp_from", None) is not None else 0
            bv, bt = self_bias(hm, Dh, va, lo=lo_h), self_bias(hm, Dh, te, lo=lo_h)
            s1, s2 = EV_val(qhv, yv, D.sd), EV_val(qhv - bv[..., None], yv, D.sd)
            adopt = s1 - s2 > 2 * sig
            log(f"v1.0 hybrid self-correction validation: raw {s1:.4f}, corrected {s2:.4f} (2 sigma = {2 * sig:.4f})"
                f" -> {'ADOPTED' if adopt else 'not adopted'}")
            res["hybrid_self_correction"] = {"raw": s1, "corrected": s2, "adopted": bool(adopt)}
            if adopt:
                qhv, qh = qhv - bv[..., None], qh - bt[..., None]
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
    run_fms(a.opponents, tag, D, te, entries, kinds, fm_meta)

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

    extra_q = {"q_h": entries["PWM-W hybrid (uses global forecasts)"]} if "PWM-W hybrid (uses global forecasts)" in entries else {}
    np.savez_compressed(os.path.join(OUT, f"wx_{tag}_preds.npz"), te=te, Y=Y, q_pw=q_pw, keep=D.keep, **extra_q)
    e2 = earth2(D, te, Y, q_pw, a.league, entries.get("PWM-W hybrid (uses global forecasts)"))

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


def run_fms(opponents, tag, D, te, entries, kinds, fm_meta):
    """Time-series foundation models on exactly the scored windows. A model that cannot run is NOT RUN; a forecast
    is never reused across variables."""
    from pw import opponents as OPP
    for key in [k for k in opponents.split(",") if k]:
        f = os.path.join(CACHE, f"wx_{tag}_{key}_v6.npz")      # v0.6: older caches are not reused (see README)
        try:
            if os.path.exists(f):
                zz = np.load(f); q, meta = zz["q"], json.loads(str(zz["meta"]))
            else:
                qq = []
                for k in range(D.K):
                    y = np.concatenate([D.Y[:, :, k], np.full((H, D.N), np.nan, np.float32)])
                    qk = None
                    for chunk in (2048, 512, 128, 32):
                        try:
                            qk, meta = OPP.run(key, y, te, np.arange(D.N), H, ctx=512, chunk=chunk, log=log)
                            break
                        except torch.cuda.OutOfMemoryError:
                            gc.collect(); torch.cuda.empty_cache()
                            log(f"    {key}: out of GPU memory at chunk {chunk}, retrying smaller")
                    if qk is None:
                        raise RuntimeError(f"{key} ran out of GPU memory on {TARGETS[k]} at every chunk size")
                    qq.append(qk)
                    gc.collect(); torch.cuda.empty_cache()
                q = np.stack(qq, 2)                                                       # [W, n, K, H, 3]
                np.savez_compressed(f, q=q, meta=np.array(json.dumps(meta)))
            entries[meta["name"]] = q
            kinds[meta["name"]] = "tsfm"
            fm_meta[key] = meta
        except Exception as e:
            log(f"opponent {key}: NOT RUN ({str(e)[:200]})")
        torch.cuda.empty_cache()


def fm_only(a):
    """Re-score saved PWM-W test forecasts against the foundation models only (used when the FM step failed)."""
    tag = a.league.lower()
    z = np.load(os.path.join(OUT, f"wx_{tag}_preds.npz"))
    D = Wx(a.league)
    assert np.array_equal(D.keep, z["keep"])
    te, Y = z["te"], z["Y"]
    entries = {"PWM-W (pure)": z["q_pw"]}
    kinds = {"PWM-W (pure)": "ours"}
    if "q_h" in z.files:
        entries["PWM-W hybrid (uses global forecasts)"] = z["q_h"]; kinds["PWM-W hybrid (uses global forecasts)"] = "hybrid"
    fm_meta = {}
    run_fms(a.opponents, tag, D, te, entries, kinds, fm_meta)
    obs = np.isfinite(Y)
    tests = {}
    for ours in [n for n in entries if kinds[n] in ("ours", "hybrid")]:
        for name in [n for n in entries if kinds[n] == "tsfm"]:
            for k, v in enumerate(TARGETS):
                m = obs[:, :, k] & np.isfinite(entries[name][:, :, k, :, 1]) & np.isfinite(entries[ours][:, :, k, :, 1])
                yk = np.where(m, Y[:, :, k], np.nan)
                t = EV.compare(entries[ours][:, :, k], entries[name][:, :, k], yk, 4, "MAE")
                tests.setdefault(ours, {}).setdefault(name, {})[v] = {"all": t}
                mae = lambda q: float(np.abs(q[:, :, k, :, 1] - np.nan_to_num(Y[:, :, k]))[m].mean())
                log(f"RESULT {a.league} {ours} vs {name} on {v}: {t['verdict']} (MAE {t['rel_diff_pct']:+.1f}%, "
                    f"p={t['p']:.2g}, 95% CI {t['ci95_pct'][0]:+.1f}..{t['ci95_pct'][1]:+.1f}%; MAE {mae(entries[ours]):.3f} "
                    f"vs {mae(entries[name]):.3f})")
    p = os.path.join(OUT, f"wx_{tag}_results.json")
    res = json.load(open(p)) if os.path.exists(p) else {"league": a.league}
    for ours, d in tests.items():
        res.setdefault("tests", {}).setdefault(ours, {}).update(d)
    res["foundation_models"] = fm_meta
    res.setdefault("log", []).extend(LOG)
    json.dump(res, open(p, "w"), indent=1, default=float)


def earth2(D, te, Y, q_pw, league, q_h=None):
    """Score PWM-W (pure) and, when available, the hybrid against the Earth-2 runs."""
    e2 = {"PWM-W (pure)": _earth2_one(D, te, Y, q_pw, league, "PWM-W (pure)")}
    if q_h is not None:
        e2["PWM-W hybrid (uses global forecasts)"] = _earth2_one(D, te, Y, q_h, league, "PWM-W hybrid (uses global forecasts)")
    return e2


def _earth2_one(D, te, Y, q_pw, league, who):
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
            err = qe - np.where(obs[ww], Y[ww], np.nan)
            bias = np.nanmean(err, 0, keepdims=True)
            # operational version: trailing 30-day bias from this model's own earlier days (>= 10 needed)
            dd = np.array([o_e[j] for j in jj]) // 24
            tb = np.full_like(qe, np.nan)
            for r in range(len(ww)):
                prev = (dd < dd[r]) & (dd >= dd[r] - 30)
                if prev.sum() >= 10:
                    cnt = np.isfinite(err[prev]).sum(0)
                    tb[r] = np.where(cnt >= 10, np.nanmean(err[prev], 0), np.nan)
        qb = qe - np.nan_to_num(bias)
        qt = qe - tb                                                  # NaN where no trailing bias is available
        nm = meta2.get("models", {}).get(key, {}).get("name", key)
        for k, v in enumerate(TARGETS):
            m = obs[ww][:, :, k] & np.isfinite(qe[:, :, k])
            if m.sum() < 100:
                continue
            yk = np.where(m, Y[ww][:, :, k], np.nan)
            r0 = EV.compare(q_pw[ww][:, :, k], det(qe[:, :, k]), yk, 1, "MAE")
            r1 = EV.compare(q_pw[ww][:, :, k], det(qb[:, :, k]), yk, 1, "MAE")
            mae = lambda q: float(np.abs(q - np.nan_to_num(Y[ww][:, :, k]))[m].mean())
            mt = m & np.isfinite(qt[:, :, k])
            r2 = EV.compare(q_pw[ww][:, :, k], det(qt[:, :, k]), np.where(mt, Y[ww][:, :, k], np.nan), 1, "MAE") \
                if mt.sum() >= 100 else None
            maet = lambda q: float(np.abs(q - np.nan_to_num(Y[ww][:, :, k]))[mt].mean()) if mt.any() else float("nan")
            vd = "BEATS" if r0 and r1 and r0["verdict"] == r1["verdict"] == "WIN" else \
                 ("LOSES TO" if r0 and r1 and "LOSS" in (r0["verdict"], r1["verdict"]) else "TIES / MIXED")
            vt = "BEATS" if r0 and r2 and r0["verdict"] == r2["verdict"] == "WIN" else \
                 ("LOSES TO" if r0 and r2 and "LOSS" in (r0["verdict"], r2["verdict"]) else "TIES / MIXED")
            e2.setdefault(nm, {})[v] = {"days": int(len(ww)), "MAE PWM-W": mae(q_pw[ww][:, :, k, :, 1]),
                                        "MAE model": mae(qe[:, :, k]), "MAE model bias-removed": mae(qb[:, :, k]),
                                        "test": r0, "test_bias_removed": r1, "verdict": vd,
                                        "test_trailing_bias": r2, "verdict_trailing_bias": vt,
                                        "MAE PWM-W (trailing hours)": maet(q_pw[ww][:, :, k, :, 1]),
                                        "MAE model trailing-bias-corrected": maet(qt[:, :, k])}
            log(f"RESULT {league} {who} vs {nm} on {v} (+6/12/18 h, {len(ww)} days): "
                f"[oracle bias, test-period mean removed] {vd} (MAE {mae(q_pw[ww][:, :, k, :, 1]):.3f} vs raw "
                f"{mae(qe[:, :, k]):.3f}, oracle-debiased {mae(qb[:, :, k]):.3f}); [trailing 30-day bias, operational] "
                f"{vt} (MAE {maet(q_pw[ww][:, :, k, :, 1]):.3f} vs {maet(qt[:, :, k]):.3f}) {UNITS[v]}")
        if not any(np.isfinite(qe[:, :, k]).any() for k in range(D.K)):
            log(f"Earth-2 {nm}: {len(ww)} days stored but every value is missing (no usable forecast)")
    return e2


def e2_only(league):
    tag = league.lower()
    z = np.load(os.path.join(OUT, f"wx_{tag}_preds.npz"))
    D = Wx(league)
    assert np.array_equal(D.keep, z["keep"])
    res = json.load(open(os.path.join(OUT, f"wx_{tag}_results.json")))
    LOG.extend(res.get("log", []))
    res["earth2"] = earth2(D, z["te"], z["Y"], z["q_pw"], league, z["q_h"] if "q_h" in z.files else None)
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
        for who, models in res["earth2"].items():
            for nm, d in models.items():
                for v, x in d.items():
                    L.append(f"- {who} vs {nm}, {v}: {x['MAE PWM-W']:.3f} vs {x['MAE model']:.3f} raw, "
                             f"{x['MAE model bias-removed']:.3f} oracle-debiased -> {x['verdict']}; trailing-bias "
                             f"{x.get('MAE model trailing-bias-corrected', float('nan')):.3f} -> "
                             f"{x.get('verdict_trailing_bias')} ({UNITS[v]}, {x['days']} days)")
    L += ["", "Not tested: GenCast and WeatherNext (no public forecast archive; data needs a Google Cloud access "
          "request).", "", "## Log", "", "```", *LOG[-400:], "```"]
    open(os.path.join(OUT, f"wx_{tag}_report.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    main()
