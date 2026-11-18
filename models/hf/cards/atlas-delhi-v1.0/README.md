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

# Atlas-Delhi v1.0

**ParadoxAI Lab · Paradox World Model series #37** (model 34 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports') |
| Parameters | 967,632 |
| Status | reported |
| Trained | 2026-11-12 (Kaggle atlas-delhi v2, 2026-11-12) |
| Released | 2026-11-17 |

## Result (as recorded)

test MAE 33.42 / 29.07 (trained / unseen stations, 3 seeds); loses to TimesFM 2.5 (30.83, +8.4%)

## What changed in this version

Atlas architecture (learned station state, geometry attention, latent steps, quantile decoder)

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `37_atlas_delhi_v1.0.pt` | 3,994,789 | `309caeb33af0739d8f5c6bcf245b2fbf59fe53048a28e43cbe37698c99f9b721` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-delhi-v1.0", "37_atlas_delhi_v1.0.pt")
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

Previous: [#36 PWM-F encoder (v2.1 run)](https://huggingface.co/paradoxailab/pwm-f-encoder-v2.1) · Next: [#38 Atlas-Delhi v1.1](https://huggingface.co/paradoxailab/atlas-delhi-v1.1) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
