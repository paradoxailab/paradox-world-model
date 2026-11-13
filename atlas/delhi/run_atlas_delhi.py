"""Atlas on real data: Delhi's CPCB air-quality stations (stage 7 of the Atlas plan).

Same data file, splits, test windows and scoring as the PWM-W Delhi league (pw/ddata.py, pw/evaluate.py from branch
delhi-v0.2): hourly station data, last 182 days = TEST, the 61 days before = VALIDATION, 20% of stations never
trained on (Track U). Forecast: the next 24 h of PM2.5 at every station, scored every 6 h.

Atlas sees the last 72 h of 15 variables at every station (PM2.5, PM10, NO2, ozone as ratios to the station's
past-week mean; CO, SO2, NH3, NO, temperature, humidity, wind speed and direction, solar radiation, pressure), the
hour and weekday, 14 daily PM2.5 means and the same hours 7 days earlier. Observations only: no weather forecasts,
no foundation-model forecasts, no pretrained weights. It forecasts all 15 variables; PM2.5 carries the loss weight.

Everything is decided on VALIDATION by rules written here; TEST is scored once per reported entry.
  1  baselines: last observed value, same hour yesterday
  2  variants (seed 0, all training data): plain / ID (in-context identification of PM2.5 dynamics) x sizes.
     Noise floor: sigma of validation PM2.5 MAE over 3 seeds of plain at the smallest size.
     Chosen = lowest validation MAE; if it does not beat plain-smallest by > 2 sigma, plain-smallest is kept.
  3  final: chosen recipe, 3 fresh seeds, ensembled, CQR on validation; Tracks S (training stations), U (unseen)
  4  what the final model uses: input groups hidden at test time; 30% of all inputs hidden
  5  foundation models zero-shot on the same windows (512 h of history each), significance tests
  6  data threshold: plain and ID at the smallest size trained on the last 0.5, 1, 2, 4 months and on everything
Stages run in this order inside a wall-clock budget; a stage that does not fit is skipped and reported as skipped.

  python tools/fetch_delhi.py && python run_atlas_delhi.py            # --quick: pipeline check, numbers meaningless
"""
import argparse, json, math, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import Delhi, SPD, FLOOR, TARGETS, DM
from pw import evaluate as E
from atlas.model import sized
from atlas import threshold as TH

L, H = 72, 24
LONG = 0          # extra hours of PM2.5-only history before the 72-h window (0 = off); set by run_atlas_threshold.py
DEV = "cuda" if torch.cuda.is_available() else "cpu"
OUT = os.environ.get("ATLAS_OUT", os.path.join(ROOT, "results"))
TEST_STRIDE, VAL_STRIDE, TRAIN_STRIDE = 6, 3, 3
CAP_MIN = float(os.environ.get("ATLAS_CAP_MIN", 50))      # no single training run may take longer than this
PER_DAY, HZ = SPD // TEST_STRIDE, (0, 5, 11, 23)
RES = {"runs": {}, "tracks": {}, "opponents": {}, "significance": {}, "threshold": {}, "threshold_fit": {}, "ablation": {}}
T0 = time.time()


def log(*a):
    print(*a, flush=True)


def save():
    os.makedirs(OUT, exist_ok=True)
    json.dump(RES, open(os.path.join(OUT, "atlas_delhi_results.json"), "w"), indent=1, default=float)


# ---------------------------------------------------------------------------------------------------- data
def make_batch(D, org, nodes, dev=DEV):
    """Windows for origins `org` at stations `nodes`. Values: 4 pollutants / station's past-week mean, then the
    standardised auxiliary variables. Returns tensors shaped for Atlas ([B, n, time, channels])."""
    D.to(dev)
    o = torch.as_tensor(org, device=dev)
    nd = torch.as_tensor(nodes, device=dev)
    B, n = len(o), len(nd)
    hl = o[:, None] + torch.arange(-L, 0, device=dev)[None]
    fo_raw = o[:, None] + torch.arange(H, device=dev)[None]
    fo = fo_raw.clamp(max=D.T - 1)
    s = D.t_s[o - 1][:, nd]                                                   # [B, n, K]
    g = lambda T, ix: T[ix][:, :, nd].permute(0, 2, 1, 3)                     # [B, n, len, C]
    yc = torch.cat([g(D.t_y, hl) / s[:, :, None], g(D.t_a, hl)], -1)
    mc = torch.cat([g(D.t_o, hl), g(D.t_ao, hl)], -1).float()
    yf = torch.cat([g(D.t_y, fo) / s[:, :, None], g(D.t_a, fo)], -1)
    of = (torch.cat([g(D.t_o, fo), g(D.t_ao, fo)], -1) & (fo_raw < D.T)[:, None, :, None]).float()

    def cal(ix):
        tod, dow = D.t_tod[ix].float() * (2 * math.pi / 24), D.t_dow[ix].float() * (2 * math.pi / 7)
        c = torch.stack([torch.sin(tod), torch.cos(tod), torch.sin(dow), torch.cos(dow)], -1)   # [B, len, 4]
        return c[:, None].expand(-1, n, -1, -1)

    dm = o[:, None] + torch.arange(-DM * SPD, 0, device=dev)[None]
    dv = D.t_y[dm][:, :, nd, 0].reshape(B, DM, SPD, n); do = D.t_o[dm][:, :, nd, 0].float().reshape(B, DM, SPD, n)
    cnt = do.sum(2)
    daily = ((dv * do).sum(2) / cnt.clamp(min=1)).permute(0, 2, 1) / s[:, :, :1]            # [B, n, DM]
    l7 = (fo_raw - 7 * SPD).clamp(min=0)
    lag7 = D.t_y[l7][:, :, nd, 0].permute(0, 2, 1) / s[:, :, :1]
    lag7o = D.t_o[l7][:, :, nd, 0].permute(0, 2, 1).float()
    static = torch.cat([daily, (cnt > 0).float().permute(0, 2, 1), lag7 * lag7o, lag7o,
                        torch.log(s[:, :, :1]) / 5, D.t_sf[o - 1][:, nd][:, :, :1].float()], -1)
    if LONG:                                              # PM2.5 alone, hours -(L+LONG) .. -L, as extra static inputs
        lg = (o[:, None] + torch.arange(-L - LONG, -L, device=dev)[None]).clamp(min=0)
        lo_ = D.t_o[lg][:, :, nd, 0].permute(0, 2, 1).float()
        static = torch.cat([static, D.t_y[lg][:, :, nd, 0].permute(0, 2, 1) / s[:, :, :1] * lo_, lo_], -1)
    A = D.t_A[nd][:, nd]
    eye = torch.eye(n, device=dev)
    geo = torch.stack([A, eye, (A > 0).float()], -1)
    basis = torch.stack([eye, A / A.sum(1, keepdim=True).clamp(min=1e-6)])
    return dict(yc=yc * mc, mc=mc, uc=cal(hl), uf=cal(fo_raw), yf=yf, of=of, static=static, geo=geo, basis=basis,
                s=s[:, :, 0])


def truth(D, org, nodes):
    return D.Y[org[:, None] + np.arange(H)[None]][:, :, nodes, 0].transpose(0, 2, 1)       # [W, n, H], NaN = missing


# ---------------------------------------------------------------------------------------------------- model
def build(D, size, sysid):
    C = D.K + D.Ca
    am = os.environ.get("ATLAS_MODEL", "")
    if am.startswith("atlasw"):                           # Atlas-W days 2-3: ATLAS_MODEL=atlasw:<width>; size is ignored
        from atlas.atlasw import AtlasW
        return AtlasW(d=int(am.split(":")[1]) if ":" in am else 32, L=L, H=H, C=C, U=4, static=2 * DM + 2 * H + 2 + 2 * LONG,
                      lo=[0.0] * D.K + [float("-inf")] * D.Ca).to(DEV)
    kw = dict(L=L, H=H, C=C, U=4, lat_steps=6, spatial=True, geo_dim=3, static=2 * DM + 2 * H + 2 + 2 * LONG,
              lo=[0.0] * D.K + [float("-inf")] * D.Ca, sysid=bool(sysid), K=2, lags=3, id_ch=1, fill="interp")
    if os.environ.get("ATLAS_PHYS") == "1":               # Atlas-P (ICML programme): the physics decoder
        kw["phys_dec"] = True
    return sized(int(size), **kw).to(DEV)


def forward(m, b, mc=None):
    return m(b["yc"] if mc is None else b["yc"] * mc, b["mc"] if mc is None else mc, b["uc"], b["uf"], b["geo"],
             b["basis"] if m.sysid else None, b["static"])


@torch.no_grad()
def predict(m, D, org, nodes, hide=None, bs=48, seed=0):
    """PM2.5 quantiles in ug/m3 [W, n, H, 3]. hide: None, a float (share of inputs hidden at random), or a list of
    channel indices hidden everywhere."""
    m.eval(); out = []
    g = torch.Generator(device=DEV).manual_seed(seed)
    for i in range(0, len(org), bs):
        b = make_batch(D, org[i:i + bs], nodes)
        mc = None
        if isinstance(hide, float):
            mc = b["mc"] * (torch.rand(b["mc"].shape, generator=g, device=DEV) >= hide).float()
        elif hide == "context48":
            mc = b["mc"].clone(); mc[:, :, :L - 24] = 0
        elif hide is not None:
            mc = b["mc"].clone(); mc[..., hide] = 0
        q = forward(m, b, mc)[0][:, :, :, 0] * b["s"][:, :, None, None]
        out.append(q.float().cpu().numpy())
    m.train()
    return np.concatenate(out)


def train(D, size, sysid, org, val_org, seed, max_steps, name, bs=16, patience=10, every=100):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    m = build(D, size, sysid)
    lr = 1e-3 if m.cfg["d"] <= 256 else 5e-4
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / 100) * (0.1 + 0.45 * (1 + math.cos(math.pi * min(1, s / max_steps)))))
    chw = torch.tensor([1.0] + [0.1] * (D.K - 1) + [0.05] * D.Ca, device=DEV)            # PM2.5 carries the loss
    qs = torch.tensor([0.1, 0.5, 0.9], device=DEV)
    yv = truth(D, val_org, D.seen)
    best, state, bad, t0, step = float("inf"), None, 0, time.time(), 0
    for step in range(1, max_steps + 1):
        b = make_batch(D, rng.choice(org, min(bs, len(org)), replace=False), D.seen)
        rate = torch.rand(b["mc"].shape[0], 1, 1, 1, device=DEV) * 0.4                    # hide 0-40% of the inputs
        mc = b["mc"] * (torch.rand(b["mc"].shape, device=DEV) >= rate).float()
        q, rec, ex = forward(m, b, mc)
        e = b["yf"][..., None] - q
        w = b["of"] * chw
        loss = (torch.maximum(qs * e, (qs - 1) * e).mean(-1) * w).sum() / w.sum().clamp(min=1)
        hid = b["mc"] - mc
        loss = loss + 0.2 * (((rec - b["yc"]) ** 2) * hid * chw).sum() / (hid * chw).sum().clamp(min=1)
        if sysid:
            o1 = b["of"][..., :1]
            loss = loss + 0.5 * ((ex["base"] - b["yf"][..., :1]).abs() * o1).sum() / o1.sum().clamp(min=1)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step(); sched.step()
        if step % every == 0 or step == max_steps:
            v = float(np.nanmean(np.abs(predict(m, D, val_org, D.seen)[..., 1] - yv)))
            if v < best - 1e-4:
                best, bad, state = v, 0, {k: x.detach().clone() for k, x in m.state_dict().items()}
            else:
                bad += 1
            log(f"  {name} step {step} val MAE {v:.3f} (best {best:.3f}) {time.time() - t0:.0f}s")
            if bad >= patience or time.time() - t0 > CAP_MIN * 60:      # early stop, or the per-run time cap
                break
    m.load_state_dict(state)
    info = dict(name=name, params=m.n_params(), d=m.cfg["d"], sysid=int(sysid), seed=seed, train_origins=len(org),
                steps=step, hit_time_cap=bool(time.time() - t0 > CAP_MIN * 60), minutes=round((time.time() - t0) / 60, 2), val_MAE=best, device=DEV)
    RES["runs"][name] = info
    log("RUN " + json.dumps(info, default=float)); save()
    return m, info


# ---------------------------------------------------------------------------------------------------- main
def main(a):
    q = a.quick
    D = Delhi(targets=TARGETS, backbone=False, wxfc=False)
    log(D.describe()); log(f"device {DEV}; stations seen {len(D.seen)}, unseen {len(D.unseen)}")
    RES["data"] = dict(describe=D.describe(), seen=len(D.seen), unseen=len(D.unseen), L=L, H=H)
    tr, va, te = D.origins("train", TRAIN_STRIDE), D.origins("val", VAL_STRIDE), D.origins("test", TEST_STRIDE)
    tr = tr[tr >= max(DM * SPD, 7 * SPD) + L]
    va_fast = va[::2]                                                        # early stopping uses every 2nd window
    if q:
        va, va_fast, te = va[:30], va[:30:2], te[:40]
    steps = 60 if q else a.steps
    sizes = [int(x) for x in a.sizes.split(",")]
    upos = np.arange(D.N)[D.unseen]
    yv, yS, yU = truth(D, va, D.seen), truth(D, te, D.seen), truth(D, te, D.unseen)
    sc = lambda qq, yy: E.score(qq, yy, horizons=HZ, floor=FLOOR["PM2.5"], step_min=60)
    preds = {"S": {}, "U": {}}
    left = lambda: a.hours * 3600 - (time.time() - T0)

    def record(name, qS, qU, extra=None):
        RES["tracks"][name] = {"S": sc(qS, yS), "U": sc(qU, yU), **(extra or {})}
        preds["S"][name], preds["U"][name] = qS, qU
        log(f"TEST {name}: Track S MAE {RES['tracks'][name]['S']['MAE']:.2f}, Track U MAE {RES['tracks'][name]['U']['MAE']:.2f}")
        save()

    # 1 baselines ---------------------------------------------------------------------------------------
    def baseline(kind, org, nodes):
        fo = org[:, None] + np.arange(H)[None]
        yd = D.Y[fo - SPD][:, :, nodes, 0]                                   # [W, H, n]
        if kind == "last":
            hi = D.Y[org[:, None] + np.arange(-24, 0)[None]][:, :, nodes, 0]
            li = np.where(~np.isnan(hi), np.arange(24)[None, :, None], -1).max(1)
            v = np.take_along_axis(hi, np.maximum(li, 0)[:, None], 1)[:, 0]
            p = np.repeat(np.where(li >= 0, v, yd[:, 0])[:, None], H, 1)
        else:
            p = yd
        p = np.nan_to_num(np.where(np.isnan(p), yd, p))
        return np.repeat(p.transpose(0, 2, 1)[..., None], 3, -1).astype(np.float32)

    for kind, nm in (("last", "Last observed value"), ("yday", "Same hour yesterday")):
        d = E.fit_cqr(baseline(kind, va, D.seen), yv)
        record(nm, E.apply_cqr(baseline(kind, te, D.seen), d), E.apply_cqr(baseline(kind, te, D.unseen), d))

    def test_model(models, name, extra=None):
        ens = lambda org, nodes, **k: np.sort(np.mean([predict(m, D, org, nodes, **k) for m in models], 0), -1)
        qv = ens(va, D.seen)
        d = E.fit_cqr(qv, yv)
        qS, qU = E.apply_cqr(ens(te, D.seen), d), E.apply_cqr(ens(te, np.arange(D.N))[:, upos], d)
        record(name, qS, qU, {"val_MAE": float(np.nanmean(np.abs(qv[..., 1] - yv))), **(extra or {})})
        return ens, d

    # 2 variants ----------------------------------------------------------------------------------------
    cand, models = {}, {}
    for size in sizes:
        for sysid in (0, 1):
            if left() < 1800:
                log("time budget: remaining variants skipped"); break
            nm = f"{'ID' if sysid else 'plain'}-{size // 1000}K"
            models[nm], info = train(D, size, sysid, tr, va_fast, 0, steps, nm)
            cand[nm] = (size, sysid)
            test_model([models[nm]], f"Atlas {nm} (1 seed)", {"params": info["params"]})
    base = f"plain-{sizes[0] // 1000}K"
    vb = [RES["runs"][base]["val_MAE"]]
    for s in (1, 2):
        _, info = train(D, sizes[0], 0, tr, va_fast, s, steps, f"{base}-s{s}")
        vb.append(info["val_MAE"])
    sigma = max(float(np.std(vb, ddof=1)), 1e-6)
    vals = {k: RES["runs"][k]["val_MAE"] for k in cand}
    best = min(vals, key=vals.get)
    pick = best if (vals[base] - vals[best]) / sigma > 2 else base
    RES["decision"] = dict(sigma_val_MAE=sigma, base_seeds=vb, val_MAE=vals, chosen=pick,
                           rule="lowest validation PM2.5 MAE if it beats the smallest plain model by > 2 sigma")
    log("DECISION " + json.dumps(RES["decision"], default=float)); save()

    # 3 final -------------------------------------------------------------------------------------------
    FINAL = f"Atlas {pick} (3 seeds)"
    size, sysid = cand[pick]
    finals = []
    for s in (100, 101, 102):
        if left() < 1200 and finals:
            break
        finals.append(train(D, size, sysid, tr, va_fast, s, steps, f"final-s{s}")[0])
    ens, dq = test_model(finals, FINAL, {"params": finals[0].n_params(), "seeds": len(finals)})
    np.savez_compressed(os.path.join(OUT, "atlas_delhi_preds.npz"), qS=preds["S"][FINAL], qU=preds["U"][FINAL], yS=yS, yU=yU,
                        test_origins=te, seen=D.seen, unseen=D.unseen, stations=np.array(D.stations))
    torch.save({"cfg": finals[0].cfg, "states": [m.state_dict() for m in finals], "stations": D.stations,
                "cqr_delta": dq.tolist()}, os.path.join(OUT, "atlas_delhi.pt"))

    # 4 what the model uses -------------------------------------------------------------------------------
    full = float(np.nanmean(np.abs(preds["S"][FINAL][..., 1] - yS)))
    groups = {"other pollutants hidden (PM10, NO2, ozone, CO, SO2, NH3, NO)": [1, 2, 3, 4, 5, 6, 7],
              "meteorology hidden (temperature, humidity, wind, sun, pressure)": list(range(8, D.K + D.Ca)),
              "only the last 24 h visible (not 72 h)": "context48", "30% of all inputs hidden at random": 0.3}
    RES["ablation"]["full"] = full
    for nm, hide in groups.items():
        v = float(np.nanmean(np.abs(ens(te, D.seen, hide=hide)[..., 1] - yS)))
        RES["ablation"][nm] = dict(test_S_MAE=v, change_pct=100 * (v / full - 1))
        log(f"ABLATION {nm}: {v:.2f} ({100 * (v / full - 1):+.1f}%)")
    save()

    # 5 foundation models ---------------------------------------------------------------------------------
    if a.opponents:
        from pw import opponents as OPP
        y2 = D.Y[:, :, 0]
        for key in a.opponents.split(","):
            if left() < 900:
                log(f"time budget: opponent {key} skipped"); RES["opponents"][key] = {"error": "skipped: time budget"}; continue
            f = os.path.join(OUT, "opponents", key + ".npz")
            try:
                if os.path.exists(f) and not q:
                    zz = np.load(f); qt, qv, meta = zz["qt"], zz["qv"], json.loads(str(zz["meta"]))
                else:
                    qt, meta = OPP.run(key, y2, te, np.arange(D.N), H, ctx=512, chunk=a.chunk, log=log)
                    qv, _ = OPP.run(key, y2, va[::4], np.arange(D.N), H, ctx=512, chunk=a.chunk, log=log)
                    os.makedirs(os.path.dirname(f), exist_ok=True)
                    np.savez_compressed(f, qt=qt, qv=qv, meta=np.array(json.dumps(meta)))
                d = E.fit_cqr(qv[:, D.seen], truth(D, va[::4], D.seen))
                nm = meta["name"] + " zero-shot"
                record(nm, E.apply_cqr(qt[:, D.seen], d), E.apply_cqr(qt[:, D.unseen], d), {"meta": meta})
                RES["opponents"][key] = {"name": nm, "meta": meta}
            except Exception as e:
                log(f"  opponent {key} failed: {type(e).__name__}: {e}")
                RES["opponents"][key] = {"error": f"{type(e).__name__}: {e}"}
            save()

    for t, yt in (("S", yS), ("U", yU)):
        RES["significance"][t] = {}
        for other, qo in preds[t].items():
            if other == FINAL:
                continue
            r = {mm: E.compare(preds[t][FINAL], qo, yt, PER_DAY, mm, reps=200 if q else 2000, floor=FLOOR["PM2.5"]) for mm in ("MAE", "RMSE", "QL")}
            RES["significance"][t][other] = {k: v for k, v in r.items() if v}
            if r["MAE"]:
                log(f"SIG track {t} vs {other}: {r['MAE']['verdict']} {r['MAE']['rel_diff_pct']:+.2f}% p={r['MAE']['p']:.2g}")
    RES["final"] = FINAL
    save(); report()

    # 6 data threshold ----------------------------------------------------------------------------------
    span = D.bounds["train"][1]
    for months in (0.5, 1, 2, 4):
        sub = tr[tr >= span - int(months * 30.4 * SPD)]
        if len(sub) < 20 or len(sub) >= len(tr) or left() < 1800:
            continue
        for sysid in (0, 1):
            nm = f"{'ID' if sysid else 'plain'}-{sizes[0] // 1000}K-{months}mo"
            m, info = train(D, sizes[0], sysid, sub, va_fast, 0, steps, nm)
            mae = float(np.nanmean(np.abs(predict(m, D, te, D.seen)[..., 1] - yS)))
            RES["threshold"][nm] = dict(months=months, sysid=sysid, train_origins=len(sub), val_MAE=info["val_MAE"], test_S_MAE=mae)
            log("THRESHOLD " + json.dumps(RES["threshold"][nm], default=float)); save()
    for sysid in (0, 1):
        nm = f"{'ID' if sysid else 'plain'}-{sizes[0] // 1000}K"
        if nm in models:
            RES["threshold"][nm + "-all"] = dict(months=round(len(tr) * TRAIN_STRIDE / (30.4 * SPD), 2), sysid=sysid, train_origins=len(tr),
                                                 val_MAE=RES["runs"][nm]["val_MAE"],
                                                 test_S_MAE=RES["tracks"][f"Atlas {nm} (1 seed)"]["S"]["MAE"])
    for sysid in (0, 1):                                   # error = floor + a * N^-alpha on the measured points
        pts = sorted((v["train_origins"], v["test_S_MAE"]) for v in RES["threshold"].values() if v["sysid"] == sysid)
        if len(pts) >= 4:
            x, y = np.log([p[0] for p in pts]), np.log([p[1] for p in pts])
            sl = float(np.polyfit(x, y, 1)[0])
            RES["threshold_fit"]["ID" if sysid else "plain"] = dict(points=pts, loglog_slope=sl)
    save()

    RES["minutes_total"] = round((time.time() - T0) / 60, 1)
    save(); report()
    log(f"done in {RES['minutes_total']} min")


def report():
    R = RES; F = R.get("final", "")
    o = ["# Atlas on Delhi PM2.5: results (generated from atlas_delhi_results.json)", "", R["data"]["describe"], ""]
    for t, title in (("S", "Track S: training stations"), ("U", "Track U: stations never trained on")):
        o += [f"## {title} (PM2.5, ug/m3, next 24 h)", "", "| Model | MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | vs final (MAE) |", "|---|---|---|---|---|---|---|---|---|---|"]
        for n, v in sorted(R["tracks"].items(), key=lambda kv: kv[1][t]["MAE"]):
            s = v[t]; g = R["significance"].get(t, {}).get(n, {}).get("MAE")
            cmp = "–" if n == F or not g else f"{'final WINS' if g['verdict'] == 'WIN' else ('final LOSES' if g['verdict'] == 'LOSS' else 'tie')} {g['rel_diff_pct']:+.1f}% (p={g['p']:.2g})"
            o.append(f"| {'**' + n + '**' if n == F else n} | {s['MAE']:.2f} | {s['RMSE']:.2f} | {s['QL']:.2f} | {s['COV80']:.0f} | {s['MAE@1h']:.2f} | {s['MAE@6h']:.2f} | {s['MAE@12h']:.2f} | {s['MAE@24h']:.2f} | {cmp} |")
        o.append("")
    if "decision" in R:
        d = R["decision"]
        o += ["## Validation choice", "", f"Noise floor (3 seeds of the smallest plain model): sigma = {d['sigma_val_MAE']:.3f} ug/m3. Rule: {d['rule']}.", "",
              "| Variant | parameters | validation MAE | training steps | minutes |", "|---|---|---|---|---|"]
        o += [f"| {k}{' (chosen)' if k == d['chosen'] else ''} | {R['runs'][k]['params']:,} | {v:.3f} | {R['runs'][k]['steps']} | {R['runs'][k]['minutes']} |" for k, v in d["val_MAE"].items()] + [""]
    th = R["threshold"]
    if th:
        o += ["## Data threshold on real data (smallest size, 1 seed)", "", "| training data | windows | plain: test MAE | ID: test MAE |", "|---|---|---|---|"]
        for mo in sorted({v["months"] for v in th.values()}):
            g = lambda s: next((f"{v['test_S_MAE']:.2f}" for v in th.values() if v["months"] == mo and v["sysid"] == s), "–")
            n = next(v["train_origins"] for v in th.values() if v["months"] == mo)
            o.append(f"| last {mo} months | {n:,} | {g(0)} | {g(1)} |")
        o += [""] + [f"{k}: error changes as (windows)^{v['loglog_slope']:.2f}" for k, v in R["threshold_fit"].items()] + [""]
    if len(R["ablation"]) > 1:
        o += ["## What the final model uses (Track S MAE with inputs hidden at test time)", "", f"All inputs: {R['ablation']['full']:.2f}", ""]
        o += [f"- {k}: {v['test_S_MAE']:.2f} ({v['change_pct']:+.1f}%)" for k, v in R["ablation"].items() if k != "full"] + [""]
    errs = {k: v["error"] for k, v in R["opponents"].items() if "error" in v}
    if errs:
        o += ["## Opponents that did not run", ""] + [f"- {k}: {v}" for k, v in errs.items()] + [""]
    open(os.path.join(OUT, "ATLAS_DELHI_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--sizes", default="250000,1000000")
    ap.add_argument("--hours", type=float, default=10.5, help="wall-clock budget; later stages are skipped, not cut")
    ap.add_argument("--opponents", default="chronos-bolt,chronos2,tfm25,tfm3")
    ap.add_argument("--chunk", type=int, default=256)
    main(ap.parse_args())
