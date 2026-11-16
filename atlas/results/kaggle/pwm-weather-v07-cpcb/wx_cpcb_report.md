# PWM-W v0.3 weather league: CPCB

Stations: 25. Chosen setting: P4 (validation only). Test origins every 6 h, 24 h ahead.

## AT (deg C)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| Chronos-2 (Amazon, 120M) | tsfm | 0.862 | 0.619 | 0.890 | 0.969 | 1.469 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.883 | 0.623 | 0.909 | 0.999 | 1.488 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 0.888 | 0.676 | 0.953 | 0.961 | 1.458 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 0.914 | 0.645 | 0.943 | 1.034 | 1.505 | 1.00 |
| PWM-W (pure) | ours | 0.921 | 0.648 | 0.958 | 1.039 | 1.525 | 1.00 |
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
| PWM-W hybrid (uses global forecasts) | hybrid | 4.620 | 3.491 | 4.894 | 5.047 | 6.557 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 4.648 | 3.338 | 4.750 | 5.252 | 6.935 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 4.653 | 3.304 | 4.766 | 5.271 | 6.901 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 4.774 | 3.410 | 4.905 | 5.390 | 6.951 | 1.00 |
| PWM-W (pure) | ours | 4.819 | 3.413 | 4.916 | 5.473 | 6.981 | 1.00 |
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
| PWM-W hybrid (uses global forecasts) | hybrid | 0.385 | 0.336 | 0.390 | 0.407 | 0.684 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.393 | 0.328 | 0.399 | 0.422 | 0.801 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 0.395 | 0.329 | 0.403 | 0.424 | 0.719 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 0.396 | 0.334 | 0.405 | 0.423 | 0.729 | 1.00 |
| PWM-W (pure) | ours | 0.414 | 0.346 | 0.424 | 0.444 | 0.737 | 1.00 |
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

## Verdicts against the global weather models

BEATS = significantly lower MAE than both the raw and the bias-corrected forecast. STRICT uses the latest run (often issued after our forecast start); ISSUED-BEFORE-START uses the newest run published before it.

- [STRICT] PWM-W (pure) vs DWD ICON (physics): AT BEATS (-55.6% / -25.7%); RH BEATS (-45.7% / -6.2%); WS BEATS (-48.7% / -29.2%)
- [STRICT] PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-52.6% / -22.3%); RH TIES / MIXED (-40.4% / -5.0%); WS BEATS (-63.3% / -45.5%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-54.3% / -25.5%); RH BEATS (-38.2% / -16.5%); WS BEATS (-63.0% / -45.1%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-55.7% / -32.3%); RH BEATS (-47.5% / -26.5%); WS BEATS (-59.9% / -42.2%)
- [STRICT] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-70.1% / -38.4%); RH BEATS (-84.2% / -42.1%); WS BEATS (-76.8% / -54.2%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics): AT BEATS (-60.8% / -33.3%); RH BEATS (-49.5% / -22.4%); WS BEATS (-54.3% / -34.9%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-54.7% / -27.7%); RH BEATS (-38.8% / -7.1%); WS BEATS (-67.5% / -50.2%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-59.6% / -33.6%); RH BEATS (-47.1% / -25.2%); WS BEATS (-62.5% / -45.1%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-66.2% / -49.3%); RH BEATS (-60.9% / -36.8%); WS BEATS (-69.6% / -56.2%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-73.2% / -46.3%); RH BEATS (-84.8% / -45.3%); WS BEATS (-77.2% / -55.9%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-57.2% / -28.4%); RH BEATS (-47.9% / -10.0%); WS BEATS (-52.3% / -34.2%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-54.3% / -25.1%); RH BEATS (-42.8% / -8.9%); WS BEATS (-65.9% / -49.3%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-55.9% / -28.1%); RH BEATS (-40.7% / -19.9%); WS BEATS (-65.6% / -48.9%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-57.3% / -34.7%); RH BEATS (-49.7% / -29.6%); WS BEATS (-62.8% / -46.3%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-71.1% / -40.6%); RH BEATS (-84.9% / -44.4%); WS BEATS (-78.5% / -57.5%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-62.2% / -35.7%); RH BEATS (-51.6% / -25.6%); WS BEATS (-57.5% / -39.5%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-56.4% / -30.3%); RH BEATS (-41.3% / -11.0%); WS BEATS (-69.8% / -53.7%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-61.0% / -36.0%); RH BEATS (-49.2% / -28.3%); WS BEATS (-65.2% / -48.9%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-65.9% / -48.8%); RH BEATS (-61.0% / -36.9%); WS BEATS (-70.6% / -57.6%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-74.2% / -48.3%); RH BEATS (-85.4% / -47.5%); WS BEATS (-78.8% / -59.0%)

## Models we ran ourselves (Earth2Studio, 00 UTC GFS start, +6/12/18 h)


Not tested: GenCast and WeatherNext (no public forecast archive; data needs a Google Cloud access request).

## Log

```
WX_CPCB: 17544 hours x 25 stations, targets ['AT', 'RH', 'WS'] (missing 2.9%, 3.5%, 19.6%), 5 other channels, spreads [3.609999895095825, 13.479999542236328, 0.9300000071525574], 184 graph links, 5 regions; splits {'train': ('2024-01-01T00', '2025-05-02T23'), 'val': ('2025-05-03T00', '2025-07-02T23'), 'test': ('2025-07-03T00', '2025-12-31T23')}
origins: train 11281, validation 241, test 725 (every 6 h); device cuda
joint-training partner WMO: 20 stations, 37515 origins ending before 2025-05-03T00; shared other channels ['WD_sin', 'WD_cos', 'P']; clock shift +6 h
variant P0 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1144 val MAE/spread 0.5142 (14s)
    step 1000/6000 loss 0.1273 val MAE/spread 0.5044 (25s)
    step 1500/6000 loss 0.1180 val MAE/spread 0.4968 (37s)
    step 2000/6000 loss 0.1096 val MAE/spread 0.4921 (48s)
    step 2500/6000 loss 0.1007 val MAE/spread 0.4940 (60s)
    step 3000/6000 loss 0.1012 val MAE/spread 0.4930 (71s)
    step 3500/6000 loss 0.0902 val MAE/spread 0.4905 (82s)
    step 4000/6000 loss 0.0894 val MAE/spread 0.4886 (94s)
    step 4500/6000 loss 0.0908 val MAE/spread 0.4916 (105s)
    step 5000/6000 loss 0.0863 val MAE/spread 0.4966 (116s)
    step 5500/6000 loss 0.0819 val MAE/spread 0.4973 (127s)
    step 6000/6000 loss 0.0828 val MAE/spread 0.4978 (139s)
variant P0 seed 1: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1304 val MAE/spread 0.5194 (11s)
    step 1000/6000 loss 0.1150 val MAE/spread 0.4979 (22s)
    step 1500/6000 loss 0.1256 val MAE/spread 0.4955 (33s)
    step 2000/6000 loss 0.1055 val MAE/spread 0.4991 (45s)
    step 2500/6000 loss 0.1132 val MAE/spread 0.5038 (56s)
    step 3000/6000 loss 0.0945 val MAE/spread 0.5050 (67s)
    step 3500/6000 loss 0.0888 val MAE/spread 0.4918 (78s)
    step 4000/6000 loss 0.0971 val MAE/spread 0.4936 (90s)
    step 4500/6000 loss 0.0857 val MAE/spread 0.4960 (101s)
    step 5000/6000 loss 0.0854 val MAE/spread 0.4969 (112s)
    step 5500/6000 loss 0.0814 val MAE/spread 0.4968 (123s)
    step 6000/6000 loss 0.0881 val MAE/spread 0.4941 (135s)
variant P0 seed 2: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1305 val MAE/spread 0.5206 (11s)
    step 1000/6000 loss 0.1212 val MAE/spread 0.5081 (22s)
    step 1500/6000 loss 0.1177 val MAE/spread 0.4963 (34s)
    step 2000/6000 loss 0.1221 val MAE/spread 0.5011 (45s)
    step 2500/6000 loss 0.1003 val MAE/spread 0.4997 (56s)
    step 3000/6000 loss 0.0941 val MAE/spread 0.4971 (67s)
    step 3500/6000 loss 0.0883 val MAE/spread 0.4988 (78s)
    step 4000/6000 loss 0.0969 val MAE/spread 0.4969 (89s)
    step 4500/6000 loss 0.1026 val MAE/spread 0.5003 (100s)
    step 5000/6000 loss 0.0880 val MAE/spread 0.4973 (111s)
    step 5500/6000 loss 0.0978 val MAE/spread 0.4989 (122s)
    step 6000/6000 loss 0.0848 val MAE/spread 0.5025 (133s)
variant P1 seed 0: {'d': 192, 'layers': 4, 'heads': 6, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1168 val MAE/spread 0.5249 (13s)
    step 1000/6000 loss 0.1276 val MAE/spread 0.5004 (27s)
    step 1500/6000 loss 0.1172 val MAE/spread 0.4929 (40s)
    step 2000/6000 loss 0.1085 val MAE/spread 0.4881 (54s)
    step 2500/6000 loss 0.1018 val MAE/spread 0.4823 (67s)
    step 3000/6000 loss 0.1004 val MAE/spread 0.4808 (80s)
    step 3500/6000 loss 0.0891 val MAE/spread 0.4797 (94s)
    step 4000/6000 loss 0.0898 val MAE/spread 0.4841 (107s)
    step 4500/6000 loss 0.0888 val MAE/spread 0.4854 (121s)
    step 5000/6000 loss 0.0836 val MAE/spread 0.4915 (134s)
    step 5500/6000 loss 0.0773 val MAE/spread 0.4878 (147s)
    step 6000/6000 loss 0.0788 val MAE/spread 0.4900 (161s)
variant P2 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': False}
    step 500/6000 loss 0.1162 val MAE/spread 0.5161 (7s)
    step 1000/6000 loss 0.1334 val MAE/spread 0.4964 (13s)
    step 1500/6000 loss 0.1243 val MAE/spread 0.4860 (20s)
    step 2000/6000 loss 0.1172 val MAE/spread 0.4903 (26s)
    step 2500/6000 loss 0.1082 val MAE/spread 0.4889 (33s)
    step 3000/6000 loss 0.1115 val MAE/spread 0.4870 (40s)
    step 3500/6000 loss 0.1010 val MAE/spread 0.4879 (46s)
    step 4000/6000 loss 0.1006 val MAE/spread 0.4902 (53s)
    step 4500/6000 loss 0.1056 val MAE/spread 0.4937 (59s)
    step 5000/6000 loss 0.0992 val MAE/spread 0.4948 (66s)
    step 5500/6000 loss 0.0918 val MAE/spread 0.4972 (72s)
    step 6000/6000 loss 0.0943 val MAE/spread 0.4993 (79s)
variant P3 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 4, 'use_graph': True}
    step 500/6000 loss 0.1474 val MAE/spread 0.5228 (23s)
    step 1000/6000 loss 0.1607 val MAE/spread 0.5015 (46s)
    step 1500/6000 loss 0.1486 val MAE/spread 0.5014 (69s)
    step 2000/6000 loss 0.1427 val MAE/spread 0.4970 (92s)
    step 2500/6000 loss 0.1333 val MAE/spread 0.4987 (115s)
    step 3000/6000 loss 0.1359 val MAE/spread 0.5022 (137s)
    step 3500/6000 loss 0.1215 val MAE/spread 0.4856 (160s)
    step 4000/6000 loss 0.1240 val MAE/spread 0.4904 (183s)
    step 4500/6000 loss 0.1244 val MAE/spread 0.4934 (206s)
    step 5000/6000 loss 0.1175 val MAE/spread 0.4989 (229s)
    step 5500/6000 loss 0.1124 val MAE/spread 0.4964 (252s)
    step 6000/6000 loss 0.1152 val MAE/spread 0.4987 (275s)
variant P4 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True}
    step 500/6000 loss 0.1520 val MAE/spread 0.5218 (11s)
    step 1000/6000 loss 0.1505 val MAE/spread 0.4964 (22s)
    step 1500/6000 loss 0.1489 val MAE/spread 0.4862 (34s)
    step 2000/6000 loss 0.1187 val MAE/spread 0.4810 (45s)
    step 2500/6000 loss 0.1109 val MAE/spread 0.4847 (56s)
    step 3000/6000 loss 0.1416 val MAE/spread 0.4843 (67s)
    step 3500/6000 loss 0.1082 val MAE/spread 0.4755 (78s)
    step 4000/6000 loss 0.1143 val MAE/spread 0.4735 (89s)
    step 4500/6000 loss 0.1436 val MAE/spread 0.4825 (100s)
    step 5000/6000 loss 0.1401 val MAE/spread 0.4799 (111s)
    step 5500/6000 loss 0.1340 val MAE/spread 0.4743 (122s)
    step 6000/6000 loss 0.1330 val MAE/spread 0.4821 (134s)
variant P5 seed 0: {'d': 192, 'layers': 4, 'heads': 6, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True}
    step 500/6000 loss 0.1519 val MAE/spread 0.5181 (14s)
    step 1000/6000 loss 0.1510 val MAE/spread 0.4952 (27s)
    step 1500/6000 loss 0.1490 val MAE/spread 0.4866 (41s)
    step 2000/6000 loss 0.1173 val MAE/spread 0.4843 (54s)
    step 2500/6000 loss 0.1081 val MAE/spread 0.4824 (68s)
    step 3000/6000 loss 0.1405 val MAE/spread 0.4984 (82s)
    step 3500/6000 loss 0.1071 val MAE/spread 0.4859 (95s)
    step 4000/6000 loss 0.1168 val MAE/spread 0.4774 (109s)
    step 4500/6000 loss 0.1414 val MAE/spread 0.4859 (123s)
    step 5000/6000 loss 0.1413 val MAE/spread 0.4826 (136s)
    step 5500/6000 loss 0.1335 val MAE/spread 0.4788 (150s)
    step 6000/6000 loss 0.1323 val MAE/spread 0.4837 (163s)
validation (MAE / spread): P0 0.4922 +- 0.0038; P1 0.4797, P2 0.4860, P3 0.4856, P4 0.4735, P5 0.4774 -> chosen P4
    step 500/6000 loss 0.1550 val MAE/spread 0.5240 (11s)
    step 1000/6000 loss 0.1211 val MAE/spread 0.5021 (22s)
    step 1500/6000 loss 0.1375 val MAE/spread 0.4881 (34s)
    step 2000/6000 loss 0.1318 val MAE/spread 0.4811 (45s)
    step 2500/6000 loss 0.1014 val MAE/spread 0.4796 (56s)
    step 3000/6000 loss 0.1091 val MAE/spread 0.4804 (67s)
    step 3500/6000 loss 0.1135 val MAE/spread 0.4751 (78s)
    step 4000/6000 loss 0.1450 val MAE/spread 0.4816 (89s)
    step 4500/6000 loss 0.1373 val MAE/spread 0.4905 (101s)
    step 5000/6000 loss 0.1444 val MAE/spread 0.4737 (112s)
    step 5500/6000 loss 0.1401 val MAE/spread 0.4764 (123s)
    step 6000/6000 loss 0.0903 val MAE/spread 0.4802 (134s)
    step 500/6000 loss 0.1170 val MAE/spread 0.5232 (11s)
    step 1000/6000 loss 0.1490 val MAE/spread 0.4989 (23s)
    step 1500/6000 loss 0.1475 val MAE/spread 0.4891 (34s)
    step 2000/6000 loss 0.1210 val MAE/spread 0.4827 (45s)
    step 2500/6000 loss 0.1459 val MAE/spread 0.4816 (56s)
    step 3000/6000 loss 0.1051 val MAE/spread 0.4831 (67s)
    step 3500/6000 loss 0.1517 val MAE/spread 0.4858 (79s)
    step 4000/6000 loss 0.1004 val MAE/spread 0.4848 (90s)
    step 4500/6000 loss 0.0993 val MAE/spread 0.4812 (101s)
    step 5000/6000 loss 0.1309 val MAE/spread 0.4844 (112s)
    step 5500/6000 loss 0.0961 val MAE/spread 0.4853 (124s)
    step 6000/6000 loss 0.1429 val MAE/spread 0.4893 (135s)
    step 500/6000 loss 0.1228 val MAE/spread 0.5160 (11s)
    step 1000/6000 loss 0.1141 val MAE/spread 0.4986 (22s)
    step 1500/6000 loss 0.1509 val MAE/spread 0.4848 (34s)
    step 2000/6000 loss 0.1366 val MAE/spread 0.4826 (45s)
    step 2500/6000 loss 0.1079 val MAE/spread 0.4771 (56s)
    step 3000/6000 loss 0.1095 val MAE/spread 0.4816 (67s)
    step 3500/6000 loss 0.0962 val MAE/spread 0.4894 (79s)
    step 4000/6000 loss 0.0999 val MAE/spread 0.4774 (90s)
    step 4500/6000 loss 0.1493 val MAE/spread 0.4785 (101s)
    step 5000/6000 loss 0.0967 val MAE/spread 0.4770 (112s)
    step 5500/6000 loss 0.0980 val MAE/spread 0.4781 (124s)
    step 6000/6000 loss 0.1029 val MAE/spread 0.4807 (135s)
    rolling update 1/9: 11281 training origins (697 recent), 34s
    rolling update 5/9: 11930 training origins (674 recent), 168s
rolling validation (ensemble MAE / spread): frozen 0.4650, weekly updates 0.4727 (2 sigma = 0.0077) -> not adopted
hybrid: 12 global-forecast channels from ['ECMWF IFS 0.25 (physics)', 'ECMWF AIFS (AI)', 'DWD ICON (physics)', 'NOAA GFS (physics)'], 11281 training origins from 2024
    step 500/6000 loss 0.1091 val MAE/spread 0.5011 (12s)
    step 1000/6000 loss 0.1144 val MAE/spread 0.4730 (23s)
    step 1500/6000 loss 0.1030 val MAE/spread 0.4700 (35s)
    step 2000/6000 loss 0.1001 val MAE/spread 0.4586 (46s)
    step 2500/6000 loss 0.0915 val MAE/spread 0.4600 (58s)
    step 3000/6000 loss 0.0919 val MAE/spread 0.4644 (69s)
    step 3500/6000 loss 0.0813 val MAE/spread 0.4594 (81s)
    step 4000/6000 loss 0.0823 val MAE/spread 0.4654 (92s)
    step 4500/6000 loss 0.0842 val MAE/spread 0.4641 (104s)
    step 5000/6000 loss 0.0776 val MAE/spread 0.4684 (115s)
    step 5500/6000 loss 0.0739 val MAE/spread 0.4662 (127s)
    step 6000/6000 loss 0.0749 val MAE/spread 0.4691 (138s)
    step 500/6000 loss 0.1134 val MAE/spread 0.4826 (12s)
    step 1000/6000 loss 0.1152 val MAE/spread 0.4788 (23s)
    step 1500/6000 loss 0.1010 val MAE/spread 0.4804 (35s)
    step 2000/6000 loss 0.0991 val MAE/spread 0.4898 (47s)
    step 2500/6000 loss 0.0966 val MAE/spread 0.4873 (59s)
    step 3000/6000 loss 0.0911 val MAE/spread 0.4829 (70s)
    step 3500/6000 loss 0.0827 val MAE/spread 0.4896 (82s)
    step 4000/6000 loss 0.0793 val MAE/spread 0.4879 (93s)
    step 4500/6000 loss 0.0803 val MAE/spread 0.4912 (105s)
    step 5000/6000 loss 0.0772 val MAE/spread 0.4932 (117s)
    step 5500/6000 loss 0.0762 val MAE/spread 0.4938 (128s)
    step 6000/6000 loss 0.0788 val MAE/spread 0.4957 (140s)
    step 500/6000 loss 0.1102 val MAE/spread 0.5069 (12s)
    step 1000/6000 loss 0.1137 val MAE/spread 0.4932 (23s)
    step 1500/6000 loss 0.1002 val MAE/spread 0.5192 (35s)
    step 2000/6000 loss 0.0973 val MAE/spread 0.5406 (46s)
    step 2500/6000 loss 0.0958 val MAE/spread 0.5309 (58s)
    step 3000/6000 loss 0.0908 val MAE/spread 0.5662 (70s)
    step 3500/6000 loss 0.0804 val MAE/spread 0.5560 (81s)
    step 4000/6000 loss 0.0781 val MAE/spread 0.5768 (93s)
    step 4500/6000 loss 0.0788 val MAE/spread 0.5677 (104s)
    step 5000/6000 loss 0.0761 val MAE/spread 0.5652 (116s)
    step 5500/6000 loss 0.0757 val MAE/spread 0.5849 (128s)
    step 6000/6000 loss 0.0780 val MAE/spread 0.5845 (139s)
hybrid validation: H1 0.4586, H2 0.4788, H3 0.4932 (2 sigma = 0.0077) -> H1
    step 500/6000 loss 0.1224 val MAE/spread 0.4983 (11s)
    step 1000/6000 loss 0.1055 val MAE/spread 0.4774 (23s)
    step 1500/6000 loss 0.0979 val MAE/spread 0.4625 (35s)
    step 2000/6000 loss 0.0966 val MAE/spread 0.4576 (46s)
    step 2500/6000 loss 0.0852 val MAE/spread 0.4658 (58s)
    step 3000/6000 loss 0.0869 val MAE/spread 0.4684 (69s)
    step 3500/6000 loss 0.0783 val MAE/spread 0.4686 (81s)
    step 4000/6000 loss 0.0809 val MAE/spread 0.4728 (92s)
    step 4500/6000 loss 0.0857 val MAE/spread 0.4757 (104s)
    step 5000/6000 loss 0.0823 val MAE/spread 0.4833 (115s)
    step 5500/6000 loss 0.0828 val MAE/spread 0.4817 (127s)
    step 6000/6000 loss 0.0767 val MAE/spread 0.4802 (138s)
    step 500/6000 loss 0.1178 val MAE/spread 0.4997 (12s)
    step 1000/6000 loss 0.1111 val MAE/spread 0.4730 (23s)
    step 1500/6000 loss 0.0989 val MAE/spread 0.4630 (34s)
    step 2000/6000 loss 0.0971 val MAE/spread 0.4583 (46s)
    step 2500/6000 loss 0.0955 val MAE/spread 0.4591 (57s)
    step 3000/6000 loss 0.0823 val MAE/spread 0.4612 (69s)
    step 3500/6000 loss 0.0905 val MAE/spread 0.4586 (80s)
    step 4000/6000 loss 0.0834 val MAE/spread 0.4632 (92s)
    step 4500/6000 loss 0.0776 val MAE/spread 0.4650 (103s)
    step 5000/6000 loss 0.0834 val MAE/spread 0.4664 (115s)
    step 5500/6000 loss 0.0812 val MAE/spread 0.4688 (126s)
    step 6000/6000 loss 0.0808 val MAE/spread 0.4694 (138s)
    step 500/6000 loss 0.1182 val MAE/spread 0.4942 (11s)
    step 1000/6000 loss 0.1089 val MAE/spread 0.4780 (23s)
    step 1500/6000 loss 0.0989 val MAE/spread 0.4655 (34s)
    step 2000/6000 loss 0.0907 val MAE/spread 0.4708 (46s)
    step 2500/6000 loss 0.0940 val MAE/spread 0.4573 (58s)
    step 3000/6000 loss 0.0839 val MAE/spread 0.4613 (69s)
    step 3500/6000 loss 0.0803 val MAE/spread 0.4752 (80s)
    step 4000/6000 loss 0.0833 val MAE/spread 0.4757 (92s)
    step 4500/6000 loss 0.0814 val MAE/spread 0.4783 (104s)
    step 5000/6000 loss 0.0793 val MAE/spread 0.4761 (115s)
    step 5500/6000 loss 0.0765 val MAE/spread 0.4794 (127s)
    step 6000/6000 loss 0.0821 val MAE/spread 0.4823 (139s)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -55.6% vs raw, -25.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -60.8% vs raw, -33.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on RH: BEATS (MAE -45.7% vs raw, -6.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on RH: BEATS (MAE -49.5% vs raw, -22.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -48.7% vs raw, -29.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -54.3% vs raw, -34.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -52.6% vs raw, -22.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -54.7% vs raw, -27.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on RH: TIES / MIXED (MAE -40.4% vs raw, -5.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on RH: BEATS (MAE -38.8% vs raw, -7.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -63.3% vs raw, -45.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -67.5% vs raw, -50.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -54.3% vs raw, -25.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -59.6% vs raw, -33.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -38.2% vs raw, -16.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -47.1% vs raw, -25.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -63.0% vs raw, -45.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -62.5% vs raw, -45.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -55.7% vs raw, -32.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -66.2% vs raw, -49.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -47.5% vs raw, -26.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -60.9% vs raw, -36.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -59.9% vs raw, -42.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -69.6% vs raw, -56.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -70.1% vs raw, -38.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -73.2% vs raw, -46.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -84.2% vs raw, -42.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -84.8% vs raw, -45.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -76.8% vs raw, -54.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -77.2% vs raw, -55.9% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on AT: LOSS (MAE +3.7%, p=0.036, 95% CI +0.7..+7.2%)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on RH: LOSS (MAE +4.3%, p=0.03, 95% CI +0.7..+8.1%)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on WS: LOSS (MAE +7.6%, p=5e-07, 95% CI +5.2..+10.4%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -17.6%, p=7.2e-19, 95% CI -20.6..-14.4%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -16.5%, p=6.8e-23, 95% CI -19.4..-13.6%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -15.8%, p=1.6e-27, 95% CI -18.3..-13.4%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -38.1%, p=5.8e-15, 95% CI -43.7..-32.4%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -28.0%, p=1e-18, 95% CI -32.4..-23.3%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -12.4%, p=5.5e-14, 95% CI -15.1..-9.8%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on AT: WIN (MAE -14.8%, p=8.7e-09, 95% CI -18.5..-10.6%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on RH: WIN (MAE -15.7%, p=2e-12, 95% CI -19.3..-12.4%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on WS: WIN (MAE -17.1%, p=5.1e-13, 95% CI -20.6..-13.7%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -27.6%, p=2e-14, 95% CI -32.9..-21.8%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -11.3%, p=0.00064, 95% CI -16.7..-5.2%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -37.9%, p=5.5e-68, 95% CI -41.0..-34.8%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on AT: LOSS (MAE +6.8%, p=1.8e-05, 95% CI +3.8..+10.1%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on RH: LOSS (MAE +3.7%, p=0.0095, 95% CI +0.8..+6.5%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on WS: LOSS (MAE +4.9%, p=7.4e-06, 95% CI +2.8..+7.1%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on AT: TIE (MAE +0.7%, p=0.67, 95% CI -2.3..+4.0%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on RH: TIE (MAE +0.9%, p=0.53, 95% CI -2.0..+3.7%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on WS: LOSS (MAE +4.6%, p=4.8e-07, 95% CI +2.6..+6.5%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on AT: LOSS (MAE +4.3%, p=0.0097, 95% CI +1.1..+7.6%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on RH: LOSS (MAE +3.6%, p=0.0097, 95% CI +0.8..+6.2%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on WS: LOSS (MAE +5.5%, p=4e-05, 95% CI +2.4..+8.0%)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -57.2% vs raw, -28.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -62.2% vs raw, -35.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -47.9% vs raw, -10.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -51.6% vs raw, -25.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -52.3% vs raw, -34.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -57.5% vs raw, -39.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -54.3% vs raw, -25.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -56.4% vs raw, -30.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -42.8% vs raw, -8.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -41.3% vs raw, -11.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -65.9% vs raw, -49.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -69.8% vs raw, -53.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -55.9% vs raw, -28.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -61.0% vs raw, -36.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -40.7% vs raw, -19.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -49.2% vs raw, -28.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -65.6% vs raw, -48.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -65.2% vs raw, -48.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -57.3% vs raw, -34.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -65.9% vs raw, -48.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -49.7% vs raw, -29.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -61.0% vs raw, -36.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -62.8% vs raw, -46.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -70.6% vs raw, -57.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -71.1% vs raw, -40.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -74.2% vs raw, -48.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -84.9% vs raw, -44.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -85.4% vs raw, -47.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -78.5% vs raw, -57.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -78.8% vs raw, -59.0% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on AT: WIN (MAE -3.6%, p=0.036, 95% CI -6.7..-0.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on RH: WIN (MAE -4.1%, p=0.03, 95% CI -7.5..-0.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on WS: WIN (MAE -7.1%, p=5e-07, 95% CI -9.4..-5.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -20.5%, p=4.7e-28, 95% CI -23.2..-17.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -19.9%, p=1e-38, 95% CI -22.5..-17.6%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -21.8%, p=1.9e-43, 95% CI -23.8..-20.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -40.3%, p=1.7e-17, 95% CI -45.5..-35.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -31.0%, p=2.2e-26, 95% CI -34.8..-27.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -18.6%, p=6.1e-21, 95% CI -21.3..-16.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on AT: WIN (MAE -17.8%, p=1.5e-09, 95% CI -21.9..-13.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on RH: WIN (MAE -19.1%, p=1.1e-12, 95% CI -23.2..-15.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on WS: WIN (MAE -23.4%, p=4.9e-18, 95% CI -26.8..-20.3%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -30.2%, p=5.4e-23, 95% CI -34.7..-25.6%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -14.9%, p=1.3e-08, 95% CI -19.2..-10.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -42.3%, p=5.1e-78, 95% CI -44.9..-39.8%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on AT: TIE (MAE +3.0%, p=0.1, 95% CI -0.5..+6.8%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on RH: TIE (MAE -0.6%, p=0.74, 95% CI -4.1..+2.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on WS: TIE (MAE -2.5%, p=0.11, 95% CI -5.1..+0.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on AT: TIE (MAE -2.9%, p=0.12, 95% CI -6.3..+0.6%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on RH: TIE (MAE -3.2%, p=0.07, 95% CI -6.6..-0.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on WS: TIE (MAE -2.8%, p=0.077, 95% CI -5.7..-0.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on AT: TIE (MAE +0.6%, p=0.77, 95% CI -3.0..+4.3%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on RH: TIE (MAE -0.7%, p=0.68, 95% CI -4.1..+2.4%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on WS: TIE (MAE -1.9%, p=0.32, 95% CI -5.6..+1.0%)
no Earth-2 runs found (E2 file missing)
no Earth-2 runs found (E2 file missing)
```