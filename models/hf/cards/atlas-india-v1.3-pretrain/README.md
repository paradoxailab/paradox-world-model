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

# Atlas v1.3 (pre-training on 13 networks)

**ParadoxAI Lab · Paradox World Model series #41** (model 38 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)') (13 networks, Delhi left out) |
| Parameters | 967,632 |
| Status | stage |
| Trained | 2026-11-13 (Kaggle atlas-v13-s320, 2026-11-13) |
| Released | 2026-11-17 |

## Result (as recorded)

pooled validation 8.507 on the 13 networks

## What changed in this version

pre-training stage of v1.3

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `41_atlas_india_v1.3_pretrain.pt` | 3,903,381 | `2efe2059c8736d83a350a55b554beacbf2506d35d14ebb8bfa8ca38ec42804e1` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-india-v1.3-pretrain", "41_atlas_india_v1.3_pretrain.pt")
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

Previous: [#40 Atlas-India v1.0](https://huggingface.co/paradoxailab/atlas-india-v1.0) · Next: [#42 Atlas-Delhi v1.3](https://huggingface.co/paradoxailab/atlas-delhi-v1.3) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
