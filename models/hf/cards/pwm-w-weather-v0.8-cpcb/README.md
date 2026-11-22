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

# PWM-W Weather v0.8

**ParadoxAI Lab · Paradox World Model series #28** (model 27 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind |
| Data | CPCB/DPCC Delhi station meteorology (25 stations); WMO synoptic stations in India (NOAA ISD) |
| Parameters | 985,853 |
| Status | reported |
| Trained | 2026-11-08 (Kaggle pwm-weather-v08-cpcb) |
| Released | 2026-11-17 |

## Result (as recorded)

validation 0.4678 (6.4 sigma better than P0); three losses to the foundation models became ties; wind still trails

## What changed in this version

14-day encoder + weight averaging

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `28_pwm-w_weather_v0.8_cpcb.pt` | 4,172,677 | `6402a3fe50e2741468b27f5ab25b0bb82cdf5f4cdfc0e980c816be01e9ae1363` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-w-weather-v0.8-cpcb", "28_pwm-w_weather_v0.8_cpcb.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch delhi-v0.8 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v0.8/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#26 PWM-W Weather v0.6](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.6-cpcb) · Next: [#29 PWM-X (v0.9)](https://huggingface.co/PARADOXAIlabs/pwm-x-cpcb) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
