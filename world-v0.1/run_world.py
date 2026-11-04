"""Paradox World Model v0.1: the whole study in one command (Google Colab or Kaggle, one T4 GPU, ~3.5 h).

  python run_world.py                      # full study
  python run_world.py --quick              # CPU pipeline check (minutes; numbers meaningless)

Question: does a compact world model learn more from less data when it combines self-supervision, sparse
experts, hierarchical (multi-scale) spatial representation, physics constraints and selective data, and can one
such model pretrained on public US networks forecast a network it has never seen (London, live 2025-26 data)
against Google's and Amazon's time-series foundation models?

Every choice is made on VALIDATION data by rules written here before the run; test windows are scored once.
  1  UK-M25 baselines (last value, yesterday, last week)
  2  UK-M25 from scratch, base recipe, seeds 0-2 (the noise floor: sigma of validation MAE)
  3  Foundation pretraining on the TRAIN split of 6 US networks (no UK data) -> zero-shot UK -> UK fine-tuning
  4  Foundation opponents zero-shot on the same windows (TimesFM 2.5 / 3.0, Chronos-Bolt, Chronos-2)
  5  Experiments at equal compute (single seed, vs base seed 0):
       A self-supervised masked pretraining phase (full data and 14 days of data)
       B sparse experts (4 experts, top-1; same active parameters)
       C mixed precision vs FP32 (speed, memory, accuracy)
       D active selection of training windows vs random, same window budget (5%)
       E physics: flow-conservation loss on detector pairs with a stable ratio
       H/W hierarchy (region + global tokens) off; weather off
  6  Data efficiency: 0 (zero-shot) / 7 / 30 days / full year, scratch vs foundation fine-tuning
  7  Scale: a larger foundation model (if time allows)
  8  Final: the recipe with the lowest validation MAE, 3 fresh seeds, ensembled, CQR-calibrated on validation,
     scored on test (Tracks S, U, D) with significance tests against every opponent and baseline
Rule for keeping a component (step 5): validation MAE better than base seed 0 by more than 2 sigma (step 2).
"""
import argparse, copy, json, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from pw.data import load_us, load_uk, unseen_split, US, H, SPD, RAW
from pw.train import train, predict, DEV
from pw import evaluate as E

S_BASE = dict(d=128, layers=3, heads=4, ff=2, experts=0, hier=True, weather=True, bs=16, lr=2e-3, amp=True,
              drop_p=0.1, gap_p=0.2, ssl_steps=0, ssl_w=0.0, phys_w=0.0)
F_BASE = dict(d=192, layers=4, heads=6, ff=2, experts=4, hier=True, weather=True, bs=16, lr=1.5e-3, amp=True,
              drop_p=0.1, gap_p=0.2, crop=256, ssl_steps=0, ssl_w=0.5, phys_w=0.1)
F_LARGE = dict(F_BASE, d=384, layers=6, heads=6, lr=1e-3)
FT = dict(lr=5e-4, ssl_w=0.0, ssl_steps=0)
OPPONENTS = ["chronos-bolt", "chronos2", "tfm25", "tfm3"]
TEST_STRIDE, VAL_STRIDE = 8, 4                     # test origins every 2 h, validation every hour
PER_DAY = SPD // TEST_STRIDE

RES = {"version": "Paradox World Model v0.1", "runs": {}, "tracks": {}, "significance": {}, "opponents": {}}
PRED = {"S": {}, "U": {}, "D": {}}
T0 = time.time()


def log(*a):
    print(*a, flush=True)


def emit(kind, **kw):
    log("RESULT " + json.dumps({"kind": kind, **kw}, default=float))


def save():
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    json.dump(RES, open(os.path.join(ROOT, "results", "world_v01_results.json"), "w"), indent=1, default=float)


def minutes_left(a):
    return a.budget - (time.time() - T0) / 60


def main(a):
    q = a.quick
    st = (lambda n: max(20, n // 100)) if q else (lambda n: n)
    log(f"Paradox World Model v0.1 on {DEV} ({torch.cuda.get_device_name(0) if DEV == 'cuda' else 'cpu'}), "
        f"budget {a.budget} min")
    uk = load_uk()
    log(uk.describe())
    nets = []
    for n in US:
        try:
            nets.append(load_us(n)); log(nets[-1].describe())
        except FileNotFoundError as e:
            log(f"  {n}: not found ({e})")
    seen, unseen = unseen_split(uk.N)
    RES["data"] = {"UK-M25": uk.describe(), "seen": len(seen), "unseen": len(unseen),
                   "us": [n.describe() for n in nets]}
    tr_all = uk.origins("train")
    val_org = uk.origins("val", VAL_STRIDE)
    test_org = uk.origins("test", TEST_STRIDE)
    if q:
        val_org, test_org = val_org[:48], test_org[:96]
    VAL = (uk, val_org, seen)
    allN = np.arange(uk.N)
    upos = np.searchsorted(allN, unseen)

    # ---------------------------------------------------------------- helpers
    cqr_cache = {}

    def uk_predict(models, track, org, use_w=True):
        qs, y = [], None
        for m in models:
            m.use_w = use_w and m.cfg["weather"]
            if track == "U":
                qq, y = predict(m, uk, org, allN); qq, y = qq[:, upos], y[:, upos]
            else:
                qq, y = predict(m, uk, org, seen, dark=0.3 if track == "D" else None)
            qs.append(qq)
        return np.sort(np.mean(qs, 0), -1), y

    def evaluate_uk(name, models, calibrate=True, use_w=True, tracks=("S", "U", "D"), keep=True, extra=None):
        out = {}
        d = None
        if calibrate:
            qv, yv = uk_predict(models, "S", val_org, use_w)
            d = E.fit_cqr(qv, yv)
            out["val_MAE"] = E.score(qv, yv)["MAE"]
        for t in tracks:
            qt, yt = uk_predict(models, t, test_org, use_w)
            if d is not None:
                qt = E.apply_cqr(qt, d)
            sc = E.score(qt, yt)
            out[t] = sc
            if keep:
                PRED[t][name] = qt
                PRED[t]["_y"] = yt
            emit("uk_test", model=name, track=t, **{k: round(v, 4) for k, v in sc.items()})
        out.update(extra or {})
        RES["tracks"][name] = out
        save()
        return out

    def baseline(kind, org, nodes):
        y = uk.y
        fo = org[:, None] + np.arange(H)[None]
        yday, wk = y[fo - SPD][:, :, nodes], y[fo - 7 * SPD][:, :, nodes]            # [W, H, n]
        if kind == "last":
            hi = y[org[:, None] + np.arange(-12, 0)[None]][:, :, nodes]               # [W, 12, n]
            ok = ~np.isnan(hi)
            li = np.where(ok, np.arange(12)[None, :, None], -1).max(1)
            v = np.take_along_axis(hi, np.maximum(li, 0)[:, None], 1)[:, 0]
            v = np.where(li >= 0, v, yday[:, 0])
            p = np.repeat(v[:, None], H, 1)
        else:
            p = yday if kind == "yday" else wk
        p = np.nan_to_num(np.where(np.isnan(p), wk, p)).transpose(0, 2, 1)
        return np.repeat(p[..., None], 3, -1).astype(np.float32)

    def fit_run(name, cfg, sources, steps, seed=0, init=None, budget_s=None):
        log(f"== {name} (seed {seed}, {steps} steps, {(time.time() - T0) / 60:.0f} min elapsed)")
        m, info = train(cfg, sources, VAL, steps=steps, seed=seed, init=init, log=log, budget_s=budget_s)
        info["config"] = {k: v for k, v in cfg.items()}
        RES["runs"][name] = info
        emit("run", name=name, seed=seed, val_MAE=round(info["val_MAE"], 4), params=info["params"],
             active_params=info["active_params"], sec_per_step=info["sec_per_step"], peak_mem_MB=info["peak_mem_MB"],
             seconds=info["seconds"])
        save()
        return m, info

    def uk_src(org=None, nodes=seen):
        return [(uk, tr_all if org is None else org, nodes, 1.0)]

    # ---------------------------------------------------------------- 1 baselines
    names = {"last": "Last observed value", "yday": "Same time yesterday", "week": "Same time last week"}
    for k, nm in names.items():
        qv = baseline(k, val_org, seen)
        out = {}
        d = None
        for t, nodes in (("S", seen), ("U", unseen)):
            qt = baseline(k, test_org, nodes)
            yt = uk.y[test_org[:, None] + np.arange(H)[None]][:, :, nodes].transpose(0, 2, 1)
            if d is None:
                yvv = uk.y[val_org[:, None] + np.arange(H)[None]][:, :, seen].transpose(0, 2, 1)
                d = E.fit_cqr(qv, yvv)
            qt = E.apply_cqr(qt, d)
            out[t] = E.score(qt, yt)
            PRED[t][nm] = qt
            emit("uk_test", model=nm, track=t, **{kk: round(v, 4) for kk, v in out[t].items()})
        RES["tracks"][nm] = out
    save()

    # ---------------------------------------------------------------- 2 scratch base, noise floor
    SCR = st(a.uk_steps)
    base_models = []
    for s in (0, 1, 2):
        m, _ = fit_run(f"scratch-base-s{s}", S_BASE, uk_src(), SCR, seed=s)
        base_models.append(m)
    vb = [RES["runs"][f"scratch-base-s{s}"]["val_MAE"] for s in (0, 1, 2)]
    sigma = float(np.std(vb, ddof=1))
    RES["noise_floor"] = {"val_MAE_seeds": vb, "sigma": sigma, "rule": "keep if better than base seed 0 by > 2 sigma"}
    evaluate_uk("Scratch base (seed 0)", base_models[:1], tracks=("S",))
    log(f"noise floor: validation MAE {vb} -> sigma {sigma:.4f}")

    # ---------------------------------------------------------------- 3 foundation pretraining
    def pretrain(name, cfg, minutes):
        src = [(n, n.origins("train"), None, float(np.sqrt(n.N * len(n.origins("train"))))) for n in nets]
        pv = next((n for n in nets if n.name == "PEMS08"), nets[0])
        pval = (pv, pv.origins("val", 16)[: (24 if q else 400)], None)
        _, probe = train(cfg, src, None, steps=20 if q else 60, seed=0)
        steps = st(int(minutes * 60 / max(probe["sec_per_step"], 1e-3)))
        log(f"== {name}: {probe['sec_per_step']:.3f} s/step -> {steps} steps in {minutes} min "
            f"({len(nets)} US networks, val on {pv.name})")
        m, info = train(cfg, src, pval, steps=steps, seed=0, log=log, budget_s=minutes * 60 * 1.15)
        info["config"] = dict(cfg); info["pretrain_val"] = f"{pv.name} validation MAE"
        RES["runs"][name] = info
        emit("pretrain", name=name, steps=info["steps"], params=info["params"], active_params=info["active_params"],
             val_MAE_pems08=round(info["val_MAE"], 4), minutes=round(info["seconds"] / 60, 1))
        us = {}
        for n in nets:                                                      # in-domain test (train split only seen)
            org = n.origins("test", 8)[: (16 if q else None)]
            qq, yy = predict(m, n, org, None, chunk=8)
            us[n.name] = E.score(qq, yy)
            emit("us_test", model=name, network=n.name, **{k: round(v, 4) for k, v in us[n.name].items()})
        RES["runs"][name]["us_test"] = us
        save()
        return m

    fbase = pretrain("F-base", F_BASE, 1 if q else a.pretrain_min)
    fstate = copy.deepcopy(fbase.state_dict())
    evaluate_uk("PWM-W F-base zero-shot", [fbase], calibrate=False, use_w=False, tracks=("S", "U"))
    FTS = st(a.ft_steps)
    ft, _ = fit_run("F-base-ft-full-s0", dict(F_BASE, **FT), uk_src(), FTS, seed=0, init=fstate)
    evaluate_uk("PWM-W F-base fine-tuned (seed 0)", [ft], tracks=("S",))

    # ---------------------------------------------------------------- 4 opponents
    if a.opponents:
        from pw import opponents as OPP
        for key in a.opponents.split(","):
            try:
                qt, meta = OPP.run(key, uk.y, test_org, allN, H, log=log)
                qv, _ = OPP.run(key, uk.y, val_org[::4], seen, H, log=log)
                yvv = uk.y[val_org[::4][:, None] + np.arange(H)[None]][:, :, seen].transpose(0, 2, 1)
                d = E.fit_cqr(qv, yvv)
                out = {"meta": meta}
                for t, ix in (("S", seen), ("U", unseen)):
                    yt = uk.y[test_org[:, None] + np.arange(H)[None]][:, :, ix].transpose(0, 2, 1)
                    for cal, qq in (("raw", qt[:, ix]), ("cqr", E.apply_cqr(qt[:, ix], d))):
                        sc = E.score(qq, yt)
                        out[f"{t}_{cal}"] = sc
                        emit("uk_test", model=f"{meta['name']} zero-shot ({cal})", track=t,
                             **{k: round(v, 4) for k, v in sc.items()})
                    PRED[t][f"{meta['name']} zero-shot"] = E.apply_cqr(qt[:, ix], d)
                RES["opponents"][key] = out
            except Exception as e:                                          # recorded, never hidden
                log(f"  opponent {key} failed: {type(e).__name__}: {e}")
                RES["opponents"][key] = {"error": f"{type(e).__name__}: {e}"}
            save()
            torch.cuda.empty_cache() if DEV == "cuda" else None

    # ---------------------------------------------------------------- 5 experiments at equal compute
    exps = {
        "A-ssl": dict(S_BASE, ssl_steps=SCR // 3, ssl_w=0.5),
        "B-experts": dict(S_BASE, experts=4),
        "C-fp32": dict(S_BASE, amp=False),
        "E-physics": dict(S_BASE, phys_w=0.1),
        "H-no-hierarchy": dict(S_BASE, hier=False),
        "W-no-weather": dict(S_BASE, weather=False),
    }
    for nm, cfg in exps.items():
        m, _ = fit_run(nm, cfg, uk_src(), SCR, seed=0)
        evaluate_uk(f"Exp {nm}", [m], tracks=("S",), keep=False)
    # data-limited: 14 days, with and without the self-supervised phase
    o14 = uk.origins("train", last_days=14)
    fit_run("scratch-14d", S_BASE, uk_src(o14), SCR, seed=0)
    fit_run("A-ssl-14d", exps["A-ssl"], uk_src(o14), SCR, seed=0)
    # D: active vs random window selection at a 5% budget (final training identical; selection cost reported)
    gen = np.random.default_rng(7)
    k = max(64, int(0.05 * len(tr_all)))
    rnd = np.sort(gen.choice(tr_all, k, replace=False))
    fit_run("D-random-5pct", S_BASE, uk_src(rnd), SCR, seed=0)
    t_sel = time.time()
    chosen = gen.choice(tr_all, int(0.4 * k), replace=False)
    for r in range(2):
        proxy, _ = train(S_BASE, uk_src(np.sort(chosen)), None, steps=max(20, SCR // 3), seed=10 + r)
        rest = np.setdiff1d(tr_all, chosen)
        cand = gen.choice(rest, min(len(rest), 4000 if not q else 64), replace=False)
        qc, _ = predict(proxy, uk, cand, seen)
        width = ((qc[..., 2] - qc[..., 0]) / np.maximum(qc[..., 1].mean((1, 2), keepdims=True), 1)).mean((1, 2))
        add = int(0.3 * k)
        top = cand[np.argsort(-width)[: add // 2]]
        others = np.setdiff1d(cand, top)
        chosen = np.concatenate([chosen, top, gen.choice(others, add - len(top), replace=False)])
    act = np.sort(np.unique(chosen))[:k]
    sel_s = time.time() - t_sel
    fit_run("D-active-5pct", S_BASE, uk_src(act), SCR, seed=0)
    RES["runs"]["D-active-5pct"]["selection_seconds"] = round(sel_s, 1)

    # rules
    b0 = RES["runs"]["scratch-base-s0"]["val_MAE"]
    better = lambda n: RES["runs"][n]["val_MAE"] < b0 - 2 * sigma
    dec = {"ssl": better("A-ssl"), "experts": better("B-experts"), "physics": better("E-physics"),
           "drop_hierarchy": better("H-no-hierarchy"), "drop_weather": better("W-no-weather"),
           "fp32_needed": better("C-fp32"),
           "active_beats_random": RES["runs"]["D-active-5pct"]["val_MAE"] <
                                  RES["runs"]["D-random-5pct"]["val_MAE"] - 2 * sigma,
           "ssl_helps_at_14d": RES["runs"]["A-ssl-14d"]["val_MAE"] < RES["runs"]["scratch-14d"]["val_MAE"] - 2 * sigma}
    best_s = dict(S_BASE)
    if dec["ssl"]: best_s.update(ssl_steps=SCR // 3, ssl_w=0.5)
    if dec["experts"]: best_s["experts"] = 4
    if dec["physics"]: best_s["phys_w"] = 0.1
    if dec["drop_hierarchy"]: best_s["hier"] = False
    if dec["drop_weather"]: best_s["weather"] = False
    if dec["fp32_needed"]: best_s["amp"] = False
    RES["decisions"] = dec
    log("decisions:", json.dumps(dec))
    emit("decisions", **dec)

    # ---------------------------------------------------------------- 6 data efficiency
    for days in (7, 30):
        o = uk.origins("train", last_days=days)
        m, _ = fit_run(f"scratch-{days}d", S_BASE, uk_src(o), SCR, seed=0)
        evaluate_uk(f"Scratch {days} days", [m], tracks=("S", "U"), keep=False)
        m, _ = fit_run(f"F-base-ft-{days}d", dict(F_BASE, **FT), uk_src(o), FTS, seed=0, init=fstate)
        evaluate_uk(f"F-base fine-tuned {days} days", [m], tracks=("S", "U"), keep=False)

    # ---------------------------------------------------------------- 7 scale
    cands = {"scratch-best": None, "F-base-ft": RES["runs"]["F-base-ft-full-s0"]["val_MAE"]}
    if best_s != S_BASE:
        fit_run("scratch-best-s0", best_s, uk_src(), SCR, seed=0)
        cands["scratch-best"] = RES["runs"]["scratch-best-s0"]["val_MAE"]
    else:
        cands["scratch-best"] = b0
    lstate = None
    if not a.no_large and minutes_left(a) > a.large_min + 55:
        flarge = pretrain("F-large", F_LARGE, 1 if q else a.large_min)
        lstate = copy.deepcopy(flarge.state_dict())
        evaluate_uk("PWM-W F-large zero-shot", [flarge], calibrate=False, use_w=False, tracks=("S", "U"))
        m, _ = fit_run("F-large-ft-full-s0", dict(F_LARGE, **FT), uk_src(), FTS, seed=0, init=lstate)
        cands["F-large-ft"] = RES["runs"]["F-large-ft-full-s0"]["val_MAE"]
        del flarge
    else:
        log(f"skipping F-large ({minutes_left(a):.0f} min left)")

    # ---------------------------------------------------------------- 8 final
    pick = min(cands, key=cands.get)
    RES["final_choice"] = {"candidates_val_MAE": cands, "chosen": pick}
    log(f"final recipe chosen on validation: {pick} {json.dumps(cands)}")
    finals = []
    for s in (100, 101, 102):
        if pick == "scratch-best":
            m, _ = fit_run(f"final-s{s}", best_s, uk_src(), SCR, seed=s)
        elif pick == "F-base-ft":
            m, _ = fit_run(f"final-s{s}", dict(F_BASE, **FT), uk_src(), FTS, seed=s, init=fstate)
        else:
            m, _ = fit_run(f"final-s{s}", dict(F_LARGE, **FT), uk_src(), FTS, seed=s, init=lstate)
        finals.append(m)
    fname = "PWM-W v0.1 (3-seed, CQR)"
    m0 = finals[0]
    b = uk.batch(test_org[:1], seen, DEV)
    with torch.no_grad():
        for _ in range(3):
            m0(b)
        if DEV == "cuda":
            torch.cuda.synchronize()
        t = time.time()
        for _ in range(20):
            m0(b)
        if DEV == "cuda":
            torch.cuda.synchronize()
    lat = (time.time() - t) / 20 * 1000
    evaluate_uk(fname, finals, extra={"params": m0.n_params(), "active_params": m0.n_params(active=True),
                                      "latency_ms_per_network_forecast": round(lat, 2), "recipe": pick})
    y = PRED["S"]["_y"]
    for t in ("S", "U"):
        yt = PRED[t]["_y"]
        RES["significance"][t] = {}
        for other in PRED[t]:
            if other in ("_y", fname):
                continue
            res = {}
            for met in ("MAE", "RMSE", "MAPE", "QL", "IS80"):
                c = E.compare(PRED[t][fname], PRED[t][other], yt, PER_DAY, met, reps=200 if q else 2000)
                if c:
                    res[met] = c
            RES["significance"][t][other] = res
            emit("sig", track=t, vs=other, **{m: f"{r['verdict']} {r['rel_diff_pct']:+.2f}% p={r['p']:.2g}"
                                              for m, r in res.items()})
    RES["minutes_total"] = round((time.time() - T0) / 60, 1)
    save()
    write_report()
    log(f"done in {RES['minutes_total']} min")


def write_report():
    """Markdown tables generated from the results JSON (no hand-typed numbers)."""
    R = RES
    L = ["# Paradox World Model v0.1 results (generated from results/world_v01_results.json)", ""]
    L += ["Data: " + R["data"]["UK-M25"], ""]
    for t, title in (("S", "Track S: seen sensors, clean input"), ("U", "Track U: unseen locations (never trained on)"),
                     ("D", "Track D: seen sensors, 30% of sensors dark")):
        L += [f"## {title}", "", "| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@15 | MAE@30 | MAE@60 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        rows = []
        for name, v in R["tracks"].items():
            if t in v:
                rows.append((v[t]["MAE"], name, v[t]))
        for key, v in R["opponents"].items():
            if f"{t}_cqr" in v:
                rows.append((v[f"{t}_cqr"]["MAE"], v["meta"]["name"] + " zero-shot (+CQR)", v[f"{t}_cqr"]))
        for _, name, s in sorted(rows):
            L.append(f"| {name} | {s['MAE']:.3f} | {s['RMSE']:.3f} | {s['MAPE']:.2f} | {s['QL']:.3f} | {s['IS80']:.2f} | "
                     f"{s['COV80']:.1f} | {s['MAE@15min']:.3f} | {s['MAE@30min']:.3f} | {s['MAE@60min']:.3f} |")
        L.append("")
    for t, sig in R["significance"].items():
        L += [f"## Significance, Track {t}: PWM-W v0.1 vs each model (negative = PWM-W better)", "",
              "| vs | MAE | RMSE | MAPE | QL | IS80 |", "|---|---|---|---|---|---|"]
        for other, res in sig.items():
            cell = lambda m: (f"{res[m]['verdict']} {res[m]['rel_diff_pct']:+.2f}%" if m in res else "-")
            L.append(f"| {other} | " + " | ".join(cell(m) for m in ("MAE", "RMSE", "MAPE", "QL", "IS80")) + " |")
        L.append("")
    L += ["## Runs (validation MAE, compute)", "", "| Run | val MAE | params | active | s/step | peak MB | min |",
          "|---|---|---|---|---|---|---|"]
    for n, v in R["runs"].items():
        L.append(f"| {n} | {v['val_MAE']:.4f} | {v['params']:,} | {v['active_params']:,} | {v['sec_per_step']} | "
                 f"{v['peak_mem_MB']} | {v['seconds'] / 60:.1f} |")
    L += ["", "Decisions (validation rules): `" + json.dumps(R.get("decisions", {})) + "`",
          "", "Final choice: `" + json.dumps(R.get("final_choice", {})) + "`", ""]
    open(os.path.join(ROOT, "results", "world_v01_report.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--budget", type=float, default=230, help="minutes for the whole study")
    ap.add_argument("--uk_steps", type=int, default=3000)
    ap.add_argument("--ft_steps", type=int, default=2000)
    ap.add_argument("--pretrain_min", type=float, default=20)
    ap.add_argument("--large_min", type=float, default=30)
    ap.add_argument("--no_large", action="store_true")
    ap.add_argument("--opponents", default=",".join(OPPONENTS))
    a = ap.parse_args()
    main(a)
