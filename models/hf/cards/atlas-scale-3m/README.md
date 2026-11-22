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

# Atlas S2 (3M parameters)

**ParadoxAI Lab · Paradox World Model series #49** (model 46 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)') |
| Parameters | 2,950,392 |
| Status | not adopted |
| Trained | 2026-11-15 (Kaggle atlas-scale3m-s400, 2026-11-15) |
| Released | 2026-11-17 |

## Result (as recorded)

validation 9.139 (+0.38% vs 1M): not adopted

## What changed in this version

parameter ladder

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `49_atlas_scale_3m.pt` | 11,827,269 | `cf583e3dc05de3ef045498d57d19803ce937a452b51e361ddb9284407ae00530` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/atlas-scale-3m", "49_atlas_scale_3m.pt")
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

Previous: [#48 Atlas-P (physics decoder)](https://huggingface.co/PARADOXAIlabs/atlas-p) · Next: [#50 Atlas S3 (10M parameters)](https://huggingface.co/PARADOXAIlabs/atlas-scale-10m) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
