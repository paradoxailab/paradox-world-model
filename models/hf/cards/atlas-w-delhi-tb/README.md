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
- india
---

# Atlas-W Delhi (T-B, real forecasts)

**ParadoxAI Lab · Paradox World Model series #54** (model 51 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports'); ECMWF day-before forecasts (Open-Meteo previous runs) |
| Parameters | 985,216 per checkpoint; this file holds 2 checkpoints (B, C), the training stages recorded for this version |
| Status | reported |
| Trained | 2026-11-16 (Kaggle atlas-tb-s320, 2026-11-16) |
| Released | 2026-11-17 |

## Result (as recorded)

Delhi winter 2024-25 MAE 28.19 vs 31.27 for the no-weather Atlas (-9.85%, p = 0.0009; stage B, 3 seeds)

## What changed in this version

weather gain holds with real forecasts

Checkpoints B, C are identical in this file.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `54_atlas-w_delhi_real_forecasts.pt` | 7,929,111 | `d7c915088665a2f2e11955b20b66a25889e1a7e647c0c34629a5c9786108a92a` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-w-delhi-tb", "54_atlas-w_delhi_real_forecasts.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict per checkpoint
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [atlas/README.md](https://github.com/paradoxailab/paradox-world-model/blob/main/atlas/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#53 Atlas W10r (10M + weather, regularised)](https://huggingface.co/PARADOXAIlabs/atlas-w10r) · Next: [#55 Atlas-5K v1](https://huggingface.co/PARADOXAIlabs/atlas-5k-v1) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
