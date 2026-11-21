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

**ParadoxAI Lab** · Aditya Kumar, Anupam Singh · v1.1 (interim), 2026-11-22. v1.0 (weather, air quality, traffic)
is final; v1.1 adds the traffic follow-ups, the India study and the hybrid with global forecasts (interim; GraphCast
and the final scoring pending). One-page scoreboard:
[`atlas/m100/STANDINGS.md`](https://github.com/paradoxailab/paradox-world-model/blob/main/atlas/m100/STANDINGS.md).

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

**Traffic (six road networks, next hour at 5-min steps): a clear loss.** LOSS in 22 of 24 comparisons against the
trained specialists STID, Graph WaveNet, STAEformer and our own PWM-Dyn v0.6r (4–27% worse); against zero-shot
foundation models WIN 7, TIE 11, LOSS 12 (loses to TimesFM 2.5 / 3.0 on the four PeMS networks). **Do not use the
traffic view where a trained traffic model is available.**

**Traffic follow-ups** (separately pre-registered, core frozen, weather and air-quality weights byte-identical):
the best, **Atlas-100M-TXL2** (20.45M traffic parameters, 118,974,606 in all), has **no loss** against the foundation
models (WIN 18, TIE 12) and WIN 4, TIE 13, LOSS 7 against the specialists and PWM-Dyn (from 0 / 2 / 22). Still not the
best traffic model: STAEformer and PWM-Dyn win on some networks.

**Weather in India** (all 68 Indian stations, 2023 and 2024–25): **level** with the foundation models, not ahead —
WIN 19, TIE 74, LOSS 7 of 100 (worldwide: 100 of 100).

**Hybrid with global forecasts — interim** (178 stations, 2025, 24 h): the weather model reading ECMWF IFS, AIFS and
NOAA GFS forecasts (H2: the freshest published run) is ahead of raw and bias-corrected IFS on temperature (−19% / −11%),
dewpoint (−25% / −16%) and wind speed (−30% / −17%), ahead of GFS on every variable, and **loses to bias-corrected IFS
on sea-level pressure (+12%)**. Interim: GraphCast is still being fetched and the final scoring uses a corrected pairing
(PREREG deviations 7 and 8). This card will be updated with the final verdicts.

## Limits (read before using)

- Task-trained against zero-shot: the foundation models were not fine-tuned on these datasets; Atlas trained on the
  same stations' earlier years and sees each station's neighbours.
- Weak on sea-level pressure and on stations it never trained on; level (not ahead) in India. Traffic improved by the
  follow-ups but still behind the best specialists. One training seed per model.
- Not a global gridded model and not compared with video / robotics world models.

## Files

| File | What |
|---|---|
| `atlas100m_best.pt` | the full multi-domain model (shared core stored once); load with `m100.multi.MultiAtlas.load` |
| `atlas100m_weather_view.pt` | weather-only view (95.5M), a plain Atlas; load with `atlas.grow.load_any` |
| `atlas100m_aq_view.pt` | air-quality view |
| `atlas100m_traffic_view.pt` | traffic view (v1.0) |
| `traffic/atlas100mT_best.pt`, `traffic/atlas100mT1d_best.pt`, `traffic/atlas100mTXL2_best.pt` | traffic follow-ups; load with `m100.traffic_plus.load_plus` |
| `hybrid/hybrid_best.pt`, `hybrid/hybrid2_best.pt` | weather view + global-forecast inputs (registered hybrid; H2); load with `atlas.grow.load_any`, inputs built by `m100.hybrid.HybridData` |
| `SHA256SUMS` | checksums, verified after upload |

```python
# git clone https://github.com/paradoxailab/paradox-world-model && cd paradox-world-model/atlas
from atlas.grow import load_any
model = load_any("atlas100m_weather_view.pt").eval()
q, recon, extras = model(yc, mc, uc, uf, geo, None, static)   # q: [batch, stations, 24 h, 5 vars, 3 quantiles]
```

Licence: Apache-2.0. Data: WEATHER-5K and NOAA ISD (weather), CPCB via the public Kaggle copy (air quality), Caltrans
PeMS / METR-LA / PEMS-BAY (traffic); see `DATA_SOURCES.md` in the repository.
