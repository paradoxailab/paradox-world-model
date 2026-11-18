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

# Atlas-Delhi I1 (operational comparison)

**ParadoxAI Lab · Paradox World Model series #46** (model 43 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports'), winter 2024-25 |
| Parameters | 967,632 per checkpoint; this file holds 2 checkpoints (B, C), the training stages recorded for this version |
| Status | reported |
| Trained | 2026-11-15 (Kaggle atlas-i1-s320, 2026-11-15) |
| Released | 2026-11-17 |

## Result (as recorded)

Delhi winter 2024-25 MAE 31.27 (stage C, 3 seeds); IITM WRF-Chem 58.75 / IMD SILAM 71.68 published (by number)

## What changed in this version

evaluated against India's operational forecasts

Checkpoints B, C are different training stages; the record says which stage each result uses.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `46_atlas_delhi_i1.pt` | 7,781,419 | `fdbe1ecc6972646ea084813823d502347fcbd57dd067555d31bc5b8adcec389c` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-delhi-i1", "46_atlas_delhi_i1.pt")
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

Previous: [#45 Atlas-W v1 (Delhi)](https://huggingface.co/paradoxailab/atlas-w-v1-delhi) · Next: [#47 Atlas v1.4n (neighbours only)](https://huggingface.co/paradoxailab/atlas-v1.4n) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
