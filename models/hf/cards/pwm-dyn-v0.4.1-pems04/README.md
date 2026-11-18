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

# PWM-Dyn v0.4.1

**ParadoxAI Lab · Paradox World Model series #06** (model 6 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-Dyn |
| Task | next 12 steps of traffic flow |
| Data | PEMS04 (Caltrans PeMS District 4, SF Bay Area; 307 sensors, Jan–Feb 2018) |
| Parameters | 335,684 |
| Status | reported |
| Trained | 2026-11-01 (Kaggle notebookab27dd6f3e (version 364348754), 2026-11-01) |
| Released | 2026-11-17 |

## Result (as recorded)

ParadoxBench-1 Track A test MAE 19.02 (3-seed ensemble; this file is seed 0)

## What changed in this version

training recipe chosen on PEMS08 validation (100 epochs); Track B PEMS08 14.38 -> 14.15

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `06_pwm-dyn_v0.4.1_PEMS04.pt` | 1,369,279 | `5213ec3869a6548e20516474fd2b6b59b60f4024e33c27390c1e207b16a67586` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-dyn-v0.4.1-pems04", "06_pwm-dyn_v0.4.1_PEMS04.pt")
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

Previous: [#05 PWM-Dyn v0.4.1](https://huggingface.co/paradoxailab/pwm-dyn-v0.4.1-pems08) · Next: [#07 PWM-Dyn v0.6](https://huggingface.co/paradoxailab/pwm-dyn-v0.6-pems08) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
