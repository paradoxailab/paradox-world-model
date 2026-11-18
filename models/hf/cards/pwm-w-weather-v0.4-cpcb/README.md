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

**ParadoxAI Lab · Paradox World Model series #23** (model 23 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind |
| Data | CPCB/DPCC Delhi station meteorology (25 stations) |
| Parameters | 2,385,504 |
| Status | reported |
| Trained | 2026-11-07 (Kaggle pwm-weather-v04-gpu) |
| Released | 2026-11-17 |

## Result (as recorded)

CPCB: pure model beats IFS 0.25, IFS 9 km and GFS on all three variables; loses to Chronos-2 by 6.0-8.3%

## What changed in this version

learned-correction hybrid and the issued-before-start rule; METAR hybrid beats ECMWF AIFS (-4.4% temp)

## Note on hybrid use

This version was used in a hybrid setup that combines its output with forecasts from outside models (see the record). Those outside models are **not** included here: this file holds only ParadoxAI Lab's own trained weights.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `23_pwm-w_weather_v0.4_cpcb.pt` | 9,755,643 | `3c05a7538662e4af7dd89400d2e8750420a35e041ab80d50f1c14f5dc2ac95f0` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-w-weather-v0.4-cpcb", "23_pwm-w_weather_v0.4_cpcb.pt")
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

Previous: [#22 PWM-W Weather v0.3 (league run)](https://huggingface.co/paradoxailab/pwm-w-weather-v0.3-wmo) · Next: [#24 PWM-W Weather v0.4](https://huggingface.co/paradoxailab/pwm-w-weather-v0.4-wmo) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
