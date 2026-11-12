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
SPD, L, H = 24, 24, 24                       # hourly; 24 h history (all variables) -> next 24 h
LH, DM = 72, 14                              # v0.2 long context: 72 h of the targets, 14 daily means
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
    def __init__(self, path=None, targets=TARGETS, min_cov=0.5, backbone=True, wxfc=True, first=None, min_cov_train=None):
        """first (ISO date, long-history file only): drop everything before it. With a long-history file
        (tools/build_delhi_long.py) the stations are still chosen on the league's own hours, so the station list,
        the seen / unseen split and the validation and test windows are exactly the league's."""
        z = np.load(path or os.path.join(RAW, "DELHI.npz"), allow_pickle=False)
        X, names = z["X"].astype(np.float32), list(z["vars"])
        self.start = np.datetime64(str(z["start"]))
        off = int(z["league_offset"]) if "league_offset" in z.files else 0
        if first is not None:
            cut = int((np.datetime64(first).astype("datetime64[h]") - self.start.astype("datetime64[h]")).astype(int))
            cut = min(max(cut, 0), off)
            X, off, self.start = X[cut:], off - cut, self.start.astype("datetime64[h]") + cut
        self.league_offset = off
        T = X.shape[0]
        n_te, n_va = TEST_DAYS * SPD, VAL_DAYS * SPD
        self.bounds = {"train": (0, T - n_te - n_va), "val": (T - n_te - n_va, T - n_te), "test": (T - n_te, T)}
        b = self.bounds["train"][1]
        pm = X[off:, :, names.index("PM2.5")]                                # the league's hours decide the stations
        cov_tr, cov_te = np.isfinite(pm[:b - off]).mean(0), np.isfinite(pm[-n_te:]).mean(0)
        keep = np.where((cov_tr >= (min_cov * 0.5 if min_cov_train is None else min_cov_train)) & (cov_te >= min_cov))[0]   # rule fixed in advance
        self.stations = [str(s) for s in z["stations"][keep]]
        X = X[:, keep]
        self.T, self.N = X.shape[:2]
        self.seen, self.unseen = unseen_split(self.N)
        self.targets = list(targets)
        self.K = len(self.targets)
        self.Y = np.stack([X[:, :, names.index(v)] for v in self.targets], -1)            # [T, N, K]
        aux, self.aux_dropped = [], []
        for v in AUX:
            x = X[:, :, names.index(v)]
            if v == "WD":
                r = np.deg2rad(x)
                aux += [np.sin(r), np.cos(r)]
            else:
                tr = x[:b][np.isfinite(x[:b])]
                tr = x[:b][:, self.seen]
                tr = tr[np.isfinite(tr)]
                if len(tr) == 0:                                   # no trained station reports it: it cannot be scaled, so it
                    aux.append(np.full_like(x, np.nan))            # is not an input for this network (2026-11-13: it used to
                    self.aux_dropped.append(v); continue           # pass through unscaled, e.g. pressure as 1000 "sigma")
                mu, sd = float(tr.mean()), float(tr.std()) + 1e-6
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
        self.WF, self.Cw = None, 0
        wf_path = os.path.join(RAW, "DELHI_wxfc.npz")
        if wxfc and os.path.exists(wf_path):                       # 1-day-ahead weather forecasts (city level)
            w = np.load(wf_path)
            off = int((self.start.astype("datetime64[h]") - np.datetime64(str(w["start"])).astype("datetime64[h]"))
                      .astype(int))
            W = w["X"][off:off + T + 2 * H].astype(np.float32)
            if len(W) < T + 2 * H:
                W = np.concatenate([W, np.full((T + 2 * H - len(W), W.shape[1]), np.nan, np.float32)])
            mu, sd = np.nanmean(W[:b], 0), np.nanstd(W[:b], 0) + 1e-6
            self.WF = ((W - mu) / sd).astype(np.float32)
            self.Cw = W.shape[1]
        self.bb_row, self.BB, self.NB = None, None, 0
        bb_path = os.path.join(RAW, "DELHI_backbone.npz")
        if backbone and os.path.exists(bb_path) and self.targets == ["PM2.5"]:
            z2 = np.load(bb_path)
            names2 = [str(x) for x in z2["stations"]]
            ix = [names2.index(st) for st in self.stations]
            keys = [k for k in ("chronos2", "tfm25") if k in z2.files]
            self.BB = np.stack([z2[k][:, ix].astype(np.float32) for k in keys], 2)        # [M, N, NB, H, 3]
            self.NB, self.bb_keys = len(keys), keys
            self.bb_row = np.full(T + 2 * H, -1, np.int64)
            self.bb_row[z2["origins"]] = np.arange(len(z2["origins"]))
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
        lo = max(a, DM * SPD + L)
        if last_days:
            lo = max(lo, b - H - last_days * SPD)
        return np.arange(lo, b - H + 1)[::stride]

    def describe(self):
        miss = 100 * np.isnan(self.Y).mean(axis=(0, 1))
        sp = {k: (str(self.dates[a]), str(self.dates[b - 1])) for k, (a, b) in self.bounds.items()}
        return (f"DELHI: {self.T} hours x {self.N} stations, targets {self.targets} (missing "
                f"{', '.join(f'{v:.1f}%' for v in miss)}), {self.Ca} input channels, "
                f"{int((self.A > 0).sum())} graph links, {self.regions.max() + 1} regions; splits {sp}"
                + (f"; no trained station reports {self.aux_dropped}: not inputs" if self.aux_dropped else ""))

    def to(self, dev):
        if self._dev == dev:
            return self
        f = lambda x: torch.as_tensor(x, device=dev)
        self.t_y, self.t_o = f(np.nan_to_num(self.Y)), f(np.isfinite(self.Y))
        self.t_a, self.t_ao = f(np.nan_to_num(self.A_aux)), f(np.isfinite(self.A_aux))
        self.t_s, self.t_sf = f(self.scale), f(self.sflag)
        self.t_A, self.t_reg = f(self.A), f(self.regions)
        self.t_tod, self.t_dow, self.t_mon = f(self.tod), f(self.dow), f(self.month)
        if self.WF is not None:
            self.t_wf, self.t_wfo = f(np.nan_to_num(self.WF)), f(np.isfinite(self.WF))
        if self.BB is not None:
            self.t_bb, self.t_bbr = f(self.BB), f(self.bb_row)
        self._dev = dev
        return self

    def batch(self, org, nodes=None, dev="cpu"):
        """org: [B] origins; history = org-24 .. org-1, forecast = org .. org+23."""
        self.to(dev)
        o = torch.as_tensor(org, device=dev)
        nd = torch.arange(self.N, device=dev) if nodes is None else torch.as_tensor(nodes, device=dev)
        hi = o[:, None] + torch.arange(-L, 0, device=dev)[None]
        hl = o[:, None] + torch.arange(-LH, 0, device=dev)[None]
        fo_raw = o[:, None] + torch.arange(H, device=dev)[None]
        lg = torch.cat([fo_raw - SPD * d for d in DAYLAGS], 1)
        fo = fo_raw.clamp(max=self.T - 1)                                           # origin = T: true forecast
        dm = o[:, None] + torch.arange(-DM * SPD, 0, device=dev)[None]
        s = self.t_s[o - 1][:, nd]                                                  # [B, n, K]
        g = lambda T, ix: T[ix][:, :, nd].permute(0, 2, 3, 1)                       # [B, n, C, len]
        B, n = len(org), len(nd)
        dv, do = g(self.t_y, dm).reshape(B, n, self.K, DM, SPD), g(self.t_o, dm).float().reshape(B, n, self.K, DM, SPD)
        cnt = do.sum(-1)
        out = self._extra(o, fo_raw, nd, s, B, n, dev)
        return {**out, "hx": g(self.t_y, hl) / s[..., None], "ho": g(self.t_o, hl).float(),
                "ax": g(self.t_a, hi), "ao": g(self.t_ao, hi).float(),
                "lx": g(self.t_y, lg) / s[..., None], "lo": g(self.t_o, lg).float(),
                "dx": (dv * do).sum(-1) / cnt.clamp(min=1) / s[..., None], "do": (cnt > 0).float(),
                "y": g(self.t_y, fo), "yo": g(self.t_o, fo) & (fo_raw < self.T)[:, None, None, :],
                "s": s, "sf": self.t_sf[o - 1][:, nd].float(),
                "tod": self.t_tod[o], "dow": self.t_dow[o], "mon": self.t_mon[o],
                "A": self.t_A[nd][:, nd], "reg": self.t_reg[nd]}


def _extra_impl(self, o, fo_raw, nd, s, B, n, dev):
    """Weather forecasts for the 24 forecast hours (city level) and backbone quantiles at this origin."""
    out = {}
    if self.WF is not None:
        out["wf"], out["wfo"] = self.t_wf[fo_raw], self.t_wfo[fo_raw].float()                    # [B, H, Cw]
    if self.BB is not None:
        r = self.t_bbr[o]
        ok = (r >= 0).float()
        q = self.t_bb[r.clamp(min=0)][:, nd]                                                     # [B, n, NB, H, 3]
        out["bb"] = torch.nan_to_num(q) / s[:, :, 0, None, None, None]
        out["bbo"] = ok
    return out


Delhi._extra = _extra_impl


def unseen_split(N):
    rng = np.random.default_rng(UNSEEN_SEED)
    p = rng.permutation(N)
    k = int(round(N * UNSEEN_SHARE))
    return np.sort(p[k:]), np.sort(p[:k])
