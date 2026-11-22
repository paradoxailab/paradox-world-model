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

# PWM-F encoder (v2.1 run)

**ParadoxAI Lab · Paradox World Model series #36** (model 33 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-W |
| Task | 10M-parameter weather encoder pre-trained on all of India |
| Data | NOAA ISD, Indian stations |
| Parameters | 10,538,577 |
| Status | see branch |
| Trained | 2026-11-10 (Kaggle pwm-v21) |
| Released | 2026-11-17 |

## Result (as recorded)

see branch india-v2.0

## What changed in this version

second pre-training run

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `36_pwm-f_encoder_v2.1_10m.pt` | 42,204,635 | `06ddbb029b15936ca296bdf23b6f60d96f9e2b1ab7a245bec82de0b04f14f1b6` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("PARADOXAIlabs/pwm-f-encoder-v2.1", "36_pwm-f_encoder_v2.1_10m.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [branch india-v2.0 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/india-v2.0/README.md)
* [branch delhi-v1.1 / README.md](https://github.com/paradoxailab/paradox-world-model/blob/delhi-v1.1/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#35 PWM-F encoder (India v2.0)](https://huggingface.co/PARADOXAIlabs/pwm-f-encoder-v2.0) · Next: [#37 Atlas-Delhi v1.0](https://huggingface.co/PARADOXAIlabs/atlas-delhi-v1.0) · [All models](https://huggingface.co/PARADOXAIlabs/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
