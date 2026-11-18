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
- india
---

# PWM-W v0.9 live

**ParadoxAI Lab · Paradox World Model series #30** (model 29 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | real-time 24 h forecasts for Indian stations |
| Data | CPCB/DPCC Delhi station meteorology (25 stations); WMO synoptic stations in India (NOAA ISD); METAR reports from six Indian airports incl. Delhi Palam |
| Parameters | 985,853 |
| Status | see paper |
| Trained | 2026-11-09 (Kaggle pwm-v09-live) |
| Released | 2026-11-17 |

## Result (as recorded)

live track (see paper-weather v0.9)

## What changed in this version

first real-time Indian forecasts

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `30_pwm-w_live_v0.9.pt` | 3,995,965 | `f6bf6c9598ab3ca31d0f24da3ebd582919e5c3e0c9639e34e49d8651a8e59956` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-w-live-v0.9", "30_pwm-w_live_v0.9.pt")
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

Previous: [#29 PWM-X (v0.9)](https://huggingface.co/paradoxailab/pwm-x-cpcb) · Next: [#32 PWM-W v1.0](https://huggingface.co/paradoxailab/pwm-w-v1.0-metar) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
