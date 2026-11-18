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

# Atlas S3 (10M parameters)

**ParadoxAI Lab · Paradox World Model series #50** (model 47 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)') |
| Parameters | 9,949,792 |
| Status | not adopted |
| Trained | 2026-11-15 (Kaggle atlas-scale10m-s400, 2026-11-15) |
| Released | 2026-11-17 |

## Result (as recorded)

validation 9.222 (+1.30% vs 1M): not adopted

## What changed in this version

parameter ladder: more parameters did not help

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `50_atlas_scale_10m.pt` | 39,825,269 | `56a9696cd915f5c408d5770f73dbbf48d673c785c641b1c5d6e1be3d992642c5` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-scale-10m", "50_atlas_scale_10m.pt")
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

Previous: [#49 Atlas S2 (3M parameters)](https://huggingface.co/paradoxailab/atlas-scale-3m) · Next: [#51 Atlas W1 (1M + weather)](https://huggingface.co/paradoxailab/atlas-w1) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
