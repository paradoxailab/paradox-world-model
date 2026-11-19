"""The three domains of Atlas-100M. Each wraps an EXISTING, published harness without changing it:

  Weather   atlas/delhi/run_atlas_5k.py      (WEATHER-5K protocol; paper 5)
  AQ        atlas/delhi/run_atlas_india.py   (all-India PM2.5 league; papers 3 and 4)
  Traffic   v0.6-conference (ParadoxBench)   (six traffic networks; paper 1)

Every domain gives: view_kw (the Atlas arguments of its view), loss(view, rng) for one training batch (the harness's own
loss), and val(view) -> one number, lower is better (the harness's own validation metric on fixed windows).
"""
import math, os, sys

import numpy as np
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.dirname(HERE)
REPO = os.path.dirname(ATLAS)
for p in (ATLAS, os.path.join(ATLAS, "delhi"), os.path.join(REPO, "v0.6-conference")):
    if p not in sys.path:
        sys.path.insert(0, p)

DEV = "cuda" if torch.cuda.is_available() else "cpu"
QS = torch.tensor([0.1, 0.5, 0.9])


def pinball(q, y, w):
    """Mean pinball loss over 10/50/90% quantiles; q [..., 3], y and w broadcastable to q[..., 0]."""
    e = y[..., None] - q
    qs = QS.to(q.device)
    return (torch.maximum(qs * e, (qs - 1) * e).mean(-1) * w).sum() / w.sum().clamp(min=1)


# ===================================================================================================== weather
class Weather:
    name = "weather"

    def __init__(self, k=32, bs=256, quick=False, seed=700):
        import run_atlas_5k as R5
        self.R = R5
        self.Z, lat, lon, elev, _ = R5.load(quick)
        self.N = self.Z.shape[0]
        nb = R5.neighbours(lat, lon, k)
        self.bt = R5.Batcher(self.Z, nb, R5.geometry(lat, lon, nb), R5.static_feats(lat, lon, elev), 24)
        self.bs, self.k = bs, k
        ta, te = R5.YEARS["train"]
        self.ta, self.tmax = ta, te - (R5.L + 24)
        self.kd = torch.arange(ta // 24, self.tmax // 24 + 1, device=DEV)
        rng = np.random.default_rng(600)                   # the SAME 300 validation stations as the 10M and 24.1M runs
        self.vst = rng.choice(self.N, min(self.N, 300 if not quick else self.N), replace=False)
        self.val_stride = 6
        if quick:                                          # PIPELINE TEST ONLY: a tiny validation
            self.vst, self.val_stride = self.vst[:3], 24 * 7
        self.view_kw = None                                # the weather view is the grown 24.1M model itself

    def loss(self, view, rng):
        bs = self.bs
        s = torch.randint(0, self.N, (bs,), device=DEV)
        t = (self.kd[torch.randint(0, len(self.kd), (bs,), device=DEV)] * 24
             + torch.randint(0, 24, (bs,), device=DEV)).clamp(self.ta, self.tmax)
        b = self.bt(s, t)
        hide = (torch.rand_like(b["mc"]) < 0.15).float() * b["mc"]
        mc = b["mc"] - hide
        q, rec, _ = view(b["yc"] * mc, mc, b["uc"], b["uf"], b["geo"], None, b["static"])
        return pinball(q.float(), b["y"], b["my"]) + 0.2 * ((rec.float() - b["yc"]).abs() * hide).sum() / hide.sum().clamp(min=1)

    @torch.no_grad()
    def val(self, view):
        v = self.R.evaluate(view, "atlas", self.bt, self.N, "val", stride=self.val_stride, stations=self.vst)
        view.train()
        return self.R.std_E(v)


# ========================================================================================================== AQ
class AQ:
    name = "aq"

    def __init__(self, quick=False):
        import run_atlas_delhi as R
        import run_atlas_india as RI
        self.R, self.RI = R, RI
        self.nets = RI.networks(quick)
        self.O = [RI.origins(D, quick) for D in self.nets]
        w = np.array([len(o[0]) for o in self.O], float)
        self.p = w / w.sum()
        D0 = self.nets[0]
        ref = R.build(D0, 1_000_000, 0)                     # the harness's own Atlas arguments (only its size differs)
        drop = {"d", "heads", "enc_depth", "dyn_depth", "mlp", "lat_steps", "spatial", "grown_from"}
        self.view_kw = {k: v for k, v in ref.cfg.items() if k not in drop}
        assert not self.view_kw.get("sysid"), "the AQ view is the plain Atlas"
        self.view_kw["spatial"] = True
        self.chw = torch.tensor([1.0] + [0.1] * (D0.K - 1) + [0.05] * D0.Ca, device=DEV)
        self.n_org = 2 if quick else 16                    # 16 windows per batch: the harness's own batch
        del ref

    def loss(self, view, rng):
        R = self.R
        i = int(rng.choice(len(self.nets), p=self.p))
        D, tr = self.nets[i], self.O[i][0]
        b = R.make_batch(D, rng.choice(tr, min(self.n_org, len(tr)), replace=False), D.seen)
        rate = torch.rand(b["mc"].shape[0], 1, 1, 1, device=DEV) * 0.4
        mc = b["mc"] * (torch.rand(b["mc"].shape, device=DEV) >= rate).float()
        qq, rec, _ = R.forward(view, b, mc)
        ww = b["of"] * self.chw
        loss = pinball(qq.float(), b["yf"], ww)
        hid = b["mc"] - mc
        return loss + 0.2 * (((rec.float() - b["yc"]) ** 2) * hid * self.chw).sum() / (hid * self.chw).sum().clamp(min=1)

    @torch.no_grad()
    def val(self, view):
        v = self.RI.pooled_val(view, self.nets, self.O)     # PM2.5 MAE, ug/m3, every network's trained stations
        view.train()
        return v


# ===================================================================================================== traffic
TRAFFIC = ["PEMS08", "PEMS04", "PEMS03", "PEMS07", "METR-LA", "PEMS-BAY"]


class TrafficNet:
    """One ParadoxBench traffic network in Atlas form: every sensor is a node; values standardised with the
    network's training mean and std (the harness's own statistics); 12 steps in, 12 out."""

    def __init__(self, task):
        from paradoxbench.spec import TASKS, validation_windows, official_windows
        from pwm.data import load
        self.task = task
        ds = load(TASKS[task][0])
        self.ds, self.N, self.L, self.H = ds, ds.N, ds.in_len, ds.out_len
        self.norm = torch.from_numpy(ds.norm).to(DEV)                              # [T, N], 0 where missing
        self.obs = torch.from_numpy(ds.observed).to(DEV).float()
        valid = ds.observed & (np.nan_to_num(ds.raw) > 1e-4 if ds.mask_zero else ds.observed)
        self.valid = torch.from_numpy(valid).to(DEV).float()
        self.tod = torch.from_numpy(ds.period_idx).to(DEV).float() * (2 * math.pi / ds.period)
        self.dow = torch.from_numpy(ds.dow).to(DEV).float() * (2 * math.pi / 7)
        A = ds.A if torch.is_tensor(ds.A) else torch.tensor(ds.A)
        A = A.to(DEV).float()
        eye = torch.eye(self.N, device=DEV)
        self.geo = torch.stack([A, eye, (torch.from_numpy(ds.A_raw).to(DEV) > 0).float()], -1)  # as the AQ league's graph
        a, b = ds.bounds["train"]
        tr = ds.norm[a:b]; ob = ds.observed[a:b]
        cnt = ob.sum(0).clip(min=1)
        mu = (tr * ob).sum(0) / cnt
        sd = np.sqrt((((tr - mu) ** 2) * ob).sum(0) / cnt)
        self.static = torch.from_numpy(np.stack([mu, sd], 1).astype(np.float32)).to(DEV)            # [N, 2]
        self.train_idx = ds.indices("train")
        self.val_idx = validation_windows(ds)
        self.test_idx = official_windows(ds)
        self.mean, self.std = ds.mean, ds.std
        self.bs_train = max(1, 2048 // self.N)
        self.bs_eval = max(1, 4096 // self.N)

    def cal(self, ix):
        c = torch.stack([torch.sin(self.tod[ix]), torch.cos(self.tod[ix]), torch.sin(self.dow[ix]), torch.cos(self.dow[ix])], -1)
        return c[:, None].expand(-1, self.N, -1, -1)                                 # [B, N, len, 4]

    def batch(self, idx):
        o = torch.as_tensor(np.asarray(idx), device=DEV)
        hi = o[:, None] + torch.arange(-self.L, 0, device=DEV)[None]
        fo = o[:, None] + torch.arange(self.H, device=DEV)[None]
        g = lambda T, ix: T[ix].permute(0, 2, 1)[..., None]                         # [B, N, len, 1]
        mc = g(self.obs, hi)
        return dict(yc=g(self.norm, hi) * mc, mc=mc, uc=self.cal(hi), uf=self.cal(fo), geo=self.geo,
                    static=self.static[None].expand(len(idx), -1, -1), y=g(self.norm, fo)[..., 0],
                    my=g(self.valid, fo)[..., 0])

    @torch.no_grad()
    def predict(self, view, idx):
        """Quantiles in real units [W, H, N, 3] (the ParadoxBench submission layout)."""
        out = []
        for i in range(0, len(idx), self.bs_eval):
            b = self.batch(idx[i:i + self.bs_eval])
            with torch.autocast(DEV, dtype=torch.bfloat16, enabled=(DEV == "cuda")):
                q = view(b["yc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])[0][..., 0, :]
            q = torch.sort(q.float(), -1).values * self.std + self.mean                 # [B, N, H, 3]
            out.append(q.permute(0, 2, 1, 3).cpu().numpy())
        return np.concatenate(out)

    def truth(self, idx):
        fo = np.asarray(idx)[:, None] + np.arange(self.H)[None]
        y = self.ds.raw[fo]
        return np.where(self.ds.valid(y), y, np.nan)                                    # [W, H, N]


class Traffic:
    name = "traffic"

    def __init__(self, tasks=None, quick=False, val_every=12):
        self.nets = [TrafficNet(t) for t in (tasks or TRAFFIC)]
        if quick:                                          # PIPELINE TEST ONLY: tiny batches and windows
            for n in self.nets:
                n.val_idx = n.val_idx[::50]; n.test_idx = n.test_idx[::50]; n.bs_train = 1; n.bs_eval = 2
        for n in self.nets:
            n.val_sub = n.val_idx[::val_every]
        w = np.array([len(n.train_idx) * n.N for n in self.nets], float)
        self.p = w / w.sum()
        self.view_kw = dict(L=12, H=12, C=1, U=4, spatial=True, geo_dim=3, static=2, fill="interp")
        self.persist = None

    def loss(self, view, rng):
        n = self.nets[int(rng.choice(len(self.nets), p=self.p))]
        b = n.batch(rng.choice(n.train_idx, n.bs_train, replace=False))
        hide = (torch.rand_like(b["mc"]) < 0.15).float() * b["mc"]
        dark = (torch.rand(b["mc"].shape[0], n.N, 1, 1, device=DEV) < 0.1).float()     # whole sensors dark (v0.6 recipe)
        mc = b["mc"] * (1 - dark) - hide * (1 - dark)
        q, rec, _ = view(b["yc"] * mc, mc, b["uc"], b["uf"], b["geo"], None, b["static"])
        hid = b["mc"] - mc
        return pinball(q[..., 0, :].float(), b["y"], b["my"]) + 0.2 * ((rec.float() - b["yc"]).abs() * hid).sum() / hid.sum().clamp(min=1)

    def _persist(self):
        out = []
        for n in self.nets:
            x = n.ds.raw; ob = n.ds.observed; idx = n.val_sub
            last = np.full((len(idx), n.N), np.nan, np.float32)
            for j in range(1, n.L + 1):                                                 # last observed reading
                v = np.where(ob[idx - j], x[idx - j], np.nan)
                last = np.where(np.isnan(last), v, last)
            y = n.truth(idx)
            out.append(np.nanmean(np.abs(np.nan_to_num(last, nan=n.mean)[:, None] - y)))
        return out

    @torch.no_grad()
    def val(self, view):
        """Mean over networks of (MAE of the median, real units) / (MAE of the last observed reading), validation."""
        if self.persist is None:
            self.persist = self._persist()
        r = []
        for n, p in zip(self.nets, self.persist):
            e = np.abs(n.predict(view, n.val_sub)[..., 1] - n.truth(n.val_sub))
            r.append(float(np.nanmean(e)) / p)
        view.train()
        return float(np.mean(r))
