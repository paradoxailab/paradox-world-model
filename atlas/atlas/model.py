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

from .sysid import identify, interpolate, ring_basis, smooth_forecast  # noqa: F401

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
                 spatial=False, geo_dim=3, lo=None, hi=None, conserve=False, dt=1.0, sysid=False, K=1, lags=2, gate=False, fill="rec",
                 static=0, id_ch=None, phys_dec=False):
        super().__init__()
        assert H % lat_steps == 0
        self.cfg = dict(d=d, L=L, H=H, C=C, U=U, enc_depth=enc_depth, dyn_depth=dyn_depth, lat_steps=lat_steps,
                        heads=heads, spatial=spatial, geo_dim=geo_dim, lo=lo, hi=hi, conserve=conserve, dt=dt,
                        sysid=sysid, K=K, lags=lags, gate=gate, fill=fill, static=static, id_ch=id_ch)
        if phys_dec:                                          # Atlas-P (README, ICML programme): only added when on,
            self.cfg["phys_dec"] = True                       # so earlier checkpoints keep their exact cfg
        self.L, self.H, self.C, self.U, self.S, self.k = L, H, C, U, lat_steps, H // lat_steps
        self.lo, self.hi, self.conserve, self.dt = lo, hi, conserve, dt
        if isinstance(lo, (list, tuple)):                     # one lower bound per variable (-inf = none)
            self.register_buffer("lo_t", torch.tensor(lo, dtype=torch.float32)[:, None], persistent=False)
        self.inp = nn.Linear(L * (2 * C + U) + static, d)     # static: extra per-node inputs (e.g. daily means)
        self.enc = nn.ModuleList([Block(d) for _ in range(enc_depth)])
        self.rec = nn.Linear(d, L * C)
        self.sp = GeoAttention(d, heads, geo_dim) if spatial else None
        self.uemb = nn.Linear(self.k * U, d)
        self.dyn = nn.ModuleList([Block(d) for _ in range(dyn_depth)])
        self.phys_dec = phys_dec
        # Atlas-P: per hour and variable the decoder gives the equilibrium offset, the relaxation rate and two spreads;
        # the median is then stepped hour by hour: x[t+1] = x[t] + k (x* - x) + kappa (neighbour mean - x)
        self.dec = nn.Linear(d, self.k * C * (4 if phys_dec else 3))
        nn.init.zeros_(self.dec.weight); nn.init.zeros_(self.dec.bias)
        if phys_dec:
            self.kappa = nn.Linear(d, C)
            nn.init.zeros_(self.kappa.weight); nn.init.constant_(self.kappa.bias, -4.0)
        self.sysid, self.K, self.p, self.use_gate, self.fill = sysid, K, lags, gate, fill
        if sysid:                       # in-context identification of the dynamics (atlas/sysid.py)
            Ci = self.Ci = id_ch or C                         # the first Ci variables are the identified ones
            FA, FB = lags * K * Ci, lags * K * U
            self.den = nn.Linear(d, L * Ci)                    # correction to the observed values (denoising)
            self.prior = nn.Linear(d, lags * K * (Ci + U) * Ci) # prior guess of the state coefficients, from the window
            self.hyper = nn.Sequential(nn.Linear(FA * Ci, 64), nn.GELU(), nn.Linear(64, FB * Ci))
            self.gate = nn.Sequential(nn.Linear(FA * Ci + 1, 32), nn.GELU(), nn.Linear(32, 1))   # trust in the identified dynamics
            # the response to forcing often cannot be seen in one window (no forcing yet): it is predicted from the
            # identified state coefficients by `hyper`, learned across training trajectories
            lam = torch.zeros(lags, K * (Ci + U)); lam[:, :K * Ci] = -4.6     # weak prior on state coefficients (0.01)
            self.lam = nn.Parameter(lam.flatten())            # log-precision per coefficient (forcing part: 1.0)
            for m in (self.den, self.prior, self.hyper[-1]):
                nn.init.zeros_(m.weight); nn.init.zeros_(m.bias)
            with torch.no_grad():                             # prior starts at persistence: x[t+1] = x[t]
                bb = self.prior.bias.view(lags * K * (Ci + U), Ci)
                for c in range(Ci): bb[c, c] = 1.0
            xm = torch.zeros(lags, K * (Ci + U), dtype=torch.bool); xm[:, :K * Ci] = True
            self.register_buffer("xmask", xm.flatten(), persistent=False)

    def n_params(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def forward(self, yc, mc, uc, uf, geo=None, basis=None, static=None):
        """yc, mc: [B, N, L, C] values and observed flags (hidden values must be zeroed by the caller);
        uc [B, N, L, U], uf [B, N, H, U] forcing; geo [N, N, geo_dim]; basis [K, N, N] (sysid only).
        Returns quantiles [B, N, H, C, 3], the reconstruction of the context [B, N, L, C], and a dict of extras."""
        B, N = yc.shape[:2]
        x = torch.cat([(yc * mc).flatten(2), mc.flatten(2), uc.flatten(2)] + ([static] if static is not None else []), -1)
        z = self.inp(x)
        for b in self.enc:
            z = b(z)
        if self.sp is not None:
            z = self.sp(z, geo)
        z0 = z
        rec = self.rec(z).reshape(B, N, self.L, self.C)
        ex = {"z": z0.mean(1)}
        if self.sysid:
            if basis is None:
                basis = torch.eye(N, device=yc.device)[None]
            Ci = self.Ci; yi, mi = yc[..., :Ci], mc[..., :Ci]
            den = self.den(z).reshape(B, N, self.L, Ci)
            # complete window for the first solve. fill="rec" (v0.2): hidden values from the network's reconstruction.
            # fill="interp" (v0.3): hidden values by linear interpolation in time; the network only adds a correction.
            if self.fill == "interp":
                xh = interpolate(yi * mi, mi) + den
            else:
                xh = mi * (yi + den) + (1 - mi) * rec[..., :Ci]
            lam = torch.exp(self.lam)
            th0 = self.prior(z.mean(1)).reshape(B, -1, Ci) * self.xmask[None, :, None]
            th1 = identify(xh, uc, basis, self.p, lam, th0, target=xh, w=mi)
            thB = self.hyper(th1[:, self.xmask].flatten(1)).reshape(B, -1, Ci)
            th0 = th0.masked_scatter((~self.xmask)[None, :, None].expand_as(th0), thB)
            theta = identify(xh, uc, basis, self.p, lam, th0, target=xh, w=mi)
            # initial state from ALL observed values (weights = observed flags), then run the dynamics forward
            ua = torch.cat([uc, uf], 2)
            if self.fill == "rec" and bool((mi < 1).any()):    # v0.2, missing values: replace the network's fill-in by the fitted trajectory, re-identify
                xs, _ = smooth_forecast(theta, yi * mi, mi, ua, basis, self.p, 0)
                xh = mi * xh + (1 - mi) * xs
                theta = identify(xh, uc, basis, self.p, lam, th0)
            xs, fc = smooth_forecast(theta, yi * mi, mi, ua, basis, self.p, self.H)
            # boundedness: a forecast may not leave 3x the observed range (plus room for forcing)
            lim = 3 * (yi * mi).abs().flatten(1).amax(1) + 3 * ua.abs().flatten(1).amax(1) + 1
            fc = torch.maximum(torch.minimum(fc, lim[:, None, None, None]), -lim[:, None, None, None])
            # how well the identified dynamics explain the window, relative to the window's own variation
            res = (((xs - yi) ** 2) * mi).flatten(1).sum(1) / ((yi - (yi * mi).flatten(1).sum(1)[:, None, None, None]
                   / mi.flatten(1).sum(1).clamp(min=1)[:, None, None, None]) ** 2 * mi).flatten(1).sum(1).clamp(min=1e-6)
            thA = theta[:, self.xmask].flatten(1)
            alpha = torch.sigmoid(self.gate(torch.cat([thA, torch.log(res + 1e-6)[:, None]], 1)))[:, :, None, None]
            idx = (mc * torch.arange(1, self.L + 1, device=yc.device)[None, None, :, None]).argmax(2, keepdim=True)
            anchor = torch.gather(yc * mc, 2, idx).expand(-1, -1, self.H, -1)
            base = alpha * fc + (1 - alpha) * anchor[..., :Ci] if self.use_gate else fc   # gate: alpha -> 0 gives the plain Atlas
            base = torch.cat([base, anchor[..., Ci:]], -1)       # variables that are not identified keep the anchor
            ex.update(theta=torch.cat([thA, torch.log(res + 1e-6)[:, None]], 1), base=fc, alpha=alpha.flatten())
        else:
            # anchor: each variable's last observed value in the window (0 if none)
            idx = (mc * torch.arange(1, self.L + 1, device=yc.device)[None, None, :, None]).argmax(2, keepdim=True)
            base = torch.gather(yc * mc, 2, idx).expand(-1, -1, self.H, -1)
        outs = []
        for s in range(self.S):
            z = z + self.uemb(uf[:, :, s * self.k:(s + 1) * self.k].flatten(2))
            for b in self.dyn:
                z = b(z)
            if self.sp is not None:
                z = self.sp(z, geo)
            outs.append(self.dec(z).reshape(B, N, self.k, self.C, 4 if self.phys_dec else 3))
        o = torch.cat(outs, 2)
        if self.phys_dec:
            tgt = base + o[..., 0]                                         # equilibrium per hour [B, N, H, C]
            kr = torch.sigmoid(o[..., 1] - 4.0)                            # starts near 0: persistence
            P = None
            if geo is not None and self.sp is not None:
                A = geo[..., 0]
                P = A / A.sum(1, keepdim=True).clamp(min=1e-6)
            kap = 0.5 * torch.sigmoid(self.kappa(z0)) if P is not None else None   # [B, N, C]
            x, xs = base[:, :, 0], []
            for t in range(self.H):
                x = x + kr[:, :, t] * (tgt[:, :, t] - x)
                if kap is not None:
                    x = x + kap * (torch.einsum("ij,bjc->bic", P, x) - x)
                xs.append(x)
            med = torch.stack(xs, 2)[..., None]
            o = torch.cat([o[..., 2:3], o[..., 0:1], o[..., 3:4]], -1)     # spreads where the quantile code expects them
        else:
            med = base[..., None] + o[..., 1:2]
        q = torch.cat([med - F.softplus(o[..., 0:1]), med, med + F.softplus(o[..., 2:3])], -1)
        return self.physics(q, yc, mc, uc, uf), rec, ex

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
        if hasattr(self, "lo_t"):
            q = torch.maximum(q, self.lo_t)
        elif self.lo is not None or self.hi is not None:
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
