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

# Atlas-Delhi v1.1

**ParadoxAI Lab · Paradox World Model series #38** (model 35 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports'), all history since 2018 |
| Parameters | 967,632 per checkpoint; this file holds 2 checkpoints (B, C), the training stages recorded for this version |
| Status | adopted |
| Trained | 2026-11-13 (Kaggle atlas-long-s300, 2026-11-13) |
| Released | 2026-11-17 |

## Result (as recorded)

validation 20.807 vs 22.127 for the 16-month model: adopted

## What changed in this version

all of Delhi's history (19,082 windows)

Checkpoints B, C are different training stages; the record says which stage each result uses.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `38_atlas_delhi_v1.1.pt` | 7,783,583 | `15085632cf0b356f5e5fe44e6e269ad98a0f859ba16fc25b0c0a4603217e3867` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-delhi-v1.1", "38_atlas_delhi_v1.1.pt")
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

Previous: [#37 Atlas-Delhi v1.0](https://huggingface.co/PARADOXAIlabs/atlas-delhi-v1.0) · Next: [#39 Atlas-Delhi v1.2](https://huggingface.co/PARADOXAIlabs/atlas-delhi-v1.2) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
