"""PWM-W Weather: the PWM-W world model on a network of weather stations.

Each station is a token built from the sun's elevation over it in the 24 forecast hours, its last 72 h of temperature,
humidity and wind, its last 24 h of the other
channels, its recent daily cycle, its weekly level and its position; tokens get hour-of-day, month and day-of-year,
then mix across the station graph with PWM-W's multi-scale graph attention and region / global tokens
(pw/model.Block). The head gives, for each target and each of the next 24 hours, the 10/50/90% quantiles as offsets
(in units of the target's network-wide spread) from the base: recent daily cycle + latest anomaly.

  use_graph=False  ablation: stations independent
  use_nwp=True     HYBRID (reported separately): adds global forecasts issued >= 48 h before (pw/leagues)
  xmoe=True        v1.1 PWM-F: the 21-day patch encoder's feed-forward layers become a shared + routed mixture of
                   experts with auxiliary-loss-free balancing (pw/moe.py)
  longctx=True     v0.8: also reads the full last 14 days hour by hour (the same window the daily cycle is averaged
                   from) through a per-day encoder with attention pooling over days; no new data, only more of it seen
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

from pw.wdata import L, H, LH, SPD, PD, LC
from pw.model import Block, Experts
from pw.moe import XLayer


class WxModel(nn.Module):
    def __init__(self, K, Ca, Cn=0, d=128, layers=3, heads=4, ff=2, experts=0, hier=True, use_graph=True,
                 use_nwp=False, Cx=0, longctx=False, xarch=False, ssl=False, xlayers=2, xmoe=False, x_experts=8, x_topk=2):
        super().__init__()
        self.cfg = dict(K=K, Ca=Ca, Cn=Cn, d=d, layers=layers, heads=heads, ff=ff, experts=experts, hier=hier,
                        use_graph=use_graph, use_nwp=use_nwp, Cx=Cx, longctx=longctx,
                        xarch=xarch, ssl=ssl, xlayers=xlayers, xmoe=xmoe, x_experts=x_experts, x_topk=x_topk)
        self.K, self.use_graph, self.use_nwp = K, use_graph, bool(use_nwp and Cn)
        fin = K * (2 * LH + 2 * SPD + 4) + 2 * Ca * L + 3 + 2 + H
        fin += 2 * Cn * H if self.use_nwp else 0
        self.Cx = Cx if self.use_nwp else 0
        fin += 2 * self.Cx * H
        self.inp = nn.Sequential(nn.Linear(fin, 2 * d), nn.GELU(), nn.Linear(2 * d, d))
        self.longctx = bool(longctx)
        if self.longctx:
            self.lc_day = nn.Sequential(nn.Linear(K * 2 * SPD, d), nn.GELU(), nn.Linear(d, d))
            self.lc_pos = nn.Parameter(torch.zeros(PD, d))
            self.lc_att = nn.Linear(d, 1)
            self.lc_out = nn.Linear(d, d)
            nn.init.zeros_(self.lc_out.weight); nn.init.zeros_(self.lc_out.bias)
        self.xarch, self.ssl = bool(xarch), bool(ssl and xarch)
        if self.xarch:
            P = LC // SPD
            self.x_patch = nn.Linear(K * 2 * SPD, d)
            self.x_pos = nn.Parameter(torch.zeros(P, d))
            self.x_mask = nn.Parameter(torch.zeros(d))
            self.xmoe = bool(xmoe)
            if self.xmoe:                       # v1.1 PWM-F: shared + fine-grained routed experts (pw/moe.py)
                self.x_enc = nn.Sequential(*[XLayer(d, heads, ff, x_experts, x_topk) for _ in range(xlayers)])
            else:
                lay = nn.TransformerEncoderLayer(d, heads, ff * d, dropout=0.1, batch_first=True, norm_first=True)
                self.x_enc = nn.TransformerEncoder(lay, xlayers, enable_nested_tensor=False)
            self.x_att = nn.Linear(d, 1)
            self.x_out = nn.Linear(2 * d, d)
            nn.init.zeros_(self.x_out.weight); nn.init.zeros_(self.x_out.bias)
            if self.ssl:
                self.x_rec = nn.Linear(d, K * SPD)
        self.ssl_loss = torch.tensor(0.0)
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
        if self.longctx:
            pdv = torch.cat([b["pd"], b["pdo"]], -1)                         # [B, n, K, PD, 2*24]
            pdv = pdv.permute(0, 1, 3, 2, 4).reshape(B, n, pdv.shape[3], -1)  # [B, n, PD, K*48]
            e = self.lc_day(pdv) + self.lc_pos[None, None]
            w = torch.softmax(self.lc_att(e).squeeze(-1), -1)
            x = x + self.lc_out((w[..., None] * e).sum(2))
        if self.xarch:
            x = x + self._xarch(b, B, n)
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

    def _xarch(self, b, B, n):
        v, m = b["lc"], b["lco"]                                       # [B, n, K, P, 24]
        cnt = m.sum((3, 4), keepdim=True).clamp(min=1)
        mu = (v * m).sum((3, 4), keepdim=True) / cnt
        var = (((v - mu) * m) ** 2).sum((3, 4), keepdim=True) / cnt
        sc = torch.maximum(var.sqrt(), 0.1 * b["sd"][None, None, :, None, None])
        z = (v - mu) / sc * m                                          # per-window normalisation
        P = z.shape[3]
        e = torch.cat([z, m], -1).permute(0, 1, 3, 2, 4).reshape(B * n, P, -1)   # [B*n, P, K*48]
        h = self.x_patch(e)
        hide = None
        if self.ssl and self.training:
            hide = torch.rand(B * n, P, device=h.device) < 0.15
            h = torch.where(hide[..., None], self.x_mask.to(h.dtype).expand_as(h), h)
        h = self.x_enc(h + self.x_pos[None])
        if hide is not None and hide.any():
            rec = self.x_rec(h).float().reshape(B * n, P, self.K, SPD)
            tgt = z.permute(0, 1, 3, 2, 4).reshape(B * n, P, self.K, SPD).float()
            mm = m.permute(0, 1, 3, 2, 4).reshape(B * n, P, self.K, SPD) * hide[..., None, None]
            self.ssl_loss = (((rec - tgt) ** 2) * mm).sum() / mm.sum().clamp(min=1)
        else:
            self.ssl_loss = torch.tensor(0.0, device=h.device)
        w = torch.softmax(self.x_att(h).squeeze(-1).float(), -1).to(h.dtype)
        pooled = torch.cat([(w[..., None] * h).sum(1), h[:, -1]], -1)
        return self.x_out(pooled).reshape(B, n, -1)

    def moe_aux(self):
        return sum(blk.ff.aux for blk in self.blocks if isinstance(blk.ff, Experts))

    def n_params(self):
        return sum(p.numel() for p in self.parameters())
