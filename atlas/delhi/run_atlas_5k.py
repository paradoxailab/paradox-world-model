"""World benchmark WB1 (README, "World benchmarks"): Atlas on WEATHER-5K, plus the protocol check (DLinear, persistence).

Data: W5K_X.npy float16 [N, T, 5] (TMP, DEW, WND_ANGLE, WND_RATE, SLP - offset) and W5K_META.npz from
tools/fetch_weather5k.py, hours from 2014-01-01T00. The benchmark's protocol (github.com/taohan10200/WEATHER-5K,
data_provider/station_dataset.py, exp/exp_global_weather_forecasting.py):
  * input the last 48 hours of the five variables, forecast the next H hours (H = 24, 72, 120, 168);
  * train 2014-2021, validation 2022, test 2023; a window lies wholly inside its year; every hourly window of every
    station is scored (the benchmark's test loader drops the last incomplete batch; we score all windows);
  * MAE and MSE per variable over all lead hours 1..H, in the variables' own units; scaling with the benchmark's fixed
    mean and standard deviation.
Atlas-5K reads each station together with its 15 nearest stations (great-circle), all over the same 48 hours.

  python run_atlas_5k.py --model atlas --H 24 --size 1000000 --seed 600 --tag w5k_atlas1m_h24
  python run_atlas_5k.py --model dlinear --H 24 --tag w5k_dlinear_h24        # protocol check C2
  python run_atlas_5k.py --model persist --H 24 --tag w5k_persist_h24        # reference: last value held
"""
import argparse, json, math, os, sys, time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ROOT))
from atlas.model import sized, QS

RAW = os.environ.get("PW_RAW", "/kaggle/working/raw")
OUT = os.environ.get("ATLAS_OUT", "/kaggle/working/out")
DEV = "cuda" if torch.cuda.is_available() else "cpu"
VARS = ["TMP", "DEW", "WND_ANGLE", "WND_RATE", "SLP"]
NAMES = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
MEAN = np.array([12.70852261, 6.52705582, 191.18867587, 3.36941836, 1014.85317029], np.float32)   # the benchmark's scaler
STD = np.array([13.08167293, 12.13875438, 99.67403125, 2.65729403, 9.17480999], np.float32)
L, K = 48, 16                                             # input hours; stations per neighbourhood (itself + 15)
START = np.datetime64("2014-01-01T00")
hour = lambda s: int((np.datetime64(s) - START) / np.timedelta64(1, "h"))
YEARS = {"train": (hour("2014-01-01T00"), hour("2022-01-01T00")), "val": (hour("2022-01-01T00"), hour("2023-01-01T00")),
         "test": (hour("2023-01-01T00"), hour("2024-01-01T00"))}


def log(*a):
    print(*a, flush=True)


def load(quick=False):
    X = np.load(os.path.join(RAW, "W5K_X.npy"), mmap_mode="r")
    M = np.load(os.path.join(RAW, "W5K_META.npz"))
    off = M["offset"].astype(np.float32) if "offset" in M.files else np.zeros(5, np.float32)
    n = 40 if quick else len(X)
    lat, lon, elev = M["lat"][:n].astype(np.float32), M["lon"][:n].astype(np.float32), M["elev"][:n].astype(np.float32)
    # standardised values on the GPU, float16: (x + offset - mean) / std; NaN = missing
    Z = torch.empty((n, X.shape[1], 5), dtype=torch.float16, device=DEV)
    mu, sd = (MEAN - off), STD
    for i in range(0, n, 256):
        Z[i:i + 256] = torch.from_numpy(((X[i:i + 256].astype(np.float32) - mu) / sd).astype(np.float16)).to(DEV)
    return Z, lat, lon, elev, M


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
        w = self.Z[ids[:, :, None], tt[:, None, :]].float()                # [B, K, L+H, 5]
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


def main(a):
    t_start = time.time()
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    Z, lat, lon, elev, M = load(a.quick)
    N = Z.shape[0]
    nb = neighbours(lat, lon); geo = geometry(lat, lon, nb); st = static_feats(lat, lon, elev)
    bt = Batcher(Z, nb, geo, st, a.H, center_only=(a.model != "atlas"))
    miss = {y: float(torch.isnan(Z[:, YEARS[y][0]:YEARS[y][1]]).float().mean()) for y in YEARS}
    log(f"W5K: {N} stations, {Z.shape[1]} hours, missing share by split {json.dumps({k: round(v, 4) for k, v in miss.items()})}; "
        f"neighbourhood median radius {np.median(geo[:, 0, :, 2].max(1)) * 1000:.0f} km; device {DEV}")
    res = dict(model=a.model, H=a.H, seed=a.seed, tag=a.tag, stations=N, protocol="WEATHER-5K: L=48, train 2014-2021, val 2022, test 2023, all hourly windows")
    model = None
    if a.model in ("atlas", "dlinear"):
        if a.model == "atlas":
            ls = {24: 6, 72: 6, 120: 6, 168: 7}[a.H] if a.H in (24, 72, 120, 168) else 6
            model = sized(a.size, L=L, H=a.H, C=5, U=4, lat_steps=ls, spatial=True, geo_dim=3, static=4, fill="interp").to(DEV)
        else:
            model = DLinear(a.H).to(DEV)
        P = sum(p.numel() for p in model.parameters())
        res["params"] = P
        log(f"{a.model}: {P:,} parameters" + (f", width {model.cfg['d']}" if a.model == "atlas" else ""))
        opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.steps, pct_start=0.03)
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
        log(f"training data: {len(days)} days x {N} stations ({a.frac:g} of 2014-2021)")
        vst = rng.choice(N, min(N, 300 if not a.quick else N), replace=False)   # validation: 300 stations, every 6th hour
        best, best_step, bad, f_best = float("inf"), 0, 0, os.path.join(OUT, f"{a.tag}_s{a.seed}.pt")
        t0 = time.time()
        for step in range(1, a.steps + 1):
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
                v = evaluate(model, a.model, bt, N, "val", stride=6, stations=vst)
                vm = v["MAE_overall_std"] if "MAE_overall_std" in v else float(np.mean([v["MAE"][n] / STD[i] for i, n in enumerate(NAMES)]))
                if vm < best:
                    best, best_step, bad = vm, step, 0
                    torch.save(dict(sd=model.state_dict(), cfg=getattr(model, "cfg", None)), f_best)
                else:
                    bad += 1
                log(f"  step {step} loss {loss.item():.4f} val MAE (standardised mean) {vm:.4f} (best {best:.4f} at {best_step}) "
                    f"T {v['MAE']['Temperature']:.3f} {(time.time() - t0) / 60:.1f} min")
                if bad >= a.patience or (time.time() - t_start) / 60 > a.cap:
                    log(f"  stop at step {step} ({'patience' if bad >= a.patience else 'time cap'})"); break
        ck = torch.load(f_best, map_location=DEV); model.load_state_dict(ck["sd"])
        res.update(val_best=best, best_step=best_step, minutes_train=round((time.time() - t0) / 60, 1))
    v = evaluate(model, a.model, bt, N, "val", stride=6, stations=None if a.quick else np.arange(0, N, 4))
    res["val"] = v
    log(f"VAL {a.model} H={a.H}: " + json.dumps(v["MAE"]))
    if not a.no_test:
        r = evaluate(model, a.model, bt, N, "test")
        res["test"] = r
        log(f"TEST {a.model} H={a.H} (all stations, every hourly window of 2023): MAE " + json.dumps(r["MAE"]) +
            f"; MSE " + json.dumps(r["MSE"]) + f"; {r['points']:,} points")
    res["minutes_total"] = round((time.time() - t_start) / 60, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, f"{a.tag}_s{a.seed}.json"), "w"), indent=1, default=float)
    log("W5K-RUN " + json.dumps(res, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["atlas", "dlinear", "persist"], default="atlas")
    ap.add_argument("--H", type=int, default=24)
    ap.add_argument("--size", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=600)
    ap.add_argument("--steps", type=int, default=60000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--every", type=int, default=2000)
    ap.add_argument("--patience", type=int, default=6)
    ap.add_argument("--cap", type=float, default=600, help="minutes")
    ap.add_argument("--tag", default="w5k")
    ap.add_argument("--no-test", action="store_true")
    ap.add_argument("--frac", type=float, default=1.0, help="threshold study: share of training days kept (nested)")
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args())
