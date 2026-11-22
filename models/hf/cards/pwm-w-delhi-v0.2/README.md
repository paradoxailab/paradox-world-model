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
- air-quality
- weather-forecasting
- india
---

# PWM-W Delhi v0.2

**ParadoxAI Lab · Paradox World Model series #20** (model 20 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of PM2.5 (hybrid: corrects Chronos-2 / TimesFM 2.5 with the station graph) |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports'); Open-Meteo day-before weather forecasts |
| Parameters | 1,060,076 |
| Status | see branch |
| Trained | 2026-11-06 (Kaggle pwm-delhi-v02-pm25) |
| Released | 2026-11-17 |

## Result (as recorded)

result in branch delhi-v0.2 README (not restated here)

## What changed in this version

long context (72 h + 14 daily means), day-ahead weather, hybrid on top of foundation models

## Note on hybrid use

This version was used in a hybrid setup that combines its output with forecasts from outside models (see the record). Those outside models are **not** included here: this file holds only ParadoxAI Lab's own trained weights.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `20_pwm-w_delhi_v0.2_pm25_hybrid.pt` | 4,315,138 | `704cda79819b85a029d5d6d2bc4592f58b8082bba02e98208e83372c2ff62f56` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-w-delhi-v0.2", "20_pwm-w_delhi_v0.2_pm25_hybrid.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch delhi-v0.2 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v0.2/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#19 PWM-W Delhi v0.1](https://huggingface.co/PARADOXAIlabs/pwm-w-delhi-v0.1) · Next: [#21 PWM-W Weather v0.3 (league run)](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.3-cpcb) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
