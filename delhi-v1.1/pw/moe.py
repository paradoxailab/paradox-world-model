"""PWM-F building blocks: a shared-plus-routed mixture of experts and the transformer layer that uses it.

Design ideas taken from published work and implemented from scratch here (no code is copied):
  * fine-grained experts plus one always-on shared expert (the DeepSeekMoE idea): many small routed experts can
    specialise (monsoon, arid, coastal, hill, urban-roof sensors ...) while the shared expert keeps what is common;
  * load balancing without an auxiliary loss (the DeepSeek-V3 idea): each expert has a routing bias that is nudged
    after every training step towards equal load; the bias only affects which experts are picked, never the
    weights given to their outputs, so balancing does not pull against the forecast loss.
The routing weights are inspectable (`last_load`, `route`), so one can ask which expert handles which stations.
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class SharedMoE(nn.Module):
    def __init__(self, d, hid, n_routed=8, topk=2, n_shared=1, bias_step=1e-3):
        super().__init__()
        self.n, self.topk, self.bias_step = n_routed, topk, bias_step
        self.router = nn.Linear(d, n_routed, bias=False)
        nn.init.normal_(self.router.weight, std=0.02)
        self.register_buffer("route_bias", torch.zeros(n_routed))
        self.w1 = nn.Parameter(torch.randn(n_routed, d, hid) / math.sqrt(d))
        self.b1 = nn.Parameter(torch.zeros(n_routed, hid))
        self.w2 = nn.Parameter(torch.randn(n_routed, hid, d) / math.sqrt(hid) * 0.5)
        self.b2 = nn.Parameter(torch.zeros(n_routed, d))
        self.shared = nn.Sequential(nn.Linear(d, hid * n_shared), nn.GELU(), nn.Linear(hid * n_shared, d))
        self.last_load = None
        self.route = None

    def forward(self, x):
        shp = x.shape
        x = x.reshape(-1, shp[-1])
        s = torch.sigmoid(self.router(x).float())                       # affinity of each token to each expert
        _, e = (s + self.route_bias).topk(self.topk, -1)                # the bias only picks experts
        g = s.gather(-1, e)
        g = g / g.sum(-1, keepdim=True).clamp(min=1e-9)                 # weights come from affinities alone
        out = self.shared(x).float()
        load = torch.zeros(self.n, device=x.device)
        for k in range(self.topk):
            for j in range(self.n):
                m = e[:, k] == j
                if m.any():
                    h = F.gelu(x[m] @ self.w1[j].to(x.dtype) + self.b1[j].to(x.dtype))
                    out[m] += g[m, k:k + 1] * (h @ self.w2[j].to(x.dtype) + self.b2[j].to(x.dtype)).float()
                    load[j] += m.float().sum()
        load = load / max(1, x.shape[0] * self.topk)
        self.last_load = load.detach()
        self.route = e.detach().reshape(shp[:-1] + (self.topk,))
        if self.training:                                               # auxiliary-loss-free balancing
            with torch.no_grad():
                self.route_bias += self.bias_step * torch.sign(load.mean() - load)
        return out.to(x.dtype).reshape(shp)


class XLayer(nn.Module):
    """Pre-norm transformer layer over a station's daily patches; the feed-forward part is a SharedMoE."""

    def __init__(self, d, heads, ff, n_routed=8, topk=2, dropout=0.1):
        super().__init__()
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.att = nn.MultiheadAttention(d, heads, dropout=dropout, batch_first=True)
        hid = max(16, (ff * d) // max(1, topk + 1))                     # fine-grained: experts smaller than a dense FFN
        self.moe = SharedMoE(d, hid, n_routed, topk)
        self.drop = nn.Dropout(dropout)

    def forward(self, h):
        a = self.n1(h)
        h = h + self.drop(self.att(a, a, a, need_weights=False)[0])
        return h + self.drop(self.moe(self.n2(h)))
