"""Delhi world-state data: CPCB's monitoring stations as a graph, hourly, many physical variables per station.

The model forecasts the next 24 hours of four pollutants together (PM2.5, PM10, NO2, ozone: the "world state"
targets) from the last 24 hours of everything every station measured: those four, CO, SO2, NH3, NO and the
meteorology (temperature, humidity, wind speed and direction, solar radiation, pressure), plus the same hours on
earlier days. Targets are scale-free: each value is divided by that station's own mean over the previous week (past
readings only), so the same weights serve clean and polluted stations alike.

Graph: Delhi's station coordinates are not in the CPCB files, so stations are linked by how their daily PM2.5
moves together (each station to its 6 most correlated stations; weights = correlation). Links between training
stations use the TRAIN period; links of the held-out stations use only the VALIDATION period (data that exists at
deployment, after training), so nothing from a held-out station's training-period data is used anywhere.
Splits are chronological: the last 182 days are TEST, the 61 days before are VALIDATION, everything earlier is TRAIN.
20% of stations (seed 2026) are never used in training: Track U ("unseen locations").
"""
import os

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
SPD, L, H = 24, 24, 24                       # hourly; 24 h history -> next 24 h
DAYLAGS = (1, 2, 7)                          # same hours 1, 2 and 7 days earlier, at the forecast times
TARGETS = ["PM2.5", "PM10", "NO2", "Ozone"]
AUX = ["CO", "SO2", "NH3", "NO", "AT", "RH", "WS", "WD", "SR", "BP"]
FLOOR = {"PM2.5": 10.0, "PM10": 20.0, "NO2": 5.0, "Ozone": 5.0}   # MAPE only where truth >= floor
TEST_DAYS, VAL_DAYS = 182, 61
UNSEEN_SEED, UNSEEN_SHARE = 2026, 0.2


def _kmeans(X, k, seed=0, iters=50):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        lab = ((X[:, None] - C[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            if (lab == j).any():
                C[j] = X[lab == j].mean(0)
    return lab


class Delhi:
    def __init__(self, path=None, targets=TARGETS, min_cov=0.5):
        z = np.load(path or os.path.join(RAW, "DELHI.npz"), allow_pickle=False)
        X, names = z["X"].astype(np.float32), list(z["vars"])
        self.start = np.datetime64(str(z["start"]))
        T = X.shape[0]
        n_te, n_va = TEST_DAYS * SPD, VAL_DAYS * SPD
        self.bounds = {"train": (0, T - n_te - n_va), "val": (T - n_te - n_va, T - n_te), "test": (T - n_te, T)}
        b = self.bounds["train"][1]
        pm = X[:, :, names.index("PM2.5")]
        cov_tr, cov_te = np.isfinite(pm[:b]).mean(0), np.isfinite(pm[-n_te:]).mean(0)
        keep = np.where((cov_tr >= min_cov * 0.5) & (cov_te >= min_cov))[0]   # rule fixed in advance
        self.stations = [str(s) for s in z["stations"][keep]]
        X = X[:, keep]
        self.T, self.N = X.shape[:2]
        self.seen, self.unseen = unseen_split(self.N)
        self.targets = list(targets)
        self.K = len(self.targets)
        self.Y = np.stack([X[:, :, names.index(v)] for v in self.targets], -1)            # [T, N, K]
        aux = []
        for v in AUX:
            x = X[:, :, names.index(v)]
            if v == "WD":
                r = np.deg2rad(x)
                aux += [np.sin(r), np.cos(r)]
            else:
                tr = x[:b][np.isfinite(x[:b])]
                tr = x[:b][:, self.seen]
                tr = tr[np.isfinite(tr)]
                mu, sd = (float(tr.mean()), float(tr.std()) + 1e-6) if len(tr) else (0.0, 1.0)
                aux.append((x - mu) / sd)
        self.A_aux = np.stack(aux, -1).astype(np.float32)                                  # [T, N, Ca]
        self.Ca = self.A_aux.shape[-1]
        t = np.arange(T)
        hours = (self.start.astype("datetime64[h]") + np.arange(T + 2 * H)).astype("datetime64[h]")  # + future
        self.tod = (hours.astype(np.int64) % 24).astype(np.int64)
        days = hours.astype("datetime64[D]")
        self.dow = ((days.astype(np.int64) + 3) % 7).astype(np.int64)                    # 1970-01-01 was a Thursday
        self.month = (days.astype("datetime64[M]").astype(np.int64) % 12).astype(np.int64)
        self.dates = hours
        obs = np.isfinite(self.Y)
        yv = np.nan_to_num(self.Y)
        cs = np.concatenate([np.zeros((1, self.N, self.K)), np.cumsum(yv, 0)])
        cn = np.concatenate([np.zeros((1, self.N, self.K)), np.cumsum(obs, 0)])
        lo = np.maximum(t - 7 * SPD, 0)
        num, den = cs[t] - cs[lo], cn[t] - cn[lo]                                          # [t-168, t): past only
        s = np.where(den >= 12, num / np.maximum(den, 1), np.nan)
        fb = np.array([np.nanmedian(s[:b, self.seen, k]) for k in range(self.K)])
        self.sflag = np.isnan(s)
        self.scale = np.maximum(np.where(self.sflag, fb[None, None], s), 0.05 * fb[None, None]).astype(np.float32)
        self.A = self._graph()
        self.regions = self._regions()
        self._dev = None

    def _daily(self, a, b):
        D = (b - a) // SPD
        with np.errstate(all="ignore"):
            d = np.nanmean(self.Y[a:a + D * SPD, :, 0].reshape(D, SPD, self.N), 1)          # daily mean PM2.5
            return d - np.nanmean(d, 0)

    def _graph(self, k=6):
        tr, va = self._daily(*self.bounds["train"]), self._daily(*self.bounds["val"])
        hold = set(self.unseen.tolist())
        C = np.zeros((self.N, self.N))
        for i in range(self.N):
            for j in range(i + 1, self.N):
                d, need = (va, 30) if (i in hold or j in hold) else (tr, 60)
                m = np.isfinite(d[:, i]) & np.isfinite(d[:, j])
                if m.sum() >= need:
                    C[i, j] = C[j, i] = np.corrcoef(d[m, i], d[m, j])[0, 1]
        A = np.zeros_like(C)
        for i in range(self.N):
            for j in np.argsort(-C[i])[:k]:
                if C[i, j] > 0:
                    A[i, j] = A[j, i] = C[i, j]
        np.fill_diagonal(A, 0)
        return (A / max(A.max(), 1e-6)).astype(np.float32)

    def _regions(self, per=6):
        A = self.A + np.eye(self.N, dtype=np.float32) * 1e-3
        dg = A.sum(1)
        Lp = np.eye(self.N) - A / np.sqrt(np.outer(dg, dg))
        _, V = np.linalg.eigh(Lp)
        return _kmeans((V[:, 1:4] * np.sqrt(self.N)).astype(np.float64), max(2, self.N // per)).astype(np.int64)

    def origins(self, split, stride=1, last_days=None):
        a, b = self.bounds[split]
        lo = max(a, 7 * SPD + L)
        if last_days:
            lo = max(lo, b - H - last_days * SPD)
        return np.arange(lo, b - H + 1)[::stride]

    def describe(self):
        miss = 100 * np.isnan(self.Y).mean(axis=(0, 1))
        sp = {k: (str(self.dates[a]), str(self.dates[b - 1])) for k, (a, b) in self.bounds.items()}
        return (f"DELHI: {self.T} hours x {self.N} stations, targets {self.targets} (missing "
                f"{', '.join(f'{v:.1f}%' for v in miss)}), {self.Ca} input channels, "
                f"{int((self.A > 0).sum())} graph links, {self.regions.max() + 1} regions; splits {sp}")

    def to(self, dev):
        if self._dev == dev:
            return self
        f = lambda x: torch.as_tensor(x, device=dev)
        self.t_y, self.t_o = f(np.nan_to_num(self.Y)), f(np.isfinite(self.Y))
        self.t_a, self.t_ao = f(np.nan_to_num(self.A_aux)), f(np.isfinite(self.A_aux))
        self.t_s, self.t_sf = f(self.scale), f(self.sflag)
        self.t_A, self.t_reg = f(self.A), f(self.regions)
        self.t_tod, self.t_dow, self.t_mon = f(self.tod), f(self.dow), f(self.month)
        self._dev = dev
        return self

    def batch(self, org, nodes=None, dev="cpu"):
        """org: [B] origins; history = org-24 .. org-1, forecast = org .. org+23."""
        self.to(dev)
        o = torch.as_tensor(org, device=dev)
        nd = torch.arange(self.N, device=dev) if nodes is None else torch.as_tensor(nodes, device=dev)
        hi = o[:, None] + torch.arange(-L, 0, device=dev)[None]
        fo_raw = o[:, None] + torch.arange(H, device=dev)[None]
        lg = torch.cat([fo_raw - SPD * d for d in DAYLAGS], 1)
        fo = fo_raw.clamp(max=self.T - 1)                                           # origin = T: true forecast
        dm = o[:, None] + torch.arange(-7 * SPD, 0, device=dev)[None]
        s = self.t_s[o - 1][:, nd]                                                  # [B, n, K]
        g = lambda T, ix: T[ix][:, :, nd].permute(0, 2, 3, 1)                       # [B, n, C, len]
        B, n = len(org), len(nd)
        dv, do = g(self.t_y, dm).reshape(B, n, self.K, 7, SPD), g(self.t_o, dm).float().reshape(B, n, self.K, 7, SPD)
        cnt = do.sum(-1)
        return {"hx": g(self.t_y, hi) / s[..., None], "ho": g(self.t_o, hi).float(),
                "ax": g(self.t_a, hi), "ao": g(self.t_ao, hi).float(),
                "lx": g(self.t_y, lg) / s[..., None], "lo": g(self.t_o, lg).float(),
                "dx": (dv * do).sum(-1) / cnt.clamp(min=1) / s[..., None], "do": (cnt > 0).float(),
                "y": g(self.t_y, fo), "yo": g(self.t_o, fo) & (fo_raw < self.T)[:, None, None, :],
                "s": s, "sf": self.t_sf[o - 1][:, nd].float(),
                "tod": self.t_tod[o], "dow": self.t_dow[o], "mon": self.t_mon[o],
                "A": self.t_A[nd][:, nd], "reg": self.t_reg[nd]}


def unseen_split(N):
    rng = np.random.default_rng(UNSEEN_SEED)
    p = rng.permutation(N)
    k = int(round(N * UNSEEN_SHARE))
    return np.sort(p[k:]), np.sort(p[:k])
