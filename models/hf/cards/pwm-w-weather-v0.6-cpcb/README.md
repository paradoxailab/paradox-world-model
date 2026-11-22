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
- rainfall
- weather-forecasting
- india
---

# PWM-W Weather v0.6

**ParadoxAI Lab · Paradox World Model series #26** (model 26 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind |
| Data | CPCB/DPCC Delhi station meteorology (25 stations); WMO synoptic stations in India (NOAA ISD) (extra training) |
| Parameters | 932,348 |
| Status | reported |
| Trained | 2026-11-08 (Kaggle pwm-weather-v06-cpcb) |
| Released | 2026-11-17 |

## Result (as recorded)

validation 0.4735 vs 0.4922 (about 5 sigma better); still trails Chronos-2 / TimesFM 3.0 by 4-7% on test

## What changed in this version

trains on the larger WMO network too

## Also stands for

* #27 PWM-W Weather v0.7: same weights as this file, so it is not stored twice.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `26_pwm-w_weather_v0.6_cpcb.pt` | 4,127,029 | `779d80e286802df695bcfecfa1667d6a642209a27ab5a5a1a063e034a647ffd0` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-w-weather-v0.6-cpcb", "26_pwm-w_weather_v0.6_cpcb.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch delhi-v0.6 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v0.6/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#25 PWM-W Weather v0.5](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.5-metar) · Next: [#28 PWM-W Weather v0.8](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.8-cpcb) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
