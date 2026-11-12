"""ATF v1.0: real-data learning curves for the Atlas Threshold Function.

For each real station network, Atlas (plain, ~250K parameters, random initialisation) is trained on the most recent
k months of data before the validation period, for a fixed schedule of k, with 2 seeds, and scored on a fixed test
period. Every run's errors are printed as one "CURVE {json}" line, and its validation and test forecasts are saved,
so the threshold function (ATF v1.1) and the combination with foundation models (ATF v1.2) can be evaluated later
without retraining.

Networks (fixed in advance; see NETWORKS):
  isd-r0 .. isd-r5   NOAA ISD airport/synoptic stations in India (WX_INDIA.npz, 2015-01 .. 2024-11, UTC), split into
                     6 regions by k-means on (lat, lon), seed 0; at most 32 stations each (best test coverage).
                     Targets AT, RH, WS. Test = last 182 days, validation = 61 days before.
  cpcb-<city>        CPCB / state-board rooftop stations of 6 cities (WX_CPCBIN.npz, 2024-01 .. 2025-05-02, IST).
                     Targets PM2.5, AT, RH, WS. Test = last 90 days, validation = 45 days before.
  delhi              Delhi's 39 CPCB/DPCC/IMD stations (DELHI.npz, 2024-01 .. 2025-12, IST).
                     Targets PM2.5, AT, RH, WS. Test = last 182 days, validation = 61 days before.

Task: from the last 72 h of every variable at every station of the network, forecast the next 24 h of the targets.
Training windows start every 3 h; validation and test windows every 12 h (00 and 12 local time alternate).
Data amount k (months, 30.4 days) = training windows whose 24-h targets end before validation starts, taken from the
most recent k months only. Model selection: early stopping on validation skill (MAE / persistence MAE, mean over
targets). Test is never used for any choice.

  python curves.py --shard 0 --nshards 4             # -> $ATF_OUT/curves/*.npz and CURVE lines
"""
import argparse, json, math, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from atlas.model import sized

RAW = os.environ.get("PW_RAW", "data/raw")
OUT = os.environ.get("ATF_OUT", "out_atf")
L, H = 72, 24
DEV = "cuda" if torch.cuda.is_available() else "cpu"
POLL = {"PM2.5", "PM10", "NO2", "Ozone", "CO", "SO2", "NH3", "NO"}
CITIES = ["mumbai", "kolkata", "chennai", "pune", "hyderabad", "bengaluru"]
ISD_AMOUNTS = [0.5, 1, 2, 4, 8, 16, 32, 64, 999]
SHORT_AMOUNTS = [0.5, 1, 2, 4, 8, 999]
MONTH = 30.4 * 24


def log(*a):
    print(*a, flush=True)


def NETWORKS():
    n = [dict(name=f"isd-r{r}", file="WX_INDIA.npz", region=r, targets=["AT", "RH", "WS"], test_days=182, val_days=61,
              offset=5.5, amounts=ISD_AMOUNTS) for r in range(6)]
    n += [dict(name=f"cpcb-{c}", file="WX_CPCBIN.npz", city=c, targets=["PM2.5", "AT", "RH", "WS"], test_days=90,
               val_days=45, offset=0.0, amounts=SHORT_AMOUNTS) for c in CITIES]
    n += [dict(name="delhi", file="DELHI.npz", targets=["PM2.5", "AT", "RH", "WS"], test_days=182, val_days=61, offset=0.0,
               amounts=SHORT_AMOUNTS)]
    return n


def kmeans(P, k, seed=0, iters=100):
    rng = np.random.default_rng(seed)
    c = P[rng.choice(len(P), k, replace=False)]
    for _ in range(iters):
        lab = ((P[:, None] - c[None]) ** 2).sum(-1).argmin(1)
        c2 = np.stack([P[lab == j].mean(0) if (lab == j).any() else c[j] for j in range(k)])
        if np.allclose(c2, c): break
        c = c2
    return lab


class Net:
    """One network: hourly values X [T, N, C] (NaN = missing), its targets, splits and geometry."""

    def __init__(self, spec):
        self.spec = spec
        z = np.load(os.path.join(RAW, spec["file"]), allow_pickle=False)
        X = z["X"].astype(np.float32)
        names = [str(v) for v in z["vars"]]
        st = np.array([str(s) for s in z["stations"]]) if "stations" in z.files else np.array([f"s{i}" for i in range(X.shape[1])])
        lat = z["lat"].astype(np.float64) if "lat" in z.files else np.zeros(X.shape[1])
        lon = z["lon"].astype(np.float64) if "lon" in z.files else np.zeros(X.shape[1])
        self.start = np.datetime64(str(z["start"]).replace(" ", "T")[:13], "h")
        T = X.shape[0]
        self.test_start = T - H - spec["test_days"] * 24
        self.val_start = self.test_start - spec["val_days"] * 24
        if "region" in spec:                                   # all-India ISD: region by k-means on position
            lab = kmeans(np.stack([lat, lon], 1), 6, seed=0)
            keep = np.where(lab == spec["region"])[0]
            cov = np.isfinite(X[self.test_start:, keep, names.index("AT")]).mean(0)
            keep = keep[np.argsort(-cov, kind="stable")][:32]
            keep = np.sort(keep[np.isfinite(X[self.test_start:, keep, names.index("AT")]).mean(0) > 0.2])
        elif "city" in spec:
            keep = np.where(np.array([str(c) for c in z["cities"]]) == spec["city"])[0]
        else:
            keep = np.arange(X.shape[1])
        X, st, lat, lon = X[:, keep], st[keep], lat[keep], lon[keep]
        if "WD" in names:                                      # wind direction -> sine and cosine
            w = np.deg2rad(X[..., names.index("WD")])
            X = np.concatenate([np.delete(X, names.index("WD"), -1), np.sin(w)[..., None], np.cos(w)[..., None]], -1)
            names = [v for v in names if v != "WD"] + ["WDsin", "WDcos"]
        tcov = np.isfinite(X[self.test_start:]).mean((0, 1))
        use = [i for i, v in enumerate(names) if tcov[i] > 0.02 or v in spec["targets"]]
        X, names = X[..., use], [names[i] for i in use]
        # stations need at least one target observed >= 20% of the test period
        ti = [names.index(v) for v in spec["targets"] if v in names]
        ok = np.isfinite(X[self.test_start:][..., ti]).mean(0).max(1) > 0.2
        self.X, self.st, self.lat, self.lon = X[:, ok], st[ok], lat[ok], lon[ok]
        self.names, self.T, self.N, self.C = names, T, int(ok.sum()), len(names)
        self.targets = [v for v in spec["targets"] if v in names and np.isfinite(self.X[self.test_start:, :, names.index(v)]).mean() > 0.05]
        self.ti = [names.index(v) for v in self.targets]
        self.O = np.isfinite(self.X)
        self.Xz = np.nan_to_num(self.X)
        hours = (self.start.astype(np.int64) + np.arange(T)).astype(np.float64) + spec["offset"]   # hours since 1970, local
        self.tod = 2 * math.pi * (hours % 24) / 24
        self.dow = 2 * math.pi * ((np.floor(hours / 24) + 3) % 7) / 7      # 1970-01-01 was a Thursday
        d = np.sqrt((self.lat[:, None] - self.lat[None]) ** 2 + ((self.lon[:, None] - self.lon[None]) * np.cos(np.deg2rad(self.lat.mean() if self.N else 0))) ** 2)
        self.geo = torch.tensor(np.stack([d / 5, (self.lat[None] - self.lat[:, None]) / 5, (self.lon[None] - self.lon[:, None]) / 5], -1), dtype=torch.float32)
        self.val_org = np.arange(self.val_start, self.test_start - H + 1, 12)
        self.test_org = np.arange(self.test_start, T - H + 1, 12)
        self.train_end = self.val_start - H                                  # last training origin (targets end before val)
        self.first = L + 24
        self.max_months = (self.train_end - self.first) / MONTH

    def describe(self):
        return (f"{self.spec['name']}: {self.N} stations, {self.C} variables {self.names}, targets {self.targets}; "
                f"{self.T} h from {self.start}; train up to {self.max_months:.1f} months before "
                f"{self.start + int(self.val_start)}; val {len(self.val_org)} windows, test {len(self.test_org)} windows from "
                f"{self.start + int(self.test_start)}; missing % in test "
                f"{[round(100 * (1 - float(self.O[self.test_start:, :, i].mean())), 1) for i in self.ti]}")

    def train_origins(self, months):
        lo = self.first if months >= 999 else max(self.first, self.train_end - int(months * MONTH))
        return np.arange(lo, self.train_end + 1, 3)

    def stats(self, org):
        """channel mean and spread over the hours the training windows cover (no later data)."""
        lo, hi = int(org.min()) - L, int(org.max()) + H
        x = self.X[lo:hi]
        mu = np.nanmean(x, (0, 1)); sd = np.nanstd(x, (0, 1))
        return np.nan_to_num(mu).astype(np.float32), np.maximum(np.nan_to_num(sd, nan=1.0), 1e-3).astype(np.float32)

    def batch(self, org, mu, sd):
        idx = org[:, None] + np.arange(-L, H)[None]                          # [B, L+H]
        x = self.Xz[idx]; o = self.O[idx]                                    # [B, L+H, N, C]
        xc, oc = x[:, :L], o[:, :L]
        cnt = oc.sum(1).clip(min=1)
        m = (xc * oc).sum(1) / cnt                                           # window mean [B, N, C]
        m = np.where(oc.any(1), m, mu)
        z = (x - m[:, None]) / sd * o
        tt = lambda a: torch.tensor(np.ascontiguousarray(a), dtype=torch.float32, device=DEV)
        cal = np.stack([np.sin(self.tod[idx]), np.cos(self.tod[idx]), np.sin(self.dow[idx]), np.cos(self.dow[idx])], -1)
        cal = np.repeat(cal[:, None], self.N, 1)                              # [B, N, L+H, 4]
        static = np.concatenate([np.repeat(np.stack([(self.lat - 22) / 8, (self.lon - 80) / 8], -1)[None], len(org), 0),
                                 (m - mu) / sd, oc.mean(1)], -1)
        return dict(yc=tt(z[:, :L].transpose(0, 2, 1, 3)), mc=tt(oc.transpose(0, 2, 1, 3)),
                    yf=tt(z[:, L:].transpose(0, 2, 1, 3)), of=tt(o[:, L:].transpose(0, 2, 1, 3)),
                    uc=tt(cal[:, :, :L]), uf=tt(cal[:, :, L:]), static=tt(static), m=m, raw_f=x[:, L:], obs_f=o[:, L:])

    def truth(self, org):
        idx = org[:, None] + np.arange(H)[None]
        y = self.X[idx][..., self.ti]                                        # [W, H, N, K]
        return y.transpose(0, 2, 1, 3)                                       # [W, N, H, K]


def clamp(net, q):
    for k, v in enumerate(net.targets):
        if v in POLL or v == "WS": q[..., k, :] = np.maximum(q[..., k, :], 0)
        if v == "RH": q[..., k, :] = np.clip(q[..., k, :], 0, 100)
    return q


@torch.no_grad()
def predict(net, m, org, mu, sd, bs=32):
    m.eval(); out = []
    for i in range(0, len(org), bs):
        b = net.batch(org[i:i + bs], mu, sd)
        q = m(b["yc"], b["mc"], b["uc"], b["uf"], net.geo.to(DEV), None, b["static"])[0]       # [B, N, H, C, 3]
        q = q[:, :, :, net.ti].float().cpu().numpy() * sd[net.ti][None, None, None, :, None] + b["m"][:, :, None, net.ti, None]
        out.append(q)
    m.train()
    return clamp(net, np.sort(np.concatenate(out), -1))                   # [W, N, H, K, 3]


def baselines(net, org):
    """persistence (last observed value in the 72-h window) and same hour yesterday, [W, N, H, K]."""
    idx = org[:, None] + np.arange(-24, 0)[None]
    x = net.X[idx][..., net.ti]                                         # [W, 24, N, K]
    li = np.where(np.isfinite(x), np.arange(24)[None, :, None, None], -1).max(1)
    last = np.take_along_axis(x, np.maximum(li, 0)[:, None], 1)[:, 0]
    yday = net.X[org[:, None] + np.arange(H)[None] - 24][..., net.ti]   # [W, H, N, K]
    last = np.where(li >= 0, last, np.nanmean(x, 1))
    p = np.repeat(last[:, :, None], H, 2)
    yd = yday.transpose(0, 2, 1, 3)
    return p, np.where(np.isfinite(yd), yd, p)


def metrics(net, q50, y):
    out = {}
    for k, v in enumerate(net.targets):
        e = np.abs(q50[..., k] - y[..., k])
        out[v] = dict(MAE=float(np.nanmean(e)), **{f"MAE@{h + 1}h": float(np.nanmean(e[:, :, h])) for h in (0, 5, 11, 23)})
    return out


def run_one(net, months, seed, steps, cap_min, size):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    org = net.train_origins(months)
    mu, sd = net.stats(org)
    m = sized(size, L=L, H=H, C=net.C, U=4, lat_steps=6, spatial=True, geo_dim=3, static=2 + 2 * net.C).to(DEV)
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=1e-4)
    sch = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1, (s + 1) / 100) * (0.1 + 0.45 * (1 + math.cos(math.pi * min(1, s / steps)))))
    w = torch.full((net.C,), 0.1, device=DEV); w[net.ti] = 1.0
    qs = torch.tensor([0.1, 0.5, 0.9], device=DEV)
    vo = net.val_org[::2]
    yv = net.truth(vo); pv, _ = baselines(net, vo)
    pers_v = np.array([np.nanmean(np.abs(pv[..., k] - yv[..., k])) for k in range(len(net.ti))])
    best, state, bad, t0, step = 1e9, None, 0, time.time(), 0
    for step in range(1, steps + 1):
        b = net.batch(rng.choice(org, min(16, len(org)), replace=False), mu, sd)
        rate = torch.rand(b["mc"].shape[0], 1, 1, 1, device=DEV) * 0.3
        mc = b["mc"] * (torch.rand(b["mc"].shape, device=DEV) >= rate).float()
        q, rec, _ = m(b["yc"] * mc, mc, b["uc"], b["uf"], net.geo.to(DEV), None, b["static"])
        e = b["yf"][..., None] - q
        ww = b["of"] * w
        loss = (torch.maximum(qs * e, (qs - 1) * e).mean(-1) * ww).sum() / ww.sum().clamp(min=1)
        hid = b["mc"] - mc
        loss = loss + 0.2 * (((rec - b["yc"]) ** 2) * hid * w).sum() / (hid * w).sum().clamp(min=1)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step(); sch.step()
        if step % 100 == 0 or step == steps:
            p = predict(net, m, vo, mu, sd)[..., 1]
            v = float(np.mean([np.nanmean(np.abs(p[..., k] - yv[..., k])) / pers_v[k] for k in range(len(net.ti))]))
            if v < best - 1e-4:
                best, bad, state = v, 0, {k: x.detach().clone() for k, x in m.state_dict().items()}
            else:
                bad += 1
            if bad >= 8 or time.time() - t0 > cap_min * 60:
                break
    m.load_state_dict(state)
    return m, mu, sd, dict(steps=step, minutes=round((time.time() - t0) / 60, 2), val_skill=best, params=m.n_params(),
                           train_windows=len(org), months=round(len(org) * 3 / MONTH, 2), hit_cap=bool(time.time() - t0 > cap_min * 60))


def main(a):
    nets = NETWORKS()
    if a.only:
        nets = [n for n in nets if n["name"] in a.only.split(",")]
    nets = nets[a.shard::a.nshards]
    os.makedirs(os.path.join(OUT, "curves"), exist_ok=True)
    T0 = time.time()
    for spec in nets:
        if not os.path.exists(os.path.join(RAW, spec["file"])):
            log(f"SKIP {spec['name']}: {spec['file']} not found"); continue
        net = Net(spec)
        log(net.describe())
        yt, yv = net.truth(net.test_org), net.truth(net.val_org)
        pt, dt = baselines(net, net.test_org); pv, dv = baselines(net, net.val_org)
        base = dict(test={"persistence": metrics(net, pt, yt), "yesterday": metrics(net, dt, yt)},
                    val={"persistence": metrics(net, pv, yv), "yesterday": metrics(net, dv, yv)})
        np.savez_compressed(os.path.join(OUT, "curves", f"{spec['name']}__truth.npz"), yt=yt.astype(np.float16),
                            yv=yv.astype(np.float16), test_org=net.test_org, val_org=net.val_org, stations=net.st,
                            targets=np.array(net.targets), start=np.array(str(net.start)), pt=pt.astype(np.float16),
                            dt=dt.astype(np.float16), pv=pv.astype(np.float16), dv=dv.astype(np.float16))
        log("NETWORK " + json.dumps(dict(network=spec["name"], stations=net.N, variables=net.names, targets=net.targets,
                                         max_months=round(net.max_months, 1), baselines=base)))
        amounts = [x for x in spec["amounts"] if x >= 999 or x < net.max_months - 0.25]
        for seed in (0, 1):
            for mo in amounts:
                if time.time() - T0 > a.hours * 3600:
                    log(f"BUDGET {spec['name']} {mo} seed {seed}: skipped (time budget)"); continue
                m, mu, sd, info = run_one(net, mo, seed, a.steps, a.cap, a.size)
                qt, qv = predict(net, m, net.test_org, mu, sd), predict(net, m, net.val_org, mu, sd)
                tag = f"{spec['name']}__{'all' if mo >= 999 else mo}mo__s{seed}"
                np.savez_compressed(os.path.join(OUT, "curves", tag + ".npz"), qt=qt.astype(np.float16), qv=qv.astype(np.float16))
                rec = dict(network=spec["name"], amount=mo, seed=seed, **info, test=metrics(net, qt[..., 1], yt),
                           val=metrics(net, qv[..., 1], yv),
                           cover80={v: float(np.nanmean((yt[..., k] >= qt[..., k, 0]) & (yt[..., k] <= qt[..., k, 2]))) for k, v in enumerate(net.targets)})
                log("CURVE " + json.dumps(rec))
                del m
    log(f"done in {(time.time() - T0) / 60:.1f} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--only", default="")
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--cap", type=float, default=15, help="minutes per training run")
    ap.add_argument("--size", type=int, default=250_000)
    ap.add_argument("--hours", type=float, default=11.0)
    a = ap.parse_args()
    if a.steps < 100: a.cap = 0.2
    main(a)
