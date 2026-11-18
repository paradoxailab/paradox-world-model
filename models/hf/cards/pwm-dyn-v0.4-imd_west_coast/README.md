---
license: apache-2.0
library_name: pytorch
pipeline_tag: time-series-forecasting
tags:
- paradoxailab
- paradox-world-model
- pwm-dyn
- forecasting
- spatiotemporal
- rainfall
- india
---

# PWM-Dyn v0.4

**ParadoxAI Lab · Paradox World Model series #04** (model 4 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-Dyn |
| Task | next days of gridded rainfall |
| Data | IMD 0.25° gridded daily rainfall, Konkan / Western Ghats (2000–2024) |
| Parameters | 352,117 |
| Status | reported |
| Trained | 2026-11-01 (Kaggle notebook0387a11c3a (version 364310290), 2026-11-01) |
| Released | 2026-11-17 |

## Result (as recorded)

ParadoxBench-1 Track A test MAE 3.41 mm/day (3-seed ensemble; this file is seed 0)

## What changed in this version

ParadoxBench-1 tracks and split-conformal calibration; rainfall 80% coverage 54.7% -> 84.7% vs v0.3

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `04_pwm-dyn_v0.4_IMD_west_coast.pt` | 1,434,481 | `2b41a78eb94943d5230b01b820a48b224aa22c89c9d72d714750d1d8a82d7355` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-dyn-v0.4-imd_west_coast", "04_pwm-dyn_v0.4_IMD_west_coast.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [RESULTS.md](https://github.com/paradoxailab/paradox-world-model/blob/main/RESULTS.md)
* [v0.4-paradoxbench/README.md](https://github.com/paradoxailab/paradox-world-model/blob/main/v0.4-paradoxbench/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#03 PWM-Dyn v0.4](https://huggingface.co/paradoxailab/pwm-dyn-v0.4-imd_central_india) · Next: [#05 PWM-Dyn v0.4.1](https://huggingface.co/paradoxailab/pwm-dyn-v0.4.1-pems08) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
