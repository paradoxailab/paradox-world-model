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

# Atlas W10 (10M + weather)

**ParadoxAI Lab · Paradox World Model series #52** (model 49 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)'); ERA5 weather at each station (Open-Meteo archive, Copernicus C3S) |
| Parameters | 9,909,792 |
| Status | not adopted |
| Trained | 2026-11-16 (Kaggle atlas-w10-s400, 2026-11-16) |
| Released | 2026-11-17 |

## Result (as recorded)

validation 8.773 (+1.02% vs W1): not adopted

## What changed in this version

10M with weather (negative)

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `52_atlas_w10_weather_10m.pt` | 39,678,933 | `febbbcf0c2b7e68f4abe4822019cd059cb7e9b6786bed11552447eac593bc760` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-w10", "52_atlas_w10_weather_10m.pt")
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

Previous: [#51 Atlas W1 (1M + weather)](https://huggingface.co/paradoxailab/atlas-w1) · Next: [#53 Atlas W10r (10M + weather, regularised)](https://huggingface.co/paradoxailab/atlas-w10r) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
