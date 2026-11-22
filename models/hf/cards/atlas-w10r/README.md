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
- air-quality
- weather-forecasting
- india
---

# Atlas W10r (10M + weather, regularised)

**ParadoxAI Lab · Paradox World Model series #53** (model 50 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)'); ERA5 weather at each station (Open-Meteo archive, Copernicus C3S) |
| Parameters | 9,909,792 |
| Status | not adopted |
| Trained | 2026-11-16 (Kaggle atlas-w10r-s400, 2026-11-16) |
| Released | 2026-11-17 |

## Result (as recorded)

validation 8.825 (+1.62% vs W1): not adopted

## What changed in this version

regularised 10M (negative)

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `53_atlas_w10r_weather_10m_reg.pt` | 39,679,365 | `01bf5b86e535c9e6961e73a9efce5a98a67de18a5cd47eb0b2460d4d8dbffcc6` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-w10r", "53_atlas_w10r_weather_10m_reg.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [atlas/README.md](https://github.com/paradoxailab/paradox-world-model/blob/main/atlas/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#52 Atlas W10 (10M + weather)](https://huggingface.co/PARADOXAIlabs/atlas-w10) · Next: [#54 Atlas-W Delhi (T-B, real forecasts)](https://huggingface.co/PARADOXAIlabs/atlas-w-delhi-tb) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
