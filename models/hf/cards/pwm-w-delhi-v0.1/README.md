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

# PWM-W Delhi v0.1

**ParadoxAI Lab · Paradox World Model series #19** (model 19 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | next 24 h of PM2.5, PM10, NO2, ozone at Delhi stations |
| Data | CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports') |
| Parameters | 884,204 |
| Status | reported |
| Trained | 2026-11-06 (Kaggle notebookce65e86211, 2026-11-05/06) |
| Released | 2026-11-17 |

## Result (as recorded)

PM2.5 test MAE 32.63 (3 seeds); beats every simple baseline by 19-29%; loses to TimesFM 3.0 (29.95) and level with Chronos

## What changed in this version

first real-data world model (Delhi air)

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `19_pwm-w_delhi_v0.1_pm25.pt` | 3,614,547 | `2191c741d7895eefa6b106e21daba3f4331101a629c419c1f937e5c7e6c37d4c` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-w-delhi-v0.1", "19_pwm-w_delhi_v0.1_pm25.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch delhi-v0.1 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v0.1/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#18 PWM-Dyn v0.7](https://huggingface.co/paradoxailab/pwm-dyn-v0.7-pems-bay) · Next: [#20 PWM-W Delhi v0.2](https://huggingface.co/paradoxailab/pwm-w-delhi-v0.2) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
