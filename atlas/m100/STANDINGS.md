# Where Atlas stands (ParadoxAI Lab, 2026-11-22)

One page with every comparison so far: wins, ties and losses, and what is still pending. Each row links to raw
results in `atlas/m100/results/`; every study was pre-registered (`PREREG.md`, `PREREG_TRAFFIC.md`) before it ran.
**WIN** = lower error, Holm-adjusted p < 0.01 and a 95% interval excluding 0; **LOSS** = the mirror image; else **TIE**.

## The models

| Model | Parameters | What it is | Weights |
|---|---|---|---|
| Atlas-100M | 98,599,994 | one shared core for weather, air quality and traffic | HF `atlas100m_*.pt` |
| Atlas-100M-T | 103,363,450 | + 4.84M traffic-only parameters (LoRA, sensor embeddings), core frozen | HF `traffic/atlas100mT_best.pt` |
| Atlas-100M-T1d | 104,878,414 | T with one day of traffic look-back | HF `traffic/atlas100mT1d_best.pt` |
| Atlas-100M-TXL2 | 118,974,606 | + 20.45M traffic-only parameters, one day of look-back | HF `traffic/atlas100mTXL2_best.pt` |
| Atlas-100M hybrid / H2 | weather view + forecast-input weights | the weather model also reading ECMWF IFS, AIFS and NOAA GFS forecasts (H2: the freshest published run) | HF `hybrid/hybrid_best.pt`, `hybrid/hybrid2_best.pt` |

Weather and air-quality weights are byte-identical across all traffic variants (SHA-256 checked before and after each run).

## Scoreboard

| Domain and test | Opponents | Result | Status |
|---|---|---|---|
| **Weather, worldwide** (709 stations, 2023 test + 2024–25 live, 24 h) | 10 zero-shot foundation models: TimesFM 2.5 / 3.0, Chronos-2 (uni / multi), Chronos-Bolt, TiRex, Sundial, Time-MoE, TTM, persistence | **WIN 100 / 100** | final |
| Weather, full 2023 test (5,672 stations) | published PhysicsFormer | better on 4 of 5 variables, **worse on pressure** (+3.1%) | final |
| **Weather + global forecasts (hybrid H2)**, 178 stations, 2025, 24 h | ECMWF IFS raw and bias-corrected | **ahead on temperature (−19% / −11%), dewpoint (−25% / −16%), wind direction (−22%), wind speed (−30% / −17%)**; pressure TIE (raw), **LOSS (bias-corrected, +12%)** | **interim** |
| | NOAA GFS raw and bias-corrected | **ahead on all five variables** (−11% to −40%) | **interim** |
| | ECMWF AIFS | 24–51% lower error, but TIE under the interim scoring (pairing error, deviation 8) | **interim** |
| | GraphCast | archive being fetched (deviation 7) | pending |
| **Weather, India** (all 68 Indian stations, 2023 + 2024–25) | the same 10 foundation models | **WIN 19, TIE 74, LOSS 7**: level with TimesFM, Chronos, TiRex, Sundial; ahead of TTM and persistence | final |
| Weather + global forecasts, India | IFS, AIFS, GFS, GraphCast at the 68 stations | archive being fetched | pending |
| **Air quality, all-India PM2.5** (trained stations) | 9 foundation models + Atlas-India v1.0 | WIN 7 of 9; **TIE** with TimesFM 3.0, TimesFM 3.0 multivariate and Atlas-India v1.0 | final |
| Air quality, never-trained stations | same | WIN only against Time-MoE and TTM; rest TIE | final |
| **Traffic** (6 road networks, next hour), Atlas-100M | 5 foundation-model configurations | WIN 7, TIE 11, **LOSS 12** | final |
| | STID, Graph WaveNet, STAEformer, PWM-Dyn | **LOSS 22 of 24** | final |
| Traffic, **Atlas-100M-TXL2** (best variant) | 5 foundation-model configurations | **WIN 18, TIE 12, LOSS 0** | final |
| | STID, Graph WaveNet, STAEformer, PWM-Dyn | WIN 4, TIE 13, **LOSS 7** | final |
| Traffic, Atlas-100M-T / T1d | foundation models · specialists | 14/16/0 · 2/8/14 and 17/10/3 · 3/10/11 (W/T/L) | final |
| Traffic, Atlas-100M-TXL (first 20.45M attempt) | — | diverged; equals Atlas-100M | final |

## What we can and cannot claim today

- **Can:** Atlas-100M is more accurate than every zero-shot time-series foundation model we tested on 24-hour station
  weather worldwide (100 of 100). With global forecasts as input (interim, final pending), it is ahead of raw and
  bias-corrected ECMWF IFS and NOAA GFS on temperature, dewpoint and wind at 178 stations in 2025.
- **Cannot:** "best weather model on earth". It loses to bias-corrected IFS on sea-level pressure, is only level with
  the foundation models in India, has not been compared with GraphCast yet, and is not a global gridded model
  (WeatherBench 2 is a different task). It is not the best traffic model: STAEformer and our single-domain PWM-Dyn
  still win on some networks.

## Predictions scored so far

| Study | Held | Failed | Pending |
|---|---|---|---|
| Atlas-100M (P1–P17) | 4 (P1, P2, P4, P6) | 9 | P14–P17 (hybrid, final scoring) |
| Hybrid H2 (P18–P22) | — | — | 5 (final scoring) |
| India (P23–P27) | — | 2 (P23, P24) | P25–P27 (India hybrid) |
| Traffic follow-ups (T1–T19) | 7 (T1–T4, T15–T17) | 12 | — |

## Deviations from the plans (all dated, with reasons)

`PREREG.md` deviations 1–8 and `PREREG_TRAFFIC.md` addendum C. The two that touch the open hybrid result:
7 (GraphCast wrongly reported missing; re-fetched) and 8 (pairing error that inflated Atlas's error where an
opponent's archive had gaps; **found after the interim score was seen**, fixed, interim kept published).
