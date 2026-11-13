"""More time-series foundation models, zero-shot, for Atlas League v2.0 (group A). Same contract as pw/opponents.py:
each wrapper takes contexts [B, ctx] (real units, gaps forward-filled) and returns quantiles [B, H, 3] (10/50/90%).

  Moirai 2.0 R small (Salesforce)   pip install --no-deps uni2ts==2.0.0  (+ einops jaxtyping gluonts lightning hydra-core python-dotenv)
  Toto Open Base 1.0 (Datadog)      pip install --no-deps toto-ts==0.2.0  (+ einops jaxtyping gluonts lightning rotary-embedding-torch)
  TiRex (NX-AI)                     pip install tirex-ts
  Granite TTM r2 (IBM)              pip install granite-tsfm   (point forecast: the three quantiles are equal before calibration)
  Sundial base 128M (Tsinghua)      transformers, trust_remote_code (the model card's own code)
Nothing here is imported by Atlas, and no weights of these models enter any Paradox model.
"""
import numpy as np
import torch

DEV = "cuda" if torch.cuda.is_available() else "cpu"


class Moirai2:
    name, licence, params = "Moirai 2.0 R small (Salesforce)", "CC-BY-NC-4.0 (evaluation only)", 11e6

    def __init__(self, ctx, H):
        from uni2ts.model.moirai2 import Moirai2Forecast, Moirai2Module
        self.m = Moirai2Forecast(prediction_length=H, target_dim=1, feat_dynamic_real_dim=0, past_feat_dynamic_real_dim=0,
                                 context_length=ctx, module=Moirai2Module.from_pretrained("Salesforce/moirai-2.0-R-small")).to(DEV).eval()
        lv = [round(float(x), 2) for x in self.m.module.quantile_levels]
        self.ix = [lv.index(0.1), lv.index(0.5), lv.index(0.9)]
        self.H = H

    def __call__(self, c):
        x = torch.tensor(c, device=DEV)[:, :, None]
        with torch.no_grad():
            q = self.m(past_target=x, past_observed_target=torch.ones_like(x, dtype=torch.bool),
                       past_is_pad=torch.zeros(x.shape[:2], dtype=torch.bool, device=DEV))
        q = q.float().cpu().numpy().reshape(len(c), -1, self.H)                  # [B, quantiles, H]
        return np.stack([q[:, i] for i in self.ix], -1)


class Toto:
    name, licence, params = "Toto Open Base 1.0 (Datadog)", "Apache-2.0", 151e6

    def __init__(self, ctx, H, samples=128):
        from toto.model.toto import Toto as T
        from toto.inference.forecaster import TotoForecaster
        self.t = T.from_pretrained("Datadog/Toto-Open-Base-1.0").to(DEV)
        self.f = TotoForecaster(self.t.model)
        self.H, self.S = H, samples

    def __call__(self, c):
        from toto.data.util.dataset import MaskedTimeseries
        x = torch.tensor(c, device=DEV)[:, None, :]                              # [B, 1 variate, ctx]
        inp = MaskedTimeseries(series=x, padding_mask=torch.ones_like(x, dtype=torch.bool),
                               id_mask=torch.zeros_like(x, dtype=torch.long),
                               timestamp_seconds=torch.zeros_like(x, dtype=torch.long),
                               time_interval_seconds=torch.full(x.shape[:2], 3600, device=DEV, dtype=torch.long))
        with torch.no_grad():
            fc = self.f.forecast(inp, prediction_length=self.H, num_samples=self.S, samples_per_batch=self.S)
        q = torch.stack([fc.quantile(p) for p in (0.1, 0.5, 0.9)], -1)            # [B, 1, H, 3]
        return q[:, 0].float().cpu().numpy()


class TiRex:
    name, licence, params = "TiRex (NX-AI)", "NXAI community licence (evaluation only)", 35e6

    def __init__(self, ctx, H):
        from tirex import load_model
        self.m = load_model("NX-AI/TiRex", device=DEV, backend="torch")
        self.H = H

    def __call__(self, c):
        q, _ = self.m.forecast(context=torch.tensor(c), prediction_length=self.H, output_type="numpy", batch_size=512)
        q = np.asarray(q)                                                        # [B, H, 9]: 0.1 .. 0.9
        return np.stack([q[..., 0], q[..., 4], q[..., 8]], -1)


class TTM:
    name, licence, params = "Granite TTM r2 (IBM)", "Apache-2.0", 1e6

    def __init__(self, ctx, H):
        from tsfm_public.toolkit.get_model import get_model
        self.m = get_model("ibm-granite/granite-timeseries-ttm-r2", context_length=ctx, prediction_length=H).to(DEV).eval()
        self.params = sum(p.numel() for p in self.m.parameters())
        self.H = H

    def __call__(self, c):
        x = torch.tensor(c, device=DEV)[:, :, None]
        with torch.no_grad():
            try:
                o = self.m(past_values=x)
            except Exception as e:                       # the selected TTM variant was trained with a frequency token
                if "freq_token" not in str(e):
                    raise
                from tsfm_public.toolkit.time_series_preprocessor import DEFAULT_FREQUENCY_MAPPING
                o = self.m(past_values=x, freq_token=torch.full((len(c),), DEFAULT_FREQUENCY_MAPPING["h"], device=DEV))
        p = o.prediction_outputs[:, :self.H, 0].float().cpu().numpy()            # point forecast [B, H]
        return np.repeat(p[..., None], 3, -1)


class Sundial:
    name, licence, params = "Sundial base 128M (Tsinghua)", "Apache-2.0", 128e6

    def __init__(self, ctx, H, samples=20):
        from transformers import AutoModelForCausalLM
        self.m = AutoModelForCausalLM.from_pretrained("thuml/sundial-base-128m", trust_remote_code=True).to(DEV).eval()
        self.H, self.S = H, samples

    def __call__(self, c):
        with torch.no_grad():
            s = self.m.generate(torch.tensor(c, device=DEV), max_new_tokens=self.H, num_samples=self.S)   # [B, S, H]
        s = s.float().cpu().numpy().reshape(len(c), self.S, -1)[:, :, :self.H]
        return np.quantile(s, [0.1, 0.5, 0.9], axis=1).transpose(1, 2, 0)


KEYS = {"moirai2": Moirai2, "toto": Toto, "tirex": TiRex, "ttm": TTM, "sundial": Sundial}
