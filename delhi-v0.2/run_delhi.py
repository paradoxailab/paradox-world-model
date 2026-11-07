"""Paradox World Model, Delhi v0.2: a hybrid world model of Delhi's air.

v0.2 changes (Delhi v0.1 lost to TimesFM / Chronos on PM2.5): PM2.5 only (v0.1's validation rule); long context
(72 h + 14 daily means); real 1-day-ahead weather forecasts (tools/fetch_wxfc.py); and a HYBRID option: the
open-licence foundation models Chronos-2 and TimesFM 2.5 forecast first (tools/backbone.py) and PWM-W learns to
correct their median with the station graph, other pollutants, meteorology and the weather forecast. Variants are
compared on validation (all trained on the same origins, every 3 h); the best is kept only if it beats the v0.1-style
model by > 2 sigma.

  python tools/fetch_delhi.py        # build data/raw/DELHI.npz from CPCB's public station data
  python run_delhi.py                # train, test, compare, write results + a next-24-hour forecast for every station
  python run_delhi.py --quick        # pipeline check in minutes (numbers meaningless)

What it does (every choice made on VALIDATION data by rules written here; test scored once):
  1  baselines: last observed value, same hour yesterday, hour x month climatology (CQR-calibrated)
  2  PWM-W Delhi, seeds 0-2: four pollutants forecast together for the next 24 h from all 14 measured variables at
     all training stations (the noise floor: sigma of validation PM2.5 MAE)
  3  does the "world" help?  (single seed each, against seed 0; a component is dropped only if removing it improves
     validation PM2.5 MAE by more than 2 sigma)
       no-aux    pollutant targets only (no meteorology, no other pollutants)
       no-graph  stations forecast independently
       pm25-only one target instead of four
  4  final: the kept recipe, 3 fresh seeds, ensembled, CQR on validation; Tracks S (training stations), U (stations
     never trained on), D (30% of stations dark) for every target
  5  foundation models zero-shot on PM2.5, same windows: Chronos-Bolt, Chronos-2, TimesFM 2.5, TimesFM 3.0
     (univariate and multivariate), 512 hours of history each; significance tests (Diebold-Mariano + day-block bootstrap)
  6  the latest forecast: next 24 h for every station from the last data in the file (results/delhi_forecast.json)
"""
import argparse, copy, json, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from pw.ddata import Delhi, H, SPD, FLOOR, TARGETS, RAW
from pw.dtrain import train, predict, build, DEV
from pw import evaluate as E

BASE = dict(d=128, layers=3, heads=4, ff=2, experts=0, hier=True, use_aux=True, use_graph=True, bs=32, lr=1.5e-3)
OPPONENTS = "chronos-bolt,chronos2,tfm25,tfm3,tfm3mv"
TEST_STRIDE, VAL_STRIDE = 6, 3
PER_DAY = SPD // TEST_STRIDE
HZ = (0, 5, 11, 23)
FINAL = "PWM-W Delhi v0.2"
CACHE = os.environ.get("PW_CACHE", os.path.join(ROOT, "results", "cache"))
RES = {"version": FINAL, "runs": {}, "tracks": {}, "opponents": {}, "significance": {}, "decisions": {}}
T0 = time.time()


def log(*a):
    print(*a, flush=True)


def emit(kind, **kw):
    log("RESULT " + json.dumps({"kind": kind, **kw}, default=float))


def save():
    for d in {os.path.join(ROOT, "results"), CACHE}:
        os.makedirs(d, exist_ok=True)
        json.dump(RES, open(os.path.join(d, "delhi_v02_results.json"), "w"), indent=1, default=float)


def main(a):
    q = a.quick
    D = Delhi(targets=["PM2.5"])
    log(D.describe())
    log(f"weather forecasts: {D.Cw} variables; backbone: {D.NB} models {getattr(D, 'bb_keys', [])}")
    RES["data"] = {"describe": D.describe(), "stations": D.stations, "seen": len(D.seen), "unseen": len(D.unseen),
                   "unseen_stations": [D.stations[i] for i in D.unseen]}
    tr = D.origins("train", 3)                     # the backbone grid; every variant trains on the same origins
    va = D.origins("val", VAL_STRIDE)
    te = D.origins("test", TEST_STRIDE)
    if q:
        va, te = va[:40], te[:60]
    steps = 40 if q else a.steps
    upos = np.arange(D.N)[D.unseen]

    def sc(qq, yy, k):
        return E.score(qq[:, :, k], yy[:, :, k], horizons=HZ, floor=FLOOR[D.targets[k]], step_min=60)

    preds = {"S": {}, "U": {}, "D": {}}

    def store(name, out, qd):
        RES["tracks"][name] = out
        for t, (qq, yy) in qd.items():
            preds[t][name] = qq
            preds[t]["_y"] = yy
        for t in out:
            if t in ("S", "U", "D"):
                emit("test", model=name, track=t, **{k: round(v, 3) for k, v in out[t]["PM2.5"].items()
                                                     if "@" not in k or "MAE" in k})
        save()

    # ----------------------------------------------------------- 1 baselines
    Y = D.Y

    def baseline(kind, org, nodes):
        fo = org[:, None] + np.arange(H)[None]
        yd = Y[fo - SPD][:, :, nodes]                                       # [W, H, n, K]
        if kind == "last":
            hi = Y[org[:, None] + np.arange(-24, 0)[None]][:, :, nodes]
            li = np.where(~np.isnan(hi), np.arange(24)[None, :, None, None], -1).max(1)
            v = np.take_along_axis(hi, np.maximum(li, 0)[:, None], 1)[:, 0]
            p = np.repeat(np.where(li >= 0, v, yd[:, 0])[:, None], H, 1)
        elif kind == "yday":
            p = yd
        else:
            b = D.bounds["train"][1]
            key = D.tod * 12 + D.month
            tab = np.full((24 * 12, D.N, D.K), np.nan, np.float32)
            for k2 in range(24 * 12):
                rows = Y[:b][key[:b] == k2][:, :, :]
                if len(rows):
                    with np.errstate(all="ignore"):
                        tab[k2] = np.nanmedian(rows, 0)
            p = tab[key[fo]][:, :, nodes]
        p = np.where(np.isnan(p), yd, p)
        return np.repeat(np.nan_to_num(p).transpose(0, 2, 3, 1)[..., None], 3, -1).astype(np.float32)

    def truth(org, nodes):
        return Y[org[:, None] + np.arange(H)[None]][:, :, nodes].transpose(0, 2, 3, 1)

    for kind, nm in (("last", "Last observed value"), ("yday", "Same hour yesterday"),
                     ("clim", "Hour x month climatology")):
        qv, yv = baseline(kind, va, D.seen), truth(va, D.seen)
        out, qd = {}, {}
        dl = [E.fit_cqr(qv[:, :, k], yv[:, :, k]) for k in range(D.K)]
        for t, nodes in (("S", D.seen), ("U", D.unseen)):
            qt, yt = baseline(kind, te, nodes), truth(te, nodes)
            for k in range(D.K):
                qt[:, :, k] = E.apply_cqr(qt[:, :, k], dl[k])
            out[t] = {D.targets[k]: sc(qt, yt, k) for k in range(D.K)}
            qd[t] = (qt[:, :, 0], yt[:, :, 0])
        store(nm, out, qd)

    # ----------------------------------------------------------- 2-3 runs
    def fit(name, cfg, data, seed=0):
        f = os.path.join(CACHE, "runs", name + ".pt")
        if os.path.exists(f) and not q:
            z = torch.load(f, map_location="cpu", weights_only=False)
            m = build(cfg, data); m.load_state_dict(z["state"]); info = z["info"]
        else:
            log(f"== {name} (seed {seed}, {(time.time() - T0) / 60:.0f} min elapsed)")
            m, info = train(cfg, data, tr, data.seen, (va, data.seen), steps=steps, seed=seed, log=lambda *x: None)
            info["config"] = dict(cfg)
            os.makedirs(os.path.dirname(f), exist_ok=True)
            torch.save({"state": m.state_dict(), "info": info}, f)
        RES["runs"][name] = info
        emit("run", name=name, **{k: v for k, v in info.items() if k != "config"})
        save()
        return m

    def evaluate(name, models, data, tracks=("S", "U", "D"), keep=True):
        qv, yv = ens(models, data, va, data.seen)
        dl = [E.fit_cqr(qv[:, :, k], yv[:, :, k]) for k in range(data.K)]
        out, qd = {"val": {data.targets[k]: sc(qv, yv, k)["MAE"] for k in range(data.K)}}, {}
        for t in tracks:
            if t == "U":
                qt, yt = ens(models, data, te, None); qt, yt = qt[:, upos], yt[:, upos]
            else:
                qt, yt = ens(models, data, te, data.seen, dark=0.3 if t == "D" else None)
            for k in range(data.K):
                qt[:, :, k] = E.apply_cqr(qt[:, :, k], dl[k])
            out[t] = {data.targets[k]: sc(qt, yt, k) for k in range(data.K)}
            qd[t] = (qt[:, :, 0], yt[:, :, 0])
        if keep:
            store(name, out, qd)
        return out, dl

    def ens(models, data, org, nodes, dark=None):
        qs, y = [], None
        for m in models:
            qq, y = predict(m, data, org, nodes, dark=dark)
            qs.append(qq)
        return np.sort(np.mean(qs, 0), -1), y

    V = {"A0-short": dict(BASE, long=False), "A1-long": dict(BASE), "A2-long+wf": dict(BASE, use_wf=True),
         "A3-long+hybrid": dict(BASE, use_bb=True), "A4-long+wf+hybrid": dict(BASE, use_wf=True, use_bb=True)}
    if not D.Cw:
        V = {k: v for k, v in V.items() if not v.get("use_wf")}
    if not D.NB:
        V = {k: v for k, v in V.items() if not v.get("use_bb")}
    base = [fit(f"A0-short-s{s}", V["A0-short"], D, s) for s in (0, 1, 2)]
    vb = [RES["runs"][f"A0-short-s{s}"]["val_MAE_PM25"] for s in (0, 1, 2)]
    sigma = max(float(np.std(vb, ddof=1)), 1e-6)
    evaluate("PWM-W v0.1-style (seed 0)", base[:1], D, tracks=("S",))
    vals = {"A0-short": vb[0]}
    for nm, cfg in V.items():
        if nm == "A0-short":
            continue
        m = fit(nm, cfg, D, 0)
        evaluate(f"Variant {nm}", [m], D, tracks=("S",))
        vals[nm] = RES["runs"][nm]["val_MAE_PM25"]
    best = min(vals, key=vals.get)
    pick = best if (vals["A0-short"] - vals[best]) / sigma > 2 else "A0-short"
    RES["decisions"] = {"sigma_val_PM25": sigma, "val_MAE_PM25": vals, "chosen": pick,
                        "rule": "the variant with the lowest validation PM2.5 MAE, if it beats A0-short by > 2 sigma"}
    emit("decisions", **RES["decisions"])
    rec, data = V[pick], D

    # ----------------------------------------------------------- 4 final
    finals = [fit(f"final-s{s}", rec, data, s) for s in (100, 101, 102)]
    out, dl = evaluate(FINAL, finals, data)
    RES["tracks"][FINAL]["params"] = finals[0].n_params()
    torch.save({"config": rec, "targets": data.targets, "stations": data.stations, "cqr_delta": [d.tolist() for d in dl],
                "states": [m.state_dict() for m in finals]}, os.path.join(CACHE, "pwm_w_delhi_v02.pt"))

    # ----------------------------------------------------------- 5 foundation models (PM2.5)
    if a.opponents:
        from pw import opponents as OPP
        y2 = D.Y[:, :, 0]
        for key in a.opponents.split(","):
            f = os.path.join(CACHE, "opponents", key + ".npz")
            try:
                if D.NB and key in getattr(D, "bb_keys", []) and (D.bb_row[te] >= 0).all() and (D.bb_row[va[::4]] >= 0).all():
                    kb = D.bb_keys.index(key)                     # same model call as the backbone: reuse it
                    qt, qv = D.BB[D.bb_row[te]][:, :, kb], D.BB[D.bb_row[va[::4]]][:, :, kb]
                    meta = {"name": {"chronos2": "Chronos-2 (Amazon, 120M)", "tfm25": "TimesFM 2.5 (Google, 200M)"}[key],
                            "source": "backbone file (same zero-shot forecasts)", "context_steps": 512}
                elif os.path.exists(f) and not q:
                    zz = np.load(f); qt, qv, meta = zz["qt"], zz["qv"], json.loads(str(zz["meta"]))
                else:
                    qt, meta = OPP.run(key, y2, te, np.arange(D.N), H, ctx=512, log=log)
                    qv, _ = OPP.run(key, y2, va[::4], np.arange(D.N), H, ctx=512, log=log)
                    os.makedirs(os.path.dirname(f), exist_ok=True)
                    np.savez_compressed(f, qt=qt, qv=qv, meta=np.array(json.dumps(meta)))
                d = E.fit_cqr(qv[:, D.seen], truth(va[::4], D.seen)[:, :, 0])
                res = {"meta": meta}
                for t, ix in (("S", D.seen), ("U", D.unseen)):
                    qq = E.apply_cqr(qt[:, ix], d)
                    yt = truth(te, ix)[:, :, 0]
                    res[t] = E.score(qq, yt, horizons=HZ, floor=FLOOR["PM2.5"], step_min=60)
                    preds[t][meta["name"] + " zero-shot"] = qq
                    emit("test", model=meta["name"] + " zero-shot (+CQR)", track=t,
                         **{k: round(v, 3) for k, v in res[t].items() if "@" not in k or "MAE" in k})
                RES["opponents"][key] = res
            except Exception as e:
                log(f"  opponent {key} failed: {type(e).__name__}: {e}")
                RES["opponents"][key] = {"error": f"{type(e).__name__}: {e}"}
            save()

    # ----------------------------------------------------------- 5b CAMS (ECMWF Copernicus) PM2.5 forecasts
    pc = os.path.join(RAW, "DELHI_cams.npz")
    if os.path.exists(pc):
        zc = np.load(pc)
        names = [str(x) for x in zc["stations"]]
        C = np.full((D.T + 2 * H, D.N), np.nan, np.float32)
        for i, stn in enumerate(D.stations):
            if stn in names:
                c = zc["pm25"][:, names.index(stn)]
                n_ = min(len(c), len(C))
                C[:n_, i] = c[:n_]
        Yp = D.Y[:, :, 0]
        def cams_at(org, nodes, bc):
            tt = org[:, None] + np.arange(H)[None]
            v = C[tt][:, :, nodes].transpose(0, 2, 1)                                   # [W, n, H]
            if bc:                                     # trailing 30-day bias, same hour of day, only days before org
                lag = tt[:, :, None] - 24 * np.arange(1, 31)[None, None]
                lag = np.clip(lag, 0, D.T - 1)
                e = (C[lag] - Yp[lag])[..., nodes]                                     # [W, H, 30, n]
                with np.errstate(all="ignore"):
                    b = np.where(np.isfinite(e).sum(2) >= 10, np.nanmean(e, 2), 0.0)
                v = v - b.transpose(0, 2, 1)
            return np.repeat(v[..., None], 3, -1).astype(np.float32)
        for bc, nm in ((False, "CAMS global (ECMWF Copernicus), latest forecast"),
                       (True, "CAMS global (ECMWF Copernicus), latest forecast + local bias correction")):
            res = {"meta": {"name": nm, "source": "Open-Meteo air-quality archive, domain cams_global"}}
            for t, ix in (("S", D.seen), ("U", D.unseen)):
                qq, yt = cams_at(te, ix, bc), truth(te, ix)[:, :, 0]
                ok = np.isfinite(qq[..., 1])
                if ok.mean() < 0.5:
                    continue
                yt = np.where(ok, yt, np.nan)
                res[t] = E.score(qq, yt, horizons=HZ, floor=FLOOR["PM2.5"], step_min=60)
                preds[t][nm] = qq
                emit("test", model=nm, track=t, **{k: round(v, 3) for k, v in res[t].items() if "@" not in k or "MAE" in k})
            RES["opponents"]["cams" + ("_bc" if bc else "")] = res
        save()

    # ----------------------------------------------------------- significance (PM2.5)
    for t in ("S", "U", "D"):
        if FINAL not in preds[t]:
            continue
        yt = preds[t]["_y"]
        RES["significance"][t] = {}
        for other, qo in preds[t].items():
            if other in ("_y", FINAL):
                continue
            yo = np.where(np.isfinite(qo[..., 1]), yt, np.nan)            # hours the opponent covers
            r = {m: E.compare(preds[t][FINAL], qo, yo, PER_DAY, m, reps=200 if q else 2000, floor=FLOOR["PM2.5"])
                 for m in ("MAE", "RMSE", "MAPE", "QL", "IS80")}
            RES["significance"][t][other] = {m: v for m, v in r.items() if v}
            emit("sig", track=t, vs=other, **{m: f"{v['verdict']} {v['rel_diff_pct']:+.2f}% p={v['p']:.2g}"
                                              for m, v in r.items() if v})
    save()

    # ----------------------------------------------------------- 6 latest forecast for every station
    qf, _ = ens(finals, data, np.array([data.T]), None)                    # origin = first hour after the data
    fc = {"first_hour": str(data.dates[data.T]), "hours": H,
          "note": "next 24 h after the last hour in the data file, from the final 3-seed model (calibrated quantiles "
                  "not applied); clock as in the CPCB files (IST)",
          "stations": {}}
    for i, st in enumerate(data.stations):
        fc["stations"][st] = {data.targets[k]: {"q10": qf[0, i, k, :, 0].round(1).tolist(),
                                                "q50": qf[0, i, k, :, 1].round(1).tolist(),
                                                "q90": qf[0, i, k, :, 2].round(1).tolist()} for k in range(data.K)}
    json.dump(fc, open(os.path.join(ROOT, "results", "delhi_forecast.json"), "w"))
    json.dump(fc, open(os.path.join(CACHE, "delhi_forecast.json"), "w"))
    RES["minutes_total"] = round((time.time() - T0) / 60, 1)
    save()
    write_report()
    log(f"done in {RES['minutes_total']} min")


def write_report():
    R = RES
    L = [f"# {FINAL} results (generated from results/delhi_v02_results.json)", "", R["data"]["describe"], "",
         f"Unseen stations (Track U): {', '.join(R['data']['unseen_stations'])}", ""]
    for t, title in (("S", "Track S: training stations"), ("U", "Track U: stations never trained on"),
                     ("D", "Track D: training stations, 30% dark")):
        rows = [(v[t]["PM2.5"]["MAE"], n, v[t]["PM2.5"]) for n, v in R["tracks"].items() if t in v]
        rows += [(v[t]["MAE"], v["meta"]["name"] + " zero-shot (+CQR)", v[t]) for v in R["opponents"].values() if t in v]
        if not rows:
            continue
        L += [f"## PM2.5, {title} (ug/m3, next 24 h)", "",
              "| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, n, s in sorted(rows, key=lambda r: r[0]):
            L.append(f"| {n} | {s['MAE']:.2f} | {s['RMSE']:.2f} | {s['MAPE']:.1f} | {s['QL']:.2f} | {s['IS80']:.1f} | "
                     f"{s['COV80']:.1f} | {s['MAE@1h']:.2f} | {s['MAE@6h']:.2f} | {s['MAE@12h']:.2f} | {s['MAE@24h']:.2f} |")
        L.append("")
    if FINAL in R["tracks"]:
        L += ["## All four targets, PWM-W Delhi v0.1 vs the best baseline (Track S)", "",
              "| Target | PWM-W MAE | PWM-W MAPE % | PWM-W COV80 % | best baseline | its MAE |", "|---|---|---|---|---|---|"]
        for tg, s in R["tracks"][FINAL]["S"].items():
            bl = min(((v["S"][tg]["MAE"], n) for n, v in R["tracks"].items()
                      if n in ("Last observed value", "Same hour yesterday", "Hour x month climatology")), default=(0, "-"))
            L.append(f"| {tg} | {s['MAE']:.2f} | {s['MAPE']:.1f} | {s['COV80']:.1f} | {bl[1]} | {bl[0]:.2f} |")
        L.append("")
    for t, sig in R["significance"].items():
        L += [f"## Significance, PM2.5 Track {t}: {FINAL} vs each (negative = PWM-W better)", "",
              "| vs | MAE | RMSE | MAPE | QL | IS80 |", "|---|---|---|---|---|---|"]
        for other, res in sig.items():
            cell = lambda m: (f"{res[m]['verdict']} {res[m]['rel_diff_pct']:+.2f}%" if m in res else "-")
            L.append(f"| {other} | " + " | ".join(cell(m) for m in ("MAE", "RMSE", "MAPE", "QL", "IS80")) + " |")
        L.append("")
    L += ["## Runs", "", "| Run | val PM2.5 MAE | params | s/step | min |", "|---|---|---|---|---|"]
    for n, v in R["runs"].items():
        L.append(f"| {n} | {v['val_MAE_PM25']:.3f} | {v['params']:,} | {v['sec_per_step']} | {v['seconds'] / 60:.1f} |")
    L += ["", "Decisions: `" + json.dumps(R.get("decisions", {})) + "`", ""]
    for d in {os.path.join(ROOT, "results"), CACHE}:
        open(os.path.join(d, "delhi_v02_report.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--opponents", default=OPPONENTS)
    main(ap.parse_args())
