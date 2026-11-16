# Atlas models — model card

ParadoxAI Lab. Status as of 2026-11-17. Every number below is from a run whose log and rules are in `README.md`.

## The models

| Model | Parameters | Task | Inputs | Status |
|---|---|---|---|---|
| **Atlas-5K v1** | 968,672 | 5-variable station weather, next 24 h, WEATHER-5K (5,672 stations worldwide) | last 48 h at the station and its 15 nearest stations; location, elevation, time | **WB1 entry at 24 h** (test 2023 scored once) |
| Atlas-5K v2a | 968,672 | as v1, 150,000 training steps | as v1 | validation −1.44% vs v1; final choice vs v2c pending, then one test |
| Atlas-5K v2c | 968,672 | as v2a, 32-station neighbourhoods | as v1, 31 neighbours | training |
| Atlas W1 | 985,216 | PM2.5 next 24 h, all-India (14 networks, 263 stations) | air-quality sensors + 8 weather series | adopted India model (weather forcing) |
| Atlas-India | 967,632 | as W1, no weather | air-quality sensors | paper-2 model |

All are one architecture (`atlas/model.py`): a station-graph world model with a learned per-station state, attention
between stations with a geometry bias, a shared transition run in latent steps, and a quantile decoder whose median
is the point forecast. Neighbourhood size does not change the parameter count (the weights are shared).

## Results

**WEATHER-5K, 24 h, test 2023, every hourly window of all 5,672 stations (MAE):**

| Model | Temperature °C | Dew point °C | Wind speed m/s | Wind direction ° | Pressure hPa |
|---|---|---|---|---|---|
| **Atlas-5K v1 (0.97M)** | **1.553** | **1.596** | **1.228** | **56.46** | **1.664** |
| PhysicsFormer (19.3M), published | 1.55 | 1.59 | 1.21 | 57.37 | 1.43 |
| ECMWF-HRES, published | 1.76 | 1.85 | 1.48 | 63.8 | 0.86 |

By number (no paired test): level with the 20× larger PhysicsFormer on temperature and dew point, ahead on wind
direction, behind on wind speed (+1.5%) and pressure (+16%); lower error than ECMWF-HRES on four of five variables,
not pressure. Under the pre-registered rules it beats neither. Our pipeline reproduces the published DLinear numbers
within 2.8% (check C2).

**India:**
* All-India test with perfect weather (ERA5): W1 19.86 / 19.92 µg/m³ (trained / never-trained stations) vs TimesFM
  2.5 22.35 / 21.93 and Atlas-F 20.75 / 20.44; significant on both tracks.
* Delhi winter 2024–25 with real day-before ECMWF forecasts: Atlas-W MAE 28.19 vs 31.27 for the no-weather Atlas
  (−9.9%, p = 0.0009). Published Day-1 numbers for IITM WRF-Chem are 58.75 and for IMD SILAM 71.68 (by number).

## Weights

The trained weights are in `models/` (released 2026-11-17), copied byte-for-byte from the Kaggle runs. The SHA-256
of each file is in `models/SHA256SUMS`:

| File | Model | SHA-256 |
|---|---|---|
| `w5k_atlas_1m_h24_s600.pt` | Atlas-5K v1 (WB1 entry) | `a21bd99a4c4c7b0a9013772153c608d4c627e3df064660a63e71ecd5a36e1181` |
| `w5k_atlas_1m_h24_v2a_s600.pt` | Atlas-5K v2a | `fe8bec3eb1145b6c1b94a9370c01dc669cd92cdf08a5c6e31773ff03693088cd` |
| `atlas_w1_s400.pt` | Atlas W1, seed 400 | `0b96038d1255832a1654816465e0b6369c9c966e332c1fb1259a119d903bbd0b` |
| `atlas_w1_s401.pt` | Atlas W1, seed 401 | `2b56a0100da53576d2d37228044ed032cee4fdf4e531b5220d9bc0b033ff1add` |
| `atlas_w1_s402.pt` | Atlas W1, seed 402 | `d6efc4292361242969810a27950721fb8f0f93d10f34f013d0c521492b6cd800` |

Atlas-5K files hold `{"sd", "cfg"}`. W1 files hold `{"cfg", "E", "F", "networks"}`: `E` is the early-stopped model
that the reported W1 numbers use (as a three-seed ensemble). Load them with:

```python
import torch
from atlas.model import Atlas
ck = torch.load("models/w5k_atlas_1m_h24_s600.pt", map_location="cpu")
model = Atlas(**ck["cfg"]); model.load_state_dict(ck["sd"]); model.eval()
ck = torch.load("models/atlas_w1_s400.pt", map_location="cpu")
w1 = Atlas(**ck["cfg"]); w1.load_state_dict(ck["E"]); w1.eval()
```

Inputs must be scaled with the benchmark's fixed mean and standard deviation (`delhi/run_atlas_5k.py`, MEAN/STD), and
neighbourhoods built as in `neighbours()` / `geometry()` there.

## Limits

* Station models: they forecast where there are measurements, not a gridded field.
* WEATHER-5K results are at 24 h only so far; 72, 120 and 168 h are not yet run.
* Comparisons with published models are by number; their forecasts are not available for a paired test.
* India results are PM2.5 at Indian stations; the all-India weather result uses reanalysis (an upper bound).
