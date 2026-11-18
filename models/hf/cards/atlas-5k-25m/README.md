---
license: apache-2.0
library_name: pytorch
pipeline_tag: time-series-forecasting
tags:
- paradoxailab
- paradox-world-model
- atlas
- forecasting
- spatiotemporal
- weather-forecasting
---

# Atlas-5K 25M (adopted)

**ParadoxAI Lab · Paradox World Model series #59** (model 56 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of temperature, dew point, wind direction, wind speed, sea-level pressure at stations |
| Data | WEATHER-5K (ICML 2026): 5,672 weather stations worldwide, hourly 2014–2023 |
| Parameters | 24,103,796 |
| Status | adopted; WB1 entry at 24 h |
| Trained | 2026-11-18 (Google Colab: steps 0-8,000 on an A100, steps 8,000-80,000 on an L4; final evaluation on an A100-40GB) |
| Released | 2026-11-18 |

## Result (as recorded)

validation E 0.27307 (-1.03% vs 10M (#58); adopted by rule 25M-A); 2023 test MAE T 1.400 / Td 1.468 / WD 53.33 / WS 1.173 / SLP 1.473: lower than PhysicsFormer (19.3M) on 4 of 5; does not beat ECMWF-HRES (pressure); head-to-head (709 stations, 2023 test and live 2024-25): significant wins on all five variables against 20 of 20 opponent-periods (TimesFM 2.5/3.0, Chronos-2, Chronos-Bolt, TiRex, Sundial, Time-MoE, TTM, persistence)

## What changed in this version

#58 grown to 24.1M parameters (hidden layer of every block 784->1,960 units with zero-output new units, one encoder block added; same forecasts at start) and trained 80,000 more steps at peak learning rate 2e-4

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `59_atlas-5k-25m_weather5k_adopted.pt` | 96,529,467 | `29e157f18c2b01355d952e88b237ef2fedc78b72abaf5259d3085007e2b94aa0` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-5k-25m", "59_atlas-5k-25m_weather5k_adopted.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

Build the model with the repository's Atlas class (clone the GitHub repository first):

```python
import sys; sys.path.insert(0, 'paradox-world-model/atlas')
from atlas.model import Atlas
model = Atlas(**{k: v for k, v in ck["cfg"].items() if k != "grown_from"})
model.load_state_dict(ck["weights"]); model.eval()
# q, recon, extras = model(yc, mc, uc, uf, geo, None, static)
# q: [batch, 32 stations, 24 hours, 5 variables, 3 quantiles]; the median q[..., 1] is the forecast
```

Inputs are built as in `atlas/delhi/run_atlas_5k.py`. Paper: [Grow, Don't Restart](https://github.com/paradoxailab/paradox-world-model/blob/main/atlas/paper4/Atlas5K_growth_preprint.pdf).

## Record

Rules, predictions and full results for this version:

* [atlas/README.md](https://github.com/paradoxailab/paradox-world-model/blob/main/atlas/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#58 Atlas-5K 10M (adopted)](https://huggingface.co/paradoxailab/atlas-5k-10m) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
