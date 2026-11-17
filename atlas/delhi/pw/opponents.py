"""Time-series foundation models, zero-shot, on exactly the windows and sensors PWM-W is scored on.

This file never imports Paradox model code, and nothing here is mixed into Paradox weights.
  TimesFM 2.5 (Google, 200M, Apache-2.0)        pip install timesfm
  TimesFM 3.0 (Google, non-commercial licence)  pip install timesfm   (module timesfm3) - evaluation only;
                                                univariate, and multivariate (all sensors of the network together)
  Chronos-Bolt base (Amazon, 205M, Apache-2.0)  pip install chronos-forecasting
  Chronos-2 (Amazon, 120M, Apache-2.0)          pip install chronos-forecasting
Added for the WEATHER-5K round of Atlas-5K 25M (atlas/README.md, "Atlas-5K 25M"), evaluation only, zero-shot:
  Sundial base (Tsinghua THUML, 128M, Apache-2.0)  transformers==4.40.1 (remote code)
  Time-MoE 200M (Apache-2.0)                       transformers==4.40.1 (remote code)
  TTM r2 (IBM Research, Apache-2.0)                pip install granite-tsfm
  TiRex (NX-AI, 35M, NXAI community licence)       pip install tirex-ts
Each gets a 1,024-step (10.7-day) univariate history per sensor, longer than PWM-W's look-back (684 steps).
Gaps are forward-filled (then back-filled at the start) because these models expect a contiguous series.
"""
import time

import numpy as np
import torch

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def contexts(y, org, nodes, ctx):
    ix = np.clip(org[:, None] + np.arange(-ctx, 0)[None], 0, None)
    c = y[ix][:, :, nodes].transpose(0, 2, 1).reshape(-1, ctx).copy()      # [W*n, ctx]
    m = np.isnan(c)
    idx = np.where(~m, np.arange(ctx), 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    c = c[np.arange(len(c))[:, None], idx]
    first = np.argmax(~np.isnan(c), 1)
    fv = c[np.arange(len(c)), first]
    c = np.where(np.isnan(c), np.nan_to_num(fv)[:, None], c)
    return c.astype(np.float32)


class TFM25:
    name, licence, params = "TimesFM 2.5 (Google, 200M)", "Apache-2.0", 200e6

    def __init__(self, ctx, H, bs=1024):
        import timesfm
        torch.set_float32_matmul_precision("high")
        self.m = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
        self.m.compile(timesfm.ForecastConfig(max_context=int(np.ceil(ctx / 32) * 32), max_horizon=128,
                                              normalize_inputs=True, use_continuous_quantile_head=True,
                                              force_flip_invariance=True, infer_is_positive=True,
                                              fix_quantile_crossing=True, per_core_batch_size=bs))
        self.H = H

    def __call__(self, c):
        _, q = self.m.forecast(horizon=self.H, inputs=list(c))
        q = np.asarray(q)
        return np.stack([q[..., 1], q[..., 5], q[..., 9]], -1)


class TFM3:
    name, licence, params = "TimesFM 3.0 (Google)", "non-commercial research licence (evaluation only)", None

    def __init__(self, ctx, H, bs=1024, multivariate=False):
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        self.m = TimesFM3Evaluator(ModelConfig(checkpoint_path="google/timesfm-3.0-pytorch",
                                               per_core_batch_size=bs if not multivariate else 64, device=DEV))
        self.H, self.mv = H, multivariate
        if multivariate:
            self.name = "TimesFM 3.0 multivariate (Google)"

    def __call__(self, c):
        if self.mv:                                   # c: [W, n, ctx] -> one multivariate series per window
            outs = list(self.m.predict_batch(contexts=list(c), horizon=self.H, return_quantiles=True))
            q = np.stack([np.asarray(o.quantiles) for o in outs]).reshape(-1, self.H, np.asarray(outs[0].quantiles).shape[-1])
            return np.stack([q[..., 0], q[..., 4], q[..., 8]], -1)
        outs = list(self.m.predict_batch(contexts=list(c), horizon=self.H, return_quantiles=True, univariate=True))
        q = np.stack([np.asarray(o.quantiles) for o in outs]).reshape(len(c), self.H, -1)
        return np.stack([q[..., 0], q[..., 4], q[..., 8]], -1)


class Chronos:
    licence = "Apache-2.0"

    def __init__(self, ctx, H, repo, name, params):
        from chronos import BaseChronosPipeline
        self.p = BaseChronosPipeline.from_pretrained(repo, device_map=DEV)
        self.H, self.name, self.params = H, name, params
        self.two = "chronos-2" in repo

    def __call__(self, c):
        x = torch.tensor(c)
        if self.two:
            x = x[:, None, :]
        q, _ = self.p.predict_quantiles(x, prediction_length=self.H, quantile_levels=[0.1, 0.5, 0.9])
        if isinstance(q, (list, tuple)):
            q = torch.stack([torch.as_tensor(t) for t in q])
        return np.asarray(q.float().cpu()).reshape(len(c), self.H, 3)


def _norm(c):
    """Per-series standardisation on the context (inverted after forecasting); constant series get scale 1."""
    x = torch.as_tensor(np.asarray(c, np.float32))
    mu, sd = x.mean(1, keepdim=True), x.std(1, keepdim=True)
    sd = torch.where(sd > 1e-6, sd, torch.ones_like(sd))
    return (x - mu) / sd, mu, sd


class Sundial:
    """Sundial base (THUML, Tsinghua University, 128M, Apache-2.0); transformers==4.40.1 (its remote code).
    Generative: 20 sample paths per series; the median of the samples is scored."""
    name, licence, params = "Sundial base (Tsinghua THUML, 128M)", "Apache-2.0", 128e6

    def __init__(self, ctx, H, samples=20):
        from transformers import AutoModelForCausalLM
        self.m = AutoModelForCausalLM.from_pretrained("thuml/sundial-base-128m", trust_remote_code=True).to(DEV).eval()
        self.H, self.k = H, samples

    @torch.no_grad()
    def __call__(self, c):
        x, mu, sd = _norm(c)
        out = []
        for i in range(0, len(x), 512):
            s = self.m.generate(x[i:i + 512].to(DEV), max_new_tokens=self.H, num_samples=self.k)   # [n, k, H]
            s = s.reshape(len(x[i:i + 512]), -1, s.shape[-1])[..., -self.H:].float()
            out.append(torch.quantile(s, torch.tensor([0.1, 0.5, 0.9], device=s.device), dim=1).permute(1, 2, 0).cpu())
        q = torch.cat(out) * sd[:, :, None] + mu[:, :, None]
        return q.numpy()


class TimeMoE:
    """Time-MoE (Shi et al., ICLR 2025; Apache-2.0), 50M or 200M; transformers==4.40.1. Point forecast (autoregressive),
    so the three 'quantiles' are the same value; only the median is scored."""
    licence = "Apache-2.0"

    def __init__(self, ctx, H, size="200M"):
        from transformers import AutoModelForCausalLM
        self.m = AutoModelForCausalLM.from_pretrained(f"Maple728/TimeMoE-{size}", trust_remote_code=True,
                                                      torch_dtype=torch.float32).to(DEV).eval()
        self.H, self.name, self.params = H, f"Time-MoE {size} (Shi et al.)", float(size[:-1]) * 1e6

    @torch.no_grad()
    def __call__(self, c):
        x, mu, sd = _norm(c)
        out = []
        for i in range(0, len(x), 256):                       # 256 series at a time keeps the KV cache under ~10 GB
            o = self.m.generate(x[i:i + 256].to(DEV), max_new_tokens=self.H)                    # [n, ctx + H]
            out.append(o[:, -self.H:].float().cpu())
        p = torch.cat(out) * sd + mu
        return np.repeat(p.numpy()[..., None], 3, -1)


class TTM:
    """Tiny Time Mixers r2 (IBM Research, about 1-5M, Apache-2.0); pip install granite-tsfm. The published model for a
    512-step context and the shortest horizon >= H is chosen by IBM's get_model; point forecast."""
    licence = "Apache-2.0"

    def __init__(self, ctx, H):
        from tsfm_public.toolkit.get_model import get_model
        self.m = get_model("ibm-granite/granite-timeseries-ttm-r2", context_length=ctx, prediction_length=H).to(DEV).eval()
        self.H, self.ctx = H, ctx
        self.params = float(sum(p.numel() for p in self.m.parameters()))
        self.name = f"TTM r2 (IBM Research, {self.params / 1e6:.1f}M)"

    @torch.no_grad()
    def __call__(self, c):
        x, mu, sd = _norm(c)
        out = []
        for i in range(0, len(x), 4096):
            o = self.m(past_values=x[i:i + 4096, -self.ctx:, None].to(DEV)).prediction_outputs          # [n, >=H, 1]
            out.append(o[:, :self.H, 0].float().cpu())
        p = torch.cat(out) * sd + mu
        return np.repeat(p.numpy()[..., None], 3, -1)


class TiRex:
    """TiRex (NX-AI, 35M, NXAI community licence: evaluation only); pip install tirex-ts. Quantiles 0.1..0.9."""
    name, licence, params = "TiRex (NX-AI, 35M)", "NXAI community licence (evaluation only)", 35e6

    def __init__(self, ctx, H, repo="NX-AI/TiRex"):
        from tirex import load_model
        self.m = load_model(repo, device=DEV)
        self.H = H

    @torch.no_grad()
    def __call__(self, c):
        x, mu, sd = _norm(c)
        q, _ = self.m.forecast(context=x, prediction_length=self.H, batch_size=1024)          # [n, H, 9]
        q = torch.as_tensor(q).float().cpu()[..., [0, 4, 8]]
        return (q * sd[:, :, None] + mu[:, :, None]).numpy()


def make(key, ctx, H):
    if key == "sundial":
        return Sundial(ctx, H)
    if key in ("timemoe50", "timemoe200"):
        return TimeMoE(ctx, H, "50M" if key == "timemoe50" else "200M")
    if key == "ttm":
        return TTM(ctx, H)
    if key == "tirex":
        return TiRex(ctx, H)
    if key == "tfm25":
        return TFM25(ctx, H)
    if key == "tfm3":
        return TFM3(ctx, H)
    if key == "tfm3mv":
        return TFM3(ctx, H, multivariate=True)
    if key == "chronos-bolt":
        return Chronos(ctx, H, "amazon/chronos-bolt-base", "Chronos-Bolt base (Amazon, 205M)", 205e6)
    if key == "chronos2":
        return Chronos(ctx, H, "amazon/chronos-2", "Chronos-2 (Amazon, 120M)", 120e6)
    raise KeyError(key)


def run(key, y, org, nodes, H, ctx=1024, chunk=2048, log=print):
    """Returns real-unit quantiles [W, n, H, 3] and metadata."""
    t0 = time.time()
    fc = make(key, ctx, H)
    c = contexts(y, org, nodes, ctx)
    out = []
    if key == "tfm3mv":                                # windows of whole networks: [W, n, ctx]
        c = c.reshape(len(org), len(nodes), ctx)
        chunk = 8
    for i in range(0, len(c), chunk):
        out.append(np.asarray(fc(c[i:i + chunk]), np.float32))
        if i == 0:
            log(f"    {fc.name}: first {min(chunk, len(c))} of {len(c)} series in {time.time() - t0:.0f}s")
    q = np.concatenate(out).reshape(len(org), len(nodes), H, 3)
    q = np.sort(np.maximum(q, 0), -1)
    return q, {"name": fc.name, "licence": fc.licence, "params": fc.params, "context_steps": ctx,
               "minutes": round((time.time() - t0) / 60, 2)}
