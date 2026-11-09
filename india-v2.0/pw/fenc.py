"""PWM-F (v2.0): a ~10M-parameter station-history encoder pretrained on every Indian NOAA ISD station.

What it borrows, as ideas (no code or weights from anyone):
  * fine-grained mixture of experts with an always-on shared expert and auxiliary-loss-free load balancing
    (the routing bias is nudged towards under-used experts instead of adding a balance loss), so each token uses
    about half of the parameters;
  * generative pretraining on a large corpus, then fine-tuning: here, forecasting the next 24 hours and
    reconstructing hidden days of 21-day station histories from all of India;
  * calibrated uncertainty and hard physical rules: 10/50/90% quantiles kept in order, and (in the runner) relative
    humidity kept in [0, 100] % and wind speed >= 0.

Input: one station's last 21 days, hour by hour, of temperature (C), relative humidity (%) and wind speed (m/s), with
observed flags; the sine of solar elevation for the 24 forecast hours; and the day of year. Each window is normalised
by its own mean and spread, so one model reads airports, synoptic stations and rooftop sensors alike.
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F

K, P, SPD, H = 3, 21, 24, 24
FLOOR = (0.3, 2.0, 0.2)          # minimum per-window spread (C, %, m/s)


class MoE(nn.Module):
    """One shared expert + E routed experts, top-k routing, auxiliary-loss-free balancing."""

    def __init__(self, d, E=8, k=2, shared_mult=2, routed_mult=1, gamma=1e-3):
        super().__init__()
        self.E, self.k, self.gamma = E, k, gamma
        self.shared = nn.Sequential(nn.Linear(d, shared_mult * d), nn.GELU(), nn.Linear(shared_mult * d, d))
        self.w1 = nn.Parameter(torch.randn(E, d, routed_mult * d) / math.sqrt(d))
        self.b1 = nn.Parameter(torch.zeros(E, routed_mult * d))
        self.w2 = nn.Parameter(torch.randn(E, routed_mult * d, d) / math.sqrt(routed_mult * d) * 0.5)
        self.b2 = nn.Parameter(torch.zeros(E, d))
        self.gate = nn.Linear(d, E, bias=False)
        self.register_buffer("bias", torch.zeros(E))          # routing bias (selection only, not weighting)
        self.register_buffer("load", torch.zeros(E))

    def forward(self, x):
        s = x.shape
        t = x.reshape(-1, s[-1])
        score = torch.sigmoid(self.gate(t).float())                                   # [T, E]
        top = torch.topk(score + self.bias, self.k, -1).indices                       # biased selection
        w = torch.gather(score, -1, top)
        w = (w / w.sum(-1, keepdim=True).clamp(min=1e-6)).to(t.dtype)                 # unbiased weights
        hid = F.gelu(torch.einsum("td,edh->teh", t, self.w1) + self.b1)               # all experts (small E)
        out = torch.einsum("teh,ehd->ted", hid, self.w2) + self.b2                    # [T, E, d]
        sel = torch.gather(out, 1, top[..., None].expand(-1, -1, s[-1]))              # [T, k, d]
        y = (w[..., None] * sel).sum(1) + self.shared(t)
        if self.training:
            with torch.no_grad():
                cnt = torch.bincount(top.reshape(-1), minlength=self.E).float()
                self.load.copy_(cnt / cnt.sum().clamp(min=1))
                self.bias += self.gamma * torch.sign(1.0 / self.E - self.load)
        return y.reshape(s)


class Layer(nn.Module):
    def __init__(self, d, heads, E, k, drop=0.1):
        super().__init__()
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.att = nn.MultiheadAttention(d, heads, dropout=drop, batch_first=True)
        self.moe = MoE(d, E, k)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        h = self.n1(x)
        x = x + self.drop(self.att(h, h, h, need_weights=False)[0])
        return x + self.drop(self.moe(self.n2(x)))


class PWMF(nn.Module):
    def __init__(self, d=288, layers=5, heads=8, E=8, k=2, drop=0.1):
        super().__init__()
        self.cfg = dict(d=d, layers=layers, heads=heads, E=E, k=k, drop=drop)
        self.d = d
        self.patch = nn.Linear(K * 2 * SPD, d)
        self.pos = nn.Parameter(torch.zeros(P + 1, d))
        self.ctx = nn.Linear(H + 2, d)                         # forecast-hour sun + day of year -> context token
        self.mask_tok = nn.Parameter(torch.zeros(d))
        self.layers = nn.ModuleList([Layer(d, heads, E, k, drop) for _ in range(layers)])
        self.norm = nn.LayerNorm(d)
        self.att = nn.Linear(d, 1)
        self.head = nn.Sequential(nn.Linear(2 * d, 2 * d), nn.GELU(), nn.Linear(2 * d, K * H * 3))
        self.rec = nn.Linear(d, K * SPD)
        nn.init.zeros_(self.head[-1].weight); nn.init.zeros_(self.head[-1].bias)

    @staticmethod
    def normalise(v, m):
        cnt = m.sum((2, 3), keepdim=True).clamp(min=1)
        mu = (v * m).sum((2, 3), keepdim=True) / cnt
        var = (((v - mu) * m) ** 2).sum((2, 3), keepdim=True) / cnt
        fl = torch.tensor(FLOOR, device=v.device, dtype=v.dtype)[None, :, None, None]
        sc = torch.maximum(var.sqrt(), fl)
        return (v - mu) / sc * m, mu, sc

    def encode(self, v, m, sun, doy, hide_frac=0.0):
        """v, m: [B, K, 21, 24] raw values and observed flags; sun: [B, 24]; doy: [B, 2].
        Returns hidden states [B, 22, d] (context token first), the normalised window and its stats, and the hidden-day mask."""
        z, mu, sc = self.normalise(v, m)
        B = v.shape[0]
        e = torch.cat([z, m], -1).permute(0, 2, 1, 3).reshape(B, P, -1)               # [B, 21, K*48]
        h = self.patch(e)
        hide = None
        if hide_frac > 0:
            hide = torch.rand(B, P, device=v.device) < hide_frac
            h = torch.where(hide[..., None], self.mask_tok.to(h.dtype).expand_as(h), h)
        c = self.ctx(torch.cat([sun, doy], -1))[:, None]
        h = torch.cat([c, h], 1) + self.pos[None]
        for lay in self.layers:
            h = lay(h)
        return self.norm(h), z, mu, sc, hide

    def pooled(self, h):
        w = torch.softmax(self.att(h).squeeze(-1).float(), -1).to(h.dtype)
        return torch.cat([(w[..., None] * h).sum(1), h[:, -1]], -1)                   # [B, 2d]

    def forward(self, v, m, sun, doy, hide_frac=0.0):
        """Quantile forecast of the next 24 h in real units: [B, K, 24, 3]; plus the reconstruction loss."""
        h, z, mu, sc, hide = self.encode(v, m, sun, doy, hide_frac)
        last = z[:, :, -1]                                                            # yesterday's 24 h, normalised
        off = self.head(self.pooled(h)).float().reshape(-1, K, H, 3)
        qn, _ = torch.sort(last[..., None].float() + off, -1)
        q = qn * sc.float() + mu.float()
        rec_loss = torch.zeros((), device=v.device)
        if hide is not None and hide.any():
            rec = self.rec(h[:, 1:]).float().reshape(-1, P, K, SPD)
            tgt = z.permute(0, 2, 1, 3).float()
            mm = m.permute(0, 2, 1, 3).float() * hide[..., None, None]
            rec_loss = (((rec - tgt) ** 2) * mm).sum() / mm.sum().clamp(min=1)
        return q, rec_loss, (mu, sc)

    def n_params(self):
        return sum(p.numel() for p in self.parameters())


def load(path, device="cpu"):
    ck = torch.load(path, map_location=device, weights_only=False)
    m = PWMF(**ck["cfg"])
    m.load_state_dict(ck["state"])
    return m
