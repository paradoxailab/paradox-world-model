"""Weather-league data for PWM-W: a network of weather stations as a graph, hourly.

Targets (pw/leagues.TARGETS): temperature, humidity and wind speed, the next 24 hours from origin o
(observations up to o-1). Inputs per station: the last 72 h of the three targets, the last 24 h of the other
channels (dew point, pressure, wind direction, visibility or solar radiation...), each hour-of-day's mean over the
last 14 days (the station's recent daily cycle), the last week's mean, and the station's position and height.
Every input is a past observation of that station or its neighbours: no forecast from any global model enters
the pure model. (The separately reported hybrid entry adds the day2 global forecasts, see pw/leagues.)

Scaling is additive: values minus the station's own last-week mean, divided by one network-wide spread per
target (from TRAIN only), so one set of weights serves every station and season.
The base forecast (what the network corrects) is the recent daily cycle plus the latest anomaly from it.
Graph: great-circle distance, each station to its 6 nearest, Gaussian weights.
"""
import math, os

import numpy as np
import torch

from pw.leagues import TARGETS, bounds, SUFFIXES, DAY1_MAX_I

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
SPD, L, H, LH, PD = 24, 24, 24, 72, 14
LC = 21 * SPD                      # v0.9 PWM-X context: 21 days (TimesFM/Chronos read 512 h here)


def haversine(lat, lon):
    la, lo = np.deg2rad(lat), np.deg2rad(lon)
    d = (np.sin((la[:, None] - la[None]) / 2) ** 2 +
         np.cos(la[:, None]) * np.cos(la[None]) * np.sin((lo[:, None] - lo[None]) / 2) ** 2)
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(d, 0, 1)))


AUX_ALIAS = {"BP": "P"}          # CPCB barometric pressure and ISD/METAR pressure share one input channel


class Wx:
    def __init__(self, league, hybrid=False, min_cov=0.5, stats_until=None, train_hours=None):
        """stats_until: optional hour index; when given, every normalisation statistic uses only hours before it
        (used for a joint-training partner, so nothing from the primary league's validation/test period leaks in)."""
        z = np.load(os.path.join(RAW, f"WX_{league}.npz"), allow_pickle=False)
        X, names = z["X"].astype(np.float32), [str(v) for v in z["vars"]]
        self.league = league
        self.start = np.datetime64(str(z["start"])).astype("datetime64[h]")
        self.T = X.shape[0]
        self.bounds = bounds(league, self.T)
        a, b = self.bounds["train"]
        if stats_until is not None:
            b = max(a + 24 * 30, min(b, int(stats_until)))
            self.bounds["train"] = (a, b)
        te0, te1 = self.bounds["test"]
        cov_tr = np.isfinite(X[a:b, :, names.index("AT")]).mean(0)
        cov_te = np.isfinite(X[te0:te1, :, :3]).mean((0, 2))
        keep = np.where((cov_tr >= min_cov * 0.5) & (cov_te >= min_cov * 0.5))[0]   # rule fixed in advance
        self.train_hours = train_hours
        if train_hours is not None:
            # data-threshold study: the model may use ONLY the last `train_hours` hours before validation, for
            # training windows (inputs included) and for every normalisation statistic. Same stations and test.
            a = max(a, b - int(train_hours))
            self.bounds["train"] = (a, b)
        X = X[:, keep]
        self.keep = keep
        self.stations = [str(s) for s in z["stations"][keep]]
        self.lat, self.lon = z["lat"][keep].astype(np.float64), z["lon"][keep].astype(np.float64)
        elev = np.nan_to_num(z["elev"][keep].astype(np.float64), nan=216.0)
        self.N = len(keep)
        self.K = len(TARGETS)
        self.Y = np.stack([X[:, :, names.index(v)] for v in TARGETS], -1)                      # [T, N, K]
        aux, self.aux_names = [], []
        for v in names:
            if v in TARGETS:
                continue
            x = X[:, :, names.index(v)]
            if v == "WD":
                r = np.deg2rad(x)
                aux += [np.sin(r), np.cos(r)]
                self.aux_names += ["WD_sin", "WD_cos"]
                continue
            self.aux_names.append(AUX_ALIAS.get(v, v))
            tr = x[a:b][np.isfinite(x[a:b])]
            if v == "PM2.5":
                x, tr = np.log1p(np.maximum(x, 0)), np.log1p(np.maximum(tr, 0))
            mu, sd = (float(tr.mean()), float(tr.std()) + 1e-6) if len(tr) else (0.0, 1.0)
            aux.append((x - mu) / sd)
        self.A_aux = np.stack(aux, -1).astype(np.float32)
        self.Ca = self.A_aux.shape[-1]
        # last-week mean (past only) and network-wide spreads, TRAIN only
        t = np.arange(self.T)
        obs = np.isfinite(self.Y)
        cs = np.concatenate([np.zeros((1, self.N, self.K)), np.cumsum(np.nan_to_num(self.Y), 0)])
        cn = np.concatenate([np.zeros((1, self.N, self.K)), np.cumsum(obs, 0)])
        lo = np.maximum(t - 7 * SPD, 0)
        num, den = cs[t] - cs[lo], cn[t] - cn[lo]
        m7 = np.where(den >= 24, num / np.maximum(den, 1), np.nan)
        with np.errstate(all="ignore"):
            st_mean = np.nanmean(self.Y[a:b], 0)                                                  # [N, K]
        st_mean = np.where(np.isfinite(st_mean), st_mean, np.nanmean(st_mean, 0, keepdims=True))
        self.mflag = np.isnan(m7)
        self.m7 = np.where(self.mflag, st_mean[None], m7).astype(np.float32)                     # [T, N, K]
        self.sd = np.array([np.nanstd((self.Y[a:b, :, k] - self.m7[a:b, :, k])) for k in range(self.K)], np.float32)
        self.mu_lvl = np.nanmean(self.m7[a:b], (0, 1)).astype(np.float32)
        self.sd_lvl = (np.nanstd(self.m7[a:b], (0, 1)) + 1e-3).astype(np.float32)
        # fixed scaling (not per network), so one model can learn across station networks
        self.static = np.stack([(self.lat - 28.0) / 5.0, (self.lon - 77.0) / 5.0, elev / 1000.0 - 0.3],
                               -1).astype(np.float32)
        hours = self.start + np.arange(self.T + 2 * H)
        self.dates = hours
        self.tod = (hours.astype(np.int64) % 24).astype(np.int64)
        days = hours.astype("datetime64[D]")
        self.month = (days.astype("datetime64[M]").astype(np.int64) % 12).astype(np.int64)
        doy = (days - days.astype("datetime64[Y]")).astype(np.int64)
        self.doy = np.stack([np.sin(2 * math.pi * doy / 365.25), np.cos(2 * math.pi * doy / 365.25)], -1).astype(np.float32)
        # sun elevation (sine) at every station and hour: deterministic geometry, no observation involved
        utc_off = 5.5 if str(z["tz"]) == "Asia/Kolkata" else 0.0
        self.utc_off = utc_off
        hh = (hours.astype(np.int64) % 24).astype(np.float64) - utc_off                      # UTC hour of day
        dec = np.deg2rad(23.44) * np.sin(2 * math.pi * (284 + doy) / 365.0)
        ha = np.deg2rad(15.0 * (hh[:, None] + self.lon[None] / 15.0 - 12.0))
        la = np.deg2rad(self.lat)[None]
        self.sun = (np.sin(la) * np.sin(dec)[:, None] + np.cos(la) * np.cos(dec)[:, None] * np.cos(ha)).astype(np.float32)
        self.A = self._graph()
        self.regions = self._regions()
        self.NWP, self.Cn, self.base_nwp, self.NWPX, self.Cx = None, 0, False, None, 0
        if hybrid:
            self._load_hybrid()
        self._dev = None

    def align_to(self, primary):
        """Make this network usable as a joint-training partner of `primary`: other channels are put in the
        primary's order by name (a channel the partner lacks is all-missing and masked), and the hour-of-day and
        month inputs are moved to the primary's clock. Sun elevation is already exact for every station."""
        A = np.full(self.A_aux.shape[:2] + (primary.Ca,), np.nan, np.float32)
        shared = []
        for j, nm in enumerate(primary.aux_names):
            if nm in self.aux_names:
                A[..., j] = self.A_aux[..., self.aux_names.index(nm)]
                shared.append(nm)
        self.A_aux, self.Ca, self.aux_names = A, primary.Ca, list(primary.aux_names)
        shift = int(round(primary.utc_off - self.utc_off))
        if shift:
            hours = self.dates + np.timedelta64(shift, "h")
            self.tod = (hours.astype(np.int64) % 24).astype(np.int64)
            self.month = (hours.astype("datetime64[D]").astype("datetime64[M]").astype(np.int64) % 12).astype(np.int64)
        self._dev = None
        return shared, shift

    def _graph(self, k=6):
        D = haversine(self.lat, self.lon)
        np.fill_diagonal(D, np.inf)
        k = min(k, self.N - 1)
        nn_ = np.sort(D, 1)[:, :k]
        sig = (float(np.median(nn_)) if nn_.size else 1.0) + 1e-6
        A = np.zeros((self.N, self.N))
        for i in range(self.N):
            for j in np.argsort(D[i])[:k]:
                w = math.exp(-(D[i, j] / sig) ** 2 / 2)
                A[i, j] = A[j, i] = max(A[i, j], w)
        return (A / max(A.max(), 1e-6)).astype(np.float32)

    def _regions(self, per=5):
        k = min(self.N, max(2, self.N // per))
        X = np.stack([self.lat, self.lon * math.cos(math.radians(self.lat.mean()))], -1)
        rng = np.random.default_rng(0)
        C = X[rng.choice(len(X), k, replace=False)]
        for _ in range(50):
            lab = ((X[:, None] - C[None]) ** 2).sum(-1).argmin(1)
            C = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
        return lab.astype(np.int64)

    def _load_hybrid(self):
        """Global forecasts as hybrid inputs: [time, station, model, day1/day2, target] plus each one's trailing
        30-day local bias (same hour of day, days before the valid time only)."""
        self.base_nwp = False
        p = os.path.join(RAW, f"NWP_{self.league}.npz")
        if not os.path.exists(p):
            return
        z = np.load(p)
        if "hybrid" not in z.files or z["hybrid"].ndim != 5:
            return
        col = z["col"][self.keep]
        Fh = z["hybrid"][:, col]                                                                  # [Tw, N, M, S, K]
        t0 = int(z["hybrid_t0"])
        Tt = self.T + 2 * H
        W = np.full((Tt,) + Fh.shape[1:], np.nan, np.float32)
        n = min(len(Fh), Tt - t0)
        W[t0:t0 + n] = Fh[:n]
        self.nwp_from = t0
        self.NWP = W
        self.NWP_bias = self._trailing_bias(W)
        self.Cn = Fh.shape[2] * self.K
        self.nwp_models = [str(m) for m in z["hybrid_models"]]
        if "hybrid_x" in z.files:                         # v0.5 extra predictors, scaled with TRAIN statistics
            Fx = z["hybrid_x"][:, col]                                                            # [Tw, N, M, S, X]
            names = [str(v) for v in z["hybrid_x_vars"]]
            if "wind_direction_10m" in names:
                j = names.index("wind_direction_10m")
                r = np.deg2rad(Fx[..., j])
                Fx = np.concatenate([np.delete(Fx, j, -1), np.sin(r)[..., None], np.cos(r)[..., None]], -1)
            X = np.full((Tt,) + Fx.shape[1:], np.nan, np.float32)
            X[t0:t0 + n] = Fx[:n]
            a, b = self.bounds["train"]
            for c in range(X.shape[-1]):
                v = X[a:b, ..., c]
                v = v[np.isfinite(v)]
                if len(v):
                    X[..., c] = (X[..., c] - v.mean()) / (v.std() + 1e-6)
            self.NWPX = X
            self.Cx = X.shape[2] * X.shape[4]

    def _trailing_bias(self, F, days=30, need=10):
        Tt = len(F)
        D = -(-Tt // SPD)
        E = np.full((D * SPD,) + F.shape[1:], np.nan, np.float32)
        Y = np.full((D * SPD,) + self.Y.shape[1:], np.nan, np.float32)
        Y[:self.T] = self.Y
        E[:Tt] = F - Y[:Tt][:, :, None, None, :]
        E = E.reshape((D, SPD) + F.shape[1:])
        ok = np.isfinite(E)
        cs = np.concatenate([np.zeros((1,) + E.shape[1:], np.float64), np.cumsum(np.where(ok, E, 0), 0)])
        cn = np.concatenate([np.zeros((1,) + E.shape[1:], np.float64), np.cumsum(ok, 0)])
        dd = np.arange(D)
        lo = np.maximum(dd - days, 0)
        num, den = cs[dd] - cs[lo], cn[dd] - cn[lo]
        B = np.where(den >= need, num / np.maximum(den, 1), np.nan).astype(np.float32)
        return B.reshape((D * SPD,) + F.shape[1:])[:Tt]

    def origins(self, split, stride=1, need_nwp=False):
        a, b = self.bounds[split]
        lo = max(a, PD * SPD + LH)
        if split == "train" and self.train_hours is not None:
            lo = max(lo, a + PD * SPD + LH)          # every input hour of a training window lies inside the budget
        if need_nwp and self.NWP is not None:
            lo = max(lo, self.nwp_from + 1)
        return np.arange(lo, b - H + 1)[::stride]

    def describe(self):
        miss = 100 * np.isnan(self.Y).mean(axis=(0, 1))
        sp = {k: (str(self.dates[a]), str(self.dates[b - 1])) for k, (a, b) in self.bounds.items()}
        return (f"WX_{self.league}: {self.T} hours x {self.N} stations, targets {TARGETS} (missing "
                f"{', '.join(f'{v:.1f}%' for v in miss)}), {self.Ca} other channels, spreads "
                f"{np.round(self.sd, 2).tolist()}, {int((self.A > 0).sum())} graph links, "
                f"{self.regions.max() + 1} regions; splits {sp}")

    def to(self, dev):
        if self._dev == dev:
            return self
        f = lambda x: torch.as_tensor(x, device=dev)
        self.t_y, self.t_o = f(np.nan_to_num(self.Y)), f(np.isfinite(self.Y))
        self.t_a, self.t_ao = f(np.nan_to_num(self.A_aux)), f(np.isfinite(self.A_aux))
        self.t_m7, self.t_mf = f(self.m7), f(self.mflag)
        self.t_sd, self.t_mu, self.t_sl = f(self.sd), f(self.mu_lvl), f(self.sd_lvl)
        self.t_st, self.t_A, self.t_reg = f(self.static), f(self.A), f(self.regions)
        self.t_tod, self.t_mon, self.t_doy = f(self.tod), f(self.month), f(self.doy)
        self.t_sun = f(self.sun)
        if self.NWP is not None:
            self.t_nwp, self.t_nwpo = f(np.nan_to_num(self.NWP)), f(np.isfinite(self.NWP))
            self.t_nwpb = f(np.nan_to_num(self.NWP_bias))
        if self.NWPX is not None:
            self.t_nwpx, self.t_nwpxo = f(np.nan_to_num(self.NWPX)), f(np.isfinite(self.NWPX))
        self._dev = dev
        return self

    def batch(self, org, nodes=None, dev="cpu"):
        self.to(dev)
        o = torch.as_tensor(org, device=dev)
        nd = torch.arange(self.N, device=dev) if nodes is None else torch.as_tensor(nodes, device=dev)
        B, n = len(org), len(nd)
        g = lambda T, ix: T[ix][:, :, nd].permute(0, 2, 3, 1)                     # [B, n, C, len]
        hi = o[:, None] + torch.arange(-L, 0, device=dev)[None]
        hl = o[:, None] + torch.arange(-LH, 0, device=dev)[None]
        pd_ = o[:, None] + torch.arange(-PD * SPD, 0, device=dev)[None]
        fo_raw = o[:, None] + torch.arange(H, device=dev)[None]
        fo = fo_raw.clamp(max=self.T - 1)
        m7 = self.t_m7[o - 1][:, nd]                                              # [B, n, K]
        sd = self.t_sd
        # recent daily cycle: column i of the 14 x 24 block has the hour of day of forecast hour o + i
        pv = g(self.t_y, pd_).reshape(B, n, self.K, PD, SPD)
        po = g(self.t_o, pd_).float().reshape(B, n, self.K, PD, SPD)
        pc = po.sum(3)
        prof = torch.where(pc >= 3, (pv * po).sum(3) / pc.clamp(min=1), m7[..., None])        # [B, n, K, 24]
        hx, ho = g(self.t_y, hl), g(self.t_o, hl).float()
        idx = torch.arange(LH, device=dev).float()
        last_i = torch.where(ho > 0, idx, torch.full_like(idx, -1)).amax(-1)                    # [B, n, K]
        any_o = (last_i >= 0).float()
        last_v = torch.gather(hx, -1, last_i.clamp(min=0).long()[..., None])[..., 0]
        col_last = ((last_i.clamp(min=0).long() - LH) % SPD)                                     # hour o-LH+i <-> col (i-LH)%24
        prof_last = torch.gather(prof, -1, col_last[..., None])[..., 0]
        anom = any_o * (last_v - prof_last)
        age = (LH - 1 - last_i).clamp(max=LH) / LH
        base = prof + anom[..., None]                                                            # [B, n, K, H]
        z = lambda v: (v - m7[..., None]) / sd[None, None, :, None]
        # v0.9 PWM-X: the last 21 days hour by hour in real units (hours before the record start are masked)
        lci = o[:, None] + torch.arange(-LC, 0, device=dev)[None]
        lcok = (lci >= 0)
        lci = lci.clamp(min=0)
        lcv = g(self.t_y, lci) * lcok[:, None, None, :]
        lco = g(self.t_o, lci).float() * lcok[:, None, None, :]
        out = {"lc": lcv.reshape(B, n, self.K, LC // SPD, SPD), "lco": lco.reshape(B, n, self.K, LC // SPD, SPD),
               "pd": (pv - m7[..., None, None]) / sd[None, None, :, None, None] * po, "pdo": po,                                                     # v0.8: full 14 x 24 h history
               "hx": z(hx) * ho, "ho": ho, "ax": g(self.t_a, hi), "ao": g(self.t_ao, hi).float(),
               "prof": z(prof), "pok": (pc >= 3).float(), "base": base, "any_o": any_o, "age": age,
               "lvl": (m7 - self.t_mu) / self.t_sl, "mf": self.t_mf[o - 1][:, nd].float(),
               "st": self.t_st[nd], "m7": m7, "sd": sd,
               "y": g(self.t_y, fo), "yo": g(self.t_o, fo) & (fo_raw < self.T)[:, None, None, :],
               "tod": self.t_tod[o], "mon": self.t_mon[o], "doy": self.t_doy[o],
               "sun": self.t_sun[fo_raw][:, :, nd].permute(0, 2, 1),
               "A": self.t_A[nd][:, nd], "reg": self.t_reg[nd]}
        if self.NWP is not None:
            sel = (torch.arange(H, device=dev) <= DAY1_MAX_I)[None, :, None, None, None]
            pick = lambda T_: torch.where(sel, T_[fo_raw][:, :, nd][..., 0, :], T_[fo_raw][:, :, nd][..., 1, :])
            w, wo, wb = pick(self.t_nwp), pick(self.t_nwpo).float(), pick(self.t_nwpb)        # [B, H, n, M, K]
            wbc = w - wb                                                                     # bias-corrected
            if getattr(self, "base_nwp", False):                                             # MOS-style base
                cnt = wo.sum(3)
                ens = (wbc * wo).sum(3) / cnt.clamp(min=1)                                   # [B, H, n, K]
                out["base"] = torch.where(cnt.permute(0, 2, 3, 1) > 0, ens.permute(0, 2, 3, 1), out["base"])
            wbc, wo = wbc.permute(0, 2, 3, 4, 1), wo.permute(0, 2, 3, 4, 1)                  # [B, n, M, K, H]
            out["nwp"] = ((wbc - m7[:, :, None, :, None]) / sd[None, None, None, :, None]) * wo
            out["nwpo"] = wo
            if self.NWPX is not None:
                xv, xo = pick(self.t_nwpx), pick(self.t_nwpxo).float()                    # [B, H, n, M, X]
                out["nwpx"] = (xv * xo).permute(0, 2, 3, 4, 1)
                out["nwpxo"] = xo.permute(0, 2, 3, 4, 1)
        return out
