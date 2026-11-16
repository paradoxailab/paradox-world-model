# Atlas weights

ParadoxAI Lab, released 2026-11-17. Copied byte-for-byte from the Kaggle training runs' outputs; every file's SHA-256
is in `SHA256SUMS` (check with `sha256sum -c SHA256SUMS`). Results, rules and limits: `../MODELS.md` and `../README.md`.

| File | Model | Parameters | Bytes | Weights key | Source run |
|---|---|---|---|---|---|
| `w5k_atlas_1m_h24_s600.pt` | Atlas-5K v1, WEATHER-5K 24 h (the scored WB1 entry) | 968,672 | 3,889,349 | `sd` | atlas-w5k-atlas1m-h24 |
| `w5k_atlas_1m_h24_v2a_s600.pt` | Atlas-5K v2a (150,000 steps; validation only, not yet tested) | 968,672 | 3,889,733 | `sd` | atlas-w5k-v2a |
| `atlas_w1_s400.pt` | Atlas W1, all-India PM2.5 + weather, seed 400 | 985,216 | 7,906,371 | `E` | atlas-w1-s400 |
| `atlas_w1_s401.pt` | Atlas W1, seed 401 | 985,216 | 7,906,371 | `E` | atlas-w1-s401 |
| `atlas_w1_s402.pt` | Atlas W1, seed 402 | 985,216 | 7,906,371 | `E` | atlas-w1-s402 |

Atlas-5K files hold the early-stopped model as `{"sd", "cfg"}`. W1 files hold `{"cfg", "E", "F", "networks"}`: `E` is
the early-stopped model (the one every reported W1 number uses, as a three-seed ensemble), `F` the weights at the last
training step.

```python
import torch
from atlas.model import Atlas                      # run from the atlas/ folder

ck = torch.load("models/w5k_atlas_1m_h24_s600.pt", map_location="cpu")
model = Atlas(**ck["cfg"]); model.load_state_dict(ck["sd"]); model.eval()

ck = torch.load("models/atlas_w1_s400.pt", map_location="cpu")
w1 = Atlas(**ck["cfg"]); w1.load_state_dict(ck["E"]); w1.eval()
```

All five were loaded this way after download (every key matched). Inputs must be prepared as in training:
`delhi/run_atlas_5k.py` (benchmark MEAN/STD scaling, `neighbours()`, `geometry()`, static and time features) for
Atlas-5K, `delhi/run_atlas_india.py` for W1.
