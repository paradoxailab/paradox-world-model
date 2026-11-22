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

# PWM-W Weather v0.4

**ParadoxAI Lab · Paradox World Model series #24** (model 24 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind |
| Data | WMO synoptic stations in India (NOAA ISD) |
| Parameters | 932,348 |
| Status | reported |
| Trained | 2026-11-07 (Kaggle pwm-weather-v04-gpu) |
| Released | 2026-11-17 |

## Result (as recorded)

WMO league: see delhi-v0.4 README

## What changed in this version

learned-correction hybrid and the issued-before-start rule; METAR hybrid beats ECMWF AIFS (-4.4% temp)

## Note on hybrid use

This version was used in a hybrid setup that combines its output with forecasts from outside models (see the record). Those outside models are **not** included here: this file holds only ParadoxAI Lab's own trained weights.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `24_pwm-w_weather_v0.4_wmo.pt` | 3,848,989 | `f3729e60839bd38a897be609104931ee199de7237e87deb8aee50508e16c0dc6` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-w-weather-v0.4-wmo", "24_pwm-w_weather_v0.4_wmo.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch delhi-v0.4 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v0.4/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#23 PWM-W Weather v0.4](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.4-cpcb) · Next: [#25 PWM-W Weather v0.5](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.5-metar) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
