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

# PWM-W v1.0

**ParadoxAI Lab · Paradox World Model series #32** (model 30 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of temperature, humidity, wind |
| Data | METAR reports from six Indian airports incl. Delhi Palam |
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
| `32_pwm-w_v1.0_metar.pt` | 5,184,207 | `627d38dbfe4ef491782c622092a060fccc0d5be7f69a695d8015eeb60319c9f5` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-w-v1.0-metar", "32_pwm-w_v1.0_metar.pt")
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

Previous: [#30 PWM-W v0.9 live](https://huggingface.co/PARADOXAIlabs/pwm-w-live-v0.9) · Next: [#33 PWM-W v1.0](https://huggingface.co/PARADOXAIlabs/pwm-w-v1.0-wmo) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
