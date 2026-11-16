# Atlas-India v1.0: all-India league results (generated from india_results.json)

Recipe decision on pooled validation: E [9.104, 9.07, 9.059] after [60000, 60000, 60000] steps; F [9.116, 9.093, 9.059] after [60000, 60000, 60000] steps; paired difference E - F -0.011, standard error 0.007: recipe E. Single models on test (trained / unseen): E [[21.47, 21.31], [21.29, 21.36], [21.35, 21.53]], F [[21.7, 21.55], [21.42, 21.54], [21.35, 21.53]].

## All networks pooled (PM2.5, ug/m3, next 24 h)

| Entry | Trained: MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | Unseen: MAE | QL | COV80 % | Atlas-India against it (trained / unseen) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Atlas-India | 20.99 | 38.89 | 6.91 | 79 | 9.55 | 19.09 | 21.75 | 23.88 | 20.86 | 6.86 | 78 | – |
| Atlas-India, recipe F (not chosen) | 21.00 | 38.74 | 6.91 | 79 | 9.57 | 19.04 | 21.82 | 23.98 | 20.97 | 6.90 | 78 | TIE -0.1% (p=0.74) / WIN -0.5% (p=0.00039) |
| TimesFM 2.5 (Google, 200M) zero-shot | 22.35 | 41.30 | 7.37 | 80 | 9.54 | 20.67 | 23.46 | 25.16 | 21.93 | 7.21 | 80 | WIN -6.1% (p=2.1e-20) / WIN -4.8% (p=3.8e-11) |
| Same hour yesterday | 29.86 | 53.86 | 11.83 | 54 | 29.48 | 29.66 | 29.66 | 29.68 | 29.30 | 11.53 | 53 | WIN -29.7% (p=1.5e-115) / WIN -28.8% (p=4.4e-100) |
| Last observed value | 32.01 | 57.63 | 12.95 | 49 | 11.65 | 32.15 | 35.64 | 28.36 | 31.13 | 12.50 | 47 | WIN -34.4% (p=3.5e-140) / WIN -33.0% (p=1.4e-104) |

Input fix applied (weights unchanged) to seeds [400] by re-forecasting: variables that no trained station of a network reports are no longer inputs there: {"Gujarat": ["BP"], "Punjab": ["AT"], "Kerala": ["BP"]}. Their single models on test as first run (trained / unseen): E [[21.47, 23.6]], F [[21.7, 23.64]]. Largest change of any trained-station forecast: 0.0000 ug/m3. Seeds [401, 402] were forecast with the fixed loader from the start.

## Each network (MAE on trained stations; Atlas-India against the entry in brackets)

| Network | stations (unseen) | mean PM2.5 in test | Atlas-India: trained / unseen | Atlas-India, recipe F (not chosen) | Same hour yesterday | Last observed value | TimesFM 2.5 (Google, 200M) zero-shot |
|---|---|---|---|---|---|---|---|
| Uttar Pradesh | 40 (8) | 77 | 20.89 / 22.46 | 20.89 (TIE +0.0%) | 30.15 (WIN -30.7%) | 33.40 (WIN -37.5%) | 22.78 (WIN -8.3%) |
| Delhi | 37 (7) | 140 | 37.34 / 35.56 | 37.58 (TIE -0.6%) | 54.74 (WIN -31.8%) | 59.63 (WIN -37.4%) | 41.87 (WIN -10.8%) |
| Haryana | 30 (6) | 86 | 24.32 / 22.31 | 24.29 (TIE +0.1%) | 35.81 (WIN -32.1%) | 34.76 (WIN -30.0%) | 25.72 (WIN -5.5%) |
| Maharashtra | 27 (5) | 74 | 19.68 / 24.92 | 19.62 (LOSS +0.3%) | 26.38 (WIN -25.4%) | 27.83 (WIN -29.3%) | 19.45 (TIE +1.2%) |
| Karnataka | 24 (5) | 34 | 8.87 / 9.20 | 8.82 (LOSS +0.5%) | 12.49 (WIN -29.0%) | 11.66 (WIN -23.9%) | 8.98 (TIE -1.2%) |
| other states | 22 (4) | 55 | 15.12 / 9.12 | 15.05 (LOSS +0.5%) | 20.01 (WIN -24.4%) | 22.37 (WIN -32.4%) | 15.19 (TIE -0.5%) |
| Madhya Pradesh | 14 (3) | 57 | 16.23 / 13.86 | 16.23 (TIE +0.0%) | 21.80 (WIN -25.5%) | 26.92 (WIN -39.7%) | 17.07 (WIN -4.9%) |
| West Bengal | 14 (3) | 75 | 14.65 / 14.81 | 14.67 (TIE -0.2%) | 21.41 (WIN -31.6%) | 22.87 (WIN -36.0%) | 15.79 (WIN -7.2%) |
| Bihar | 12 (2) | 121 | 27.74 / 25.05 | 27.65 (TIE +0.4%) | 39.71 (WIN -30.1%) | 43.96 (WIN -36.9%) | 29.35 (WIN -5.5%) |
| Rajasthan | 10 (2) | 63 | 19.07 / 15.33 | 18.99 (LOSS +0.4%) | 26.71 (WIN -28.6%) | 29.40 (WIN -35.2%) | 19.67 (WIN -3.1%) |
| Gujarat | 9 (2) | 67 | 18.47 / 18.41 | 18.49 (TIE -0.1%) | 23.66 (WIN -21.9%) | 27.83 (WIN -33.6%) | 18.20 (TIE +1.5%) |
| Tamil Nadu | 9 (2) | 42 | 12.64 / 16.39 | 12.65 (TIE -0.0%) | 17.37 (WIN -27.2%) | 17.25 (WIN -26.7%) | 13.39 (WIN -5.6%) |
| Punjab | 8 (2) | 65 | 17.31 / 28.08 | 17.29 (TIE +0.1%) | 23.86 (WIN -27.5%) | 24.30 (WIN -28.8%) | 18.20 (WIN -4.9%) |
| Kerala | 7 (1) | 43 | 8.51 / 12.32 | 8.50 (TIE +0.1%) | 12.44 (WIN -31.6%) | 10.91 (WIN -22.0%) | 7.96 (LOSS +6.9%) |

Networks where Atlas-India wins / ties / loses (trained stations): Atlas-India, recipe F (not chosen): 0 / 10 / 4; Same hour yesterday: 14 / 0 / 0; Last observed value: 14 / 0 / 0; TimesFM 2.5 (Google, 200M) zero-shot: 9 / 4 / 1

## Verdicts under the rules written before the run

- Atlas-India, recipe F (not chosen): level
- Same hour yesterday: BEATS
- Last observed value: BEATS
- TimesFM 2.5 (Google, 200M) zero-shot: BEATS

