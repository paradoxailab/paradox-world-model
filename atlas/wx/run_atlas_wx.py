"""Atlas-WX Stage 1 (atlas/PREREG_WX.md section 3): the observation core on every qualifying ISD station.

Data: wx_<YYYY>.npz (values [stations, hours, 6] float16: T, Td, WD, WS, SLP, P6) and stations.json from
atlas/wx/fetch_isd_all.py, hours from 1995-01-01T00. Stage 1 reads the first five variables (P6 enters in Stage 2).
Recipe as Atlas-5K (atlas/delhi/run_atlas_5k.py): input the last 48 hours of the station and its k-1 nearest stations,
forecast the next H = 24 hours, pinball loss on the 10/50/90% quantiles plus reconstruction of 15% hidden inputs.
Splits (fixed by the pre-registration): train 1995-2022, validation 2023 (every 4th station, every 6th hour).
E = mean over the five variables of MAE / the WEATHER-5K benchmark's scale. No test year is scored in Stage 1: the
test (2025) belongs to the Stage 2 hybrid.

The values live in CPU memory (about 27 GB for 10,000 stations; a high-RAM runtime) unless the GPU has room for them.

  python run_atlas_wx.py --size 10000000 --tag wx_s1_10m --pause-at-cap --cap 600
  python run_atlas_wx.py --init <wx_s1_10m_s600.pt> --grow 2,7,7 --tag wx_s1_30m ...   # function-preserving growth
Re-running the same command resumes from {tag}_s{seed}_last.pt in ATLAS_OUT.
"""
import argparse, glob, json, math, os, sys, time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ROOT))
from atlas.model import sized, QS

RAW = os.environ.get("WX_DATA", "/content/drive/MyDrive/PWM-WX/isd")
OUT = os.environ.get("ATLAS_OUT", "/content/drive/MyDrive/PWM-WX/runs")
DEV = "cuda" if torch.cuda.is_available() else "cpu"
VARS = ["TMP", "DEW", "WND_ANGLE", "WND_RATE", "SLP"]
NAMES = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
MEAN = np.array([12.70852261, 6.52705582, 191.18867587, 3.36941836, 1014.85317029], np.float32)   # the benchmark's scaler
STD = np.array([13.08167293, 12.13875438, 99.67403125, 2.65729403, 9.17480999], np.float32)
L, K = 48, 16                                             # input hours; stations per neighbourhood (itself + 15)
START = np.datetime64("1995-01-01T00")
hour = lambda s: int((np.datetime64(s) - START) / np.timedelta64(1, "h"))
YEARS = {"train": (hour("1995-01-01T00"), hour("2023-01-01T00")), "val": (hour("2023-01-01T00"), hour("2024-01-01T00"))}
Y_LAST = 2023                                             # Stage 1 never loads 2024 or 2025


def log(*a):
    print(*a, flush=True)


def load(quick=False):
    st = json.load(open(os.path.join(RAW, "stations.json")))
    n = 40 if quick else len(st)
    lat = np.array([x["lat"] for x in st[:n]], np.float32); lon = np.array([x["lon"] for x in st[:n]], np.float32)
    elev = np.array([x["elev"] for x in st[:n]], np.float32)
    files = [os.path.join(RAW, f"wx_{y}.npz") for y in range(1995, Y_LAST + 1)]
    T = YEARS["val"][1]
    need = n * T * 5 * 2
    free = torch.cuda.mem_get_info()[0] if DEV == "cuda" else 0
    where = DEV if free > need + 8e9 else "cpu"           # values on the GPU only when 8 GB stay free for the model
    if os.environ.get("WX_DATA_CPU"):                     # large models: leave the whole GPU to the model
        where = "cpu"
    Z = torch.empty((n, T, 5), dtype=torch.float16, device=where)
    mu, sd = MEAN, STD
    t = 0
    for f in files:                                       # standardised values, float16: (x - mean) / std; NaN = missing
        v = np.load(f)["values"][:n, :, :5]
        Z[:, t:t + v.shape[1]] = torch.from_numpy(((v.astype(np.float32) - mu) / sd).astype(np.float16)).to(where)
        t += v.shape[1]; del v
    assert t == T, (t, T)
    log(f"loaded {n} stations x {T} hours into {where} ({need / 1e9:.1f} GB)")
    return Z, lat, lon, elev, dict(stations=[x["id"] for x in st[:n]])


def neighbours(lat, lon, k=K):
    la, lo = np.radians(np.nan_to_num(lat)), np.radians(np.nan_to_num(lon))
    x = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], 1)
    nb = np.zeros((len(lat), k), np.int64)
    for i in range(0, len(lat), 1024):
        d = -(x[i:i + 1024] @ x.T)
        nb[i:i + 1024] = np.argsort(d, 1)[:, :k]
    for i in range(len(lat)):                             # the station itself first
        row = [i] + [j for j in nb[i] if j != i]
        nb[i] = row[:k]
    return nb


def geometry(lat, lon, nb):
    """[N, K, K, 3]: east and north offset and distance between the K stations of each neighbourhood, in 1,000 km."""
    la, lo = np.radians(lat[nb]), np.radians(lon[nb])                  # [N, K]
    dlo = (lo[:, None, :] - lo[:, :, None] + np.pi) % (2 * np.pi) - np.pi
    east = 6.371 * dlo * np.cos((la[:, None, :] + la[:, :, None]) / 2)
    north = 6.371 * (la[:, None, :] - la[:, :, None])
    return np.stack([east, north, np.sqrt(east ** 2 + north ** 2)], -1).astype(np.float32)


def static_feats(lat, lon, elev):
    return np.stack([lat / 90, np.sin(np.radians(lon)), np.cos(np.radians(lon)), np.nan_to_num(elev) / 1000], 1).astype(np.float32)


def time_feats(t0, n):
    h = torch.arange(n, device=DEV)[None] + t0[:, None]                # absolute hour index
    hod = 2 * math.pi * (h % 24) / 24
    doy = 2 * math.pi * ((h / 24.0) % 365.2425) / 365.2425
    return torch.stack([torch.sin(hod), torch.cos(hod), torch.sin(doy), torch.cos(doy)], -1)   # [B, n, 4]


class Batcher:
    def __init__(self, Z, nb, geo, st, H, center_only=False):
        self.Z, self.H = Z, H
        if center_only:                                   # persistence and DLinear read only the station itself
            nb = nb[:, :1]; geo = geo[:, :1, :1]
        self.nb = torch.from_numpy(nb).to(DEV); self.geo = torch.from_numpy(geo).to(DEV); self.st = torch.from_numpy(st).to(DEV)

    def __call__(self, s, t0):
        """s [B] stations, t0 [B] first input hour. Returns the Atlas inputs and the truth [B, K, H, 5] (standardised)."""
        H, B = self.H, len(s)
        ids = self.nb[s]                                                    # [B, K]
        tt = t0[:, None] + torch.arange(L + H, device=DEV)[None]           # [B, L+H]
        zd = self.Z.device
        w = self.Z[ids[:, :, None].to(zd), tt[:, None, :].to(zd)].to(DEV, non_blocking=True).float()   # [B, K, L+H, 5]
        m = torch.isfinite(w).float(); w = torch.nan_to_num(w)
        tf = time_feats(t0, L + H)[:, None].expand(-1, ids.shape[1], -1, -1)
        return dict(yc=w[:, :, :L], mc=m[:, :, :L], uc=tf[:, :, :L], uf=tf[:, :, L:], geo=self.geo[s],
                    static=self.st[ids], y=w[:, :, L:], my=m[:, :, L:])


class DLinear(nn.Module):
    """DLinear (Zeng et al., AAAI 2023), shared across stations and channels as in the benchmark (individual=False):
    moving-average decomposition (kernel 25), one linear map L -> H for trend and one for the remainder."""
    def __init__(self, H, k=25):
        super().__init__()
        self.k = k; self.s = nn.Linear(L, H); self.t = nn.Linear(L, H)

    def forward(self, x):                                                   # x [B, L, C]
        p = (self.k - 1) // 2
        xp = torch.cat([x[:, :1].expand(-1, p, -1), x, x[:, -1:].expand(-1, p, -1)], 1)
        trend = F.avg_pool1d(xp.transpose(1, 2), self.k, 1).transpose(1, 2)
        return (self.s((x - trend).transpose(1, 2)) + self.t(trend.transpose(1, 2))).transpose(1, 2)   # [B, H, C]


def pinball(q, y, m):
    e = y[..., None] - q
    qs = torch.tensor(QS, device=q.device)
    return (torch.maximum(qs * e, (qs - 1) * e) * m[..., None]).sum() / m.sum().clamp(min=1) / 3


def predict_center(model, kind, b):
    """Median forecast for the centre station [B, H, 5] (standardised)."""
    if kind == "persist":
        idx = (b["mc"][:, 0] * torch.arange(1, L + 1, device=DEV)[None, :, None]).argmax(1, keepdim=True)
        last = torch.gather(b["yc"][:, 0], 1, idx)
        return last.expand(-1, b["y"].shape[2], -1)
    if kind == "dlinear":
        x = b["yc"][:, 0]                                                   # missing inputs are 0 (= the mean)
        return model(x)
    q, _, _ = model(b["yc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])
    return q[:, 0, :, :, 1]


def evaluate(model, kind, bt, N, year, stride=1, stations=None, bs=2048):
    """MAE and MSE per variable in the variables' own units over every window wholly inside `year`."""
    a, e = YEARS[year]
    t0s = torch.arange(a, e - (L + bt.H) + 1, stride, device=DEV)
    S = torch.arange(N, device=DEV) if stations is None else torch.as_tensor(stations, device=DEV)
    sd = torch.tensor(STD, device=DEV)
    sae = torch.zeros(5, device=DEV, dtype=torch.float64); sse = torch.zeros_like(sae); cnt = torch.zeros_like(sae)
    if model is not None:
        model.eval()
    with torch.no_grad():
        for s in S.tolist():
            for i in range(0, len(t0s), bs):
                t0 = t0s[i:i + bs]; ss = torch.full_like(t0, s)
                b = bt(ss, t0)
                with torch.autocast(DEV, dtype=torch.float16, enabled=(DEV == "cuda" and kind == "atlas")):
                    p = predict_center(model, kind, b).float()
                err = (p - b["y"][:, 0]) * sd                                   # own units
                m = b["my"][:, 0]
                sae += (err.abs() * m).sum((0, 1)).double(); sse += (err ** 2 * m).sum((0, 1)).double(); cnt += m.sum((0, 1)).double()
    mae, mse = (sae / cnt).cpu().numpy(), (sse / cnt).cpu().numpy()
    return dict(MAE=dict(zip(NAMES, mae.round(4).tolist())), MSE=dict(zip(NAMES, mse.round(4).tolist())),
                MAE_overall=float(mae.mean()), MSE_overall=float(mse.mean()), points=int(cnt[0].item()), windows_per_station=len(t0s))


def std_E(v):
    """The rule's E: mean over the five variables of MAE divided by the benchmark's scale."""
    return float(np.mean([v["MAE"][n] / STD[i] for i, n in enumerate(NAMES)]))


def main(a):
    t_start = time.time()
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    Z, lat, lon, elev, M = load(a.quick)
    N = Z.shape[0]
    nb = neighbours(lat, lon, a.k); geo = geometry(lat, lon, nb); st = static_feats(lat, lon, elev)
    bt = Batcher(Z, nb, geo, st, a.H, center_only=(a.model != "atlas"))
    smp = torch.arange(0, N, max(1, N // 200))           # missing share from 200 stations (the full array is too large)
    miss = {y: float(torch.isnan(Z[smp, YEARS[y][0]:YEARS[y][1]]).float().mean()) for y in YEARS}
    log(f"WX: {N} stations, {Z.shape[1]} hours, missing share by split {json.dumps({k: round(v, 4) for k, v in miss.items()})}; "
        f"neighbourhood median radius {np.median(geo[:, 0, :, 2].max(1)) * 1000:.0f} km; device {DEV}")
    res = dict(model=a.model, H=a.H, seed=a.seed, tag=a.tag, stations=N, k=a.k, steps=a.steps, protocol="Atlas-WX Stage 1 (PREREG_WX): ISD-Lite, L=48, train 1995-2022, val 2023 (every 4th station, every 6th hour)")
    res["gpu"] = torch.cuda.get_device_name(0) if DEV == "cuda" else "cpu"
    model = None
    if a.eval:                                            # score a saved model once; no training
        f = a.eval if os.path.exists(a.eval) else next(iter(glob.glob(f"/kaggle/input/**/{a.eval}", recursive=True)), a.eval)
        from atlas.grow import load_any
        model = load_any(f, DEV).to(DEV); model.eval()
        res.update(params=sum(p.numel() for p in model.parameters()), eval_of=os.path.basename(f))
        log(f"EVAL {f}: {res['params']:,} parameters, k={a.k}")
    elif a.model in ("atlas", "dlinear"):
        if a.model == "atlas" and a.init:                 # continue from a trained model (optionally grown)
            from atlas.grow import grow, load_any
            f = a.init if os.path.exists(a.init) else next(iter(glob.glob(f"/kaggle/input/**/{os.path.basename(a.init)}", recursive=True)), a.init)
            model = load_any(f)
            res.update(init=os.path.basename(f), init_params=model.n_params())
            if a.grow:
                g = [int(x) for x in a.grow.split(",")]
                gf, ge, gd = g[:3]
                model = grow(model, f=gf, enc_depth=ge, dyn_depth=gd, noise=a.grow_noise, seed=a.seed, mlp=g[3] if len(g) > 3 else None)
                res["grown"] = model.cfg["grown_from"]
            model = model.to(DEV)
            log(f"init from {f}: {res['init_params']:,} parameters" + (f", grown by {a.grow} (width x, encoder, dynamics blocks)" if a.grow else ""))
        elif a.model == "atlas":
            ls = {24: 6, 72: 6, 120: 6, 168: 7}[a.H] if a.H in (24, 72, 120, 168) else 6
            model = sized(a.size, L=L, H=a.H, C=5, U=4, lat_steps=ls, spatial=True, geo_dim=3, static=4, fill="interp").to(DEV)
        else:
            model = DLinear(a.H).to(DEV)
        P = sum(p.numel() for p in model.parameters())
        res["params"] = P
        assert P <= a.max_params or a.model != "atlas", f"{P:,} parameters is over the {a.max_params:,} cap"
        log(f"{a.model}: {P:,} parameters" + (f", width {model.cfg['d']}" if a.model == "atlas" else ""))
        opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=a.wd)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.steps, pct_start=a.warmup)
        scaler = torch.amp.GradScaler(enabled=(DEV == "cuda" and a.model == "atlas"))
        ta, te = YEARS["train"]
        rng = np.random.default_rng(a.seed)
        tmax = te - (L + a.H)                                                # last valid first-input hour
        days = np.arange(ta // 24, tmax // 24 + 1)
        if a.frac < 1:                                    # threshold study: a fixed, nested share of training days
            perm = np.random.default_rng(12345).permutation(days)            # same for every size and seed
            days = np.sort(perm[:int(math.ceil(a.frac * len(days)))])
        kd = torch.from_numpy(days).to(DEV)
        res.update(frac=a.frac, train_days=int(len(days)), train_station_days=int(len(days)) * N)
        log(f"training data: {len(days)} days x {N} stations ({a.frac:g} of 1995-2022)")
        vst = rng.choice(N, min(N, 300 if not a.quick else N), replace=False)   # validation: 300 stations, every 6th hour
        best, best_step, bad, f_best = float("inf"), 0, 0, os.path.join(OUT, f"{a.tag}_s{a.seed}.pt")
        f_last, first, done = os.path.join(OUT, f"{a.tag}_s{a.seed}_last.pt"), 1, False
        os.makedirs(OUT, exist_ok=True)
        if os.path.exists(f_last):                        # resume: everything needed to continue exactly where it stopped
            ck = torch.load(f_last, map_location=DEV, weights_only=False)
            model.load_state_dict(ck["sd"]); opt.load_state_dict(ck["opt"]); sched.load_state_dict(ck["sched"])
            scaler.load_state_dict(ck["scaler"])
            best, best_step, bad, first, done = ck["best"], ck["best_step"], ck["bad"], ck["step"] + 1, ck.get("done", False)
            res.update(ck.get("res_extra", {}))
            log(f"RESUME from {f_last}: step {ck['step']}, best {best:.4f} at {best_step}" + (" (training already finished)" if done else ""))
            torch.manual_seed(a.seed + ck["step"])
        elif a.init:                                      # the starting point's validation, same stations as every check
            v = evaluate(model, a.model, bt, N, "val", stride=6, stations=vst)
            res["val_step0"] = std_E(v)
            log(f"  step 0 (as initialised) val MAE (standardised mean) {res['val_step0']:.4f} T {v['MAE']['Temperature']:.3f}")

        def save_last(step, done=False):
            torch.save(dict(sd=model.state_dict(), opt=opt.state_dict(), sched=sched.state_dict(), scaler=scaler.state_dict(),
                            step=step, best=best, best_step=best_step, bad=bad, done=done, cfg=getattr(model, "cfg", None),
                            res_extra={k: res[k] for k in ("val_step0", "init", "init_params", "grown") if k in res}), f_last + ".tmp")
            os.replace(f_last + ".tmp", f_last)           # never a half-written checkpoint, even if the session dies

        t0, t_eval = time.time(), 0.0                     # t_eval: time spent validating (not training)
        for step in (range(first, a.steps + 1) if not done else []):
            model.train()
            s = torch.randint(0, N, (a.bs,), device=DEV)
            t = (kd[torch.randint(0, len(kd), (a.bs,), device=DEV)] * 24 + torch.randint(0, 24, (a.bs,), device=DEV)).clamp(ta, tmax)
            b = bt(s, t)
            with torch.autocast(DEV, dtype=torch.float16, enabled=(DEV == "cuda" and a.model == "atlas")):
                if a.model == "atlas":
                    hide = (torch.rand_like(b["mc"]) < 0.15).float() * b["mc"]       # reconstruction of hidden inputs
                    mc = b["mc"] - hide
                    q, rec, _ = model(b["yc"] * mc, mc, b["uc"], b["uf"], b["geo"], None, b["static"])
                    loss = pinball(q.float(), b["y"], b["my"]) + 0.2 * ((rec.float() - b["yc"]).abs() * hide).sum() / hide.sum().clamp(min=1)
                else:
                    p = model(b["yc"][:, 0])
                    loss = F.mse_loss(p * b["my"][:, 0], b["y"][:, 0] * b["my"][:, 0])     # DLinear's own loss (MSE)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward(); scaler.unscale_(opt)
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(opt); scaler.update(); sched.step()
            if step % a.every == 0 or step == a.steps:
                te0 = time.time()
                v = evaluate(model, a.model, bt, N, "val", stride=6, stations=vst)
                vm = v["MAE_overall_std"] if "MAE_overall_std" in v else float(np.mean([v["MAE"][n] / STD[i] for i, n in enumerate(NAMES)]))
                if vm < best:
                    best, best_step, bad = vm, step, 0
                    torch.save(dict(sd=model.state_dict(), cfg=getattr(model, "cfg", None)), f_best)
                else:
                    bad += 1
                t_eval += time.time() - te0
                sps = (time.time() - t0 - t_eval) / max(1, step - first + 1)
                log(f"  step {step} loss {loss.item():.4f} val MAE (standardised mean) {vm:.4f} (best {best:.4f} at {best_step}) "
                    f"T {v['MAE']['Temperature']:.3f} {(time.time() - t0) / 60:.1f} min, {sps:.3f} s/step, "
                    f"about {(sps * (a.steps - step) + t_eval / max(1, (step - first + 1) // a.every) * (a.steps - step) / a.every) / 3600:.1f} h left at most")
                stop = bad >= a.patience or step == a.steps
                save_last(step, done=stop)
                if stop:
                    log(f"  stop at step {step} ({'patience' if bad >= a.patience else 'end of schedule'})"); break
                if (time.time() - t_start) / 60 > a.cap:
                    if a.pause_at_cap:                    # a Colab/Kaggle session is ending: keep the state, finish later
                        log(f"PAUSED at step {step} (time cap {a.cap} min). Run the same command again to resume.")
                        return
                    save_last(step, done=True)
                    log(f"  stop at step {step} (time cap)"); break
        ck = torch.load(f_best, map_location=DEV); model.load_state_dict(ck["sd"])
        res.update(val_best=best, best_step=best_step, minutes_train=round((time.time() - t0) / 60, 1))
    v = evaluate(model, a.model, bt, N, "val", stride=6, stations=None if a.quick else np.arange(0, N, 4))
    res["val"] = v; res["val_E"] = std_E(v)
    log(f"VAL {a.model} H={a.H}: " + json.dumps(v["MAE"]) + f"; E {res['val_E']:.5f}")
    res["minutes_total"] = round((time.time() - t_start) / 60, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, f"{a.tag}_s{a.seed}.json"), "w"), indent=1, default=float)
    log("WX-RUN " + json.dumps(res, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["atlas", "dlinear", "persist"], default="atlas")
    ap.add_argument("--H", type=int, default=24)
    ap.add_argument("--size", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=600)
    ap.add_argument("--steps", type=int, default=200000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--every", type=int, default=2000)
    ap.add_argument("--patience", type=int, default=6)
    ap.add_argument("--cap", type=float, default=600, help="minutes")
    ap.add_argument("--tag", default="wx_s1")
    ap.add_argument("--k", type=int, default=K, help="stations per neighbourhood (itself + k-1 nearest)")
    ap.add_argument("--frac", type=float, default=1.0, help="threshold study: share of training days kept (nested)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--eval", default="", help="checkpoint to score once on validation; no training")
    ap.add_argument("--init", default="", help="start from this trained checkpoint (training-script or models/series file)")
    ap.add_argument("--grow", default="", help="f,enc_depth,dyn_depth[,mlp]: width x f, blocks appended, hidden width mlp x d (function kept at start)")
    ap.add_argument("--grow-noise", type=float, default=0.05)
    ap.add_argument("--max-params", type=int, default=110_000_000, help="parameter cap (the largest Stage 1 candidate is 100M)")
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--warmup", type=float, default=0.03, help="share of steps spent raising the learning rate")
    ap.add_argument("--pause-at-cap", action="store_true", help="at the time cap save and exit; re-run to resume")
    main(ap.parse_args())
