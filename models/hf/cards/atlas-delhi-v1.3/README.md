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
- rainfall
- air-quality
- india
---

# Atlas-Delhi v1.3

**ParadoxAI Lab · Paradox World Model series #42** (model 39 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports'); CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)') (pre-training) |
| Parameters | 967,632 per checkpoint; this file holds 2 checkpoints (B, C), the training stages recorded for this version |
| Status | adopted |
| Trained | 2026-11-13 (Kaggle atlas-v13-s320, 2026-11-13) |
| Released | 2026-11-17 |

## Result (as recorded)

adopted; League v2.0 MAE 28.91 / 25.56, beats Moirai 2.0 (30.50) by 5.2%

## What changed in this version

pre-trained on the rest of India, then Delhi

Checkpoints B, C are identical in this file.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `42_atlas_delhi_v1.3.pt` | 7,830,751 | `ad74f793f20e274d1469bf432af77c1ad6336c21197b6a1829a484c1af582dca` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-delhi-v1.3", "42_atlas_delhi_v1.3.pt")
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

Previous: [#41 Atlas v1.3 (pre-training on 13 networks)](https://huggingface.co/paradoxailab/atlas-india-v1.3-pretrain) · Next: [#43 Atlas-W v0 (air core)](https://huggingface.co/paradoxailab/atlas-w-v0) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
