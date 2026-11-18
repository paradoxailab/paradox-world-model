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

# Atlas W1 (1M + weather)

**ParadoxAI Lab · Paradox World Model series #51** (model 48 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)'); ERA5 weather at each station (Open-Meteo archive, Copernicus C3S) |
| Parameters | 985,216 |
| Status | adopted |
| Trained | 2026-11-16 (Kaggle atlas-w1-s400, 2026-11-16) |
| Released | 2026-11-17 |

## Result (as recorded)

validation 8.684 (-4.61%): adopted; all-India test 19.86 / 19.92 with ERA5 weather (upper bound) vs TimesFM 2.5 22.35 / 21.93

## What changed in this version

weather forcing

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `51_atlas_w1_weather.pt` | 4,020,709 | `5502f8073ba770617d49fdbb5a572642572a01ea5ad31191d5f305eff9732167` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-w1", "51_atlas_w1_weather.pt")
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

Previous: [#50 Atlas S3 (10M parameters)](https://huggingface.co/paradoxailab/atlas-scale-10m) · Next: [#52 Atlas W10 (10M + weather)](https://huggingface.co/paradoxailab/atlas-w10) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
