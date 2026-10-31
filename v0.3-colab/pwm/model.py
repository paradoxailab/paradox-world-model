"""PWM-Dyn: the first trained component of Paradox World Model.

A spatiotemporal dynamics model over a physical network. It learns:
  * temporal dynamics   - how each location's state evolves over the last hour
  * periodic structure  - daily / weekly rhythms (time-of-day, day-of-week embeddings)
  * spatial propagation - how state flows along the REAL road graph (distance-weighted)
                          plus an optional learned "latent" connectivity
  * uncertainty         - quantile heads (10th / 50th / 90th percentile) for every forecast

Two variants:
  transductive=True  : adds per-location identity embeddings + learned adjacency (max accuracy
                       on a known region; cannot transfer to a new region by construction)
  transductive=False : region-agnostic - uses only observations, time and the physical graph,
                       so the same weights can be run on a road network it has never seen.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

QUANTILES = (0.1, 0.5, 0.9)


class GraphMix(nn.Module):
    """Two-hop diffusion over the physical graph (+ learned graph), gated residual."""

    def __init__(self, d, n_graphs, hops=2, drop=0.1):
        super().__init__()
        self.hops = hops
        self.proj = nn.Linear(d * (1 + n_graphs * hops), d)
        self.ff = nn.Sequential(nn.Linear(d, 2 * d), nn.GELU(), nn.Dropout(drop), nn.Linear(2 * d, d))
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.drop = nn.Dropout(drop)

    def forward(self, h, graphs):  # h [B, N, d]
        outs = [h]
        for A in graphs:
            z = h
            for _ in range(self.hops):
                z = torch.einsum("nm,bmd->bnd", A, z)
                outs.append(z)
        h = self.n1(h + self.drop(self.proj(torch.cat(outs, -1))))
        return self.n2(h + self.drop(self.ff(h)))


class PWMDyn(nn.Module):
    def __init__(self, n_nodes=None, in_len=12, out_len=12, d=96, layers=3,
                 transductive=True, drop=0.1, steps_per_day=288, mask_aware=False):
        super().__init__()
        self.transductive, self.out_len, self.mask_aware = transductive, out_len, mask_aware
        k = 2 if mask_aware else 1   # v0.2+: each input step also carries an "observed?" flag
        self.temporal = nn.Sequential(nn.Linear(in_len * k, d), nn.GELU(), nn.Linear(d, d))
        self.stats = nn.Linear(3 + (1 if mask_aware else 0), d)  # last, mean, trend (+ share observed)
        self.tod = nn.Embedding(steps_per_day, d)
        self.dow = nn.Embedding(7, d)
        n_g = 1
        if transductive:
            self.node = nn.Parameter(torch.randn(n_nodes, d) * 0.1)
            self.src = nn.Parameter(torch.randn(n_nodes, 16) * 0.1)
            self.dst = nn.Parameter(torch.randn(n_nodes, 16) * 0.1)
            n_g = 2
        self.blocks = nn.ModuleList([GraphMix(d, n_g, drop=drop) for _ in range(layers)])
        self.head = nn.Linear(d, out_len * len(QUANTILES))

    def learned_graph(self):
        return F.softmax(F.relu(self.src @ self.dst.T), dim=-1)

    def forward(self, x, tod, dow, A, obs=None):
        # x [B, L, N] normalised history; obs [B, L, N] 1 = observed, 0 = missing
        xt = x.transpose(1, 2)                                     # [B, N, L]
        if self.mask_aware:
            o = torch.ones_like(xt) if obs is None else obs.transpose(1, 2).float()
            xt = xt * o
            cues = torch.stack([xt[..., -1], (xt.sum(-1) / o.sum(-1).clamp(min=1)),
                                xt[..., -1] - xt[..., 0], o.mean(-1)], -1)
            h = self.temporal(torch.cat([xt, o], -1)) + self.stats(cues)
        else:
            cues = torch.stack([xt[..., -1], xt.mean(-1), xt[..., -1] - xt[..., 0]], -1)
            h = self.temporal(xt) + self.stats(cues)
        h = h + (self.tod(tod) + self.dow(dow))[:, None, :]
        graphs = [A]
        if self.transductive:
            h = h + self.node[None]
            graphs.append(self.learned_graph())
        for blk in self.blocks:
            h = blk(h, graphs)
        out = self.head(h).view(x.shape[0], x.shape[2], self.out_len, len(QUANTILES))
        out = out + xt[..., -1:, None]                             # predict change from last state
        q = out.permute(0, 2, 1, 3)                                # [B, H, N, Q]
        return torch.sort(q, dim=-1).values                        # enforce q10 <= q50 <= q90


def pinball(pred, y, mask):
    """Quantile (pinball) loss; pred [B,H,N,Q], y [B,H,N] (both normalised)."""
    qs = torch.tensor(QUANTILES, device=pred.device)
    e = y[..., None] - pred
    l = torch.maximum(qs * e, (qs - 1) * e)
    m = mask[..., None].float()
    return (l * m).sum() / (m.sum() * len(QUANTILES)).clamp(min=1)
