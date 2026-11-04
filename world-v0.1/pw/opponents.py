"""Time-series foundation models, zero-shot, on exactly the windows and sensors PWM-W is scored on.

This file never imports Paradox model code, and nothing here is mixed into Paradox weights.
  TimesFM 2.5 (Google, 200M, Apache-2.0)        pip install timesfm
  TimesFM 3.0 (Google, non-commercial licence)  pip install timesfm   (module timesfm3) - evaluation only
  Chronos-Bolt base (Amazon, 205M, Apache-2.0)  pip install chronos-forecasting
  Chronos-2 (Amazon, 120M, Apache-2.0)          pip install chronos-forecasting
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

    def __init__(self, ctx, H, bs=256):
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

    def __init__(self, ctx, H, bs=256):
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        self.m = TimesFM3Evaluator(ModelConfig(checkpoint_path="google/timesfm-3.0-pytorch",
                                               per_core_batch_size=bs, device=DEV))
        self.H = H

    def __call__(self, c):
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


def make(key, ctx, H):
    if key == "tfm25":
        return TFM25(ctx, H)
    if key == "tfm3":
        return TFM3(ctx, H)
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
    for i in range(0, len(c), chunk):
        out.append(np.asarray(fc(c[i:i + chunk]), np.float32))
        if i == 0:
            log(f"    {fc.name}: first {min(chunk, len(c))} of {len(c)} series in {time.time() - t0:.0f}s")
    q = np.concatenate(out).reshape(len(org), len(nodes), H, 3)
    q = np.sort(np.maximum(q, 0), -1)
    return q, {"name": fc.name, "licence": fc.licence, "params": fc.params, "context_steps": ctx,
               "minutes": round((time.time() - t0) / 60, 2)}
