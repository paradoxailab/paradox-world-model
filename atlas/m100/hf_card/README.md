---
license: apache-2.0
library_name: pytorch
pipeline_tag: time-series-forecasting
tags:
- paradoxailab
- paradox-world-model
- atlas
- forecasting
- spatiotemporal
- weather-forecasting
- air-quality
- traffic-forecasting
---

# Atlas-100M: one compact world model for weather, air quality and traffic

**ParadoxAI Lab** · Aditya Kumar, Anupam Singh · interim release 2026-11-21 (weather and air quality evaluated;
traffic and the hybrid comparison with ECMWF / GFS still running).

| | |
|---|---|
| Parameters | **98,599,994** in one set of weights: shared core 94,755,808 + adapters (weather 779,932 · air quality 2,983,932 · traffic 80,322) |
| Architecture | per-station encoder (8 residual blocks) → attention between stations with a learned geometry bias → latent dynamics stepped forward in time (7 blocks per step) → quantile decoder (10 / 50 / 90 %) that predicts the change from the last observation; width 784, 16 heads |
| Built from | Atlas-5K 24.1M (paradoxailab/atlas-5k-25m), grown exactly (check G0: same forecasts before training) |
| Training | 100,000 steps, real station data only: WEATHER-5K (5,672 stations), CPCB all-India PM2.5 (263 stations), six US road networks; one A100, 317.6 min, seed 700 |
| Pre-registration | [`atlas/m100/PREREG.md`](https://github.com/paradoxailab/paradox-world-model/blob/main/atlas/m100/PREREG.md), committed before the first GPU run |
| Full report | [`atlas/m100/RESULTS.md`](https://github.com/paradoxailab/paradox-world-model/blob/main/atlas/m100/RESULTS.md): every win, tie and loss |

## Results so far (paired tests, Holm-corrected; WIN needs p < 0.01 and a 95% interval excluding 0)

**Weather, full 2023 test** (all 5,672 stations, MAE): temperature 1.396 · dew point 1.466 · wind direction 53.23 ·
wind speed 1.172 · sea-level pressure 1.474. Better than the published PhysicsFormer on 4 of 5 variables (−9.9%,
−7.8%, −7.2%, −3.1%), **worse on pressure (+3.1%)**; worse than ECMWF-HRES on pressure (0.86). Equal to our 24.1M model.

**Weather, head-to-head with ten zero-shot foundation models** (709 stations, 2023 test and the 2024–25 live period):
WIN in **100 of 100** comparisons. Against TimesFM 3.0 on the 2023 test: temperature −25.9%, dew point −25.6%,
wind direction −14.6%, wind speed −11.2%, pressure −25.1%.

**Air quality, all-India PM2.5** (trained stations / never-trained stations): WIN against Chronos-Bolt, Chronos-2,
Sundial, TimesFM 2.5, Time-MoE, TiRex and TTM on trained stations; **TIE** with TimesFM 3.0, TimesFM 3.0 multivariate
(+0.8%, slightly worse) and our Atlas-India v1.0. On never-trained stations WIN only against Time-MoE and TTM.

**Traffic and hybrid:** pending; this card will be updated with the scored results.

## Limits (read before using)

- Task-trained against zero-shot: the foundation models were not fine-tuned on these datasets; Atlas trained on the
  same stations' earlier years and sees each station's neighbours.
- Weak on sea-level pressure and on stations it never trained on. One training seed.
- Not a global gridded model and not compared with video / robotics world models.

## Files

| File | What |
|---|---|
| `atlas100m_best.pt` | the full multi-domain model (shared core stored once); load with `m100.multi.MultiAtlas.load` |
| `atlas100m_weather_view.pt` | weather-only view (95.5M), a plain Atlas; load with `atlas.grow.load_any` |
| `atlas100m_aq_view.pt` | air-quality view |
| `atlas100m_traffic_view.pt` | traffic view |
| `SHA256SUMS` | checksums, verified after upload |

```python
# git clone https://github.com/paradoxailab/paradox-world-model && cd paradox-world-model/atlas
from atlas.grow import load_any
model = load_any("atlas100m_weather_view.pt").eval()
q, recon, extras = model(yc, mc, uc, uf, geo, None, static)   # q: [batch, stations, 24 h, 5 vars, 3 quantiles]
```

Licence: Apache-2.0. Data: WEATHER-5K and NOAA ISD (weather), CPCB via the public Kaggle copy (air quality), Caltrans
PeMS / METR-LA / PEMS-BAY (traffic); see `DATA_SOURCES.md` in the repository.
