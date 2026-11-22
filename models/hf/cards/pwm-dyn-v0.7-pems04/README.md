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

**ParadoxAI Lab · Paradox World Model series #14** (model 14 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-Dyn |
| Task | next 12 steps of traffic under sensor outages |
| Data | PEMS04 (Caltrans PeMS District 4, SF Bay Area; 307 sensors, Jan–Feb 2018) |
| Parameters | 334,628 |
| Status | reported |
| Trained | 2026-11-04 (Kaggle notebook8ffe55b5c8 (version 365414722), commit b0f6a08, 2026-11-04) |
| Released | 2026-11-17 |

## Result (as recorded)

ParadoxBench-1.2 test MAE clean 18.53, real outages (Track G) 21.05 (3-seed ensemble; this file is seed 200)

## What changed in this version

fallback base + outage training: real-outage error -11 to -22% vs v0.6 on five networks; clean +0.4-1.8%

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `14_pwm-dyn_v0.7_PEMS04.pt` | 1,374,337 | `a61c1911cd3063e6d40c041382e44e7e98adeafe0e14bbc15623f762e1a13be5` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-dyn-v0.7-pems04", "14_pwm-dyn_v0.7_PEMS04.pt")
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

Previous: [#13 PWM-Dyn v0.7](https://huggingface.co/PARADOXAIlabs/pwm-dyn-v0.7-pems08) · Next: [#15 PWM-Dyn v0.7](https://huggingface.co/PARADOXAIlabs/pwm-dyn-v0.7-pems03) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
