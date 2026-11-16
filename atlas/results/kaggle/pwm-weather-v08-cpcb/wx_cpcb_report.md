# PWM-W v0.3 weather league: CPCB

Stations: 25. Chosen setting: P8 (validation only). Test origins every 6 h, 24 h ahead.

## AT (deg C)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| Chronos-2 (Amazon, 120M) | tsfm | 0.862 | 0.619 | 0.890 | 0.969 | 1.469 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.883 | 0.623 | 0.909 | 0.999 | 1.488 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 0.892 | 0.666 | 0.960 | 0.971 | 1.465 | 1.00 |
| PWM-W (pure) | ours | 0.905 | 0.645 | 0.949 | 1.013 | 1.505 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 0.914 | 0.645 | 0.943 | 1.034 | 1.505 | 1.00 |
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
| PWM-W hybrid (uses global forecasts) | hybrid | 4.621 | 3.472 | 4.890 | 5.061 | 6.559 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 4.648 | 3.338 | 4.750 | 5.252 | 6.935 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 4.653 | 3.304 | 4.766 | 5.271 | 6.901 | 1.00 |
| PWM-W (pure) | ours | 4.712 | 3.438 | 4.845 | 5.283 | 6.837 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 4.774 | 3.410 | 4.905 | 5.390 | 6.951 | 1.00 |
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
| PWM-W hybrid (uses global forecasts) | hybrid | 0.382 | 0.335 | 0.389 | 0.402 | 0.684 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.393 | 0.328 | 0.399 | 0.422 | 0.801 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 0.395 | 0.329 | 0.403 | 0.424 | 0.719 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 0.396 | 0.334 | 0.405 | 0.423 | 0.729 | 1.00 |
| PWM-W (pure) | ours | 0.410 | 0.348 | 0.419 | 0.437 | 0.732 | 1.00 |
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

- [STRICT] PWM-W (pure) vs DWD ICON (physics): AT BEATS (-56.4% / -27.0%); RH BEATS (-46.9% / -8.3%); WS BEATS (-49.2% / -30.0%)
- [STRICT] PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-53.4% / -23.7%); RH BEATS (-41.7% / -7.1%); WS BEATS (-63.7% / -46.1%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-55.1% / -26.8%); RH BEATS (-39.6% / -18.4%); WS BEATS (-63.4% / -45.7%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-56.5% / -33.4%); RH BEATS (-48.7% / -28.2%); WS BEATS (-60.4% / -42.8%)
- [STRICT] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-70.6% / -39.5%); RH BEATS (-84.6% / -43.3%); WS BEATS (-77.1% / -54.7%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics): AT BEATS (-61.5% / -34.4%); RH BEATS (-50.6% / -24.1%); WS BEATS (-54.8% / -35.6%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-55.5% / -28.9%); RH BEATS (-40.1% / -9.2%); WS BEATS (-67.9% / -50.8%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-60.3% / -34.8%); RH BEATS (-48.2% / -26.9%); WS BEATS (-62.9% / -45.6%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-66.2% / -49.3%); RH BEATS (-61.1% / -37.1%); WS BEATS (-70.1% / -56.8%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-73.7% / -47.3%); RH BEATS (-85.2% / -46.5%); WS BEATS (-77.4% / -56.3%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-57.0% / -28.0%); RH BEATS (-47.9% / -10.0%); WS BEATS (-52.7% / -34.8%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-54.1% / -24.8%); RH BEATS (-42.8% / -8.9%); WS BEATS (-66.2% / -49.8%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-55.7% / -27.8%); RH BEATS (-40.7% / -19.9%); WS BEATS (-65.9% / -49.4%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-57.1% / -34.4%); RH BEATS (-49.6% / -29.6%); WS BEATS (-63.1% / -46.7%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-71.0% / -40.4%); RH BEATS (-84.9% / -44.4%); WS BEATS (-78.6% / -57.8%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-62.0% / -35.4%); RH BEATS (-51.6% / -25.6%); WS BEATS (-57.9% / -40.0%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-56.2% / -29.9%); RH BEATS (-41.3% / -10.9%); WS BEATS (-70.1% / -54.1%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-60.9% / -35.7%); RH BEATS (-49.2% / -28.3%); WS BEATS (-65.5% / -49.4%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-65.0% / -47.5%); RH BEATS (-60.9% / -36.8%); WS BEATS (-70.9% / -58.0%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-74.0% / -48.0%); RH BEATS (-85.4% / -47.5%); WS BEATS (-79.0% / -59.3%)

## Models we ran ourselves (Earth2Studio, 00 UTC GFS start, +6/12/18 h)


Not tested: GenCast and WeatherNext (no public forecast archive; data needs a Google Cloud access request).

## Log

```
WX_CPCB: 17544 hours x 25 stations, targets ['AT', 'RH', 'WS'] (missing 2.9%, 3.5%, 19.6%), 5 other channels, spreads [3.609999895095825, 13.479999542236328, 0.9300000071525574], 184 graph links, 5 regions; splits {'train': ('2024-01-01T00', '2025-05-02T23'), 'val': ('2025-05-03T00', '2025-07-02T23'), 'test': ('2025-07-03T00', '2025-12-31T23')}
origins: train 11281, validation 241, test 725 (every 6 h); device cuda
joint-training partner WMO: 20 stations, 37515 origins ending before 2025-05-03T00; shared other channels ['WD_sin', 'WD_cos', 'P']; clock shift +6 h
variant P0 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1144 val MAE/spread 0.5142 (15s)
    step 1000/6000 loss 0.1273 val MAE/spread 0.5044 (28s)
    step 1500/6000 loss 0.1180 val MAE/spread 0.4968 (41s)
    step 2000/6000 loss 0.1096 val MAE/spread 0.4921 (54s)
    step 2500/6000 loss 0.1007 val MAE/spread 0.4940 (67s)
    step 3000/6000 loss 0.1012 val MAE/spread 0.4930 (80s)
    step 3500/6000 loss 0.0902 val MAE/spread 0.4905 (93s)
    step 4000/6000 loss 0.0894 val MAE/spread 0.4886 (106s)
    step 4500/6000 loss 0.0908 val MAE/spread 0.4916 (119s)
    step 5000/6000 loss 0.0863 val MAE/spread 0.4966 (132s)
    step 5500/6000 loss 0.0819 val MAE/spread 0.4973 (145s)
    step 6000/6000 loss 0.0828 val MAE/spread 0.4978 (158s)
variant P0 seed 1: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1304 val MAE/spread 0.5194 (13s)
    step 1000/6000 loss 0.1150 val MAE/spread 0.4979 (26s)
    step 1500/6000 loss 0.1256 val MAE/spread 0.4955 (39s)
    step 2000/6000 loss 0.1055 val MAE/spread 0.4991 (52s)
    step 2500/6000 loss 0.1132 val MAE/spread 0.5038 (64s)
    step 3000/6000 loss 0.0945 val MAE/spread 0.5050 (77s)
    step 3500/6000 loss 0.0888 val MAE/spread 0.4918 (90s)
    step 4000/6000 loss 0.0971 val MAE/spread 0.4936 (103s)
    step 4500/6000 loss 0.0857 val MAE/spread 0.4960 (116s)
    step 5000/6000 loss 0.0854 val MAE/spread 0.4969 (129s)
    step 5500/6000 loss 0.0814 val MAE/spread 0.4968 (141s)
    step 6000/6000 loss 0.0881 val MAE/spread 0.4941 (154s)
variant P0 seed 2: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1305 val MAE/spread 0.5206 (13s)
    step 1000/6000 loss 0.1212 val MAE/spread 0.5081 (26s)
    step 1500/6000 loss 0.1177 val MAE/spread 0.4963 (38s)
    step 2000/6000 loss 0.1221 val MAE/spread 0.5011 (51s)
    step 2500/6000 loss 0.1003 val MAE/spread 0.4997 (64s)
    step 3000/6000 loss 0.0941 val MAE/spread 0.4971 (77s)
    step 3500/6000 loss 0.0883 val MAE/spread 0.4988 (90s)
    step 4000/6000 loss 0.0969 val MAE/spread 0.4969 (103s)
    step 4500/6000 loss 0.1026 val MAE/spread 0.5003 (115s)
    step 5000/6000 loss 0.0880 val MAE/spread 0.4973 (128s)
    step 5500/6000 loss 0.0978 val MAE/spread 0.4989 (141s)
    step 6000/6000 loss 0.0848 val MAE/spread 0.5025 (154s)
variant P1 seed 0: {'d': 192, 'layers': 4, 'heads': 6, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1168 val MAE/spread 0.5249 (16s)
    step 1000/6000 loss 0.1276 val MAE/spread 0.5004 (31s)
    step 1500/6000 loss 0.1172 val MAE/spread 0.4929 (45s)
    step 2000/6000 loss 0.1085 val MAE/spread 0.4881 (59s)
    step 2500/6000 loss 0.1018 val MAE/spread 0.4823 (73s)
    step 3000/6000 loss 0.1004 val MAE/spread 0.4808 (87s)
    step 3500/6000 loss 0.0891 val MAE/spread 0.4797 (101s)
    step 4000/6000 loss 0.0898 val MAE/spread 0.4841 (116s)
    step 4500/6000 loss 0.0888 val MAE/spread 0.4854 (130s)
    step 5000/6000 loss 0.0836 val MAE/spread 0.4915 (144s)
    step 5500/6000 loss 0.0773 val MAE/spread 0.4878 (159s)
    step 6000/6000 loss 0.0788 val MAE/spread 0.4900 (174s)
variant P2 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': False}
    step 500/6000 loss 0.1162 val MAE/spread 0.5161 (8s)
    step 1000/6000 loss 0.1334 val MAE/spread 0.4964 (15s)
    step 1500/6000 loss 0.1243 val MAE/spread 0.4860 (23s)
    step 2000/6000 loss 0.1172 val MAE/spread 0.4903 (31s)
    step 2500/6000 loss 0.1082 val MAE/spread 0.4889 (39s)
    step 3000/6000 loss 0.1115 val MAE/spread 0.4870 (47s)
    step 3500/6000 loss 0.1010 val MAE/spread 0.4879 (54s)
    step 4000/6000 loss 0.1006 val MAE/spread 0.4902 (62s)
    step 4500/6000 loss 0.1056 val MAE/spread 0.4937 (70s)
    step 5000/6000 loss 0.0992 val MAE/spread 0.4948 (78s)
    step 5500/6000 loss 0.0918 val MAE/spread 0.4972 (85s)
    step 6000/6000 loss 0.0943 val MAE/spread 0.4993 (93s)
variant P3 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 4, 'use_graph': True}
    step 500/6000 loss 0.1474 val MAE/spread 0.5228 (26s)
    step 1000/6000 loss 0.1607 val MAE/spread 0.5015 (53s)
    step 1500/6000 loss 0.1486 val MAE/spread 0.5014 (78s)
    step 2000/6000 loss 0.1427 val MAE/spread 0.4970 (105s)
    step 2500/6000 loss 0.1333 val MAE/spread 0.4987 (131s)
    step 3000/6000 loss 0.1359 val MAE/spread 0.5022 (157s)
    step 3500/6000 loss 0.1215 val MAE/spread 0.4856 (183s)
    step 4000/6000 loss 0.1240 val MAE/spread 0.4904 (209s)
    step 4500/6000 loss 0.1244 val MAE/spread 0.4934 (235s)
    step 5000/6000 loss 0.1175 val MAE/spread 0.4989 (262s)
    step 5500/6000 loss 0.1124 val MAE/spread 0.4964 (287s)
    step 6000/6000 loss 0.1152 val MAE/spread 0.4987 (313s)
variant P4 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True}
    step 500/6000 loss 0.1520 val MAE/spread 0.5218 (13s)
    step 1000/6000 loss 0.1505 val MAE/spread 0.4964 (26s)
    step 1500/6000 loss 0.1489 val MAE/spread 0.4862 (39s)
    step 2000/6000 loss 0.1187 val MAE/spread 0.4810 (52s)
    step 2500/6000 loss 0.1109 val MAE/spread 0.4847 (65s)
    step 3000/6000 loss 0.1416 val MAE/spread 0.4843 (78s)
    step 3500/6000 loss 0.1082 val MAE/spread 0.4755 (91s)
    step 4000/6000 loss 0.1143 val MAE/spread 0.4735 (104s)
    step 4500/6000 loss 0.1436 val MAE/spread 0.4825 (117s)
    step 5000/6000 loss 0.1401 val MAE/spread 0.4799 (130s)
    step 5500/6000 loss 0.1340 val MAE/spread 0.4743 (143s)
    step 6000/6000 loss 0.1330 val MAE/spread 0.4821 (156s)
variant P5 seed 0: {'d': 192, 'layers': 4, 'heads': 6, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True}
    step 500/6000 loss 0.1519 val MAE/spread 0.5181 (16s)
    step 1000/6000 loss 0.1510 val MAE/spread 0.4952 (32s)
    step 1500/6000 loss 0.1490 val MAE/spread 0.4866 (47s)
    step 2000/6000 loss 0.1173 val MAE/spread 0.4843 (63s)
    step 2500/6000 loss 0.1081 val MAE/spread 0.4824 (79s)
    step 3000/6000 loss 0.1405 val MAE/spread 0.4984 (95s)
    step 3500/6000 loss 0.1071 val MAE/spread 0.4859 (110s)
    step 4000/6000 loss 0.1168 val MAE/spread 0.4774 (126s)
    step 4500/6000 loss 0.1414 val MAE/spread 0.4859 (142s)
    step 5000/6000 loss 0.1413 val MAE/spread 0.4826 (158s)
    step 5500/6000 loss 0.1335 val MAE/spread 0.4788 (174s)
    step 6000/6000 loss 0.1323 val MAE/spread 0.4837 (189s)
variant P6 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'longctx': True}
    step 500/6000 loss 0.1524 val MAE/spread 0.5185 (14s)
    step 1000/6000 loss 0.1502 val MAE/spread 0.4925 (28s)
    step 1500/6000 loss 0.1490 val MAE/spread 0.4850 (42s)
    step 2000/6000 loss 0.1183 val MAE/spread 0.4789 (56s)
    step 2500/6000 loss 0.1081 val MAE/spread 0.4775 (70s)
    step 3000/6000 loss 0.1366 val MAE/spread 0.4762 (84s)
    step 3500/6000 loss 0.1077 val MAE/spread 0.4748 (97s)
    step 4000/6000 loss 0.1136 val MAE/spread 0.4714 (111s)
    step 4500/6000 loss 0.1371 val MAE/spread 0.4762 (124s)
    step 5000/6000 loss 0.1343 val MAE/spread 0.4722 (138s)
    step 5500/6000 loss 0.1299 val MAE/spread 0.4739 (152s)
    step 6000/6000 loss 0.1294 val MAE/spread 0.4777 (166s)
variant P7 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'ema': True}
    step 500/6000 loss 0.1520 val MAE/spread 0.5198 (14s)
    step 1000/6000 loss 0.1505 val MAE/spread 0.4937 (29s)
    step 1500/6000 loss 0.1489 val MAE/spread 0.4817 (43s)
    step 2000/6000 loss 0.1187 val MAE/spread 0.4766 (57s)
    step 2500/6000 loss 0.1109 val MAE/spread 0.4729 (71s)
    step 3000/6000 loss 0.1416 val MAE/spread 0.4736 (86s)
    step 3500/6000 loss 0.1082 val MAE/spread 0.4721 (100s)
    step 4000/6000 loss 0.1143 val MAE/spread 0.4730 (115s)
    step 4500/6000 loss 0.1436 val MAE/spread 0.4743 (130s)
    step 5000/6000 loss 0.1401 val MAE/spread 0.4761 (144s)
    step 5500/6000 loss 0.1340 val MAE/spread 0.4768 (158s)
    step 6000/6000 loss 0.1330 val MAE/spread 0.4783 (171s)
variant P8 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'longctx': True, 'ema': True}
    step 500/6000 loss 0.1524 val MAE/spread 0.5216 (14s)
    step 1000/6000 loss 0.1502 val MAE/spread 0.4917 (28s)
    step 1500/6000 loss 0.1490 val MAE/spread 0.4776 (42s)
    step 2000/6000 loss 0.1183 val MAE/spread 0.4735 (56s)
    step 2500/6000 loss 0.1081 val MAE/spread 0.4694 (70s)
    step 3000/6000 loss 0.1366 val MAE/spread 0.4702 (84s)
    step 3500/6000 loss 0.1077 val MAE/spread 0.4678 (98s)
    step 4000/6000 loss 0.1136 val MAE/spread 0.4689 (113s)
    step 4500/6000 loss 0.1371 val MAE/spread 0.4684 (128s)
    step 5000/6000 loss 0.1343 val MAE/spread 0.4706 (144s)
    step 5500/6000 loss 0.1299 val MAE/spread 0.4733 (159s)
    step 6000/6000 loss 0.1294 val MAE/spread 0.4747 (174s)
validation (MAE / spread): P0 0.4922 +- 0.0038; P1 0.4797, P2 0.4860, P3 0.4856, P4 0.4735, P5 0.4774, P6 0.4714, P7 0.4721, P8 0.4678 -> chosen P8
    step 500/6000 loss 0.1511 val MAE/spread 0.5174 (15s)
    step 1000/6000 loss 0.1169 val MAE/spread 0.4879 (31s)
    step 1500/6000 loss 0.1318 val MAE/spread 0.4780 (47s)
    step 2000/6000 loss 0.1247 val MAE/spread 0.4725 (62s)
    step 2500/6000 loss 0.0966 val MAE/spread 0.4706 (78s)
    step 3000/6000 loss 0.1053 val MAE/spread 0.4685 (94s)
    step 3500/6000 loss 0.1057 val MAE/spread 0.4684 (109s)
    step 4000/6000 loss 0.1358 val MAE/spread 0.4700 (125s)
    step 4500/6000 loss 0.1300 val MAE/spread 0.4739 (141s)
    step 5000/6000 loss 0.1381 val MAE/spread 0.4757 (155s)
    step 5500/6000 loss 0.1330 val MAE/spread 0.4773 (171s)
    step 6000/6000 loss 0.0835 val MAE/spread 0.4793 (186s)
    step 500/6000 loss 0.1131 val MAE/spread 0.5168 (16s)
    step 1000/6000 loss 0.1440 val MAE/spread 0.4875 (31s)
    step 1500/6000 loss 0.1448 val MAE/spread 0.4768 (47s)
    step 2000/6000 loss 0.1208 val MAE/spread 0.4735 (62s)
    step 2500/6000 loss 0.1392 val MAE/spread 0.4714 (78s)
    step 3000/6000 loss 0.0996 val MAE/spread 0.4691 (93s)
    step 3500/6000 loss 0.1436 val MAE/spread 0.4715 (109s)
    step 4000/6000 loss 0.0981 val MAE/spread 0.4723 (125s)
    step 4500/6000 loss 0.0973 val MAE/spread 0.4736 (140s)
    step 5000/6000 loss 0.1252 val MAE/spread 0.4744 (155s)
    step 5500/6000 loss 0.0915 val MAE/spread 0.4762 (171s)
    step 6000/6000 loss 0.1367 val MAE/spread 0.4764 (186s)
    step 500/6000 loss 0.1229 val MAE/spread 0.5195 (16s)
    step 1000/6000 loss 0.1127 val MAE/spread 0.4891 (31s)
    step 1500/6000 loss 0.1484 val MAE/spread 0.4781 (46s)
    step 2000/6000 loss 0.1323 val MAE/spread 0.4729 (62s)
    step 2500/6000 loss 0.1056 val MAE/spread 0.4697 (78s)
    step 3000/6000 loss 0.1075 val MAE/spread 0.4706 (93s)
    step 3500/6000 loss 0.0968 val MAE/spread 0.4713 (109s)
    step 4000/6000 loss 0.0936 val MAE/spread 0.4720 (125s)
    step 4500/6000 loss 0.1403 val MAE/spread 0.4719 (140s)
    step 5000/6000 loss 0.0942 val MAE/spread 0.4729 (156s)
    step 5500/6000 loss 0.0947 val MAE/spread 0.4746 (172s)
    step 6000/6000 loss 0.0961 val MAE/spread 0.4751 (187s)
hybrid: 12 global-forecast channels from ['ECMWF IFS 0.25 (physics)', 'ECMWF AIFS (AI)', 'DWD ICON (physics)', 'NOAA GFS (physics)'], 11281 training origins from 2024
    step 500/6000 loss 0.1049 val MAE/spread 0.4850 (16s)
    step 1000/6000 loss 0.1091 val MAE/spread 0.4590 (32s)
    step 1500/6000 loss 0.0987 val MAE/spread 0.4520 (47s)
    step 2000/6000 loss 0.0966 val MAE/spread 0.4453 (63s)
    step 2500/6000 loss 0.0895 val MAE/spread 0.4450 (79s)
    step 3000/6000 loss 0.0881 val MAE/spread 0.4444 (95s)
    step 3500/6000 loss 0.0759 val MAE/spread 0.4459 (110s)
    step 4000/6000 loss 0.0760 val MAE/spread 0.4475 (126s)
    step 4500/6000 loss 0.0786 val MAE/spread 0.4491 (142s)
    step 5000/6000 loss 0.0739 val MAE/spread 0.4508 (158s)
    step 5500/6000 loss 0.0685 val MAE/spread 0.4526 (173s)
    step 6000/6000 loss 0.0716 val MAE/spread 0.4543 (189s)
    step 500/6000 loss 0.1122 val MAE/spread 0.4799 (16s)
    step 1000/6000 loss 0.1159 val MAE/spread 0.4744 (32s)
    step 1500/6000 loss 0.0986 val MAE/spread 0.4715 (48s)
    step 2000/6000 loss 0.0956 val MAE/spread 0.4759 (64s)
    step 2500/6000 loss 0.0945 val MAE/spread 0.4763 (80s)
    step 3000/6000 loss 0.0891 val MAE/spread 0.4776 (96s)
    step 3500/6000 loss 0.0783 val MAE/spread 0.4787 (112s)
    step 4000/6000 loss 0.0770 val MAE/spread 0.4809 (128s)
    step 4500/6000 loss 0.0774 val MAE/spread 0.4829 (144s)
    step 5000/6000 loss 0.0741 val MAE/spread 0.4846 (160s)
    step 5500/6000 loss 0.0745 val MAE/spread 0.4860 (176s)
    step 6000/6000 loss 0.0760 val MAE/spread 0.4874 (192s)
    step 500/6000 loss 0.1098 val MAE/spread 0.5005 (16s)
    step 1000/6000 loss 0.1116 val MAE/spread 0.5132 (32s)
    step 1500/6000 loss 0.0961 val MAE/spread 0.5234 (48s)
    step 2000/6000 loss 0.0941 val MAE/spread 0.5285 (64s)
    step 2500/6000 loss 0.0930 val MAE/spread 0.5277 (80s)
    step 3000/6000 loss 0.0881 val MAE/spread 0.5327 (96s)
    step 3500/6000 loss 0.0755 val MAE/spread 0.5383 (110s)
    step 4000/6000 loss 0.0752 val MAE/spread 0.5417 (125s)
    step 4500/6000 loss 0.0752 val MAE/spread 0.5431 (138s)
    step 5000/6000 loss 0.0731 val MAE/spread 0.5451 (152s)
    step 5500/6000 loss 0.0730 val MAE/spread 0.5484 (167s)
    step 6000/6000 loss 0.0746 val MAE/spread 0.5512 (181s)
hybrid validation: H1 0.4444, H2 0.4715, H3 0.5005 (2 sigma = 0.0077) -> H1
    step 500/6000 loss 0.1195 val MAE/spread 0.4882 (14s)
    step 1000/6000 loss 0.1025 val MAE/spread 0.4603 (28s)
    step 1500/6000 loss 0.0912 val MAE/spread 0.4514 (43s)
    step 2000/6000 loss 0.0921 val MAE/spread 0.4497 (57s)
    step 2500/6000 loss 0.0790 val MAE/spread 0.4511 (73s)
    step 3000/6000 loss 0.0842 val MAE/spread 0.4525 (89s)
    step 3500/6000 loss 0.0741 val MAE/spread 0.4551 (104s)
    step 4000/6000 loss 0.0775 val MAE/spread 0.4576 (120s)
    step 4500/6000 loss 0.0785 val MAE/spread 0.4604 (136s)
    step 5000/6000 loss 0.0763 val MAE/spread 0.4625 (152s)
    step 5500/6000 loss 0.0756 val MAE/spread 0.4645 (168s)
    step 6000/6000 loss 0.0722 val MAE/spread 0.4657 (183s)
    step 500/6000 loss 0.1149 val MAE/spread 0.4858 (15s)
    step 1000/6000 loss 0.1071 val MAE/spread 0.4579 (31s)
    step 1500/6000 loss 0.0959 val MAE/spread 0.4538 (46s)
    step 2000/6000 loss 0.0937 val MAE/spread 0.4531 (61s)
    step 2500/6000 loss 0.0885 val MAE/spread 0.4540 (76s)
    step 3000/6000 loss 0.0787 val MAE/spread 0.4542 (91s)
    step 3500/6000 loss 0.0839 val MAE/spread 0.4557 (107s)
    step 4000/6000 loss 0.0799 val MAE/spread 0.4588 (122s)
    step 4500/6000 loss 0.0722 val MAE/spread 0.4604 (138s)
    step 5000/6000 loss 0.0771 val MAE/spread 0.4619 (153s)
    step 5500/6000 loss 0.0745 val MAE/spread 0.4635 (168s)
    step 6000/6000 loss 0.0759 val MAE/spread 0.4648 (183s)
    step 500/6000 loss 0.1133 val MAE/spread 0.4873 (15s)
    step 1000/6000 loss 0.1030 val MAE/spread 0.4643 (31s)
    step 1500/6000 loss 0.0947 val MAE/spread 0.4566 (46s)
    step 2000/6000 loss 0.0866 val MAE/spread 0.4561 (61s)
    step 2500/6000 loss 0.0896 val MAE/spread 0.4582 (76s)
    step 3000/6000 loss 0.0788 val MAE/spread 0.4606 (92s)
    step 3500/6000 loss 0.0766 val MAE/spread 0.4620 (107s)
    step 4000/6000 loss 0.0787 val MAE/spread 0.4638 (122s)
    step 4500/6000 loss 0.0753 val MAE/spread 0.4660 (137s)
    step 5000/6000 loss 0.0732 val MAE/spread 0.4678 (152s)
    step 5500/6000 loss 0.0716 val MAE/spread 0.4697 (167s)
    step 6000/6000 loss 0.0764 val MAE/spread 0.4709 (183s)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -56.4% vs raw, -27.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -61.5% vs raw, -34.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on RH: BEATS (MAE -46.9% vs raw, -8.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on RH: BEATS (MAE -50.6% vs raw, -24.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -49.2% vs raw, -30.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -54.8% vs raw, -35.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -53.4% vs raw, -23.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -55.5% vs raw, -28.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on RH: BEATS (MAE -41.7% vs raw, -7.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on RH: BEATS (MAE -40.1% vs raw, -9.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -63.7% vs raw, -46.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -67.9% vs raw, -50.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -55.1% vs raw, -26.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -60.3% vs raw, -34.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -39.6% vs raw, -18.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -48.2% vs raw, -26.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -63.4% vs raw, -45.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -62.9% vs raw, -45.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -56.5% vs raw, -33.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -66.2% vs raw, -49.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -48.7% vs raw, -28.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -61.1% vs raw, -37.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -60.4% vs raw, -42.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -70.1% vs raw, -56.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -70.6% vs raw, -39.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -73.7% vs raw, -47.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -84.6% vs raw, -43.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -85.2% vs raw, -46.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -77.1% vs raw, -54.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -77.4% vs raw, -56.3% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on AT: TIE (MAE +1.4%, p=0.35, 95% CI -1.2..+4.5%)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on RH: TIE (MAE +2.0%, p=0.23, 95% CI -1.0..+5.2%)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on WS: LOSS (MAE +7.3%, p=9.7e-08, 95% CI +5.3..+9.8%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -19.0%, p=2.6e-27, 95% CI -21.7..-16.4%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -18.3%, p=3e-39, 95% CI -20.8..-16.0%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -16.7%, p=4e-34, 95% CI -18.9..-14.5%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -39.2%, p=4.4e-16, 95% CI -44.5..-33.7%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -29.6%, p=3.7e-22, 95% CI -33.8..-25.1%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -13.3%, p=1.3e-16, 95% CI -15.9..-10.8%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on AT: WIN (MAE -16.2%, p=2e-11, 95% CI -19.6..-12.5%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on RH: WIN (MAE -17.5%, p=7.4e-16, 95% CI -20.9..-14.3%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on WS: WIN (MAE -17.9%, p=1.1e-14, 95% CI -21.3..-14.7%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -28.8%, p=7.3e-17, 95% CI -33.9..-23.2%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -13.2%, p=2.3e-05, 95% CI -18.4..-7.5%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -38.5%, p=2.1e-70, 95% CI -41.6..-35.5%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on AT: LOSS (MAE +5.0%, p=0.00012, 95% CI +2.5..+7.7%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on RH: TIE (MAE +1.4%, p=0.2, 95% CI -0.8..+3.5%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on WS: LOSS (MAE +3.8%, p=8.3e-05, 95% CI +1.9..+5.8%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on AT: TIE (MAE -1.0%, p=0.49, 95% CI -3.6..+1.8%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on RH: TIE (MAE -1.3%, p=0.32, 95% CI -3.9..+1.0%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on WS: LOSS (MAE +3.5%, p=1.8e-05, 95% CI +1.8..+5.2%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on AT: TIE (MAE +2.5%, p=0.079, 95% CI -0.2..+5.4%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on RH: TIE (MAE +1.3%, p=0.22, 95% CI -0.9..+3.2%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on WS: LOSS (MAE +4.4%, p=0.00022, 95% CI +1.6..+6.6%)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -57.0% vs raw, -28.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -62.0% vs raw, -35.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -47.9% vs raw, -10.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -51.6% vs raw, -25.6% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -52.7% vs raw, -34.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -57.9% vs raw, -40.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -54.1% vs raw, -24.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -56.2% vs raw, -29.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -42.8% vs raw, -8.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -41.3% vs raw, -10.9% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -66.2% vs raw, -49.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -70.1% vs raw, -54.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -55.7% vs raw, -27.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -60.9% vs raw, -35.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -40.7% vs raw, -19.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -49.2% vs raw, -28.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -65.9% vs raw, -49.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -65.5% vs raw, -49.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -57.1% vs raw, -34.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -65.0% vs raw, -47.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -49.6% vs raw, -29.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -60.9% vs raw, -36.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -63.1% vs raw, -46.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -70.9% vs raw, -58.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -71.0% vs raw, -40.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -74.0% vs raw, -48.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -84.9% vs raw, -44.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -85.4% vs raw, -47.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -78.6% vs raw, -57.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -79.0% vs raw, -59.3% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on AT: TIE (MAE -1.4%, p=0.35, 95% CI -4.3..+1.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on RH: TIE (MAE -1.9%, p=0.23, 95% CI -5.0..+1.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on WS: WIN (MAE -6.8%, p=9.7e-08, 95% CI -8.9..-5.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -20.2%, p=9.4e-25, 95% CI -22.9..-17.4%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -19.9%, p=1.3e-39, 95% CI -22.4..-17.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -22.4%, p=3.6e-45, 95% CI -24.5..-20.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -40.0%, p=3.1e-17, 95% CI -45.1..-35.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -31.0%, p=7.1e-27, 95% CI -34.8..-27.3%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -19.2%, p=2.5e-22, 95% CI -21.9..-16.8%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on AT: WIN (MAE -17.4%, p=4.3e-09, 95% CI -21.6..-13.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on RH: WIN (MAE -19.1%, p=5.6e-13, 95% CI -23.1..-15.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on WS: WIN (MAE -24.1%, p=4.6e-19, 95% CI -27.5..-21.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -29.8%, p=1.6e-22, 95% CI -34.2..-25.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -14.9%, p=2e-08, 95% CI -19.2..-10.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -42.7%, p=3.7e-80, 95% CI -45.4..-40.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on AT: TIE (MAE +3.5%, p=0.067, 95% CI -0.2..+7.3%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on RH: TIE (MAE -0.6%, p=0.75, 95% CI -4.0..+2.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on WS: WIN (MAE -3.3%, p=0.032, 95% CI -5.9..-0.8%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on AT: TIE (MAE -2.4%, p=0.2, 95% CI -5.8..+1.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on RH: TIE (MAE -3.2%, p=0.067, 95% CI -6.5..-0.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on WS: WIN (MAE -3.6%, p=0.021, 95% CI -6.4..-1.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on AT: TIE (MAE +1.1%, p=0.6, 95% CI -2.6..+4.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on RH: TIE (MAE -0.7%, p=0.69, 95% CI -3.9..+2.3%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on WS: TIE (MAE -2.7%, p=0.16, 95% CI -6.2..+0.2%)
no Earth-2 runs found (E2 file missing)
no Earth-2 runs found (E2 file missing)
```