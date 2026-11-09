"""PWM-W Delhi: an inductive world-state model for a city's station network.

Each station is a token built from everything it measured in the last 24 h (target pollutants and, with
use_aux, the other pollutants and the meteorology), the same forecast hours 1, 2 and 7 days earlier, and the last
week's daily means. Tokens get hour-of-day, day-of-week and month, then mix across the station graph with the same
multi-scale graph attention and region/global tokens as PWM-W (pw/model.py Block). The head predicts, for every
target pollutant and each of the next 24 hours, the 10/50/90% quantiles as offsets from the last observed value.

  use_aux=False   ablation: pollutant targets only (no meteorology, no other pollutants)
  use_graph=False ablation: stations independent (self-attention only, no regions)
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

from pw.ddata import L, H, DAYLAGS, LH, DM
from pw.model import Block, Experts


class DelhiModel(nn.Module):
    def __init__(self, K, Ca, Cw=0, NB=0, d=128, layers=3, heads=4, ff=2, experts=0, hier=True, use_aux=True,
                 use_graph=True, use_wf=False, use_bb=False, long=True):
        super().__init__()
        self.cfg = dict(K=K, Ca=Ca, Cw=Cw, NB=NB, d=d, layers=layers, heads=heads, ff=ff, experts=experts, hier=hier,
                        use_aux=use_aux, use_graph=use_graph, use_wf=use_wf, use_bb=use_bb, long=long)
        self.long = long
        self.K, self.use_aux, self.use_graph = K, use_aux, use_graph
        self.use_wf, self.use_bb = bool(use_wf and Cw), bool(use_bb and NB)
        lh, dm = (LH, DM) if long else (L, 7)                            # long=False: the v0.1 input window
        fin = K * (2 * lh + 2 * len(DAYLAGS) * H + 2 * dm + 4) + (2 * Ca * L if use_aux else 0)
        fin += 2 * Cw * H if self.use_wf else 0
        fin += NB * H * 3 + 1 if self.use_bb else 0
        self.inp = nn.Sequential(nn.Linear(fin, 2 * d), nn.GELU(), nn.Linear(2 * d, d))
        self.tod, self.dow, self.mon = nn.Embedding(24, d), nn.Embedding(7, d), nn.Embedding(12, d)
        self.blocks = nn.ModuleList([Block(d, heads, ff, experts, hier and use_graph) for _ in range(layers)])
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, K * H * 3)
        nn.init.zeros_(self.head.weight); nn.init.zeros_(self.head.bias)

    @staticmethod
    def base_of(b):
        ho, hx = b["ho"], b["hx"]                                         # [B, n, K, L]
        Lh = hx.shape[-1]
        idx = torch.arange(Lh, device=hx.device).float()
        last_i = torch.where(ho > 0, idx, torch.full_like(idx, -1)).amax(-1)
        any_o = (last_i >= 0).float()
        locf = torch.gather(hx, -1, last_i.clamp(min=0).long()[..., None])[..., 0]
        yday = torch.where(b["lo"][..., 0] > 0, b["lx"][..., 0], torch.ones_like(locf))
        return any_o * locf + (1 - any_o) * yday, any_o, (Lh - 1 - last_i).clamp(max=Lh) / Lh

    def forward(self, b):
        if not self.long:
            b = dict(b, hx=b["hx"][..., -L:], ho=b["ho"][..., -L:], dx=b["dx"][..., -7:], do=b["do"][..., -7:])
        base, any_o, age = self.base_of(b)
        B, n = base.shape[:2]
        f = [b["hx"] * b["ho"], b["ho"], b["lx"] * b["lo"], b["lo"], b["dx"] * b["do"], b["do"],
             torch.stack([base, any_o, age, torch.log(b["s"].clamp(min=1e-3)) / 5], -1)]
        f = torch.cat(f, -1).reshape(B, n, -1)
        if self.use_aux:
            f = torch.cat([f, (b["ax"] * b["ao"]).reshape(B, n, -1), b["ao"].reshape(B, n, -1)], -1)
        if self.use_wf:                                                   # city-level weather forecast, every station
            w = torch.cat([(b["wf"] * b["wfo"]).reshape(B, -1), b["wfo"].reshape(B, -1)], -1)
            f = torch.cat([f, w[:, None].expand(B, n, -1)], -1)
        if self.use_bb:                                                   # foundation-model forecasts at this station
            f = torch.cat([f, (b["bb"] * b["bbo"][:, None, None, None, None]).reshape(B, n, -1),
                           b["bbo"][:, None, None].expand(B, n, 1)], -1)
        x = self.inp(f) + (self.tod(b["tod"]) + self.dow(b["dow"]) + self.mon(b["mon"]))[:, None]
        if self.use_graph:
            A = b["A"]
            A2 = A @ A
            A2 = A2 / A2.amax().clamp(min=1e-6)
            G = torch.stack([A, A2, torch.eye(len(A), device=A.device)])
            _, inv = torch.unique(b["reg"], return_inverse=True)
            M = F.one_hot(inv).float()
            M = M / M.sum(0, keepdim=True)
        else:                                                             # stations independent: one token each
            x = x.reshape(B * n, 1, -1)
            G = torch.zeros(3, 1, 1, device=x.device); G[2] = 1
            M = torch.ones(1, 1, device=x.device)
        for blk in self.blocks:
            x = blk(x, G, M)
        z = self.norm(x).reshape(B, n, -1)
        off = self.head(z).float().reshape(B, n, self.K, H, 3)
        bh = base[..., None].expand(B, n, self.K, H)
        if self.use_bb:                                                   # hybrid: correct the backbone's median
            bbm = b["bb"][..., 1].mean(2)[:, :, None]                     # [B, n, 1, H]
            okb = b["bbo"][:, None, None, None]
            bh = okb * bbm + (1 - okb) * bh
        q, _ = torch.sort(bh[..., None] + off, -1)
        return q, z                                                       # [B, n, K, H, 3] in weekly-mean units

    def moe_aux(self):
        return sum(blk.ff.aux for blk in self.blocks if isinstance(blk.ff, Experts))

    def n_params(self):
        return sum(p.numel() for p in self.parameters())
