"""Atlas-W air core v0: an output-first, information-efficient state model (rules: atlas/README.md).

Same interface as atlas.model.Atlas, so the Delhi training loop, batches and scoring are reused unchanged.
What differs:
  minimum information   the window is summarised per variable (last value, 6/24/72 h means relative to it, share
                        observed, any-value flag) instead of being read whole;
  representation        the forecast is an explicit hourly update of the variables themselves, in transport form:
                            x[t+1] = x[t] + k[t] * (x*[t] - x[t]) + kappa * (mean of graph neighbours - x[t])
                        relaxation to an equilibrium x* at rate k (sources, sinks, dilution) and exchange between
                        places at rate kappa. The network outputs only x*, k, kappa and the quantile spread;
  fewest parameters     about 14,000 at width 32. Untrained it is persistence (k and kappa start near zero).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

from .model import Block


class AtlasW(nn.Module):
    sysid = False

    def __init__(self, d=32, L=72, H=24, C=15, U=4, static=78, lo=None, spans=(6, 24, 72), summary=True, exchange=True):
        super().__init__()
        self.cfg = dict(d=d, L=L, H=H, C=C, U=U, static=static, lo=lo, spans=tuple(spans), summary=summary, exchange=exchange)
        self.L, self.H, self.C, self.spans, self.exchange = L, H, C, tuple(spans), exchange
        if isinstance(lo, (list, tuple)):
            self.register_buffer("lo_t", torch.tensor(lo, dtype=torch.float32)[:, None], persistent=False)
        self.inp = nn.Linear((len(spans) + 3) * C + static, d)
        self.enc = Block(d)
        self.mix = nn.Linear(d, d, bias=False)             # one exchange of the summary between graph neighbours
        self.uemb = nn.Linear(U, d)
        self.target = nn.Linear(d, C)                      # equilibrium, as an offset from the last observed value
        self.rate = nn.Linear(d, C)                        # relaxation rate per hour, in (0, 1)
        self.kappa = nn.Linear(d, C)                       # exchange rate with neighbours per hour, in (0, 0.5)
        self.width = nn.Linear(d, 2 * C)
        self.lead = nn.Parameter(torch.zeros(H, C, 2))     # how the spread grows with lead time
        for m in (self.target, self.mix):
            nn.init.zeros_(m.weight)
        nn.init.zeros_(self.target.bias)
        for m in (self.rate, self.kappa):
            nn.init.zeros_(m.weight); nn.init.constant_(m.bias, -4.0)

    def n_params(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def summarise(self, yc, mc):
        t = torch.arange(1, self.L + 1, device=yc.device)[None, None, :, None]
        idx = (mc * t).argmax(2, keepdim=True)
        a = torch.gather(yc * mc, 2, idx)[:, :, 0]                             # last observed value [B, N, C]
        f = [a, (mc.sum(2) > 0).float()]
        for s in self.spans:
            n = mc[:, :, -s:].sum(2)
            mean = (yc * mc)[:, :, -s:].sum(2) / n.clamp(min=1)
            f.append(torch.where(n > 0, mean - a, torch.zeros_like(a)))
        f.append(mc[:, :, -24:].mean(2))
        return a, torch.cat(f, -1)

    def forward(self, yc, mc, uc, uf, geo=None, basis=None, static=None):
        B, N = yc.shape[:2]
        a, f = self.summarise(yc, mc)
        z = self.enc(self.inp(torch.cat([f] + ([static] if static is not None else []), -1)))
        if geo is not None:
            A = geo[..., 0]
            P = A / A.sum(1, keepdim=True).clamp(min=1e-6)                     # row-normalised neighbours [N, N]
            z = z + self.mix(torch.einsum("ij,bjd->bid", P, z))
        else:
            P = None
        kap = 0.5 * torch.sigmoid(self.kappa(z)) if (self.exchange and P is not None) else None
        h = z[:, :, None] + self.uemb(uf)                                      # [B, N, H, d]
        tgt = a[:, :, None] + self.target(h)                                   # equilibrium per hour [B, N, H, C]
        k = torch.sigmoid(self.rate(h))
        x, xs = a, []
        for t in range(self.H):
            x = x + k[:, :, t] * (tgt[:, :, t] - x)
            if kap is not None:
                x = x + kap * (torch.einsum("ij,bjc->bic", P, x) - x)
            xs.append(x)
        med = torch.stack(xs, 2)                                               # [B, N, H, C]
        w = F.softplus(self.width(h).reshape(B, N, self.H, self.C, 2) + self.lead)
        q = torch.stack([med - w[..., 0], med, med + w[..., 1]], -1)
        if hasattr(self, "lo_t"):
            q = torch.maximum(q, self.lo_t)
        rec = (a[:, :, None] * torch.ones_like(yc))                            # no reconstruction head: the last value
        return q, rec, {"z": z.mean(1), "rate": k.mean().detach(), "kappa": None if kap is None else kap.mean().detach()}
