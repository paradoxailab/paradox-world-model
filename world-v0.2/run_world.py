"""Paradox World Model v0.2: the whole study in one command (Google Colab or Kaggle, one T4 GPU, ~4.5 h).

  python run_world.py                      # full study
  python run_world.py --quick              # CPU pipeline check (minutes; numbers meaningless)

v0.2 answers v0.1's limitations:
  * two test cities never seen in pretraining: London (UK-M25, same task as v0.1) and Greater Manchester (UK-MAN),
    live 2025-26 data;
  * ~7x more pretraining data: 6 US networks + 5 regional networks from the rest of England (2024-07 .. 2026-03,
    ending before any test period; both cities excluded with a margin);
  * long context (the forecast times on each of the last 7 days, yesterday's lead-in, last 24 h hourly) for the
    60-minute horizon; a relative-error loss for MAPE; each kept only by a validation rule;
  * the five efficiency techniques re-tested at foundation scale: two pretrainings at EQUAL wall-clock compute,
    "F-tech" (sparse experts + masked self-supervision + physics + hierarchy) vs "F-plain" (none of them);
  * gentler fine-tuning, and the final model chosen on validation among scratch / fine-tuned / mixed ensembles;
  * TimesFM 3.0 also in multivariate mode (all sensors of the city together).

Every choice is made on VALIDATION data by the rules written here before the run; test windows are scored once.
"""
import argparse, copy, json, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from pw.data import load_us, load_uk, load_eng, eng_names, unseen_split, US, CITIES, H, SPD, RAW
from pw.train import train, predict, build, DEV
from pw import evaluate as E

V1 = dict(d=128, layers=3, heads=4, ff=2, experts=0, hier=True, weather=True, lc=False, bs=16, lr=2e-3, amp=True,
          drop_p=0.1, gap_p=0.2, ssl_steps=0, ssl_w=0.0, phys_w=0.0, rel_w=0.0)          # the v0.1 recipe
F_TECH = dict(d=256, layers=6, heads=8, ff=2, experts=4, hier=True, weather=True, lc=True, bs=16, lr=1e-3,
              amp=True, drop_p=0.1, gap_p=0.2, crop=256, ssl_steps=0, ssl_w=0.5, phys_w=0.1, rel_w=0.0)
F_PLAIN = dict(F_TECH, experts=0, hier=False, ssl_w=0.0, phys_w=0.0)
FT = dict(lr=2e-4, ssl_w=0.0, ssl_steps=0, phys_w=0.0)
OPP_ORDER = [("UK-M25", "tfm3"), ("UK-M25", "chronos2"), ("UK-MAN", "tfm3"), ("UK-MAN", "chronos2"),
             ("UK-M25", "tfm3mv"), ("UK-MAN", "tfm3mv")]
OPP_MIN = {"tfm3": 45, "chronos2": 20, "tfm3mv": 45}          # rough T4 minutes per city (from v0.1), for skipping
TEST_STRIDE, VAL_STRIDE = 8, 4
PER_DAY = SPD // TEST_STRIDE
FINAL = "PWM-W v0.2"

CACHE = os.environ.get("PW_CACHE", os.path.join(ROOT, "results", "cache"))   # checkpoints: a dropped session resumes
RES = {"version": "Paradox World Model v0.2", "cities": {}, "runs": {}, "pretrain": {}, "decisions": {}}
T0 = time.time()


def log(*a):
    print(*a, flush=True)


def emit(kind, **kw):
    log("RESULT " + json.dumps({"kind": kind, **kw}, default=float))


def save():
    for d in {os.path.join(ROOT, "results"), CACHE}:
        os.makedirs(d, exist_ok=True)
        json.dump(RES, open(os.path.join(d, "world_v02_results.json"), "w"), indent=1, default=float)


def ckpt(kind, name):
    d = os.path.join(CACHE, kind)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name.replace("/", "__") + (".pt" if kind != "opponents" else ".npz"))


class City:
    def __init__(self, net, q):
        self.net = net
        self.seen, self.unseen = unseen_split(net.N)
        self.all = np.arange(net.N)
        self.upos = np.searchsorted(self.all, self.unseen)
        self.tr = net.origins("train")
        self.val = net.origins("val", VAL_STRIDE)
        self.test = net.origins("test", TEST_STRIDE)
        if q:
            self.val, self.test = self.val[:48], self.test[:96]
        self.VAL = (net, self.val, self.seen)
        self.pred = {"S": {}, "U": {}, "D": {}}
        self.res = {"data": net.describe(), "seen": len(self.seen), "unseen": len(self.unseen), "tracks": {},
                    "opponents": {}, "significance": {}}
        RES["cities"][net.name] = self.res

    def truth(self, org, nodes):
        return self.net.y[org[:, None] + np.arange(H)[None]][:, :, nodes].transpose(0, 2, 1)

    def predict(self, models, track, org, use_w=True):
        qs, y = [], None
        for m in models:
            m.use_w = use_w and m.cfg["weather"]
            if track == "U":
                qq, y = predict(m, self.net, org, self.all); qq, y = qq[:, self.upos], y[:, self.upos]
            else:
                qq, y = predict(m, self.net, org, self.seen, dark=0.3 if track == "D" else None)
            qs.append(qq)
        return np.sort(np.mean(qs, 0), -1), y

    def val_mae(self, models, use_w=True):
        qv, yv = self.predict(models, "S", self.val, use_w)
        return E.score(qv, yv)["MAE"]

    def evaluate(self, name, models, calibrate=True, use_w=True, tracks=("S", "U", "D"), keep=True, extra=None):
        out, d = {}, None
        if calibrate:
            qv, yv = self.predict(models, "S", self.val, use_w)
            d = E.fit_cqr(qv, yv)
            out["val"] = E.score(qv, yv)
        for t in tracks:
            qt, yt = self.predict(models, t, self.test, use_w)
            if d is not None:
                qt = E.apply_cqr(qt, d)
            out[t] = E.score(qt, yt)
            if keep:
                self.pred[t][name] = qt
                self.pred[t]["_y"] = yt
            emit("test", city=self.net.name, model=name, track=t, **{k: round(v, 4) for k, v in out[t].items()})
        out.update(extra or {})
        self.res["tracks"][name] = out
        save()
        return out

    def baselines(self):
        y = self.net.y
        for kind, nm in (("last", "Last observed value"), ("week", "Same time last week")):
            def make(org, nodes):
                fo = org[:, None] + np.arange(H)[None]
                wk = y[fo - 7 * SPD][:, :, nodes]
                if kind == "last":
                    hi = y[org[:, None] + np.arange(-12, 0)[None]][:, :, nodes]
                    li = np.where(~np.isnan(hi), np.arange(12)[None, :, None], -1).max(1)
                    v = np.take_along_axis(hi, np.maximum(li, 0)[:, None], 1)[:, 0]
                    v = np.where(li >= 0, v, y[fo - SPD][:, 0][:, nodes])
                    p = np.repeat(v[:, None], H, 1)
                else:
                    p = wk
                p = np.nan_to_num(np.where(np.isnan(p), wk, p)).transpose(0, 2, 1)
                return np.repeat(p[..., None], 3, -1).astype(np.float32)
            d = E.fit_cqr(make(self.val, self.seen), self.truth(self.val, self.seen))
            out = {}
            for t, nodes in (("S", self.seen), ("U", self.unseen)):
                qt = E.apply_cqr(make(self.test, nodes), d)
                out[t] = E.score(qt, self.truth(self.test, nodes))
                self.pred[t][nm] = qt
                emit("test", city=self.net.name, model=nm, track=t, **{k: round(v, 4) for k, v in out[t].items()})
            self.res["tracks"][nm] = out

    def significance(self, reps):
        for t in ("S", "U", "D"):
            if FINAL not in self.pred[t]:
                continue
            yt = self.pred[t]["_y"]
            self.res["significance"][t] = {}
            for other in self.pred[t]:
                if other in ("_y", FINAL):
                    continue
                res = {}
                for met in ("MAE", "RMSE", "MAPE", "QL", "IS80"):
                    c = E.compare(self.pred[t][FINAL], self.pred[t][other], yt, PER_DAY, met, reps=reps)
                    if c:
                        res[met] = c
                self.res["significance"][t][other] = res
        save()


def main(a):
    q = a.quick
    st = (lambda n: max(20, n // 100)) if q else (lambda n: n)
    left = lambda: a.budget - (time.time() - T0) / 60
    log(f"Paradox World Model v0.2 on {DEV} ({torch.cuda.get_device_name(0) if DEV == 'cuda' else 'cpu'}), "
        f"budget {a.budget} min")
    cities = {}
    for c in CITIES:
        try:
            cities[c] = City(load_uk(c), q); log(cities[c].net.describe())
        except FileNotFoundError as e:
            log(f"  {c}: not found ({e})")
    pre = []
    for n in US:
        try:
            pre.append(load_us(n)); log(pre[-1].describe())
        except FileNotFoundError as e:
            log(f"  {n}: not found ({e})")
    eng = [load_eng(n) for n in eng_names()]
    for n in eng:
        log(n.describe())
    pre += eng
    RES["pretraining_networks"] = [n.describe() for n in pre]
    RES["pretraining_points"] = int(sum(np.isfinite(n.y[:n.bounds["train"][1]]).sum() for n in pre))
    log(f"pretraining: {len(pre)} networks, {RES['pretraining_points']:,} observed training values")

    def fit(name, cfg, city, org=None, steps=None, seed=0, init=None):
        log(f"== {name} (seed {seed}, {(time.time() - T0) / 60:.0f} min elapsed)")
        f = ckpt("runs", name)
        if os.path.exists(f) and (not q or os.environ.get("PW_TEST_RESUME")):
            z = torch.load(f, map_location="cpu", weights_only=False)
            m = build(cfg); m.load_state_dict(z["state"]); info = z["info"]; info["resumed"] = True
        else:
            src = [(city.net, city.tr if org is None else org, city.seen, 1.0)]
            m, info = train(cfg, src, city.VAL, steps=steps, seed=seed, init=init, log=lambda *x: None)
            info["config"] = dict(cfg)
            info.pop("curve", None)
            torch.save({"state": m.state_dict(), "info": info}, f)
        RES["runs"][name] = info
        emit("run", name=name, seed=seed, val_MAE=round(info["val_MAE"], 4), val_MAPE=round(info["val_MAPE"], 3),
             params=info["params"], active=info["active_params"], sec_per_step=info["sec_per_step"],
             seconds=info["seconds"])
        save()
        return m, info

    # ------------------------------------------------------------ 1 baselines
    for c in cities.values():
        c.baselines()
    save()

    # ------------------------------------------------------------ 2 scratch recipe: v0.1 vs + long context vs + relative loss
    SCR, FTS = st(a.uk_steps), st(a.ft_steps)
    for cn, c in cities.items():
        for s in (0, 1, 2):
            fit(f"{cn}/v1-s{s}", V1, c, steps=SCR, seed=s)
        fit(f"{cn}/lc-s0", dict(V1, lc=True), c, steps=SCR)
        fit(f"{cn}/lc-rel-s0", dict(V1, lc=True, rel_w=0.3), c, steps=SCR)
    z_lc, z_rel_mae, rel_mape = [], [], []
    for cn in cities:
        v = [RES["runs"][f"{cn}/v1-s{s}"]["val_MAE"] for s in (0, 1, 2)]
        sig = max(float(np.std(v, ddof=1)), 1e-6)
        RES["decisions"][f"{cn}/sigma"] = sig
        z_lc.append((RES["runs"][f"{cn}/v1-s0"]["val_MAE"] - RES["runs"][f"{cn}/lc-s0"]["val_MAE"]) / sig)
        z_rel_mae.append((RES["runs"][f"{cn}/lc-s0"]["val_MAE"] - RES["runs"][f"{cn}/lc-rel-s0"]["val_MAE"]) / sig)
        rel_mape.append(RES["runs"][f"{cn}/lc-rel-s0"]["val_MAPE"] / RES["runs"][f"{cn}/lc-s0"]["val_MAPE"] - 1)
    keep_lc = bool(np.mean(z_lc) > 2)
    keep_rel = bool(np.mean(rel_mape) < -0.02 and np.mean(z_rel_mae) > -2)
    RES["decisions"].update({"long_context": keep_lc, "z_long_context": z_lc, "relative_loss": keep_rel,
                             "rel_MAPE_change": rel_mape, "z_rel_MAE": z_rel_mae,
                             "rules": "long context kept if mean (over cities) val-MAE gain > 2 sigma; relative loss "
                                      "kept if mean val MAPE falls > 2% and val MAE does not worsen by > 2 sigma"})
    REC = dict(V1, lc=keep_lc, rel_w=0.3 if keep_rel else 0.0)
    emit("decisions", **{k: v for k, v in RES["decisions"].items() if not k.endswith("sigma")})

    # ------------------------------------------------------------ 3 foundation pretraining at equal compute
    def pretrain(name, cfg, minutes):
        cfg = dict(cfg, lc=keep_lc, rel_w=REC["rel_w"])
        src = [(n, n.origins("train"), None, float(np.sqrt(n.N * len(n.origins("train"))))) for n in pre]
        big = max(eng or pre, key=lambda n: n.N)
        pval = (big, big.origins("val", 16)[: (24 if q else 600)], None)
        f = ckpt("pretrain", name)
        if os.path.exists(f) and (not q or os.environ.get("PW_TEST_RESUME")):
            z = torch.load(f, map_location="cpu", weights_only=False)
            m = build(cfg); m.load_state_dict(z["state"]); info = z["info"]; info["resumed"] = True
            log(f"== {name}: resumed from checkpoint")
        else:
            _, probe = train(cfg, src, None, steps=20 if q else 80, seed=0)
            steps = st(int(minutes * 60 / max(probe["sec_per_step"], 1e-3)))
            log(f"== {name}: {probe['sec_per_step']:.3f} s/step -> {steps} steps in {minutes} min")
            m, info = train(cfg, src, pval, steps=steps, seed=0, log=log, budget_s=minutes * 60 * 1.15)
            info.pop("curve", None)
            torch.save({"state": m.state_dict(), "info": info}, f)
        nm = []
        for n in (eng or pre):                                        # held-out time of the pretraining regions
            org = n.origins("val", 16)[: (16 if q else None)]
            qq, yy = predict(m, n, org, None, chunk=8)
            nm.append(E.score(qq, yy)["MAE"] / max(float(np.nanmean(np.abs(yy))), 1e-6))
        info.pop("curve", None)
        info.update(config=cfg, selection_score=float(np.mean(nm)),
                    selection="mean over England regions of validation MAE / mean flow (held-out time)")
        RES["pretrain"][name] = info
        emit("pretrain", name=name, steps=info["steps"], params=info["params"], active=info["active_params"],
             selection_score=round(info["selection_score"], 5), minutes=round(info["seconds"] / 60, 1))
        for c in cities.values():
            c.evaluate(f"PWM-W {name} zero-shot", [m], calibrate=False, use_w=False, tracks=("S", "U"))
        save()
        return copy.deepcopy(m.state_dict())

    states = {"F-tech": pretrain("F-tech", F_TECH, 1 if q else a.pretrain_min),
              "F-plain": pretrain("F-plain", F_PLAIN, 1 if q else a.pretrain_min)}
    fpick = min(states, key=lambda k: RES["pretrain"][k]["selection_score"])
    FCFG = dict(F_TECH if fpick == "F-tech" else F_PLAIN, lc=keep_lc, rel_w=REC["rel_w"])
    RES["decisions"]["pretraining"] = {"chosen": fpick, "scores": {k: RES["pretrain"][k]["selection_score"]
                                                                   for k in states},
                                      "five_techniques_help_at_scale": fpick == "F-tech"}
    emit("decisions", pretraining=fpick)

    # ------------------------------------------------------------ 4 final models per city
    for cn, c in cities.items():
        scr = [fit(f"{cn}/final-scratch-s{s}", REC, c, steps=SCR, seed=s)[0] for s in (100, 101, 102)]
        ftm = [fit(f"{cn}/final-ft-s{s}", dict(FCFG, **FT), c, steps=FTS, seed=s, init=states[fpick])[0]
               for s in (100, 101, 102)]
        cand = {"scratch": scr, "fine-tuned": ftm, "mixed": scr + ftm}
        vm = {k: c.val_mae(v) for k, v in cand.items()}
        pick = min(vm, key=vm.get)
        c.res["final_choice"] = {"val_MAE": vm, "chosen": pick}
        emit("final_choice", city=cn, chosen=pick, **{k: round(v, 4) for k, v in vm.items()})
        ms = cand[pick]
        b = c.net.batch(c.test[:1], c.seen, DEV)
        with torch.no_grad():
            for m in ms:
                m(b)
            if DEV == "cuda":
                torch.cuda.synchronize()
            t = time.time()
            for _ in range(5):
                for m in ms:
                    m(b)
            if DEV == "cuda":
                torch.cuda.synchronize()
        lat = (time.time() - t) / 5 * 1000
        c.evaluate(FINAL, ms, extra={"members": len(ms), "recipe": pick,
                                     "params_per_member": sorted({m.n_params() for m in ms}),
                                     "latency_ms_per_network_forecast": round(lat, 2)})
        c.significance(200 if q else 2000)
        del scr, ftm, cand
        torch.cuda.empty_cache() if DEV == "cuda" else None
    write_report()

    # ------------------------------------------------------------ 5 foundation-model opponents (zero-shot)
    if a.opponents:
        from pw import opponents as OPP
        want = set(a.opponents.split(","))
        for cn, key in OPP_ORDER:
            if key not in want or cn not in cities:
                continue
            if left() < OPP_MIN[key] and not q:
                log(f"  skipping {key} on {cn}: {left():.0f} min left")
                cities[cn].res["opponents"][key] = {"skipped": f"time budget ({left():.0f} min left)"}
                continue
            c = cities[cn]
            try:
                vo = c.val[::4]
                f = ckpt("opponents", f"{cn}_{key}")
                if os.path.exists(f) and (not q or os.environ.get("PW_TEST_RESUME")):
                    z = np.load(f, allow_pickle=False)
                    qt, qv, meta = z["qt"], z["qv"], json.loads(str(z["meta"]))
                    log(f"  {key} on {cn}: resumed from cached forecasts")
                else:
                    qt, meta = OPP.run(key, c.net.y, c.test, c.all, H, log=log)
                    qv, _ = OPP.run(key, c.net.y, vo, c.all, H, log=log)
                    np.savez_compressed(f, qt=qt.astype(np.float32), qv=qv.astype(np.float32),
                                        meta=np.array(json.dumps(meta)))
                d = E.fit_cqr(qv[:, c.seen], c.truth(vo, c.seen))
                out = {"meta": meta}
                for t, ix in (("S", c.seen), ("U", c.unseen)):
                    qq = E.apply_cqr(qt[:, ix], d)
                    out[t] = E.score(qq, c.truth(c.test, ix))
                    c.pred[t][f"{meta['name']} zero-shot"] = qq
                    emit("test", city=cn, model=meta["name"] + " zero-shot (+CQR)", track=t,
                         **{k: round(v, 4) for k, v in out[t].items()})
                c.res["opponents"][key] = out
            except Exception as e:
                log(f"  opponent {key} on {cn} failed: {type(e).__name__}: {e}")
                cities[cn].res["opponents"][key] = {"error": f"{type(e).__name__}: {e}"}
            c.significance(200 if q else 2000)
            for t, sig in c.res["significance"].items():
                for other, res in sig.items():
                    if "zero-shot" in other and "PWM" not in other:
                        emit("sig", city=cn, track=t, vs=other,
                             **{m: f"{r['verdict']} {r['rel_diff_pct']:+.2f}% p={r['p']:.2g}" for m, r in res.items()})
            write_report()
            torch.cuda.empty_cache() if DEV == "cuda" else None

    RES["minutes_total"] = round((time.time() - T0) / 60, 1)
    save()
    write_report()
    log(f"done in {RES['minutes_total']} min")


def write_report():
    """Markdown tables generated from the results JSON (no hand-typed numbers)."""
    R = RES
    L = ["# Paradox World Model v0.2 results (generated from results/world_v02_results.json)", "",
         f"Pretraining: {len(R.get('pretraining_networks', []))} networks, "
         f"{R.get('pretraining_points', 0):,} observed training values.", ""]
    for cn, C in R["cities"].items():
        L += [f"# {cn}", "", "Data: " + C["data"], ""]
        names = {"S": "Track S: seen sensors", "U": "Track U: locations never trained on",
                 "D": "Track D: seen sensors, 30% dark"}
        for t, title in names.items():
            rows = [(v[t]["MAE"], n, v[t]) for n, v in C["tracks"].items() if t in v]
            rows += [(v[t]["MAE"], v["meta"]["name"] + " zero-shot (+CQR)", v[t]) for v in C["opponents"].values()
                     if t in v]
            if not rows:
                continue
            L += [f"## {title}", "", "| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@15 | MAE@30 | MAE@60 |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
            for _, n, s in sorted(rows, key=lambda r: r[0]):
                L.append(f"| {n} | {s['MAE']:.3f} | {s['RMSE']:.3f} | {s['MAPE']:.2f} | {s['QL']:.3f} | {s['IS80']:.2f} | "
                         f"{s['COV80']:.1f} | {s['MAE@15min']:.3f} | {s['MAE@30min']:.3f} | {s['MAE@60min']:.3f} |")
            L.append("")
        for t, sig in C.get("significance", {}).items():
            if not sig:
                continue
            L += [f"## Significance, {cn} Track {t}: {FINAL} vs each model (negative = PWM-W better)", "",
                  "| vs | MAE | RMSE | MAPE | QL | IS80 |", "|---|---|---|---|---|---|"]
            for other, res in sig.items():
                cell = lambda m: (f"{res[m]['verdict']} {res[m]['rel_diff_pct']:+.2f}% (p={res[m]['p']:.2g})"
                                  if m in res else "-")
                L.append(f"| {other} | " + " | ".join(cell(m) for m in ("MAE", "RMSE", "MAPE", "QL", "IS80")) + " |")
            L.append("")
        if "final_choice" in C:
            L += ["Final choice (validation MAE): `" + json.dumps(C["final_choice"]) + "`", ""]
        skipped = {k: v for k, v in C["opponents"].items() if "meta" not in v}
        if skipped:
            L += ["Opponents not scored: `" + json.dumps(skipped) + "`", ""]
    L += ["# Runs", "", "| Run | val MAE | val MAPE | params | active | s/step | min |", "|---|---|---|---|---|---|---|"]
    for n, v in list(R["runs"].items()) + [(f"pretrain {k}", v) for k, v in R["pretrain"].items()]:
        L.append(f"| {n} | {v['val_MAE']:.4f} | {v.get('val_MAPE') or float('nan'):.3f} | {v['params']:,} | "
                 f"{v['active_params']:,} | {v['sec_per_step']} | {v['seconds'] / 60:.1f} |")
    L += ["", "Decisions (validation rules): `" + json.dumps(R.get("decisions", {})) + "`", ""]
    for d in {os.path.join(ROOT, "results"), CACHE}:
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "world_v02_report.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--budget", type=float, default=280, help="minutes for the whole study (after data download)")
    ap.add_argument("--uk_steps", type=int, default=3000)
    ap.add_argument("--ft_steps", type=int, default=2000)
    ap.add_argument("--pretrain_min", type=float, default=25)
    ap.add_argument("--opponents", default="tfm3,chronos2,tfm3mv")
    main(ap.parse_args())
