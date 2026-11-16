# Atlas on Delhi PM2.5: results (generated from atlas_delhi_results.json)

DELHI: 17544 hours x 39 stations, targets ['PM2.5', 'PM10', 'NO2', 'Ozone'] (missing 7.0%, 6.1%, 6.5%, 9.7%), 11 input channels, 376 graph links, 6 regions; splits {'train': ('2024-01-01T00', '2025-05-02T23'), 'val': ('2025-05-03T00', '2025-07-02T23'), 'test': ('2025-07-03T00', '2025-12-31T23')}

## Track S: training stations (PM2.5, ug/m3, next 24 h)

| Model | MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | vs final (MAE) |
|---|---|---|---|---|---|---|---|---|---|
| TimesFM 2.5 (Google, 200M) zero-shot | 30.83 | 55.52 | 10.15 | 78 | 13.95 | 29.17 | 32.91 | 35.34 | final LOSES +8.4% (p=0.00059) |
| Chronos-2 (Amazon, 120M) zero-shot | 31.17 | 55.81 | 10.23 | 79 | 14.10 | 29.29 | 32.93 | 35.99 | final LOSES +7.2% (p=0.0025) |
| Chronos-Bolt base (Amazon, 205M) zero-shot | 31.35 | 56.00 | 10.26 | 79 | 14.21 | 29.33 | 33.35 | 36.26 | final LOSES +6.6% (p=0.0053) |
| **Atlas plain-1000K (3 seeds)** | 33.42 | 60.96 | 11.39 | 78 | 14.88 | 30.02 | 36.28 | 37.69 | – |
| Atlas plain-250K (1 seed) | 34.73 | 60.79 | 11.52 | 78 | 15.71 | 31.16 | 36.98 | 39.69 | final WINS -3.8% (p=0.016) |
| Atlas ID-1000K (1 seed) | 34.97 | 60.22 | 11.73 | 78 | 23.33 | 30.65 | 36.71 | 38.29 | final WINS -4.4% (p=0.038) |
| Atlas plain-1000K (1 seed) | 35.45 | 61.11 | 11.95 | 76 | 16.22 | 30.91 | 37.60 | 40.67 | final WINS -5.7% (p=0.004) |
| Atlas ID-250K (1 seed) | 35.79 | 61.95 | 11.87 | 78 | 23.84 | 30.53 | 37.39 | 39.34 | final WINS -6.6% (p=0.0018) |
| Same hour yesterday | 40.30 | 70.24 | 15.28 | 71 | 39.98 | 39.94 | 40.06 | 40.35 | final WINS -17.1% (p=2.8e-08) |
| Last observed value | 46.01 | 81.07 | 18.06 | 67 | 16.58 | 47.16 | 54.74 | 38.94 | final WINS -27.4% (p=4.2e-21) |

## Track U: stations never trained on (PM2.5, ug/m3, next 24 h)

| Model | MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | vs final (MAE) |
|---|---|---|---|---|---|---|---|---|---|
| TimesFM 2.5 (Google, 200M) zero-shot | 27.10 | 50.72 | 8.97 | 78 | 12.03 | 25.61 | 29.26 | 31.56 | final LOSES +7.3% (p=0.00094) |
| Chronos-2 (Amazon, 120M) zero-shot | 27.41 | 50.80 | 9.07 | 80 | 12.26 | 25.77 | 29.18 | 32.19 | final LOSES +6.1% (p=0.007) |
| Chronos-Bolt base (Amazon, 205M) zero-shot | 27.94 | 51.57 | 9.17 | 79 | 12.39 | 26.05 | 30.04 | 33.00 | tie +4.0% (p=0.083) |
| **Atlas plain-1000K (3 seeds)** | 29.07 | 54.21 | 9.98 | 79 | 13.09 | 26.80 | 31.56 | 33.01 | – |
| Atlas plain-250K (1 seed) | 30.34 | 54.04 | 10.12 | 77 | 13.90 | 27.65 | 32.31 | 34.71 | final WINS -4.2% (p=0.0085) |
| Atlas ID-1000K (1 seed) | 30.48 | 53.03 | 10.26 | 78 | 20.70 | 27.18 | 32.08 | 33.74 | final WINS -4.6% (p=0.0087) |
| Atlas plain-1000K (1 seed) | 31.09 | 54.09 | 10.42 | 77 | 13.95 | 27.64 | 33.12 | 36.12 | final WINS -6.5% (p=0.0017) |
| Atlas ID-250K (1 seed) | 31.78 | 57.07 | 10.76 | 78 | 21.12 | 26.90 | 33.59 | 35.61 | final WINS -8.5% (p=1.6e-05) |
| Same hour yesterday | 35.39 | 62.90 | 13.30 | 75 | 34.87 | 35.49 | 35.58 | 35.74 | final WINS -17.9% (p=6.7e-09) |
| Last observed value | 38.69 | 70.25 | 14.91 | 71 | 13.82 | 39.06 | 45.10 | 34.80 | final WINS -24.9% (p=1.7e-16) |

## Validation choice

Noise floor (3 seeds of the smallest plain model): sigma = 0.107 ug/m3. Rule: lowest validation PM2.5 MAE if it beats the smallest plain model by > 2 sigma.

| Variant | parameters | validation MAE | training steps | minutes |
|---|---|---|---|---|
| plain-250K | 231,312 | 22.595 | 3100 | 5.75 |
| ID-250K | 238,637 | 22.704 | 3700 | 50.13 |
| plain-1000K (chosen) | 967,632 | 22.023 | 4000 | 12.29 |
| ID-1000K | 984,749 | 22.911 | 3400 | 51.25 |

## Data threshold on real data (smallest size, 1 seed)

| training data | windows | plain: test MAE | ID: test MAE |
|---|---|---|---|
| last 15.46 months | 3,761 | 34.73 | 35.79 |


## What the final model uses (Track S MAE with inputs hidden at test time)

All inputs: 33.42

- other pollutants hidden (PM10, NO2, ozone, CO, SO2, NH3, NO): 37.96 (+13.6%)
- meteorology hidden (temperature, humidity, wind, sun, pressure): 36.37 (+8.8%)
- only the last 24 h visible (not 72 h): 36.47 (+9.1%)
- 30% of all inputs hidden at random: 34.40 (+2.9%)

## Opponents that did not run

- tfm3: skipped: time budget

