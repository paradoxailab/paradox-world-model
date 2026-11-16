"""Grow a trained Atlas into a larger one that computes the same function at the start (README, "Atlas-5K 10M").

Width: d -> f*d (f an integer), heads -> f*heads (head size unchanged). Every vector of the residual stream is tiled f
times ([z, z, ...]); LayerNorm of a tiled vector equals the tiled LayerNorm, so every layer can be mapped exactly:
  * a layer that WRITES the stream or a hidden layer (out axis): its rows are tiled;
  * a layer that READS a tiled vector (in axis): its columns are tiled and divided by f, and a zero-sum perturbation
    (copies get W/f + e_i with sum_i e_i = 0) is added. Because the f inputs are identical copies, the output is
    unchanged exactly, while the copies get different gradients, so they can specialise (symmetry is broken).
  * attention: q, k, v are tiled per head (new head j = old head j mod h); the geometry bias is tiled per head; the
    scale 1/sqrt(head size) does not change.
Depth: new encoder and dynamics blocks are appended with the output layer at zero, so each starts as the identity.

  from atlas.grow import grow
  big = grow(small_model, f=2, enc_depth=7, dyn_depth=7, noise=0.05, seed=0)
"""
import torch

from .model import Atlas, Block


def _tile_out(w, f, groups=1):
    """Tile along dim 0. groups > 1: dim 0 is [groups, n] (e.g. q, k, v) and each group is tiled separately."""
    if groups == 1:
        return w.repeat(f, *([1] * (w.dim() - 1)))
    g = w.reshape(groups, w.shape[0] // groups, *w.shape[1:])
    return g.repeat(1, f, *([1] * (w.dim() - 1))).reshape(groups * f * (w.shape[0] // groups), *w.shape[1:])


def _tile_in(w, f, noise, gen):
    """Tile along dim 1, divide by f, add a perturbation that sums to zero over the f copies."""
    out, n = w.shape
    t = (w / f).repeat(1, f).reshape(out, f, n)
    if noise > 0 and f > 1:
        e = torch.randn(t.shape, generator=gen) * (noise * float(w.std()) / f)
        t = t + (e - e.mean(1, keepdim=True))
    return t.reshape(out, f * n)


@torch.no_grad()
def grow(small, f=2, enc_depth=None, dyn_depth=None, noise=0.05, seed=0):
    cfg = dict(small.cfg)
    assert not cfg.get("sysid") and not cfg.get("phys_dec") and not cfg.get("sp_gate"), "grow() covers the plain Atlas only"
    d, h = cfg["d"], cfg["heads"]
    e0, y0 = cfg["enc_depth"], cfg["dyn_depth"]
    cfg.update(d=f * d, heads=f * h, enc_depth=enc_depth or e0, dyn_depth=dyn_depth or y0)
    assert cfg["enc_depth"] >= e0 and cfg["dyn_depth"] >= y0
    big = Atlas(**cfg)
    gen = torch.Generator().manual_seed(seed)
    s, b = small.state_dict(), big.state_dict()
    new = {}

    def lin(name, out_tile=False, in_tile=False, groups=1):
        w, bb = s[name + ".weight"], s[name + ".bias"]
        if out_tile:
            w, bb = _tile_out(w, f, groups), _tile_out(bb, f, groups)
        if in_tile:
            w = _tile_in(w, f, noise, gen)
        new[name + ".weight"], new[name + ".bias"] = w, bb

    def block(p):
        new[p + ".n.weight"], new[p + ".n.bias"] = _tile_out(s[p + ".n.weight"], f), _tile_out(s[p + ".n.bias"], f)
        lin(p + ".a", out_tile=True, in_tile=True)                 # stream -> hidden (2d -> 2fd)
        lin(p + ".b", out_tile=True, in_tile=True)                 # hidden -> stream

    lin("inp", out_tile=True)
    for i in range(e0):
        block(f"enc.{i}")
    lin("rec", in_tile=True)
    if cfg["spatial"]:
        new["sp.n.weight"], new["sp.n.bias"] = _tile_out(s["sp.n.weight"], f), _tile_out(s["sp.n.bias"], f)
        lin("sp.qkv", out_tile=True, in_tile=True, groups=3)
        lin("sp.o", out_tile=True, in_tile=True)
        for k in ("sp.geo.0.weight", "sp.geo.0.bias"):
            new[k] = s[k]
        lin("sp.geo.2", out_tile=True)                             # one bias per head; new head j = old head j mod h
    lin("uemb", out_tile=True)
    for i in range(y0):
        block(f"dyn.{i}")
    lin("dec", in_tile=True)
    for k, v in b.items():                                         # appended blocks: random input layer, zero output
        if k not in new:
            assert k.startswith(("enc.", "dyn.")), k
            new[k] = torch.zeros_like(v) if (".b." in k) else v
    for k in new:
        assert new[k].shape == b[k].shape, (k, new[k].shape, b[k].shape)
    big.load_state_dict(new)
    big.cfg["grown_from"] = dict(d=d, heads=h, enc_depth=e0, dyn_depth=y0, f=f, noise=noise, seed=seed)
    return big


def load_any(path, map_location="cpu"):
    """An Atlas from a checkpoint saved by the training scripts ({"sd", "cfg"}) or a models/series file
    ({"weights", "cfg", "meta", ...})."""
    ck = torch.load(path, map_location=map_location, weights_only=False)
    sd = ck.get("sd", ck.get("weights"))
    cfg = {k: v for k, v in ck["cfg"].items() if k != "grown_from"}
    m = Atlas(**cfg)
    m.load_state_dict(sd)
    if "grown_from" in ck["cfg"]:
        m.cfg["grown_from"] = ck["cfg"]["grown_from"]
    return m
