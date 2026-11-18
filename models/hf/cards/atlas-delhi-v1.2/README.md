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

# Atlas-Delhi v1.2

**ParadoxAI Lab · Paradox World Model series #39** (model 36 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | Atlas |
| Task | next 24 h of PM2.5 at stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports'), all history since 2018 |
| Parameters | 967,632 |
| Status | adopted |
| Trained | 2026-11-13 (Kaggle atlas-long2-a, 2026-11-13) |
| Released | 2026-11-17 |

## Result (as recorded)

adopted on validation; not better than v1.1 on test (recorded honestly)

## What changed in this version

whole schedule, more seeds

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `39_atlas_delhi_v1.2.pt` | 3,901,541 | `02bad59d9ade989b4b9157002648228ebe297fa1f903881e4fc47e588188837c` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/atlas-delhi-v1.2", "39_atlas_delhi_v1.2.pt")
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

Previous: [#38 Atlas-Delhi v1.1](https://huggingface.co/paradoxailab/atlas-delhi-v1.1) · Next: [#40 Atlas-India v1.0](https://huggingface.co/paradoxailab/atlas-india-v1.0) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
