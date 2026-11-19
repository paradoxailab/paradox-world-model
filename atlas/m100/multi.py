"""Atlas-100M: one world model for three physical domains (rules: atlas/m100/PREREG.md).

The model is the adopted Atlas-5K 24.1M (models/series/59) grown once more by the exact width map of atlas/grow.py
(width 392 -> 784, heads 8 -> 16, same depths, hidden width 5 d), so on weather it starts as the 24.1M model exactly.
Its core -- the encoder blocks, the spatial attention (except the geometry bias) and the dynamics blocks -- is SHARED
by three domains:

  weather   WEATHER-5K stations (5 variables, 48 h in, 24 h out), the grown 24.1M model's own input/output layers
  aq        all-India PM2.5 league (15 variables, 72 h in, 24 h out), new input/output layers
  traffic   ParadoxBench traffic networks (1 variable, 12 steps in, 12 out), new input/output layers

Each domain's VIEW is a plain atlas.model.Atlas whose core sub-modules are the shared ones. A view can therefore be
saved as an ordinary Atlas checkpoint ({"sd", "cfg"}) and scored by the existing, unchanged scripts
(score_tsfm_w5k.py, run_atlas_5k.py --eval, run_atlas_india.py's forecast format, ParadoxBench submissions).

Per-domain parts (adapters): inp, rec, uemb, dec, sp.geo (the geometry -> attention-bias MLP; geometry means
different things in each domain) and the physical bounds. A new domain's decoder starts at zero, so its first forecast
is its last observation (persistence) -- nothing is borrowed from another domain's output layer.
"""
import copy

import torch
import torch.nn as nn

from atlas.model import Atlas
from atlas.grow import grow, load_any

DOMAINS = ("weather", "aq", "traffic")
CORE_KEYS = ("d", "heads", "enc_depth", "dyn_depth", "mlp", "lat_steps", "spatial")


def _tie(dst, src):
    """Make dst's core modules the very same objects as src's (shared parameters)."""
    dst.enc = src.enc
    dst.dyn = src.dyn
    dst.sp.n, dst.sp.qkv, dst.sp.o = src.sp.n, src.sp.qkv, src.sp.o


class MultiAtlas(nn.Module):
    def __init__(self, views):
        super().__init__()
        assert set(views) <= set(DOMAINS)
        self.views = nn.ModuleDict(views)
        base = self.views["weather"]
        for k, v in self.views.items():
            if v is not base:
                for c in CORE_KEYS:
                    assert v.cfg.get(c, 2 if c == "mlp" else None) == base.cfg.get(c, 2 if c == "mlp" else None), (k, c)
                _tie(v, base)

    def view(self, domain):
        return self.views[domain]

    def forward(self, domain, *a, **kw):
        return self.views[domain](*a, **kw)

    # ------------------------------------------------------------------ parameter accounting
    def core_params(self):
        b = self.views["weather"]
        mods = list(b.enc) + list(b.dyn) + [b.sp.n, b.sp.qkv, b.sp.o]
        return [p for m in mods for p in m.parameters()]

    def adapter_params(self, domain=None):
        core = {id(p) for p in self.core_params()}
        doms = [domain] if domain else list(self.views)
        seen, out = set(), []
        for d in doms:
            for p in self.views[d].parameters():
                if id(p) not in core and id(p) not in seen:
                    seen.add(id(p)); out.append(p)
        return out

    def n_params(self):
        return sum(p.numel() for p in self.parameters())          # parameters() counts each shared tensor once

    def breakdown(self):
        out = {"core (shared)": sum(p.numel() for p in self.core_params())}
        for d in self.views:
            out[f"{d} adapter"] = sum(p.numel() for p in self.adapter_params(d))
        out["total"] = self.n_params()
        return out

    # ------------------------------------------------------------------ save / load
    def export_view(self, domain, path, meta=None):
        """An ordinary Atlas checkpoint of one domain's view, loadable with atlas.grow.load_any."""
        v = self.views[domain]
        torch.save(dict(sd={k: t.detach().cpu() for k, t in v.state_dict().items()}, cfg=copy.deepcopy(v.cfg),
                        meta=dict(meta or {}, domain=domain, from_model="Atlas-100M", total_params=self.n_params())), path)

    def unique_state(self):
        """state_dict with every shared tensor stored once (the weather view's name is kept)."""
        seen, out = set(), {}
        for k, t in self.state_dict().items():
            key = (t.data_ptr(), tuple(t.shape))
            if key in seen:
                continue
            seen.add(key); out[k] = t.detach().cpu()
        return out

    def save(self, path, extra=None):
        torch.save(dict(cfgs={k: copy.deepcopy(v.cfg) for k, v in self.views.items()},
                        sd=self.unique_state(), **(extra or {})), path)

    @staticmethod
    def from_cfgs(cfgs):
        views = {}
        for k, c in cfgs.items():
            c2 = {kk: vv for kk, vv in c.items() if kk != "grown_from"}
            views[k] = Atlas(**c2)
            if "grown_from" in c:
                views[k].cfg["grown_from"] = c["grown_from"]
        return MultiAtlas(views)

    @staticmethod
    def load(path, map_location="cpu"):
        ck = torch.load(path, map_location=map_location, weights_only=False)
        m = MultiAtlas.from_cfgs(ck["cfgs"])
        res = m.load_state_dict(ck["sd"], strict=False)
        assert not res.unexpected_keys, res.unexpected_keys
        shared = {k for k, t in m.state_dict().items()}
        loaded = set(ck["sd"])
        ptr = {}
        for k, t in m.state_dict().items():                       # every missing key must be a shared tensor
            ptr.setdefault((t.data_ptr(), tuple(t.shape)), []).append(k)
        for ks in ptr.values():
            assert any(k in loaded for k in ks), f"not saved: {ks[:3]}"
        del shared
        return m, ck


def core_cfg(weather_view):
    return {k: weather_view.cfg.get(k) for k in CORE_KEYS if k in weather_view.cfg}


def make_view(core, **domain_kw):
    """A new domain's view with the core's shape; its adapters are freshly initialised (decoder at zero)."""
    kw = dict(domain_kw)
    kw.update(core)
    return Atlas(**kw)


def build_from_24m(path_24m, aq_kw=None, traffic_kw=None, f=2, noise=0.05, seed=700):
    """The 24.1M model grown by width x f (exact), plus new aq / traffic views sharing its core."""
    small = load_any(path_24m)
    w = grow(small, f=f, noise=noise, seed=seed)                  # depths and hidden width kept: width map only
    views = {"weather": w}
    core = core_cfg(w)
    torch.manual_seed(seed + 1)
    if aq_kw is not None:
        views["aq"] = make_view(core, **aq_kw)
    if traffic_kw is not None:
        views["traffic"] = make_view(core, **traffic_kw)
    return MultiAtlas(views)
