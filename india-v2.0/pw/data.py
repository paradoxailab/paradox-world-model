"""Paradox World Model v0.2 data layer: every road network becomes the same 15-minute sensor graph.

A network holds
  y      [T, N]  target in real units (flow: vehicles / 15 min; speed: mph), NaN = not observed
  aux    [T, N]  optional second variable (speed for flow networks that have it), NaN = not observed
  tod, dow        15-minute slot of day (0..95), day of week (0 = Monday)
  A      [N, N]  symmetric road-graph weights in [0, 1]
  weather         optional hourly weather per sensor (UK-M25 only), used only up to the forecast origin

Inputs are scale-free (foundation-style): every value is divided by the sensor's own mean over the previous
week (computed from past readings only), so one model can read flow and speed networks of any size.

Splits are chronological. Pretraining uses only the TRAIN part of each US network. UK-M25 is never seen in
pretraining; 20% of its sensors (seed 2026) are also held out of every UK training run ("unseen locations").
"""
import os

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
SPD = 96                 # 15-minute steps per day
L, H = 12, 4             # 3 h of history -> next 60 min (15, 30, 45, 60 min)
LAG_D, LAG_W = 96, 672   # same time yesterday, same time last week
US = ["PEMS03", "PEMS04", "PEMS07", "PEMS08", "METR-LA", "PEMS-BAY"]
CITIES = ["UK-M25", "UK-MAN"]                 # test cities: never in pretraining
SPLITS = {"flow": (0.6, 0.2), "speed": (0.7, 0.1), "uk": (0.7, 0.1), "eng": (0.9, 0.1)}
DAYS = 7                                      # v0.2 long context: the forecast times on each of the last 7 days
UNSEEN_SEED, UNSEEN_SHARE = 2026, 0.2


def _agg15(x5, tod5, kind):
    """5-minute -> 15-minute steps, aligned so each 15-minute step starts at a slot divisible by 3."""
    s = int(np.argmax(tod5 % 3 == 0))
    T = (len(x5) - s) // 3 * 3
    x = x5[s:s + T].reshape(T // 3, 3, -1)
    o = ~np.isnan(x)
    cnt = o.sum(1)
    tot = np.where(o, x, 0).sum(1)
    if kind == "flow":
        v = np.where(cnt >= 2, tot * 3.0 / np.maximum(cnt, 1), np.nan)
    else:
        v = np.where(cnt >= 1, tot / np.maximum(cnt, 1), np.nan)
    return v.astype(np.float32), s, T


def _kmeans(X, k, seed=0, iters=50):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        lab = ((X[:, None] - C[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            if (lab == j).any():
                C[j] = X[lab == j].mean(0)
    return lab


class Net:
    def __init__(self, name, y, tod, dow, A, kind, split, aux=None, weather=None, desc=None, lat=None, lon=None):
        self.name, self.kind = name, kind
        self.y = y.astype(np.float32)
        self.T, self.N = y.shape
        self.tod, self.dow = tod.astype(np.int64) % SPD, dow.astype(np.int64) % 7
        A = np.maximum(A, A.T).astype(np.float32)
        np.fill_diagonal(A, 0)
        self.A = A / max(A.max(), 1e-6)
        self.aux, self.weather, self.desc, self.lat, self.lon = aux, weather, desc, lat, lon
        ftr, fva = split
        n_tr, n_va = int(round(self.T * ftr)), int(round(self.T * fva))
        self.bounds = {"train": (0, n_tr), "val": (n_tr, n_tr + n_va), "test": (n_tr + n_va, self.T)}
        obs = ~np.isnan(self.y)
        yv = np.nan_to_num(self.y)
        cs = np.concatenate([np.zeros((1, self.N)), np.cumsum(yv, 0)])
        cn = np.concatenate([np.zeros((1, self.N)), np.cumsum(obs, 0)])
        t = np.arange(self.T)
        lo = np.maximum(t - LAG_W, 0)
        num, den = cs[t] - cs[lo], cn[t] - cn[lo]                      # readings in [t-672, t): past only
        s = np.where(den >= 12, num / np.maximum(den, 1), np.nan)
        b = self.bounds["train"][1]
        self.s_fallback = float(np.nanmedian(s[:b])) if np.isfinite(s[:b]).any() else 1.0
        self.sflag = np.isnan(s)
        self.scale = np.maximum(np.where(self.sflag, self.s_fallback, s), 0.05 * self.s_fallback).astype(np.float32)
        self.regions = self._regions()
        self.pairs = self._pairs() if kind == "flow" else np.zeros((0, 2), np.int64)
        self.ratio = getattr(self, "ratio", np.zeros(0, np.float32))
        self._dev = None

    # ------------------------------------------------------------------ structure
    def _regions(self, per=16):
        """Hierarchy: sensors grouped into regions by k-means on the graph's spectral embedding."""
        A = self.A + np.eye(self.N, dtype=np.float32) * 1e-3
        d = A.sum(1)
        Lp = np.eye(self.N) - A / np.sqrt(np.outer(d, d))
        w, V = np.linalg.eigh(Lp)
        emb = V[:, 1:5] * np.sqrt(self.N)
        k = max(2, self.N // per)
        return _kmeans(emb.astype(np.float64), k).astype(np.int64)

    def _pairs(self, cv_max=0.08, min_n=500):
        """Physics (flow conservation): linked detector pairs whose train-split flow ratio is nearly constant are
        treated as on the same stretch of road with no junction between them; the model is asked to keep that
        ratio. Ratio r and its robust spread are measured on TRAIN data only."""
        b = self.bounds["train"][1]
        Y = self.y[:b]
        mu = np.nanmean(Y, 0)
        ii, jj = np.where(np.triu(self.A > 0))
        keep, rat = [], []
        for i, j in zip(ii, jj):
            a, c = Y[:, i], Y[:, j]
            m = ~np.isnan(a) & ~np.isnan(c) & (a > 0.3 * mu[i]) & (c > 0.3 * mu[j])
            if m.sum() < min_n:
                continue
            r = c[m] / a[m]
            med = np.median(r)
            if np.median(np.abs(r - med)) / med < cv_max:
                keep.append((i, j)); rat.append(med)
        self.ratio = np.array(rat, np.float32)
        return np.array(keep, np.int64).reshape(-1, 2)

    def origins(self, split, stride=1, last_days=None):
        a, b = self.bounds[split]
        lo = max(a, LAG_W + L)
        if last_days:
            lo = max(lo, b - H - last_days * SPD)
        return np.arange(lo, b - H + 1)[::stride]

    def describe(self):
        n = {k: len(self.origins(k)) for k in self.bounds}
        miss = 100 * np.isnan(self.y).mean()
        return (f"{self.name} [{self.kind}]: {self.T} x {self.N}, {int((self.A > 0).sum())} links, missing {miss:.1f}%, "
                f"{self.regions.max() + 1} regions, {len(self.pairs)} conservation pairs, origins {n}")

    # ------------------------------------------------------------------ tensors
    def to(self, dev):
        if self._dev == dev:
            return self
        f = lambda x: torch.as_tensor(x, device=dev)
        self.t_y = f(np.nan_to_num(self.y)); self.t_o = f(~np.isnan(self.y))
        self.t_s = f(self.scale); self.t_sf = f(self.sflag)
        if self.aux is not None:
            self.t_a = f(np.nan_to_num(self.aux) / 70.0); self.t_ao = f(~np.isnan(self.aux))
        if self.weather is not None:
            self.t_w = f(self.weather)
        self.t_A = f(self.A); self.t_reg = f(self.regions)
        self.t_tod = f(self.tod); self.t_dow = f(self.dow)
        self._dev = dev
        return self

    def batch(self, org, nodes=None, dev="cpu"):
        """org: [B] forecast origins (history = steps org-12..org-1, target = org..org+3)."""
        self.to(dev)
        o = torch.as_tensor(org, device=dev)
        nd = torch.arange(self.N, device=dev) if nodes is None else torch.as_tensor(nodes, device=dev)
        hi = o[:, None] + torch.arange(-L, 0, device=dev)[None]
        fo = o[:, None] + torch.arange(H, device=dev)[None]
        lg = torch.cat([fo - LAG_D * d for d in range(1, DAYS + 1)], 1)           # [B, 7*H]: day 1 first
        yh = hi - LAG_D                                                            # yesterday's lead-in
        dh = o[:, None] + torch.arange(-LAG_D, 0, device=dev)[None]               # last 24 h
        s = self.t_s[o - 1][:, nd]                                     # scale known at the origin
        g = lambda T, ix: T[ix][:, :, nd].transpose(1, 2)              # [B, n, len]
        b = {"hx": g(self.t_y, hi) / s[..., None], "ho": g(self.t_o, hi).float(),
             "lx": g(self.t_y, lg) / s[..., None], "lo": g(self.t_o, lg).float(),
             "yx": g(self.t_y, yh) / s[..., None], "yho": g(self.t_o, yh).float(),
             "y": g(self.t_y, fo), "yo": g(self.t_o, fo), "s": s, "sf": self.t_sf[o - 1][:, nd].float(),
             "tod": self.t_tod[o], "dow": self.t_dow[o], "A": self.t_A[nd][:, nd], "reg": self.t_reg[nd],
             "kind": 0 if self.kind != "speed" else 1}
        B, n = s.shape
        dv, do = g(self.t_y, dh).reshape(B, n, 24, 4), g(self.t_o, dh).float().reshape(B, n, 24, 4)
        cnt = do.sum(-1)
        b["dx"] = (dv * do).sum(-1) / cnt.clamp(min=1) / s[..., None]                # hourly means, last 24 h
        b["do"] = (cnt > 0).float()
        if self.aux is not None:
            b["ax"], b["ao"] = g(self.t_a, hi), g(self.t_ao, hi).float()
        else:
            b["ax"] = b["ao"] = torch.zeros(B, n, L, device=dev)
        if self.weather is not None:                                   # weather up to the last observed hour only
            hr = torch.clamp((o - 1) // 4, min=3)
            w0, w3 = self.t_w[hr][:, nd], self.t_w[hr - 3][:, nd]
            b["w"] = torch.cat([w0, w0 - w3], -1)
        else:
            b["w"] = torch.zeros(B, n, 6, device=dev)
        b["has_w"] = float(self.weather is not None)
        return b


# ---------------------------------------------------------------------------------------------- loaders
def _kernel_from_edges(path, n, ids=None):
    e = np.atleast_2d(np.genfromtxt(path, delimiter=",", skip_header=1))
    dist = np.full((n, n), np.inf)
    pos = {s: i for i, s in enumerate(ids)} if ids is not None else None
    for s, t, c in e:
        if pos is not None:
            if int(s) not in pos or int(t) not in pos:
                continue
            s, t = pos[int(s)], pos[int(t)]
        dist[int(s), int(t)] = dist[int(t), int(s)] = c
    fin = np.isfinite(dist)
    A = np.where(fin, np.exp(-(dist / dist[fin].std()) ** 2), 0.0)
    A[A < 0.1] = 0
    return A


def load_us(name):
    import datetime as dt
    if name in ("PEMS04", "PEMS08"):
        z = np.load(f"{RAW}/{name}.npz")["data"].astype(np.float32)
        flow, spd = z[..., 0], z[..., 2]
        T5, N = flow.shape
        tod5 = np.arange(T5) % 288
        start = {"PEMS08": dt.date(2016, 7, 1), "PEMS04": dt.date(2018, 1, 1)}[name]
        dow5 = (np.arange(T5) // 288 + start.weekday()) % 7
        A = _kernel_from_edges(f"{RAW}/{name}.csv", N)
        flow = np.where(flow > 0, flow, np.nan); spd = np.where(spd > 0, spd, np.nan)
        y, s, T = _agg15(flow, tod5, "flow")
        aux, _, _ = _agg15(spd, tod5, "speed")
        return Net(name, y, tod5[s:s + T:3] // 3, dow5[s:s + T:3], A, "flow", SPLITS["flow"], aux=aux)
    z = np.load(f"{RAW}/{name}.pb.npz")
    x5 = z["data"].astype(np.float32)
    kind = "speed" if name in ("METR-LA", "PEMS-BAY") else "flow"
    x5 = np.where(x5 > 0, x5, np.nan)
    y, s, T = _agg15(x5, z["tod"], kind)
    return Net(name, y, z["tod"][s:s + T:3] // 3, z["dow"][s:s + T:3], z["adj"], kind, SPLITS[kind])


def load_eng(name):
    """England pretraining region (WebTRIS, 2024-07 .. 2026-03): 90% train / 10% validation, no test."""
    z = np.load(f"{RAW}/{name}.pb.npz")
    return Net(name, z["data"].astype(np.float32), z["tod"], z["dow"], z["adj"], "flow", SPLITS["eng"],
               aux=z["speed"].astype(np.float32), lat=z["lat"], lon=z["lon"])


def eng_names():
    return sorted(f[:-7] for f in os.listdir(RAW) if f.startswith("ENG-R") and f.endswith(".pb.npz"))


def load_uk(name="UK-M25"):
    z = np.load(f"{RAW}/{name}.pb.npz")
    y = z["data"].astype(np.float32)
    T, N = y.shape
    w = None
    wf = f"{RAW}/{name}.weather.npz"
    if os.path.exists(wf):
        q = np.load(wf)
        W = q["weather"].astype(np.float32)                           # [hours, G, 3]
        W = np.where(np.isnan(W), np.nanmean(W, (0, 1), keepdims=True), W)
        W = np.stack([(W[..., 0] - 10) / 8, np.log1p(np.maximum(W[..., 1], 0)), W[..., 2] / 20], -1)
        d = (z["lat"][:, None] - q["lat"][None]) ** 2 + ((z["lon"][:, None] - q["lon"][None]) * 0.62) ** 2
        w = W[:, d.argmin(1)].astype(np.float32)                       # nearest grid point -> [hours, N, 3]
        need = T // 4 + 1
        if len(w) < need:
            w = np.concatenate([w, np.repeat(w[-1:], need - len(w), 0)])
    desc = z["desc"] if "desc" in z.files else None
    return Net(name, y, z["tod"], z["dow"], z["adj"], "flow", SPLITS["uk"], aux=z["speed"].astype(np.float32),
               weather=w, desc=desc, lat=z["lat"], lon=z["lon"])


def unseen_split(N):
    rng = np.random.default_rng(UNSEEN_SEED)
    p = rng.permutation(N)
    k = int(round(N * UNSEEN_SHARE))
    return np.sort(p[k:]), np.sort(p[:k])        # seen, unseen
