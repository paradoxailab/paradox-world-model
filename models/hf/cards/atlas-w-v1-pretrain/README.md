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

# Atlas-W v1 (pre-training)

**ParadoxAI Lab · Paradox World Model series #44** (model 41 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)') (13 networks) |
| Parameters | 14,043 |
| Status | stage |
| Trained | 2026-11-13 (Kaggle atlasw-v13-s320, 2026-11-13) |
| Released | 2026-11-17 |

## Result (as recorded)

pooled validation 8.83-8.86

## What changed in this version

Atlas-W trained the v1.3 way

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `44_atlas-w_v1_pretrain.pt` | 86,701 | `55d7be51fef1f7fe496363664b44c5e823812ff2e93ac3cd9e45d82635b57fd9` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-w-v1-pretrain", "44_atlas-w_v1_pretrain.pt")
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

Previous: [#43 Atlas-W v0 (air core)](https://huggingface.co/PARADOXAIlabs/atlas-w-v0) · Next: [#45 Atlas-W v1 (Delhi)](https://huggingface.co/PARADOXAIlabs/atlas-w-v1-delhi) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
