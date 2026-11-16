# PWM-W v0.3 weather league: CPCB

Stations: 25. Chosen setting: P1 (validation only). Test origins every 6 h, 24 h ahead.

## AT (deg C)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| Chronos-2 (Amazon, 120M) | tsfm | 0.862 | 0.619 | 0.890 | 0.969 | 1.469 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.883 | 0.623 | 0.909 | 0.999 | 1.488 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 0.896 | 0.678 | 0.953 | 0.977 | 1.460 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 0.914 | 0.645 | 0.943 | 1.034 | 1.505 | 1.00 |
| PWM-W (pure) | ours | 0.933 | 0.669 | 0.974 | 1.045 | 1.535 | 1.00 |
| Baseline: same hour yesterday | baseline | 1.068 | 1.065 | 1.065 | 1.070 | 1.789 | 0.98 |
| Baseline: daily cycle + latest anomaly | baseline | 1.117 | 0.774 | 1.254 | 1.221 | 1.758 | 1.00 |
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 1.186 | 1.184 | 1.185 | 1.187 | 1.741 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 1.236 | 1.234 | 1.235 | 1.237 | 1.795 | 1.00 |
| DWD ICON (physics) [latest run] + local bias correction | global | 1.239 | 1.239 | 1.239 | 1.239 | 1.799 | 1.00 |
| Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) | global-ensemble | 1.271 | 1.267 | 1.268 | 1.274 | 1.827 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] + local bias correction | global | 1.273 | 1.277 | 1.278 | 1.268 | 1.830 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 1.359 | 1.358 | 1.359 | 1.360 | 1.948 | 1.00 |
| DWD ICON (physics) [issued before forecast start] + local bias correction | global | 1.380 | 1.349 | 1.351 | 1.409 | 1.933 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] + local bias correction | global | 1.387 | 1.383 | 1.383 | 1.391 | 1.966 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 1.488 | 1.483 | 1.486 | 1.491 | 2.160 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 1.495 | 1.494 | 1.494 | 1.497 | 2.090 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] + local bias correction | global | 1.559 | 1.552 | 1.553 | 1.565 | 2.185 | 0.50 |
| NOAA GFS (physics) [issued before forecast start] + local bias correction | global | 1.716 | 1.707 | 1.709 | 1.724 | 2.392 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 1.942 | 1.941 | 1.941 | 1.943 | 2.556 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 2.013 | 2.012 | 2.012 | 2.015 | 2.612 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] | global | 2.035 | 2.043 | 2.043 | 2.026 | 2.669 | 1.00 |
| DWD ICON (physics) [latest run] | global | 2.075 | 2.076 | 2.076 | 2.075 | 2.704 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] | global | 2.080 | 2.078 | 2.079 | 2.083 | 2.688 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] | global | 2.279 | 2.256 | 2.257 | 2.302 | 2.903 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] | global | 2.338 | 2.325 | 2.327 | 2.350 | 2.976 | 0.50 |
| DWD ICON (physics) [issued before forecast start] | global | 2.349 | 2.301 | 2.301 | 2.398 | 2.970 | 1.00 |
| NOAA GFS (physics) [latest run] | global | 3.075 | 3.068 | 3.070 | 3.081 | 3.793 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] | global | 3.437 | 3.413 | 3.413 | 3.462 | 4.188 | 1.00 |

## RH (%)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| Chronos-2 (Amazon, 120M) | tsfm | 4.648 | 3.338 | 4.750 | 5.252 | 6.935 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 4.652 | 3.482 | 4.886 | 5.119 | 6.591 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 4.653 | 3.304 | 4.766 | 5.271 | 6.901 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 4.774 | 3.410 | 4.905 | 5.390 | 6.951 | 1.00 |
| PWM-W (pure) | ours | 4.971 | 3.532 | 5.065 | 5.643 | 7.192 | 1.00 |
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 5.071 | 5.067 | 5.070 | 5.074 | 6.838 | 1.00 |
| DWD ICON (physics) [latest run] + local bias correction | global | 5.136 | 5.131 | 5.136 | 5.139 | 6.998 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] + local bias correction | global | 5.189 | 5.177 | 5.180 | 5.199 | 7.029 | 1.00 |
| Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) | global-ensemble | 5.431 | 5.404 | 5.410 | 5.455 | 7.289 | 1.00 |
| Baseline: same hour yesterday | baseline | 5.667 | 5.651 | 5.653 | 5.682 | 8.332 | 0.98 |
| Baseline: daily cycle + latest anomaly | baseline | 5.769 | 3.975 | 6.380 | 6.362 | 8.037 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 5.771 | 5.768 | 5.769 | 5.774 | 7.699 | 1.00 |
| DWD ICON (physics) [issued before forecast start] + local bias correction | global | 6.212 | 6.083 | 6.092 | 6.336 | 8.237 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] + local bias correction | global | 6.444 | 6.431 | 6.433 | 6.455 | 8.603 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 6.560 | 6.557 | 6.557 | 6.562 | 8.777 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 6.693 | 6.670 | 6.680 | 6.711 | 8.922 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] + local bias correction | global | 6.953 | 6.898 | 6.903 | 7.006 | 9.163 | 0.51 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 7.796 | 7.798 | 7.793 | 7.797 | 10.267 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] | global | 7.872 | 7.861 | 7.856 | 7.885 | 10.197 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 8.081 | 8.096 | 8.085 | 8.071 | 10.365 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 8.315 | 8.293 | 8.304 | 8.332 | 10.715 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] + local bias correction | global | 8.801 | 8.756 | 8.771 | 8.839 | 11.361 | 1.00 |
| DWD ICON (physics) [latest run] | global | 8.876 | 8.890 | 8.881 | 8.867 | 11.197 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] | global | 9.101 | 8.930 | 8.926 | 9.275 | 11.743 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] | global | 9.178 | 9.174 | 9.171 | 9.183 | 12.007 | 1.00 |
| DWD ICON (physics) [issued before forecast start] | global | 9.546 | 9.453 | 9.443 | 9.645 | 12.035 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] | global | 11.235 | 10.949 | 10.954 | 11.519 | 14.336 | 0.51 |
| NOAA GFS (physics) [latest run] | global | 30.535 | 30.439 | 30.502 | 30.600 | 35.495 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] | global | 31.743 | 31.577 | 31.622 | 31.886 | 36.726 | 1.00 |

## WS (m/s)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| PWM-W hybrid (uses global forecasts) | hybrid | 0.384 | 0.335 | 0.391 | 0.405 | 0.684 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.393 | 0.328 | 0.399 | 0.422 | 0.801 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 0.395 | 0.329 | 0.403 | 0.424 | 0.719 | 1.00 |
| PWM-W (pure) | ours | 0.419 | 0.351 | 0.429 | 0.447 | 0.749 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 0.473 | 0.471 | 0.472 | 0.475 | 0.822 | 1.00 |
| Baseline: daily cycle + latest anomaly | baseline | 0.492 | 0.390 | 0.521 | 0.529 | 0.847 | 1.00 |
| Baseline: same hour yesterday | baseline | 0.499 | 0.499 | 0.499 | 0.500 | 0.857 | 0.92 |
| DWD ICON (physics) [latest run] + local bias correction | global | 0.586 | 0.585 | 0.585 | 0.586 | 0.962 | 1.00 |
| DWD ICON (physics) [issued before forecast start] + local bias correction | global | 0.636 | 0.622 | 0.622 | 0.651 | 1.020 | 1.00 |
| Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) | global-ensemble | 0.667 | 0.666 | 0.667 | 0.668 | 1.021 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] + local bias correction | global | 0.709 | 0.703 | 0.705 | 0.714 | 1.216 | 0.44 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 0.717 | 0.716 | 0.716 | 0.717 | 1.072 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] + local bias correction | global | 0.754 | 0.750 | 0.752 | 0.758 | 1.110 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 0.754 | 0.753 | 0.754 | 0.755 | 1.109 | 1.00 |
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 0.760 | 0.759 | 0.760 | 0.761 | 1.109 | 1.00 |
| DWD ICON (physics) [latest run] | global | 0.807 | 0.807 | 0.807 | 0.807 | 1.157 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] + local bias correction | global | 0.833 | 0.835 | 0.835 | 0.830 | 1.183 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 0.906 | 0.904 | 0.905 | 0.907 | 1.283 | 1.00 |
| DWD ICON (physics) [issued before forecast start] | global | 0.907 | 0.889 | 0.889 | 0.924 | 1.254 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] + local bias correction | global | 0.939 | 0.928 | 0.928 | 0.950 | 1.324 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] | global | 1.024 | 1.016 | 1.016 | 1.032 | 1.449 | 0.44 |
| ECMWF IFS 9 km (physics) [latest run] | global | 1.034 | 1.034 | 1.034 | 1.035 | 1.375 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] | global | 1.106 | 1.098 | 1.098 | 1.113 | 1.435 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 1.120 | 1.120 | 1.120 | 1.121 | 1.467 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 1.130 | 1.129 | 1.129 | 1.130 | 1.478 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] | global | 1.277 | 1.281 | 1.281 | 1.273 | 1.622 | 1.00 |
| NOAA GFS (physics) [latest run] | global | 1.789 | 1.792 | 1.789 | 1.787 | 2.162 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] | global | 1.817 | 1.817 | 1.817 | 1.817 | 2.197 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 70.322 | 70.207 | 70.332 | 70.375 | 71.893 | 1.00 |

## Verdicts against the global weather models

BEATS = significantly lower MAE than both the raw and the bias-corrected forecast. STRICT uses the latest run (often issued after our forecast start); ISSUED-BEFORE-START uses the newest run published before it.

- [STRICT] PWM-W (pure) vs DWD ICON (physics): AT BEATS (-55.0% / -24.7%); RH TIES / MIXED (-44.0% / -3.2%); WS BEATS (-48.1% / -28.5%)
- [STRICT] PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-51.9% / -21.3%); RH TIES / MIXED (-38.5% / -2.0%); WS BEATS (-62.9% / -44.9%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-53.6% / -24.5%); RH BEATS (-36.2% / -13.9%); WS BEATS (-62.6% / -44.5%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-55.1% / -31.3%); RH BEATS (-45.8% / -24.2%); WS BEATS (-59.5% / -41.6%)
- [STRICT] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-69.6% / -37.6%); RH BEATS (-83.7% / -40.2%); WS BEATS (-76.6% / -53.8%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics): AT BEATS (-60.3% / -32.4%); RH BEATS (-47.9% / -20.0%); WS BEATS (-53.8% / -34.2%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-54.1% / -26.7%); RH TIES / MIXED (-36.9% / -4.2%); WS BEATS (-67.2% / -49.7%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-59.0% / -32.7%); RH BEATS (-45.4% / -22.9%); WS BEATS (-62.1% / -44.5%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-65.7% / -48.5%); RH BEATS (-59.4% / -34.4%); WS BEATS (-69.6% / -56.1%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-72.8% / -45.6%); RH BEATS (-84.3% / -43.5%); WS BEATS (-77.0% / -55.4%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-56.8% / -27.7%); RH BEATS (-47.6% / -9.4%); WS BEATS (-52.4% / -34.4%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-53.8% / -24.4%); RH BEATS (-42.4% / -8.3%); WS BEATS (-66.0% / -49.5%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-55.5% / -27.5%); RH BEATS (-40.3% / -19.4%); WS BEATS (-65.7% / -49.1%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-56.9% / -34.1%); RH BEATS (-49.3% / -29.1%); WS BEATS (-62.8% / -46.4%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-70.9% / -40.1%); RH BEATS (-84.8% / -44.1%); WS BEATS (-78.5% / -57.6%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-61.8% / -35.0%); RH BEATS (-51.3% / -25.1%); WS BEATS (-57.6% / -39.6%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-55.9% / -29.6%); RH BEATS (-40.9% / -10.4%); WS BEATS (-69.9% / -53.9%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-60.7% / -35.4%); RH BEATS (-48.9% / -27.8%); WS BEATS (-65.3% / -49.1%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-65.1% / -47.7%); RH BEATS (-60.3% / -35.9%); WS BEATS (-70.6% / -57.5%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-73.9% / -47.8%); RH BEATS (-85.3% / -47.1%); WS BEATS (-78.9% / -59.1%)

Not tested: GenCast and WeatherNext (no public forecast archive; data needs a Google Cloud access request).

## Log

```
WX_CPCB: 17544 hours x 25 stations, targets ['AT', 'RH', 'WS'] (missing 2.9%, 3.5%, 19.6%), 5 other channels, spreads [3.609999895095825, 13.479999542236328, 0.9300000071525574], 184 graph links, 5 regions; splits {'train': ('2024-01-01T00', '2025-05-02T23'), 'val': ('2025-05-03T00', '2025-07-02T23'), 'test': ('2025-07-03T00', '2025-12-31T23')}
origins: train 11281, validation 241, test 725 (every 6 h); device cuda
variant P0 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1144 val MAE/spread 0.5142 (12s)
    step 1000/6000 loss 0.1273 val MAE/spread 0.5044 (24s)
    step 1500/6000 loss 0.1180 val MAE/spread 0.4968 (35s)
    step 2000/6000 loss 0.1096 val MAE/spread 0.4921 (47s)
    step 2500/6000 loss 0.1007 val MAE/spread 0.4940 (59s)
    step 3000/6000 loss 0.1012 val MAE/spread 0.4930 (71s)
    step 3500/6000 loss 0.0902 val MAE/spread 0.4905 (82s)
    step 4000/6000 loss 0.0894 val MAE/spread 0.4886 (94s)
    step 4500/6000 loss 0.0908 val MAE/spread 0.4916 (106s)
    step 5000/6000 loss 0.0863 val MAE/spread 0.4966 (117s)
    step 5500/6000 loss 0.0819 val MAE/spread 0.4973 (129s)
    step 6000/6000 loss 0.0828 val MAE/spread 0.4978 (140s)
variant P0 seed 1: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1304 val MAE/spread 0.5194 (12s)
    step 1000/6000 loss 0.1150 val MAE/spread 0.4979 (23s)
    step 1500/6000 loss 0.1256 val MAE/spread 0.4955 (35s)
    step 2000/6000 loss 0.1055 val MAE/spread 0.4991 (46s)
    step 2500/6000 loss 0.1132 val MAE/spread 0.5038 (58s)
    step 3000/6000 loss 0.0945 val MAE/spread 0.5050 (70s)
    step 3500/6000 loss 0.0888 val MAE/spread 0.4918 (81s)
    step 4000/6000 loss 0.0971 val MAE/spread 0.4936 (93s)
    step 4500/6000 loss 0.0857 val MAE/spread 0.4960 (104s)
    step 5000/6000 loss 0.0854 val MAE/spread 0.4969 (116s)
    step 5500/6000 loss 0.0814 val MAE/spread 0.4968 (128s)
    step 6000/6000 loss 0.0881 val MAE/spread 0.4941 (139s)
variant P0 seed 2: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1305 val MAE/spread 0.5206 (12s)
    step 1000/6000 loss 0.1212 val MAE/spread 0.5081 (23s)
    step 1500/6000 loss 0.1177 val MAE/spread 0.4963 (35s)
    step 2000/6000 loss 0.1221 val MAE/spread 0.5011 (47s)
    step 2500/6000 loss 0.1003 val MAE/spread 0.4997 (59s)
    step 3000/6000 loss 0.0941 val MAE/spread 0.4971 (71s)
    step 3500/6000 loss 0.0883 val MAE/spread 0.4988 (82s)
    step 4000/6000 loss 0.0969 val MAE/spread 0.4969 (94s)
    step 4500/6000 loss 0.1026 val MAE/spread 0.5003 (105s)
    step 5000/6000 loss 0.0880 val MAE/spread 0.4973 (117s)
    step 5500/6000 loss 0.0978 val MAE/spread 0.4989 (129s)
    step 6000/6000 loss 0.0848 val MAE/spread 0.5025 (140s)
variant P1 seed 0: {'d': 192, 'layers': 4, 'heads': 6, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1168 val MAE/spread 0.5249 (14s)
    step 1000/6000 loss 0.1276 val MAE/spread 0.5004 (28s)
    step 1500/6000 loss 0.1172 val MAE/spread 0.4929 (43s)
    step 2000/6000 loss 0.1085 val MAE/spread 0.4881 (57s)
    step 2500/6000 loss 0.1018 val MAE/spread 0.4823 (71s)
    step 3000/6000 loss 0.1004 val MAE/spread 0.4808 (85s)
    step 3500/6000 loss 0.0891 val MAE/spread 0.4797 (99s)
    step 4000/6000 loss 0.0898 val MAE/spread 0.4841 (114s)
    step 4500/6000 loss 0.0888 val MAE/spread 0.4854 (128s)
    step 5000/6000 loss 0.0836 val MAE/spread 0.4915 (142s)
    step 5500/6000 loss 0.0773 val MAE/spread 0.4878 (156s)
    step 6000/6000 loss 0.0788 val MAE/spread 0.4900 (171s)
variant P2 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': False}
    step 500/6000 loss 0.1162 val MAE/spread 0.5161 (7s)
    step 1000/6000 loss 0.1334 val MAE/spread 0.4964 (14s)
    step 1500/6000 loss 0.1243 val MAE/spread 0.4860 (21s)
    step 2000/6000 loss 0.1172 val MAE/spread 0.4903 (28s)
    step 2500/6000 loss 0.1082 val MAE/spread 0.4889 (34s)
    step 3000/6000 loss 0.1115 val MAE/spread 0.4870 (41s)
    step 3500/6000 loss 0.1010 val MAE/spread 0.4879 (48s)
    step 4000/6000 loss 0.1006 val MAE/spread 0.4902 (55s)
    step 4500/6000 loss 0.1056 val MAE/spread 0.4937 (62s)
    step 5000/6000 loss 0.0992 val MAE/spread 0.4948 (69s)
    step 5500/6000 loss 0.0918 val MAE/spread 0.4972 (76s)
    step 6000/6000 loss 0.0943 val MAE/spread 0.4993 (82s)
variant P3 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 4, 'use_graph': True}
    step 500/6000 loss 0.1474 val MAE/spread 0.5228 (24s)
    step 1000/6000 loss 0.1607 val MAE/spread 0.5015 (47s)
    step 1500/6000 loss 0.1486 val MAE/spread 0.5014 (71s)
    step 2000/6000 loss 0.1427 val MAE/spread 0.4970 (95s)
    step 2500/6000 loss 0.1333 val MAE/spread 0.4987 (119s)
    step 3000/6000 loss 0.1359 val MAE/spread 0.5022 (143s)
    step 3500/6000 loss 0.1215 val MAE/spread 0.4856 (167s)
    step 4000/6000 loss 0.1240 val MAE/spread 0.4904 (191s)
    step 4500/6000 loss 0.1244 val MAE/spread 0.4934 (215s)
    step 5000/6000 loss 0.1175 val MAE/spread 0.4989 (239s)
    step 5500/6000 loss 0.1124 val MAE/spread 0.4964 (263s)
    step 6000/6000 loss 0.1152 val MAE/spread 0.4987 (287s)
validation (MAE / spread): P0 0.4922 +- 0.0038; P1 0.4797, P2 0.4860, P3 0.4856 -> chosen P1
    step 500/6000 loss 0.1308 val MAE/spread 0.5266 (14s)
    step 1000/6000 loss 0.1190 val MAE/spread 0.4996 (29s)
    step 1500/6000 loss 0.1132 val MAE/spread 0.5040 (44s)
    step 2000/6000 loss 0.1124 val MAE/spread 0.4962 (58s)
    step 2500/6000 loss 0.0952 val MAE/spread 0.5004 (72s)
    step 3000/6000 loss 0.0943 val MAE/spread 0.4934 (87s)
    step 3500/6000 loss 0.0857 val MAE/spread 0.4969 (101s)
    step 4000/6000 loss 0.0908 val MAE/spread 0.4951 (115s)
    step 4500/6000 loss 0.0915 val MAE/spread 0.4920 (129s)
    step 5000/6000 loss 0.0880 val MAE/spread 0.4940 (143s)
    step 5500/6000 loss 0.0887 val MAE/spread 0.4932 (158s)
    step 6000/6000 loss 0.0823 val MAE/spread 0.4954 (172s)
    step 500/6000 loss 0.1315 val MAE/spread 0.5198 (14s)
    step 1000/6000 loss 0.1317 val MAE/spread 0.5052 (28s)
    step 1500/6000 loss 0.1122 val MAE/spread 0.4943 (43s)
    step 2000/6000 loss 0.1072 val MAE/spread 0.4909 (57s)
    step 2500/6000 loss 0.1064 val MAE/spread 0.4877 (71s)
    step 3000/6000 loss 0.0899 val MAE/spread 0.4928 (86s)
    step 3500/6000 loss 0.0985 val MAE/spread 0.4897 (100s)
    step 4000/6000 loss 0.0908 val MAE/spread 0.4880 (114s)
    step 4500/6000 loss 0.0811 val MAE/spread 0.4877 (129s)
    step 5000/6000 loss 0.0892 val MAE/spread 0.4899 (143s)
    step 5500/6000 loss 0.0863 val MAE/spread 0.4892 (158s)
    step 6000/6000 loss 0.0853 val MAE/spread 0.4915 (172s)
    step 500/6000 loss 0.1294 val MAE/spread 0.5219 (14s)
    step 1000/6000 loss 0.1180 val MAE/spread 0.4999 (28s)
    step 1500/6000 loss 0.1110 val MAE/spread 0.4901 (43s)
    step 2000/6000 loss 0.0993 val MAE/spread 0.4869 (57s)
    step 2500/6000 loss 0.1024 val MAE/spread 0.4886 (71s)
    step 3000/6000 loss 0.0910 val MAE/spread 0.4944 (85s)
    step 3500/6000 loss 0.0864 val MAE/spread 0.4925 (99s)
    step 4000/6000 loss 0.0909 val MAE/spread 0.4932 (113s)
    step 4500/6000 loss 0.0887 val MAE/spread 0.4939 (127s)
    step 5000/6000 loss 0.0847 val MAE/spread 0.4960 (141s)
    step 5500/6000 loss 0.0798 val MAE/spread 0.4973 (155s)
    step 6000/6000 loss 0.0862 val MAE/spread 0.5013 (170s)
hybrid: 12 global-forecast channels from ['ECMWF IFS 0.25 (physics)', 'ECMWF AIFS (AI)', 'DWD ICON (physics)', 'NOAA GFS (physics)'], 11281 training origins from 2024
    step 500/6000 loss 0.1083 val MAE/spread 0.5003 (15s)
    step 1000/6000 loss 0.1132 val MAE/spread 0.4647 (29s)
    step 1500/6000 loss 0.1013 val MAE/spread 0.4665 (43s)
    step 2000/6000 loss 0.0992 val MAE/spread 0.4548 (59s)
    step 2500/6000 loss 0.0893 val MAE/spread 0.4540 (73s)
    step 3000/6000 loss 0.0882 val MAE/spread 0.4558 (87s)
    step 3500/6000 loss 0.0771 val MAE/spread 0.4582 (101s)
    step 4000/6000 loss 0.0793 val MAE/spread 0.4602 (116s)
    step 4500/6000 loss 0.0786 val MAE/spread 0.4628 (130s)
    step 5000/6000 loss 0.0737 val MAE/spread 0.4637 (145s)
    step 5500/6000 loss 0.0705 val MAE/spread 0.4656 (159s)
    step 6000/6000 loss 0.0706 val MAE/spread 0.4663 (173s)
    step 500/6000 loss 0.1123 val MAE/spread 0.4848 (14s)
    step 1000/6000 loss 0.1152 val MAE/spread 0.4752 (29s)
    step 1500/6000 loss 0.0986 val MAE/spread 0.4726 (43s)
    step 2000/6000 loss 0.0973 val MAE/spread 0.4773 (58s)
    step 2500/6000 loss 0.0936 val MAE/spread 0.4710 (72s)
    step 3000/6000 loss 0.0890 val MAE/spread 0.4734 (87s)
    step 3500/6000 loss 0.0790 val MAE/spread 0.4731 (101s)
    step 4000/6000 loss 0.0743 val MAE/spread 0.4736 (115s)
    step 4500/6000 loss 0.0740 val MAE/spread 0.4750 (130s)
    step 5000/6000 loss 0.0716 val MAE/spread 0.4792 (144s)
    step 5500/6000 loss 0.0717 val MAE/spread 0.4817 (160s)
    step 6000/6000 loss 0.0736 val MAE/spread 0.4828 (174s)
hybrid validation: H1 0.4540, H2 0.4710 (2 sigma = 0.0077) -> H1
    step 500/6000 loss 0.1233 val MAE/spread 0.4989 (14s)
    step 1000/6000 loss 0.1048 val MAE/spread 0.4783 (29s)
    step 1500/6000 loss 0.0973 val MAE/spread 0.4695 (43s)
    step 2000/6000 loss 0.0967 val MAE/spread 0.4658 (58s)
    step 2500/6000 loss 0.0828 val MAE/spread 0.4573 (72s)
    step 3000/6000 loss 0.0849 val MAE/spread 0.4728 (86s)
    step 3500/6000 loss 0.0753 val MAE/spread 0.4666 (101s)
    step 4000/6000 loss 0.0769 val MAE/spread 0.4737 (115s)
    step 4500/6000 loss 0.0800 val MAE/spread 0.4705 (129s)
    step 5000/6000 loss 0.0778 val MAE/spread 0.4751 (144s)
    step 5500/6000 loss 0.0772 val MAE/spread 0.4711 (158s)
    step 6000/6000 loss 0.0720 val MAE/spread 0.4725 (172s)
    step 500/6000 loss 0.1195 val MAE/spread 0.4979 (14s)
    step 1000/6000 loss 0.1103 val MAE/spread 0.4705 (29s)
    step 1500/6000 loss 0.0979 val MAE/spread 0.4640 (43s)
    step 2000/6000 loss 0.0954 val MAE/spread 0.4652 (57s)
    step 2500/6000 loss 0.0941 val MAE/spread 0.4659 (72s)
    step 3000/6000 loss 0.0808 val MAE/spread 0.4670 (87s)
    step 3500/6000 loss 0.0859 val MAE/spread 0.4634 (101s)
    step 4000/6000 loss 0.0785 val MAE/spread 0.4649 (116s)
    step 4500/6000 loss 0.0733 val MAE/spread 0.4661 (130s)
    step 5000/6000 loss 0.0779 val MAE/spread 0.4666 (145s)
    step 5500/6000 loss 0.0760 val MAE/spread 0.4660 (159s)
    step 6000/6000 loss 0.0760 val MAE/spread 0.4695 (174s)
    step 500/6000 loss 0.1159 val MAE/spread 0.4906 (14s)
    step 1000/6000 loss 0.1072 val MAE/spread 0.4809 (29s)
    step 1500/6000 loss 0.0975 val MAE/spread 0.4661 (43s)
    step 2000/6000 loss 0.0878 val MAE/spread 0.4673 (57s)
    step 2500/6000 loss 0.0913 val MAE/spread 0.4592 (71s)
    step 3000/6000 loss 0.0806 val MAE/spread 0.4677 (86s)
    step 3500/6000 loss 0.0762 val MAE/spread 0.4654 (100s)
    step 4000/6000 loss 0.0794 val MAE/spread 0.4647 (114s)
    step 4500/6000 loss 0.0768 val MAE/spread 0.4671 (129s)
    step 5000/6000 loss 0.0750 val MAE/spread 0.4684 (143s)
    step 5500/6000 loss 0.0715 val MAE/spread 0.4686 (157s)
    step 6000/6000 loss 0.0766 val MAE/spread 0.4698 (172s)
    TimesFM 2.5 (Google, 200M): first 4096 of 18125 series in 27s
    tfm25: out of GPU memory at chunk 4096, retrying smaller
    TimesFM 2.5 (Google, 200M): first 1024 of 18125 series in 13s
    tfm25: out of GPU memory at chunk 4096, retrying smaller
    tfm25: out of GPU memory at chunk 1024, retrying smaller
    tfm25: out of GPU memory at chunk 256, retrying smaller
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -55.0% vs raw, -24.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -60.3% vs raw, -32.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on RH: TIES / MIXED (MAE -44.0% vs raw, -3.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on RH: BEATS (MAE -47.9% vs raw, -20.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -48.1% vs raw, -28.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -53.8% vs raw, -34.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -51.9% vs raw, -21.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -54.1% vs raw, -26.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on RH: TIES / MIXED (MAE -38.5% vs raw, -2.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on RH: TIES / MIXED (MAE -36.9% vs raw, -4.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -62.9% vs raw, -44.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -67.2% vs raw, -49.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -53.6% vs raw, -24.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -59.0% vs raw, -32.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -36.2% vs raw, -13.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -45.4% vs raw, -22.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -62.6% vs raw, -44.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -62.1% vs raw, -44.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -55.1% vs raw, -31.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -65.7% vs raw, -48.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -45.8% vs raw, -24.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -59.4% vs raw, -34.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -59.5% vs raw, -41.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -69.6% vs raw, -56.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -69.6% vs raw, -37.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -72.8% vs raw, -45.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -83.7% vs raw, -40.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -84.3% vs raw, -43.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -76.6% vs raw, -53.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -77.0% vs raw, -55.4% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on AT: LOSS (MAE +4.1%, p=0.033, 95% CI +0.7..+7.9%)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on RH: LOSS (MAE +6.9%, p=0.00064, 95% CI +3.3..+10.6%)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on WS: LOSS (MAE +9.0%, p=5.1e-07, 95% CI +6.3..+12.3%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -16.5%, p=2.8e-16, 95% CI -19.6..-13.3%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -13.8%, p=2e-16, 95% CI -16.9..-11.0%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -14.9%, p=2.4e-21, 95% CI -17.6..-12.3%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -37.3%, p=2.1e-14, 95% CI -42.8..-31.5%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -25.7%, p=3.7e-17, 95% CI -30.2..-21.3%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -11.5%, p=2.6e-12, 95% CI -14.3..-8.7%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on AT: WIN (MAE -13.6%, p=1.1e-07, 95% CI -17.4..-9.4%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on RH: WIN (MAE -13.1%, p=1.5e-08, 95% CI -16.9..-9.5%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on WS: WIN (MAE -16.1%, p=2.6e-11, 95% CI -19.9..-12.5%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -26.6%, p=1.5e-13, 95% CI -31.9..-20.7%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -8.5%, p=0.011, 95% CI -14.1..-2.4%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -37.2%, p=2.9e-65, 95% CI -40.5..-34.0%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on AT: LOSS (MAE +8.3%, p=1.1e-06, 95% CI +5.0..+11.8%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on RH: LOSS (MAE +6.9%, p=1.2e-06, 95% CI +4.1..+9.7%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on WS: LOSS (MAE +6.0%, p=5.9e-07, 95% CI +3.6..+8.3%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on AT: TIE (MAE +2.1%, p=0.24, 95% CI -1.1..+5.4%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on RH: LOSS (MAE +4.1%, p=0.0094, 95% CI +1.0..+7.0%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on WS: WIN (MAE -99.4%, p=0, 95% CI -99.4..-99.4%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on AT: LOSS (MAE +5.7%, p=0.0014, 95% CI +2.4..+9.4%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on RH: LOSS (MAE +6.8%, p=1.7e-06, 95% CI +4.0..+9.5%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on WS: LOSS (MAE +6.7%, p=2.1e-06, 95% CI +3.4..+9.2%)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -56.8% vs raw, -27.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -61.8% vs raw, -35.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -47.6% vs raw, -9.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -51.3% vs raw, -25.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -52.4% vs raw, -34.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -57.6% vs raw, -39.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -53.8% vs raw, -24.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -55.9% vs raw, -29.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -42.4% vs raw, -8.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -40.9% vs raw, -10.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -66.0% vs raw, -49.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -69.9% vs raw, -53.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -55.5% vs raw, -27.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -60.7% vs raw, -35.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -40.3% vs raw, -19.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -48.9% vs raw, -27.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -65.7% vs raw, -49.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -65.3% vs raw, -49.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -56.9% vs raw, -34.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -65.1% vs raw, -47.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -49.3% vs raw, -29.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -60.3% vs raw, -35.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -62.8% vs raw, -46.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -70.6% vs raw, -57.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -70.9% vs raw, -40.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -73.9% vs raw, -47.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -84.8% vs raw, -44.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -85.3% vs raw, -47.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -78.5% vs raw, -57.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -78.9% vs raw, -59.1% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on AT: WIN (MAE -4.0%, p=0.033, 95% CI -7.3..-0.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on RH: WIN (MAE -6.4%, p=0.00064, 95% CI -9.6..-3.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on WS: WIN (MAE -8.3%, p=5.1e-07, 95% CI -10.9..-6.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -19.8%, p=3.9e-22, 95% CI -22.9..-16.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -19.4%, p=3.2e-34, 95% CI -22.0..-16.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -21.9%, p=4.5e-42, 95% CI -24.1..-20.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -39.8%, p=4.8e-17, 95% CI -44.9..-34.8%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -30.5%, p=4.8e-25, 95% CI -34.4..-26.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -18.8%, p=1.3e-21, 95% CI -21.4..-16.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on AT: WIN (MAE -17.0%, p=1.6e-08, 95% CI -21.5..-12.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on RH: WIN (MAE -18.5%, p=3.5e-12, 95% CI -22.7..-14.6%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on WS: WIN (MAE -23.6%, p=1.5e-18, 95% CI -27.1..-20.6%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -29.5%, p=7.5e-23, 95% CI -33.9..-25.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -14.3%, p=4e-08, 95% CI -18.5..-10.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -42.4%, p=7.1e-79, 95% CI -45.0..-39.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on AT: TIE (MAE +4.0%, p=0.049, 95% CI -0.0..+8.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on RH: TIE (MAE +0.1%, p=0.97, 95% CI -3.6..+3.4%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on WS: TIE (MAE -2.7%, p=0.081, 95% CI -5.4..-0.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on AT: TIE (MAE -2.0%, p=0.32, 95% CI -5.6..+1.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on RH: TIE (MAE -2.6%, p=0.15, 95% CI -6.0..+0.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on WS: WIN (MAE -99.5%, p=0, 95% CI -99.5..-99.4%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on AT: TIE (MAE +1.5%, p=0.46, 95% CI -2.3..+5.4%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on RH: TIE (MAE -0.0%, p=0.99, 95% CI -3.6..+3.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on WS: TIE (MAE -2.1%, p=0.26, 95% CI -5.9..+0.8%)
no Earth-2 runs found (E2 file missing)
```