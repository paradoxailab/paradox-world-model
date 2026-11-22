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

# Atlas-W v0 (air core)

**ParadoxAI Lab · Paradox World Model series #43** (model 40 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports') |
| Parameters | 14,043 |
| Status | reported |
| Trained | 2026-11-13 (Kaggle atlasw-v0, 2026-11-13) |
| Released | 2026-11-17 |

## Result (as recorded)

14,043 parameters; 6-13% lower error than Atlas at every amount of data

## What changed in this version

information-efficient output-first design

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `43_atlas-w_v0_14k.pt` | 144,107 | `28c313770f06d349b633b12c0ee5cfc9c33d2b7ec5f614e50a774f56d33bf63b` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-w-v0", "43_atlas-w_v0_14k.pt")
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

Previous: [#42 Atlas-Delhi v1.3](https://huggingface.co/PARADOXAIlabs/atlas-delhi-v1.3) · Next: [#44 Atlas-W v1 (pre-training)](https://huggingface.co/PARADOXAIlabs/atlas-w-v1-pretrain) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
