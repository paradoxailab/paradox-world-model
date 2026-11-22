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

# Atlas-India v1.0

**ParadoxAI Lab · Paradox World Model series #40** (model 37 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)') |
| Parameters | 967,632 |
| Status | reported |
| Trained | 2026-11-13 (Kaggle atlas-india-s400, 2026-11-13) |
| Released | 2026-11-17 |

## Result (as recorded)

all-India test MAE 20.99 / 20.86 vs TimesFM 2.5 22.35 / 21.93

## What changed in this version

one model for all of India (263 stations); beats TimesFM 2.5

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `40_atlas_india_v1.0.pt` | 3,995,365 | `d7f836dfd15d0778a291cb4707840873daf74fe4eafd0964de954fd4464661e7` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-india-v1.0", "40_atlas_india_v1.0.pt")
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

Previous: [#39 Atlas-Delhi v1.2](https://huggingface.co/PARADOXAIlabs/atlas-delhi-v1.2) · Next: [#41 Atlas v1.3 (pre-training on 13 networks)](https://huggingface.co/PARADOXAIlabs/atlas-india-v1.3-pretrain) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
