"""OPPONENT benchmark: Google TimesFM, zero-shot, on exactly the same test windows as PWM.

Run ONLY with the separate opponents environment's python. This file imports the shared
data loader and scoring function from pwm/, but never PWM's model, and nothing here is ever
saved into or mixed with PWM weights.

  opponents_env/bin/python opponents/run_timesfm.py --data PEMS08 --model tfm25 --ctx 512
  opponents_env/bin/python opponents/run_timesfm.py --data PEMS08 --model tfm3  --ctx 512 --mode multivariate

Fairness choices (all in TimesFM's favour or neutral):
  * TimesFM gets a LONG history (default 512 steps) while PWM sees only 12 (PeMS) / 30 (IMD).
  * TimesFM 3.0 can also run multivariate, letting it look at other locations too.
  * Scoring uses the same function, windows and masking as PWM.
Licences: TimesFM 2.5 weights = Apache-2.0. TimesFM 3.0 weights = non-commercial research only.
"""
import argparse, json, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from pwm.data import load, ROOT          # data + scoring only


def contexts_for(ds, idx, ctx):
    """[W, N, ctx] real-unit histories ending just before each window (NaN gaps forward-filled)."""
    lo = idx[:, None] + np.arange(-ctx, 0)[None]
    lo = np.clip(lo, 0, None)
    c = ds.raw[lo]                                            # [W, ctx, N]
    c = c.transpose(0, 2, 1).copy()
    for w in range(c.shape[0]):                               # forward fill, then 0
        x = c[w]
        mask = np.isnan(x)
        if mask.any():
            idxs = np.where(~mask, np.arange(x.shape[1]), 0)
            np.maximum.accumulate(idxs, axis=1, out=idxs)
            c[w] = np.nan_to_num(x[np.arange(x.shape[0])[:, None], idxs], nan=0.0)
    return c.astype(np.float32)


class TFM25:
    name, licence = "TimesFM-2.5 (Google, 200M)", "Apache-2.0"

    def __init__(self, ctx, H, bs):
        import timesfm, torch
        torch.set_float32_matmul_precision("high")
        self.m = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
        self.m.compile(timesfm.ForecastConfig(
            max_context=int(np.ceil(ctx / 32) * 32), max_horizon=128, normalize_inputs=True,
            use_continuous_quantile_head=True, force_flip_invariance=True,
            infer_is_positive=True, fix_quantile_crossing=True, per_core_batch_size=bs))
        self.H = H

    def __call__(self, series):                              # list of 1-D arrays
        point, q = self.m.forecast(horizon=self.H, inputs=series)
        return q[..., 1], q[..., 5], q[..., 9]                # 10th, median, 90th percentile


class TFM3:
    name, licence = "TimesFM-3.0 (Google)", "non-commercial research licence"

    def __init__(self, ctx, H, bs, mode):
        import torch
        from timesfm3 import TimesFM3Evaluator, ModelConfig
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.m = TimesFM3Evaluator(ModelConfig(checkpoint_path="google/timesfm-3.0-pytorch",
                                               per_core_batch_size=bs, device=dev))
        self.H, self.mode = H, mode
        if mode == "multivariate":
            self.name += " multivariate"

    def __call__(self, series):
        if self.mode == "multivariate":                       # series: list of [N, ctx]
            outs = list(self.m.predict_batch(contexts=series, horizon=self.H, return_quantiles=True))
            q = np.stack([o.quantiles for o in outs])          # [W, N, H, 9]
            q = q.reshape(-1, self.H, q.shape[-1])
        else:
            outs = list(self.m.predict_batch(contexts=series, horizon=self.H,
                                             return_quantiles=True, univariate=True))
            q = np.stack([o.quantiles for o in outs])          # [B, H, 9]
        return q[..., 0], q[..., 4], q[..., 8]


class Stub:
    """TEST ONLY - lets the pipeline be checked without downloading weights. Never reported."""
    name, licence = "STUB (pipeline test, not a model)", "n/a"

    def __init__(self, ctx, H, bs, mode="univariate"):
        self.H, self.mode = H, mode

    def __call__(self, series):
        s = np.stack(series)
        if self.mode == "multivariate":
            s = s.reshape(-1, s.shape[-1])
        last = np.repeat(s[:, -1:], self.H, 1)
        return last * 0.8, last, last * 1.2


def main(a):
    """ParadoxBench-1 mode: official test windows, predictions saved as a submission and scored by ParadoxBench."""
    from paradoxbench.spec import TASKS, official_windows
    from paradoxbench.score import record
    ds = load(TASKS[a.task][0])
    idx = official_windows(ds)
    if a.model == "stub":
        fc = Stub(a.ctx, ds.out_len, a.bs, a.mode)
    elif a.model == "tfm25":
        fc = TFM25(a.ctx, ds.out_len, a.bs)
    else:
        fc = TFM3(a.ctx, ds.out_len, a.bs, a.mode)
    print(f"{fc.name} on ParadoxBench-1 {a.task}: {len(idx)} windows x {ds.N} locations, context {a.ctx}", flush=True)
    W, H, N = len(idx), ds.out_len, ds.N
    q10, q50, q90 = (np.zeros((W, H, N), np.float32) for _ in range(3))
    t0 = time.time()
    for s in range(0, W, a.chunk):
        c = contexts_for(ds, idx[s:s + a.chunk], a.ctx)       # [w, N, ctx]
        w = len(c)
        series = list(c) if a.mode == "multivariate" and a.model in ("tfm3", "stub") \
            else list(c.reshape(w * N, a.ctx))
        lo, mid, hi = fc(series)
        for arr, v in ((q10, lo), (q50, mid), (q90, hi)):
            arr[s:s + w] = np.asarray(v, np.float32).reshape(w, N, H).transpose(0, 2, 1)
        if (s // a.chunk) % 20 == 0:
            print(f"  {min(s + a.chunk, W)}/{W} windows ({(time.time()-t0)/60:.1f} min)", flush=True)
    if a.model == "stub":
        print("stub run: pipeline OK, not recorded"); return
    q10, q90 = np.minimum(q10, q50), np.maximum(q90, q50)
    sizes = {"tfm25": 200e6, "tfm3": None}
    record(a.task, "B", fc.name + f" (zero-shot, ctx {a.ctx})", q10, q50, q90,
           {"type": "foundation (Google, zero-shot)", "params": sizes[a.model], "context_steps": a.ctx,
            "trained_on": "Google pretraining corpus; no task data", "licence": fc.licence,
            "minutes": (time.time() - t0) / 60}, ds)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--model", default="tfm25", choices=["tfm25", "tfm3", "stub"])
    ap.add_argument("--mode", default="univariate", choices=["univariate", "multivariate"])
    ap.add_argument("--ctx", type=int, default=512)
    ap.add_argument("--chunk", type=int, default=32, help="windows per forward batch")
    ap.add_argument("--bs", type=int, default=256)
    main(ap.parse_args())
