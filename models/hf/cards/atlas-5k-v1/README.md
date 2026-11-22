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

# Atlas-5K v1

**ParadoxAI Lab · Paradox World Model series #55** (model 52 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of temperature, dew point, wind direction, wind speed, sea-level pressure at stations |
| Data | WEATHER-5K (ICML 2026): 5,672 weather stations worldwide, hourly 2014–2023 |
| Parameters | 968,672 |
| Status | reported |
| Trained | 2026-11-16 (Kaggle atlas-w5k-atlas1m-h24, 2026-11-16) |
| Released | 2026-11-17 |

## Result (as recorded)

WEATHER-5K test 2023 MAE: T 1.553, Td 1.596, WS 1.228, WD 56.46, SLP 1.664; level with PhysicsFormer (19.3M) on T/Td; beats neither under the pre-registered rules

## What changed in this version

world benchmark entry

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `55_atlas-5k_v1_weather5k.pt` | 3,942,805 | `6d6ce30b6edff83c1e8b2b90153e1935c68208897f0f162941591fade74dcfbc` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-5k-v1", "55_atlas-5k_v1_weather5k.pt")
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

Previous: [#54 Atlas-W Delhi (T-B, real forecasts)](https://huggingface.co/PARADOXAIlabs/atlas-w-delhi-tb) · Next: [#56 Atlas-5K v2a](https://huggingface.co/PARADOXAIlabs/atlas-5k-v2a) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
