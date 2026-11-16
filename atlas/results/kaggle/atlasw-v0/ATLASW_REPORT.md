# Atlas-W air core v0 on Delhi (generated)

## Data threshold: single-model test MAE on trained stations, mean of 2 seeds

| model | parameters | 0.5 mo | 1 mo | 2 mo | 4 mo | 8 mo | all (15 mo) |
|---|---|---|---|---|---|---|---|
| Atlas-W width 32 | 14,043 | 37.1 | 37.4 | 39.5 | 37.3 | 33.0 | 32.1 |
| Atlas-W width 64 | 37,531 | 37.9 | 37.4 | 39.2 | 36.6 | 33.4 | 32.3 |
| Atlas (stage 8B) | 50,232 | 47.3 | 48.3 | 50.6 | 43.1 | 38.0 | 35.1 |
| Atlas (stage 8B) | 231,312 | 43.5 | 47.1 | 51.9 | 43.6 | 36.9 | 34.9 |
| Atlas (stage 8B) | 967,632 | 42.7 | 42.8 | 44.2 | 40.0 | 35.4 | 34.3 |

Rule 2: {"months": [0.5, 1, 2, 4, 8, 99], "atlasw": {"32": [37.07075500488281, 37.42240524291992, 39.48998260498047, 37.275197982788086, 32.99136734008789, 32.12957572937012], "64": [37.931894302368164, 37.4097957611084, 39.150638580322266, 36.55483627319336, 33.377811431884766, 32.31170654296875]}, "atlasw_best": [37.07075500488281, 37.4097957611084, 39.150638580322266, 36.55483627319336, 32.99136734008789, 32.12957572937012], "atlas_best": [42.7, 42.8, 44.2, 40.0, 35.4, 34.3], "more_data_efficient": true, "months_to_below_same_hour_yesterday_40_30": {"atlasw": 0.5, "atlas": 4}, "months_to_below_36": {"atlasw": 8, "atlas": 8}}

## Full data, 3-seed ensemble, calibrated

| Entry | Trained: MAE | Never trained: MAE | QL | COV80 % | MAE@1h | MAE@6h | MAE@24h |
|---|---|---|---|---|---|---|---|
| Atlas-W v0 (14,043 parameters, 3 seeds, 16 months of Delhi) | 31.97 | 27.43 | 10.51 | 79 | 14.89 | 30.47 | 35.34 |
| TimesFM 2.5 (Google, zero-shot) | 30.83 | 27.10 | 10.15 | 78 | 13.95 | 29.17 | 35.34 |
| Chronos-2 (Amazon, zero-shot) | 31.17 | 27.41 | 10.23 | 79 | 14.10 | 29.29 | 35.99 |
| Chronos-Bolt (Amazon, zero-shot) | 31.35 | 27.94 | 10.26 | 79 | 14.21 | 29.33 | 36.26 |
| Atlas v1.0 (recorded) | 33.42 | 29.07 | | | | | |

- against TimesFM 2.5 (Google, zero-shot): Atlas-W LOSES to it
- against Chronos-2 (Amazon, zero-shot): level
- against Chronos-Bolt (Amazon, zero-shot): level
