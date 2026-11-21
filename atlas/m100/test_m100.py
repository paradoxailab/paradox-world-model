"""CPU checks of Atlas-100M's guarantees (run before any GPU job):  python atlas/m100/test_m100.py

1  growth: the grown weather view forecasts as the adopted 24.1M model (float32 rounding only)
2  sharing: the three views share one core; the parameter count is 98,599,994
3  save/load: the shared core is stored once and reloads shared; an exported view loads with atlas.grow.load_any
4  new domains start at persistence: an untrained AQ / traffic view's median equals each node's last observation
5  hybrid widening: extra forcing channels with zero weights leave every forecast unchanged
6  H2 (addendum): 4 systems x 7 channels also start unchanged; the day1 run is used only where published by the start
"""
import os, sys, tempfile

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from m100.multi import MultiAtlas, build_from_24m
from atlas.grow import load_any

REPO = os.path.dirname(os.path.dirname(HERE))
P24 = os.path.join(REPO, "models", "series", "59_atlas-5k-25m_weather5k_adopted.pt")
AQ = dict(L=72, H=24, C=15, U=4, spatial=True, geo_dim=3, static=78, lo=[0.0] * 4 + [float("-inf")] * 11, fill="interp")
TR = dict(L=12, H=12, C=1, U=4, spatial=True, geo_dim=3, static=2, fill="interp")


def inputs(B, N, L, H, C, U, S, g):
    yc = torch.randn(B, N, L, C, generator=g); mc = (torch.rand(B, N, L, C, generator=g) > 0.1).float()
    return yc * mc, mc, torch.randn(B, N, L, U, generator=g), torch.randn(B, N, H, U, generator=g), \
        torch.rand(B, N, N, 3, generator=g), torch.randn(B, N, S, generator=g)


def main():
    g = torch.Generator().manual_seed(0)
    m = build_from_24m(P24, AQ, TR).eval()
    small = load_any(P24).eval()
    x = inputs(2, 32, 48, 24, 5, 4, 4, g)
    with torch.no_grad():
        a = small(*x[:5], None, x[5])[0]; b = m.view("weather")(*x[:5], None, x[5])[0]
    gap = float((a - b).abs().max()); print(f"1 growth: max |24.1M - grown| = {gap:.2e}"); assert gap < 1e-3

    n = m.n_params(); print(f"2 parameters: {n:,}"); assert n == 98_599_994
    assert m.view("aq").enc is m.view("weather").enc and m.view("traffic").sp.qkv is m.view("weather").sp.qkv

    with tempfile.TemporaryDirectory() as d:
        m.save(os.path.join(d, "m.pt")); m2, _ = MultiAtlas.load(os.path.join(d, "m.pt"))
        size = os.path.getsize(os.path.join(d, "m.pt")) / 1e6
        assert m2.view("traffic").dyn is m2.view("weather").dyn and m2.n_params() == n
        m.export_view("aq", os.path.join(d, "aq.pt")); v = load_any(os.path.join(d, "aq.pt"))
        assert v.n_params() == sum(p.numel() for p in m.view("aq").parameters())
        print(f"3 save/load: {size:.0f} MB (core stored once), views shared after reload, exported view loads")

    for dom, kw, B in (("aq", AQ, 2), ("traffic", TR, 2)):
        x = inputs(B, 8, kw["L"], kw["H"], kw["C"], kw["U"], kw["static"], g)
        with torch.no_grad():
            q = m.view(dom)(*x[:5], None, x[5])[0][..., 1]                   # [B, N, H, C] median
        idx = (x[1] * torch.arange(1, kw["L"] + 1)[None, None, :, None]).argmax(2, keepdim=True)
        last = torch.gather(x[0] * x[1], 2, idx).expand(-1, -1, kw["H"], -1)
        if dom == "aq":
            last = torch.maximum(last, m.view("aq").lo_t[:, 0])
        gap = float((q - last).abs().max()); print(f"4 {dom}: untrained median - last observation = {gap:.1e}"); assert gap < 1e-5

    from m100.hybrid import widen_forcing
    w = m.view("weather"); big = widen_forcing(w, 24).eval()
    x = inputs(2, 16, 48, 24, 5, 4, 4, g)
    ex_c, ex_f = torch.randn(2, 16, 48, 24, generator=g), torch.randn(2, 16, 24, 24, generator=g)
    with torch.no_grad():
        a = w(*x[:5], None, x[5])[0]
        b = big(x[0], x[1], torch.cat([x[2], ex_c], -1), torch.cat([x[3], ex_f], -1), x[4], None, x[5])[0]
    gap = float((a - b).abs().max()); print(f"5 hybrid widening: max change = {gap:.1e} (float32 summation order)"); assert gap < 1e-3
    from m100.hybrid import fresh_mask
    big2 = widen_forcing(w, 28).eval()
    ex_c, ex_f = torch.randn(2, 16, 48, 28, generator=g), torch.randn(2, 16, 24, 28, generator=g)
    with torch.no_grad():
        b2 = big2(x[0], x[1], torch.cat([x[2], ex_c], -1), torch.cat([x[3], ex_f], -1), x[4], None, x[5])[0]
    gap = float((a - b2).abs().max()); print(f"6 H2 widening (28 channels): max change = {gap:.1e}"); assert gap < 1e-3
    u = fresh_mask(12, 48, 24)
    assert u[:48].all() and u[48:60].all() and not u[60:].any(), u     # leads 1-12 day1, 13-24 day2 at a 12 h delay
    u6 = fresh_mask(6, 48, 24)
    assert u6[48:66].all() and not u6[66:].any()                       # = the opponents' rule (LATENCY 6): leads 1-18
    print("6 H2 freshness: day1 for leads 1-12 at a 12 h delay (1-18 at 6 h), past hours always")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
