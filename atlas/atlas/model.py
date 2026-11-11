"""Atlas: a compact numerical world model (never more than 10M trainable parameters).

Modules (the eight parts of the design):
  1 numerical encoder      each node's observed window (values, observed-flags, forcing) -> a vector
  2 system state           z [B, N, d]: one latent state per node at the forecast start
  3 spatial engine         attention between nodes with a bias computed from their geometry (offset, distance)
  4 temporal engine        the encoder reads the whole window; the transition below is iterated in time
  5 world dynamics         ONE transition network applied repeatedly: z <- z + f(z, forcing), then spatial exchange
  6 physics constraints    hard projections applied to every forecast: bounds, and conservation of total amount
  7 intervention           the future forcing enters the transition, so a changed forcing gives a changed future
  8 uncertainty            10/50/90% quantiles that cannot cross; their width is the "not enough information" signal

The same weights are used at every node and at every transition step.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

QS = (0.1, 0.5, 0.9)
MAX_PARAMS = 10_000_000


class Block(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.n = nn.LayerNorm(d); self.a = nn.Linear(d, 2 * d); self.b = nn.Linear(2 * d, d)

    def forward(self, x):
        return x + self.b(F.gelu(self.a(self.n(x))))


class GeoAttention(nn.Module):
    """Attention between nodes; an MLP of the pair geometry adds a bias per head (who can influence whom)."""

    def __init__(self, d, heads, geo_dim):
        super().__init__()
        self.h = heads
        self.n = nn.LayerNorm(d); self.qkv = nn.Linear(d, 3 * d); self.o = nn.Linear(d, d)
        self.geo = nn.Sequential(nn.Linear(geo_dim, 16), nn.GELU(), nn.Linear(16, heads))

    def forward(self, z, geo):
        B, N, d = z.shape
        q, k, v = self.qkv(self.n(z)).reshape(B, N, 3, self.h, d // self.h).permute(2, 0, 3, 1, 4)
        bias = self.geo(geo).permute(2, 0, 1)[None]                      # [1, h, N, N]
        y = F.scaled_dot_product_attention(q, k, v, attn_mask=bias)
        return z + self.o(y.transpose(1, 2).reshape(B, N, d))


class Atlas(nn.Module):
    def __init__(self, d=64, L=16, H=16, C=1, U=1, enc_depth=2, dyn_depth=2, lat_steps=4, heads=4,
                 spatial=False, geo_dim=3, lo=None, hi=None, conserve=False, dt=1.0):
        super().__init__()
        assert H % lat_steps == 0
        self.cfg = dict(d=d, L=L, H=H, C=C, U=U, enc_depth=enc_depth, dyn_depth=dyn_depth, lat_steps=lat_steps,
                        heads=heads, spatial=spatial, geo_dim=geo_dim, lo=lo, hi=hi, conserve=conserve, dt=dt)
        self.L, self.H, self.C, self.U, self.S, self.k = L, H, C, U, lat_steps, H // lat_steps
        self.lo, self.hi, self.conserve, self.dt = lo, hi, conserve, dt
        self.inp = nn.Linear(L * (2 * C + U), d)
        self.enc = nn.ModuleList([Block(d) for _ in range(enc_depth)])
        self.rec = nn.Linear(d, L * C)
        self.sp = GeoAttention(d, heads, geo_dim) if spatial else None
        self.uemb = nn.Linear(self.k * U, d)
        self.dyn = nn.ModuleList([Block(d) for _ in range(dyn_depth)])
        self.dec = nn.Linear(d, self.k * C * 3)
        nn.init.zeros_(self.dec.weight); nn.init.zeros_(self.dec.bias)
        assert self.n_params() <= MAX_PARAMS, "Atlas must not exceed 10M trainable parameters"

    def n_params(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def forward(self, yc, mc, uc, uf, geo=None):
        """yc, mc: [B, N, L, C] values and observed flags (hidden values must be zeroed by the caller);
        uc [B, N, L, U], uf [B, N, H, U] forcing; geo [N, N, geo_dim].
        Returns quantiles [B, N, H, C, 3] and the reconstruction of the context [B, N, L, C]."""
        B, N = yc.shape[:2]
        x = torch.cat([(yc * mc).flatten(2), mc.flatten(2), uc.flatten(2)], -1)
        z = self.inp(x)
        for b in self.enc:
            z = b(z)
        if self.sp is not None:
            z = self.sp(z, geo)
        rec = self.rec(z).reshape(B, N, self.L, self.C)
        # anchor: each variable's last observed value in the window (0 if none)
        idx = (mc * torch.arange(1, self.L + 1, device=yc.device)[None, None, :, None]).argmax(2, keepdim=True)
        anchor = torch.gather(yc * mc, 2, idx)                           # [B, N, 1, C]
        outs = []
        for s in range(self.S):
            z = z + self.uemb(uf[:, :, s * self.k:(s + 1) * self.k].flatten(2))
            for b in self.dyn:
                z = b(z)
            if self.sp is not None:
                z = self.sp(z, geo)
            outs.append(self.dec(z).reshape(B, N, self.k, self.C, 3))
        o = torch.cat(outs, 2)
        med = anchor[..., None] + o[..., 1:2]
        q = torch.cat([med - F.softplus(o[..., 0:1]), med, med + F.softplus(o[..., 2:3])], -1)
        return self.physics(q, yc, mc, uc, uf), rec

    def physics(self, q, yc, mc, uc, uf):
        """Hard rules. (a) conservation: on a closed system the total amount changes only by the known sources,
        total[t+1] = total[t] + dt * sum(sources[t]); every forecast is shifted so its node total obeys this.
        The starting total is estimated from the observed window. (b) bounds: values clipped to [lo, hi]."""
        if self.conserve:
            N = q.shape[1]
            cnt = mc.sum(1).clamp(min=1)                                  # [B, L, C] observed nodes per step
            mean_c = (yc * mc).sum(1) / cnt                               # mean concentration per step
            ok = (mc.sum(1) > 0).float()
            src_c = uc.sum(1).sum(-1, keepdim=True) * self.dt / N         # mean added per step [B, L, 1]
            # carry each observed step forward to the forecast start: add the sources from that step on
            later = torch.flip(torch.cumsum(torch.flip(src_c, [1]), 1), [1])
            m0 = ((mean_c + later) * ok).sum(1, keepdim=True) / ok.sum(1, keepdim=True).clamp(min=1)   # [B, 1, C]
            src_f = uf.sum(1).sum(-1, keepdim=True) * self.dt / N         # [B, H, 1]
            tgt = m0 + torch.cumsum(src_f, 1) - src_f                     # mean at each forecast step [B, H, C]
            q = q + (tgt[:, None, :, :, None] - q[..., 1:2].mean(1, keepdim=True))
        if self.lo is not None or self.hi is not None:
            q = q.clamp(min=self.lo, max=self.hi)
        return q


def ring_geo(M):
    """Geometry of a ring of M equally spaced nodes: sin, cos of the signed angular offset, and the distance."""
    i = torch.arange(M)
    off = (i[None] - i[:, None]) * (2 * torch.pi / M)
    dist = torch.minimum((i[None] - i[:, None]) % M, (i[:, None] - i[None]) % M).float() / (M / 2)
    return torch.stack([torch.sin(off), torch.cos(off), dist], -1)


def sized(target, **kw):
    """The Atlas whose parameter count is the largest not exceeding `target` (width is the only thing changed)."""
    heads = kw.get("heads", 4)
    lo, hi = 1, 400
    while lo < hi:
        mid = (lo + hi + 1) // 2
        try:
            n = Atlas(d=mid * heads, **kw).n_params()
        except AssertionError:
            n = 10 ** 12
        if n <= target: lo = mid
        else: hi = mid - 1
    return Atlas(d=lo * heads, **kw)
