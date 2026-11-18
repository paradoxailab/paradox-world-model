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
- traffic-forecasting
---

# PWM-Dyn v0.6

**ParadoxAI Lab · Paradox World Model series #11** (model 11 of 56 released; series numbers 01–59).

| | |
|---|---|
| Family | PWM-Dyn |
| Task | next 12 steps of traffic |
| Data | METR-LA (Los Angeles highway loop detectors; 207 sensors) |
| Parameters | 321,636 |
| Status | reported |
| Trained | 2026-11-03 (Kaggle notebookd0ba070ac4 (version 365009705), 2026-11-02/03) |
| Released | 2026-11-17 |

## Result (as recorded)

ParadoxBench-1.1 Track A test MAE 2.92 (3-seed ensemble, fresh seeds 100-102; this file is seed 100)

## What changed in this version

climatology input removed (the v0.4 loss); beats v0.3 on PEMS08/04; best on PEMS04, PEMS07, METR-LA, PEMS-BAY vs re-run STID/Graph WaveNet/STAEformer

## Files

| File | Bytes | SHA-256 |
|---|---|---|
| `11_pwm-dyn_v0.6_METR-LA.pt` | 1,314,354 | `5c65bb2986ef4e5e8da4d492bb2ed629f6d21d283e971c41e94f4a3997a9fe4f` |

## Load

```python
import torch
from huggingface_hub import hf_hub_download
path = hf_hub_download("paradoxailab/pwm-dyn-v0.6-metr-la", "11_pwm-dyn_v0.6_METR-LA.pt")
ck = torch.load(path, map_location="cpu", weights_only=False)
print(ck["meta"])            # name, task, data, parameters, result, source run
weights = ck["weights"]       # PyTorch state dict
results = ck["results"]       # every recorded result, the record text and the run logs
```

The architecture code for this version is in the [GitHub repository](https://github.com/paradoxailab/paradox-world-model) (see the record below); the configuration it was trained with is stored in the file (`ck['cfg']`).

## Record

Rules, predictions and full results for this version:

* [RESULTS.md](https://github.com/paradoxailab/paradox-world-model/blob/main/RESULTS.md)
* [v0.6-conference/README.md](https://github.com/paradoxailab/paradox-world-model/blob/main/v0.6-conference/README.md)
* [Series index (all models)](https://github.com/paradoxailab/paradox-world-model/blob/main/models/series/README.md)

Training data are not included; their sources and terms are in [DATA_SOURCES.md](https://github.com/paradoxailab/paradox-world-model/blob/main/DATA_SOURCES.md).

## Series

Previous: [#10 PWM-Dyn v0.6](https://huggingface.co/paradoxailab/pwm-dyn-v0.6-pems07) · Next: [#12 PWM-Dyn v0.6](https://huggingface.co/paradoxailab/pwm-dyn-v0.6-pems-bay) · [All models](https://huggingface.co/paradoxailab/paradox-world-model-series)

## Licence and citation

Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). Cite with [CITATION.cff](https://github.com/paradoxailab/paradox-world-model/blob/main/CITATION.cff).
