---
license: apache-2.0
library_name: pytorch
pipeline_tag: time-series-forecasting
tags:
- paradoxailab
- paradox-world-model
- pwm-dyn
- forecasting
- spatiotemporal
- traffic-forecasting
---

# PWM-Dyn v0.4

**ParadoxAI Lab · Paradox World Model series #01** (model 1 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-Dyn |
| Task | next 12 steps of traffic flow |
| Data | PEMS08 (Caltrans PeMS District 8, San Bernardino; 170 sensors, Jul–Aug 2016) |
| Parameters | 318,148 |
| Status | reported |
| Trained | 2026-11-01 (Kaggle notebook0387a11c3a (version 364310290), 2026-11-01) |
| Released | 2026-11-17 |

## Result (as recorded)

ParadoxBench-1 Track A test MAE 14.53 (3-seed ensemble; this file is seed 0)

## What changed in this version

ParadoxBench-1 tracks and split-conformal calibration; rainfall 80% coverage 54.7% -> 84.7% vs v0.3

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `01_pwm-dyn_v0.4_PEMS08.pt` | 1,299,673 | `0b3cbb5a172a5bb0caef183e6e2760d3518d5ee7d9a28d834bfb6c03cbe12f18` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-dyn-v0.4-pems08", "01_pwm-dyn_v0.4_PEMS08.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [RESULTS.md](https://github.com/paradoxailab/paradox-world-model/blob/main/RESULTS.md)
* [v0.4-paradoxbench/README.md](https://github.com/paradoxailab/paradox-world-model/blob/main/v0.4-paradoxbench/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Next: [#02 PWM-Dyn v0.4](https://huggingface.co/PARADOXAIlabs/pwm-dyn-v0.4-pems04) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
