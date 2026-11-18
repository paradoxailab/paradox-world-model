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

# PWM-Dyn v0.7

**ParadoxAI Lab · Paradox World Model series #15** (model 15 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-Dyn |
| Task | next 12 steps of traffic under sensor outages |
| Data | PEMS03 (Caltrans PeMS District 3; 358 sensors) |
| Parameters | 341,156 |
| Status | reported |
| Trained | 2026-11-04 (Kaggle notebook8ffe55b5c8 (version 365414722), commit b0f6a08, 2026-11-04) |
| Released | 2026-11-17 |

## Result (as recorded)

ParadoxBench-1.2 test MAE clean 14.60, real outages (Track G) 18.39 (3-seed ensemble; this file is seed 200)

## What changed in this version

fallback base + outage training: real-outage error -11 to -22% vs v0.6 on five networks; clean +0.4-1.8%

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `15_pwm-dyn_v0.7_PEMS03.pt` | 1,399,041 | `154e52d707459ed42e2c5d4d84565a3210cf20be181e17df47c3922392a5c76c` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-dyn-v0.7-pems03", "15_pwm-dyn_v0.7_PEMS03.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [RESULTS.md](https://github.com/paradoxailab/paradox-world-model/blob/main/RESULTS.md)
* [v0.7-realworld/README.md](https://github.com/paradoxailab/paradox-world-model/blob/main/v0.7-realworld/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#14 PWM-Dyn v0.7](https://huggingface.co/paradoxailab/pwm-dyn-v0.7-pems04) · Next: [#16 PWM-Dyn v0.7](https://huggingface.co/paradoxailab/pwm-dyn-v0.7-pems07) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
