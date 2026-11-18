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

# Atlas-5K v2c (adopted)

**ParadoxAI Lab · Paradox World Model series #57** (model 54 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of temperature, dew point, wind direction, wind speed, sea-level pressure at stations |
| Data | WEATHER-5K (ICML 2026): 5,672 weather stations worldwide, hourly 2014–2023 |
| Parameters | 968,672 |
| Status | adopted, tested; grown into #58 (10M) and #59 (25M) |
| Trained | 2026-11-17 (Kaggle atlas-w5k-v2c, 2026-11-16/17) |
| Released | 2026-11-17 |

## Result (as recorded)

validation E 0.28140 (-3.93% vs v1); 2023 test MAE T 1.474 / Td 1.520 / WD 54.84 / WS 1.202 / SLP 1.533: lower than PhysicsFormer on 4 of 5; grown into #58 and #59

## What changed in this version

32 stations per neighbourhood + 150,000 steps

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `57_atlas-5k_v2c_weather5k_adopted.pt` | 3,906,309 | `c47c268e6e88022d02927b97da739059b9b983a56d75ce409eba7b1c0ee4fc0b` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-5k-v2c", "57_atlas-5k_v2c_weather5k_adopted.pt")
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

Previous: [#56 Atlas-5K v2a](https://huggingface.co/paradoxailab/atlas-5k-v2a) · Next: [#58 Atlas-5K 10M (adopted)](https://huggingface.co/paradoxailab/atlas-5k-10m) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
