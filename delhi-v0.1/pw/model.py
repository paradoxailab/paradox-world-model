"""Paradox World Model v0.2 (PWM-W): an inductive spatio-temporal world model for road networks.

Every sensor is a token. There is no per-sensor embedding, so the same weights run on any network, of any size,
including networks and sensors never seen in training (foundation use).

  token   = MLP([recent history, observed flags, second variable, values at the forecast times on each of the
            last 7 days, yesterday's lead-in, the last 24 h as hourly means (v0.2 long context; v0.1 used only
            yesterday and last week), scale cues, past weather]) + kind (flow / speed) + time of day + day of week
  block   = multi-scale graph attention (each head mixes neighbours at its own learned graph range; local,
            1-hop, 2-hop and global heads)                                      -> hierarchical (local level)
          + region tokens: sensors pooled into spectral regions and a global token, attention among them,
            broadcast back                                                       -> hierarchical (region/global)
          + feed-forward: dense, or sparse experts (top-1 routing per token)    -> sparse world experts
  heads   = forecast: q10 / q50 / q90 for the next 4 steps as offsets from a base (last observed reading,
            else yesterday's value at that time, else the weekly mean), in units of the sensor's weekly mean
          + reconstruction of masked history (self-supervised objective)
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from pw.data import L, H, DAYS


class Experts(nn.Module):
    """Sparse mixture of experts (Switch-style top-1 routing, load-balancing loss). Each expert has the dense
    FFN's size, so active parameters per token equal the dense model's."""

    def __init__(self, d, hid, n, topk=1):
        super().__init__()
        self.n, self.topk = n, topk
        self.router = nn.Linear(d, n, bias=False)
        self.w1 = nn.Parameter(torch.randn(n, d, hid) / math.sqrt(d))
        self.b1 = nn.Parameter(torch.zeros(n, hid))
        self.w2 = nn.Parameter(torch.randn(n, hid, d) / math.sqrt(hid))
        self.b2 = nn.Parameter(torch.zeros(n, d))
        self.aux = torch.tensor(0.0)
        self.load = None

    def forward(self, x):
        shp = x.shape
        x = x.reshape(-1, shp[-1])
        p = F.softmax(self.router(x).float(), -1)
        g, e = p.topk(self.topk, -1)
        g = g / g.sum(-1, keepdim=True)
        out = torch.zeros_like(x)
        frac = torch.zeros(self.n, device=x.device)
        for k in range(self.topk):
            for j in range(self.n):
                m = e[:, k] == j
                if m.any():
                    h = F.gelu(x[m] @ self.w1[j] + self.b1[j])
                    out[m] += (g[m, k:k + 1] * (h @ self.w2[j] + self.b2[j]).float()).to(out.dtype)
                    frac[j] += m.float().mean() / self.topk
        self.aux = self.n * (frac * p.mean(0)).sum()
        self.load = frac.detach()
        return out.reshape(shp)


class Block(nn.Module):
    def __init__(self, d, heads, ff, experts, hier):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.n1, self.n2, self.n3 = nn.LayerNorm(d), nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.o = nn.Linear(d, 3 * d), nn.Linear(d, d)
        # per-head mixing of graph ranges: bias = a*A + b*A2 + c*I (+ const): heads specialise in scales
        init = torch.tensor([[0., 0., 0.], [4., 0., 0.], [2., 4., 0.], [0., 0., 4.]])[:, None].repeat(1, math.ceil(heads / 4), 1)
        self.gb = nn.Parameter(init.reshape(-1, 3)[:heads].clone())
        self.hier = hier
        if hier:
            self.rn = nn.LayerNorm(d)
            self.ratt = nn.MultiheadAttention(d, heads, batch_first=True)
            self.gtok = nn.Parameter(torch.zeros(1, 1, d))
            self.rout = nn.Linear(d, d)
            nn.init.zeros_(self.rout.weight); nn.init.zeros_(self.rout.bias)
        self.ff = Experts(d, ff * d, experts) if experts else nn.Sequential(
            nn.Linear(d, ff * d), nn.GELU(), nn.Linear(ff * d, d))

    def forward(self, x, G, M):
        B, n, d = x.shape
        q, k, v = self.qkv(self.n1(x)).reshape(B, n, 3, self.h, self.dh).permute(2, 0, 3, 1, 4)
        bias = torch.einsum("hc,cij->hij", self.gb, G).to(q.dtype)        # [heads, n, n]
        a = F.scaled_dot_product_attention(q, k, v, attn_mask=bias[None].expand(B, -1, -1, -1))
        x = x + self.o(a.transpose(1, 2).reshape(B, n, d))
        if self.hier:                                                     # regions + global token
            z = self.rn(x)
            r = torch.einsum("bnd,nr->brd", z, M)                          # region means
            r = torch.cat([self.gtok.expand(B, -1, -1), r], 1)
            r, _ = self.ratt(r, r, r, need_weights=False)
            x = x + self.rout(torch.einsum("brd,nr->bnd", r[:, 1:], (M > 0).to(r.dtype)) + r[:, :1])
        return x + self.ff(self.n2(x))


class WorldModel(nn.Module):
    def __init__(self, d=128, layers=3, heads=4, ff=2, experts=0, hier=True, weather=True, lc=True):
        super().__init__()
        self.cfg = dict(d=d, layers=layers, heads=heads, ff=ff, experts=experts, hier=hier, weather=weather, lc=lc)
        self.use_w, self.lc = weather, lc
        fin = 4 * L + (2 * DAYS * H + 2 * L + 48 if lc else 4 * H) + 6 + 6
        self.inp = nn.Sequential(nn.Linear(fin, 2 * d), nn.GELU(), nn.Linear(2 * d, d))
        self.kind = nn.Embedding(2, d)
        self.tod, self.dow = nn.Embedding(96, d), nn.Embedding(7, d)
        self.blocks = nn.ModuleList([Block(d, heads, ff, experts, hier) for _ in range(layers)])
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, 3 * H)
        self.rec = nn.Linear(d, L)
        nn.init.zeros_(self.head.weight); nn.init.zeros_(self.head.bias)

    @staticmethod
    def base_of(b):
        """Last observed reading of the window; else yesterday's value at the first forecast step; else 1 (the weekly
        mean). In units of the sensor's weekly mean."""
        ho, hx = b["ho"], b["hx"]
        idx = torch.arange(L, device=hx.device).float()
        last_i = torch.where(ho > 0, idx, torch.full_like(idx, -1)).amax(-1)
        any_o = (last_i >= 0).float()
        locf = torch.gather(hx, -1, last_i.clamp(min=0).long()[..., None])[..., 0]
        yday = torch.where(b["lo"][..., 0] > 0, b["lx"][..., 0], torch.ones_like(locf))
        base = any_o * locf + (1 - any_o) * yday
        age = (L - 1 - last_i).clamp(max=L) / L
        return base, any_o, age

    def encode(self, b):
        base, any_o, age = self.base_of(b)
        w = b["w"] * (1.0 if self.use_w else 0.0)
        if self.lc:
            ctx = [b["lx"] * b["lo"], b["lo"], b["yx"] * b["yho"], b["yho"], b["dx"] * b["do"], b["do"]]
        else:                                                              # v0.1: yesterday and last week only
            ix = torch.cat([torch.arange(H), torch.arange((DAYS - 1) * H, DAYS * H)]).to(b["lx"].device)
            ctx = [b["lx"][..., ix] * b["lo"][..., ix], b["lo"][..., ix]]
        feats = torch.cat([b["hx"] * b["ho"], b["ho"], b["ax"] * b["ao"], b["ao"]] + ctx + [w,
                           torch.stack([base, any_o, age, b["sf"], torch.log(b["s"].clamp(min=1e-3)) / 5,
                                        torch.full_like(base, b["has_w"] * float(self.use_w))], -1)], -1)
        x = self.inp(feats) + self.kind.weight[b["kind"]] + (self.tod(b["tod"]) + self.dow(b["dow"]))[:, None]
        A = b["A"]
        A2 = A @ A
        A2 = A2 / A2.amax().clamp(min=1e-6)
        G = torch.stack([A, A2, torch.eye(len(A), device=A.device)])
        reg = b["reg"]
        _, inv = torch.unique(reg, return_inverse=True)
        M = F.one_hot(inv).float()
        M = M / M.sum(0, keepdim=True)
        for blk in self.blocks:
            x = blk(x, G, M)
        return self.norm(x), base

    def forward(self, b):
        z, base = self.encode(b)
        off = self.head(z).float().reshape(*z.shape[:2], H, 3)
        q = base[..., None, None] + off
        q, _ = torch.sort(q, -1)
        return q, z                                                       # q: [B, n, H, 3] in weekly-mean units

    def reconstruct(self, z):
        return self.rec(z).float()

    def moe_aux(self):
        return sum(blk.ff.aux for blk in self.blocks if isinstance(blk.ff, Experts))

    def n_params(self, active=False):
        tot = sum(p.numel() for p in self.parameters())
        if not active:
            return tot
        for blk in self.blocks:
            if isinstance(blk.ff, Experts):
                e = blk.ff
                per = e.w1[0].numel() + e.b1[0].numel() + e.w2[0].numel() + e.b2[0].numel()
                tot -= per * (e.n - e.topk)
        return tot
