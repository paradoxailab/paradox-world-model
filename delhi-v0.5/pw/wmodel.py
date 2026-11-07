"""PWM-W Weather: the PWM-W world model on a network of weather stations.

Each station is a token built from the sun's elevation over it in the 24 forecast hours, its last 72 h of temperature,
humidity and wind, its last 24 h of the other
channels, its recent daily cycle, its weekly level and its position; tokens get hour-of-day, month and day-of-year,
then mix across the station graph with PWM-W's multi-scale graph attention and region / global tokens
(pw/model.Block). The head gives, for each target and each of the next 24 hours, the 10/50/90% quantiles as offsets
(in units of the target's network-wide spread) from the base: recent daily cycle + latest anomaly.

  use_graph=False  ablation: stations independent
  use_nwp=True     HYBRID (reported separately): adds global forecasts issued >= 48 h before (pw/leagues)
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

from pw.wdata import L, H, LH, SPD
from pw.model import Block, Experts


class WxModel(nn.Module):
    def __init__(self, K, Ca, Cn=0, d=128, layers=3, heads=4, ff=2, experts=0, hier=True, use_graph=True,
                 use_nwp=False, Cx=0):
        super().__init__()
        self.cfg = dict(K=K, Ca=Ca, Cn=Cn, d=d, layers=layers, heads=heads, ff=ff, experts=experts, hier=hier,
                        use_graph=use_graph, use_nwp=use_nwp, Cx=Cx)
        self.K, self.use_graph, self.use_nwp = K, use_graph, bool(use_nwp and Cn)
        fin = K * (2 * LH + 2 * SPD + 4) + 2 * Ca * L + 3 + 2 + H
        fin += 2 * Cn * H if self.use_nwp else 0
        self.Cx = Cx if self.use_nwp else 0
        fin += 2 * self.Cx * H
        self.inp = nn.Sequential(nn.Linear(fin, 2 * d), nn.GELU(), nn.Linear(2 * d, d))
        self.tod, self.mon = nn.Embedding(24, d), nn.Embedding(12, d)
        self.blocks = nn.ModuleList([Block(d, heads, ff, experts, hier and use_graph) for _ in range(layers)])
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, K * H * 3)
        nn.init.zeros_(self.head.weight); nn.init.zeros_(self.head.bias)

    def forward(self, b):
        B, n = b["base"].shape[:2]
        f = [b["hx"], b["ho"], b["prof"] * b["pok"], b["pok"],
             torch.stack([b["any_o"], b["age"], b["lvl"], b["mf"]], -1)]
        f = torch.cat(f, -1).reshape(B, n, -1)
        f = torch.cat([f, (b["ax"] * b["ao"]).reshape(B, n, -1), b["ao"].reshape(B, n, -1),
                       b["st"][None].expand(B, n, -1), b["doy"][:, None].expand(B, n, -1), b["sun"]], -1)
        if self.use_nwp:
            f = torch.cat([f, b["nwp"].reshape(B, n, -1), b["nwpo"].reshape(B, n, -1)], -1)
            if self.Cx:
                f = torch.cat([f, b["nwpx"].reshape(B, n, -1), b["nwpxo"].reshape(B, n, -1)], -1)
        x = self.inp(f) + (self.tod(b["tod"]) + self.mon(b["mon"]))[:, None]
        if self.use_graph:
            A = b["A"]
            A2 = A @ A
            A2 = A2 / A2.amax().clamp(min=1e-6)
            G = torch.stack([A, A2, torch.eye(len(A), device=A.device)])
            _, inv = torch.unique(b["reg"], return_inverse=True)
            M = F.one_hot(inv).float()
            M = M / M.sum(0, keepdim=True)
        else:
            x = x.reshape(B * n, 1, -1)
            G = torch.zeros(3, 1, 1, device=x.device); G[2] = 1
            M = torch.ones(1, 1, device=x.device)
        for blk in self.blocks:
            x = blk(x, G, M)
        z = self.norm(x).reshape(B, n, -1)
        off = self.head(z).float().reshape(B, n, self.K, H, 3) * b["sd"][None, None, :, None, None]
        q, _ = torch.sort(b["base"][..., None] + off, -1)
        return q, z                                                       # [B, n, K, H, 3] real units

    def moe_aux(self):
        return sum(blk.ff.aux for blk in self.blocks if isinstance(blk.ff, Experts))

    def n_params(self):
        return sum(p.numel() for p in self.parameters())
