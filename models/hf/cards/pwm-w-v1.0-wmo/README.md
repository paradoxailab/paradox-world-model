---
license: apache-2.0
library_name: pytorch
pipeline_tag: time-series-forecasting
tags:
- paradoxailab
- paradox-world-model
- pwm-w
- forecasting
- spatiotemporal
- weather-forecasting
- india
---

# PWM-W v1.0

**ParadoxAI Lab · Paradox World Model series #33** (model 31 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind |
| Data | WMO synoptic stations in India (NOAA ISD) |
| Parameters | 1,260,997 |
| Status | not recorded |
| Trained | 2026-11-09 (Kaggle pwm-v10) |
| Released | 2026-11-17 |

## Result (as recorded)

no result recorded in the delhi-v1.0 README

## What changed in this version

self-correction and a two-architecture ensemble (adopted only if >2 sigma better)

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `33_pwm-w_v1.0_wmo.pt` | 5,173,083 | `f9ac347d981a2d0658d5fcf923b527cd76b6a65267ec3d591e4ac2bf2b070b56` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-w-v1.0-wmo", "33_pwm-w_v1.0_wmo.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch delhi-v1.0 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v1.0/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#32 PWM-W v1.0](https://huggingface.co/paradoxailab/pwm-w-v1.0-metar) · Next: [#35 PWM-F encoder (India v2.0)](https://huggingface.co/paradoxailab/pwm-f-encoder-v2.0) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
