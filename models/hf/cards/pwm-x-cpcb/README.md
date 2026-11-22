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

# PWM-X (v0.9)

**ParadoxAI Lab · Paradox World Model series #29** (model 28 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind |
| Data | CPCB/DPCC Delhi station meteorology (25 stations); WMO synoptic stations in India (NOAA ISD); METAR reports from six Indian airports incl. Delhi Palam |
| Parameters | 1,260,997 |
| Status | reported |
| Trained | 2026-11-09 (Kaggle pwm-x-cpcb) |
| Released | 2026-11-17 |

## Result (as recorded)

data-threshold study: about 24 months of local history to stop losing to TimesFM/Chronos, about 48 to beat them

## What changed in this version

cross-network model; the data threshold measured

## Also stands for

* #31 PWM-W v1.0: same weights as this file, so it is not stored twice.
* #34 PWM-W India v2.0: same weights as this file, so it is not stored twice.

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `29_pwm-x_v0.9_cpcb.pt` | 5,589,589 | `06708fe9c526bc40622eb5c49cc1cc5ef23e4a461af4d4aa6ddfe00486ad20b1` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-x-cpcb", "29_pwm-x_v0.9_cpcb.pt")
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

Previous: [#28 PWM-W Weather v0.8](https://huggingface.co/PARADOXAIlabs/pwm-w-weather-v0.8-cpcb) · Next: [#30 PWM-W v0.9 live](https://huggingface.co/PARADOXAIlabs/pwm-w-live-v0.9) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
