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

# PWM-F encoder (India v2.0)

**ParadoxAI Lab · Paradox World Model series #35** (model 32 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | 10M-parameter weather encoder pre-trained on all of India |
| Data | NOAA ISD, 187 Indian stations, 2015-01 to 2024-11 |
| Parameters | 10,538,577 |
| Status | not adopted |
| Trained | 2026-11-09 (Kaggle pwm-v20, 2026-11-09) |
| Released | 2026-11-17 |

## Result (as recorded)

held-out MAE 0.862 °C, 4.80 %RH, 0.578 m/s; not adopted for CPCB (validation 0.4620 vs 0.4597)

## What changed in this version

pre-training at 10M

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `35_pwm-f_encoder_v2.0_10m.pt` | 42,332,123 | `c5046eb48820d1da1a5f29e1f42b17b0f5a4145f19ab07ccd7de41d30a581431` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-f-encoder-v2.0", "35_pwm-f_encoder_v2.0_10m.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch india-v2.0 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/india-v2.0/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#33 PWM-W v1.0](https://huggingface.co/paradoxailab/pwm-w-v1.0-wmo) · Next: [#36 PWM-F encoder (v2.1 run)](https://huggingface.co/paradoxailab/pwm-f-encoder-v2.1) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
