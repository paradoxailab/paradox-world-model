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

# PWM-W Weather v0.5

**ParadoxAI Lab · Paradox World Model series #25** (model 25 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind |
| Data | METAR reports from six Indian airports incl. Delhi Palam |
| Parameters | 932,348 |
| Status | see branch |
| Trained | 2026-11-07 (Kaggle pwm-weather-v05-metar) |
| Released | 2026-11-17 |

## Result (as recorded)

see branch delhi-v0.5 README

## What changed in this version

more global-model predictors for the correction (cloud, radiation, dew point, pressure, wind direction)

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `25_pwm-w_weather_v0.5_metar.pt` | 3,945,293 | `49e959062c20d6271e4415324392169ffa6880978b0b4c793881119cca9fe9ca` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-w-weather-v0.5-metar", "25_pwm-w_weather_v0.5_metar.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch delhi-v0.5 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v0.5/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#24 PWM-W Weather v0.4](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.4-wmo) · Next: [#26 PWM-W Weather v0.6](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.6-cpcb) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
