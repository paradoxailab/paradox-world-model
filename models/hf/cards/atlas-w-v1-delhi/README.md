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

# Atlas-W v1 (Delhi)

**ParadoxAI Lab · Paradox World Model series #45** (model 42 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports') |
| Parameters | 14,043 per checkpoint; this file holds 2 checkpoints (B, C), the training stages recorded for this version |
| Status | reported |
| Trained | 2026-11-13 (Kaggle atlasw-v13-s320, 2026-11-13) |
| Released | 2026-11-17 |

## Result (as recorded)

see League v2.0 (Atlas-W day 2 results)

## What changed in this version

small model at v1.3 recipe

Checkpoints B, C are identical in this file.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `45_atlas-w_v1_delhi.pt` | 149,267 | `fc0522481c4cf26a06c5b5724434eacbeb3ac0391dea8aca7fdc7aa1be364724` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-w-v1-delhi", "45_atlas-w_v1_delhi.pt")
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

Previous: [#44 Atlas-W v1 (pre-training)](https://huggingface.co/PARADOXAIlabs/atlas-w-v1-pretrain) · Next: [#46 Atlas-Delhi I1 (operational comparison)](https://huggingface.co/PARADOXAIlabs/atlas-delhi-i1) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
