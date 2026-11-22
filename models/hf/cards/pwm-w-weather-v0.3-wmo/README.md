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

# PWM-W Weather v0.3 (league run)

**ParadoxAI Lab · Paradox World Model series #22** (model 22 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind at stations |
| Data | WMO synoptic stations in India (NOAA ISD) |
| Parameters | 932,348 |
| Status | see paper |
| Trained | 2026-11-07 (Kaggle pwm-weather-league-gpu) |
| Released | 2026-11-17 |

## Result (as recorded)

weather league against the global AI weather models; results in paper-weather (v0.3 section)

## What changed in this version

from air quality to weather; station-only world model vs global models

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `22_pwm-w_weather_v0.3_wmo.pt` | 3,788,253 | `76cce210f71e44d8ebcf20924664edc13b509d8d361a81ff3422c65403861f14` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-w-weather-v0.3-wmo", "22_pwm-w_weather_v0.3_wmo.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch delhi-v0.3 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v0.3/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#21 PWM-W Weather v0.3 (league run)](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.3-cpcb) · Next: [#23 PWM-W Weather v0.4](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.4-cpcb) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
