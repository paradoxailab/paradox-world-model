# PWM-W v0.3 weather league: CPCB

Stations: 25. Chosen setting: P10 (validation only). Test origins every 6 h, 24 h ahead.

## AT (deg C)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| Chronos-2 (Amazon, 120M) | tsfm | 0.862 | 0.619 | 0.890 | 0.969 | 1.469 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.883 | 0.623 | 0.909 | 0.999 | 1.488 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 0.886 | 0.660 | 0.947 | 0.968 | 1.462 | 1.00 |
| PWM-W (pure) | ours | 0.891 | 0.635 | 0.926 | 1.002 | 1.490 | 1.00 |
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
| PWM-W hybrid (uses global forecasts) | hybrid | 4.642 | 3.487 | 4.851 | 5.115 | 6.630 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 4.648 | 3.338 | 4.750 | 5.252 | 6.935 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 4.653 | 3.304 | 4.766 | 5.271 | 6.901 | 1.00 |
| PWM-W (pure) | ours | 4.662 | 3.372 | 4.730 | 5.273 | 6.773 | 1.00 |
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
| PWM-W hybrid (uses global forecasts) | hybrid | 0.383 | 0.333 | 0.390 | 0.405 | 0.685 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.393 | 0.328 | 0.399 | 0.422 | 0.801 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 0.395 | 0.329 | 0.403 | 0.424 | 0.719 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 0.396 | 0.334 | 0.405 | 0.423 | 0.729 | 1.00 |
| PWM-W (pure) | ours | 0.408 | 0.344 | 0.417 | 0.435 | 0.727 | 1.00 |
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

- [STRICT] PWM-W (pure) vs DWD ICON (physics): AT BEATS (-57.1% / -28.1%); RH BEATS (-47.5% / -9.2%); WS BEATS (-49.5% / -30.4%)
- [STRICT] PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-54.1% / -24.8%); RH BEATS (-42.3% / -8.1%); WS BEATS (-63.9% / -46.4%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-55.7% / -27.9%); RH BEATS (-40.2% / -19.2%); WS BEATS (-63.6% / -46.0%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-57.2% / -34.4%); RH BEATS (-49.2% / -28.9%); WS BEATS (-60.6% / -43.1%)
- [STRICT] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-71.0% / -40.4%); RH BEATS (-84.7% / -43.9%); WS BEATS (-77.2% / -55.0%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics): AT BEATS (-62.1% / -35.4%); RH BEATS (-51.2% / -25.0%); WS BEATS (-55.1% / -36.0%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-56.2% / -30.0%); RH BEATS (-40.8% / -10.2%); WS BEATS (-68.1% / -51.1%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-60.9% / -35.7%); RH BEATS (-48.8% / -27.7%); WS BEATS (-63.1% / -46.0%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-66.5% / -49.7%); RH BEATS (-61.4% / -37.7%); WS BEATS (-70.2% / -57.0%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-74.1% / -48.1%); RH BEATS (-85.3% / -47.0%); WS BEATS (-77.6% / -56.6%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-57.3% / -28.5%); RH BEATS (-47.7% / -9.6%); WS BEATS (-52.6% / -34.6%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-54.4% / -25.3%); RH BEATS (-42.6% / -8.5%); WS BEATS (-66.1% / -49.6%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-56.0% / -28.3%); RH BEATS (-40.5% / -19.6%); WS BEATS (-65.8% / -49.2%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-57.4% / -34.8%); RH BEATS (-49.4% / -29.2%); WS BEATS (-63.0% / -46.6%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-71.2% / -40.8%); RH BEATS (-84.8% / -44.2%); WS BEATS (-78.6% / -57.7%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-62.3% / -35.8%); RH BEATS (-51.4% / -25.3%); WS BEATS (-57.8% / -39.8%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-56.5% / -30.4%); RH BEATS (-41.0% / -10.5%); WS BEATS (-70.0% / -54.0%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-61.1% / -36.2%); RH BEATS (-49.0% / -28.0%); WS BEATS (-65.4% / -49.2%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-65.5% / -48.2%); RH BEATS (-60.4% / -36.0%); WS BEATS (-70.9% / -58.0%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-74.2% / -48.4%); RH BEATS (-85.4% / -47.3%); WS BEATS (-78.9% / -59.2%)

## Models we ran ourselves (Earth2Studio, 00 UTC GFS start, +6/12/18 h)


Not tested: GenCast and WeatherNext (no public forecast archive; data needs a Google Cloud access request).

## Log

```
WX_CPCB: 17544 hours x 25 stations, targets ['AT', 'RH', 'WS'] (missing 2.9%, 3.5%, 19.6%), 5 other channels, spreads [3.609999895095825, 13.479999542236328, 0.9300000071525574], 184 graph links, 5 regions; splits {'train': ('2024-01-01T00', '2025-05-02T23'), 'val': ('2025-05-03T00', '2025-07-02T23'), 'test': ('2025-07-03T00', '2025-12-31T23')}
origins: train 11281, validation 241, test 725 (every 6 h); device cuda
joint-training partner WMO: 20 stations, 37515 origins ending before 2025-05-03T00; shared other channels ['WD_sin', 'WD_cos', 'P']; clock shift +6 h
variant P0 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1144 val MAE/spread 0.5142 (14s)
    step 1000/6000 loss 0.1273 val MAE/spread 0.5044 (27s)
    step 1500/6000 loss 0.1180 val MAE/spread 0.4968 (39s)
    step 2000/6000 loss 0.1096 val MAE/spread 0.4921 (51s)
    step 2500/6000 loss 0.1007 val MAE/spread 0.4940 (63s)
    step 3000/6000 loss 0.1012 val MAE/spread 0.4930 (75s)
    step 3500/6000 loss 0.0902 val MAE/spread 0.4905 (87s)
    step 4000/6000 loss 0.0894 val MAE/spread 0.4886 (100s)
    step 4500/6000 loss 0.0908 val MAE/spread 0.4916 (112s)
    step 5000/6000 loss 0.0863 val MAE/spread 0.4966 (124s)
    step 5500/6000 loss 0.0819 val MAE/spread 0.4973 (136s)
    step 6000/6000 loss 0.0828 val MAE/spread 0.4978 (148s)
variant P0 seed 1: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1304 val MAE/spread 0.5194 (12s)
    step 1000/6000 loss 0.1150 val MAE/spread 0.4979 (24s)
    step 1500/6000 loss 0.1256 val MAE/spread 0.4955 (36s)
    step 2000/6000 loss 0.1055 val MAE/spread 0.4991 (48s)
    step 2500/6000 loss 0.1132 val MAE/spread 0.5038 (61s)
    step 3000/6000 loss 0.0945 val MAE/spread 0.5050 (73s)
    step 3500/6000 loss 0.0888 val MAE/spread 0.4918 (85s)
    step 4000/6000 loss 0.0971 val MAE/spread 0.4936 (97s)
    step 4500/6000 loss 0.0857 val MAE/spread 0.4960 (109s)
    step 5000/6000 loss 0.0854 val MAE/spread 0.4969 (121s)
    step 5500/6000 loss 0.0814 val MAE/spread 0.4968 (133s)
    step 6000/6000 loss 0.0881 val MAE/spread 0.4941 (145s)
variant P0 seed 2: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1305 val MAE/spread 0.5206 (12s)
    step 1000/6000 loss 0.1212 val MAE/spread 0.5081 (24s)
    step 1500/6000 loss 0.1177 val MAE/spread 0.4963 (36s)
    step 2000/6000 loss 0.1221 val MAE/spread 0.5011 (48s)
    step 2500/6000 loss 0.1003 val MAE/spread 0.4997 (61s)
    step 3000/6000 loss 0.0941 val MAE/spread 0.4971 (73s)
    step 3500/6000 loss 0.0883 val MAE/spread 0.4988 (85s)
    step 4000/6000 loss 0.0969 val MAE/spread 0.4969 (97s)
    step 4500/6000 loss 0.1026 val MAE/spread 0.5003 (109s)
    step 5000/6000 loss 0.0880 val MAE/spread 0.4973 (121s)
    step 5500/6000 loss 0.0978 val MAE/spread 0.4989 (133s)
    step 6000/6000 loss 0.0848 val MAE/spread 0.5025 (145s)
variant P8 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'longctx': True, 'ema': True}
    step 500/6000 loss 0.1524 val MAE/spread 0.5216 (14s)
    step 1000/6000 loss 0.1502 val MAE/spread 0.4917 (28s)
    step 1500/6000 loss 0.1490 val MAE/spread 0.4776 (42s)
    step 2000/6000 loss 0.1183 val MAE/spread 0.4735 (56s)
    step 2500/6000 loss 0.1081 val MAE/spread 0.4694 (70s)
    step 3000/6000 loss 0.1366 val MAE/spread 0.4702 (85s)
    step 3500/6000 loss 0.1077 val MAE/spread 0.4678 (98s)
    step 4000/6000 loss 0.1136 val MAE/spread 0.4689 (112s)
    step 4500/6000 loss 0.1371 val MAE/spread 0.4684 (126s)
    step 5000/6000 loss 0.1343 val MAE/spread 0.4706 (140s)
    step 5500/6000 loss 0.1299 val MAE/spread 0.4733 (155s)
    step 6000/6000 loss 0.1294 val MAE/spread 0.4747 (168s)
variant P9 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'xarch': True, 'ema': True}
    step 500/6000 loss 0.1448 val MAE/spread 0.5008 (19s)
    step 1000/6000 loss 0.1414 val MAE/spread 0.4796 (38s)
    step 1500/6000 loss 0.1388 val MAE/spread 0.4678 (57s)
    step 2000/6000 loss 0.1094 val MAE/spread 0.4624 (76s)
    step 2500/6000 loss 0.1027 val MAE/spread 0.4606 (95s)
    step 3000/6000 loss 0.1326 val MAE/spread 0.4630 (114s)
    step 3500/6000 loss 0.0995 val MAE/spread 0.4630 (132s)
    step 4000/6000 loss 0.1052 val MAE/spread 0.4629 (151s)
    step 4500/6000 loss 0.1320 val MAE/spread 0.4659 (170s)
    step 5000/6000 loss 0.1283 val MAE/spread 0.4688 (189s)
    step 5500/6000 loss 0.1249 val MAE/spread 0.4709 (208s)
    step 6000/6000 loss 0.1257 val MAE/spread 0.4726 (227s)
variant P10 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'xarch': True, 'ssl': True, 'ema': True}
    step 500/6000 loss 0.1971 val MAE/spread 0.5033 (20s)
    step 1000/6000 loss 0.1944 val MAE/spread 0.4829 (39s)
    step 1500/6000 loss 0.1863 val MAE/spread 0.4715 (59s)
    step 2000/6000 loss 0.1516 val MAE/spread 0.4658 (78s)
    step 2500/6000 loss 0.1339 val MAE/spread 0.4614 (97s)
    step 3000/6000 loss 0.1757 val MAE/spread 0.4608 (117s)
    step 3500/6000 loss 0.1336 val MAE/spread 0.4597 (136s)
    step 4000/6000 loss 0.1367 val MAE/spread 0.4622 (156s)
    step 4500/6000 loss 0.1737 val MAE/spread 0.4643 (175s)
    step 5000/6000 loss 0.1680 val MAE/spread 0.4656 (195s)
    step 5500/6000 loss 0.1645 val MAE/spread 0.4687 (214s)
    step 6000/6000 loss 0.1669 val MAE/spread 0.4709 (234s)
validation (MAE / spread): P0 0.4922 +- 0.0038; P8 0.4678, P9 0.4606, P10 0.4597 -> chosen P10
    step 500/6000 loss 0.2029 val MAE/spread 0.5031 (19s)
    step 1000/6000 loss 0.1550 val MAE/spread 0.4816 (39s)
    step 1500/6000 loss 0.1728 val MAE/spread 0.4736 (58s)
    step 2000/6000 loss 0.1656 val MAE/spread 0.4658 (78s)
    step 2500/6000 loss 0.1303 val MAE/spread 0.4632 (98s)
    step 3000/6000 loss 0.1337 val MAE/spread 0.4648 (117s)
    step 3500/6000 loss 0.1339 val MAE/spread 0.4670 (137s)
    step 4000/6000 loss 0.1714 val MAE/spread 0.4668 (156s)
    step 4500/6000 loss 0.1673 val MAE/spread 0.4685 (176s)
    step 5000/6000 loss 0.1716 val MAE/spread 0.4712 (195s)
    step 5500/6000 loss 0.1697 val MAE/spread 0.4742 (215s)
    step 6000/6000 loss 0.1122 val MAE/spread 0.4760 (234s)
    step 500/6000 loss 0.1511 val MAE/spread 0.5033 (19s)
    step 1000/6000 loss 0.1894 val MAE/spread 0.4803 (39s)
    step 1500/6000 loss 0.1855 val MAE/spread 0.4697 (58s)
    step 2000/6000 loss 0.1532 val MAE/spread 0.4636 (78s)
    step 2500/6000 loss 0.1787 val MAE/spread 0.4605 (98s)
    step 3000/6000 loss 0.1301 val MAE/spread 0.4574 (117s)
    step 3500/6000 loss 0.1792 val MAE/spread 0.4589 (137s)
    step 4000/6000 loss 0.1227 val MAE/spread 0.4617 (156s)
    step 4500/6000 loss 0.1265 val MAE/spread 0.4643 (176s)
    step 5000/6000 loss 0.1617 val MAE/spread 0.4673 (195s)
    step 5500/6000 loss 0.1163 val MAE/spread 0.4704 (215s)
    step 6000/6000 loss 0.1750 val MAE/spread 0.4717 (234s)
    step 500/6000 loss 0.1593 val MAE/spread 0.5027 (20s)
    step 1000/6000 loss 0.1499 val MAE/spread 0.4817 (39s)
    step 1500/6000 loss 0.1931 val MAE/spread 0.4711 (58s)
    step 2000/6000 loss 0.1741 val MAE/spread 0.4658 (78s)
    step 2500/6000 loss 0.1373 val MAE/spread 0.4611 (97s)
    step 3000/6000 loss 0.1391 val MAE/spread 0.4607 (117s)
    step 3500/6000 loss 0.1215 val MAE/spread 0.4612 (136s)
    step 4000/6000 loss 0.1227 val MAE/spread 0.4619 (156s)
    step 4500/6000 loss 0.1765 val MAE/spread 0.4623 (175s)
    step 5000/6000 loss 0.1191 val MAE/spread 0.4640 (195s)
    step 5500/6000 loss 0.1235 val MAE/spread 0.4661 (214s)
    step 6000/6000 loss 0.1235 val MAE/spread 0.4672 (234s)
hybrid: 12 global-forecast channels from ['ECMWF IFS 0.25 (physics)', 'ECMWF AIFS (AI)', 'DWD ICON (physics)', 'NOAA GFS (physics)'], 11281 training origins from 2024
    step 500/6000 loss 0.1472 val MAE/spread 0.4710 (21s)
    step 1000/6000 loss 0.1427 val MAE/spread 0.4538 (42s)
    step 1500/6000 loss 0.1355 val MAE/spread 0.4506 (62s)
    step 2000/6000 loss 0.1255 val MAE/spread 0.4512 (83s)
    step 2500/6000 loss 0.1133 val MAE/spread 0.4557 (103s)
    step 3000/6000 loss 0.1137 val MAE/spread 0.4597 (124s)
    step 3500/6000 loss 0.1029 val MAE/spread 0.4602 (144s)
    step 4000/6000 loss 0.1041 val MAE/spread 0.4616 (165s)
    step 4500/6000 loss 0.1041 val MAE/spread 0.4647 (185s)
    step 5000/6000 loss 0.1034 val MAE/spread 0.4677 (206s)
    step 5500/6000 loss 0.0954 val MAE/spread 0.4693 (227s)
    step 6000/6000 loss 0.0954 val MAE/spread 0.4710 (247s)
    step 500/6000 loss 0.1516 val MAE/spread 0.4780 (21s)
    step 1000/6000 loss 0.1500 val MAE/spread 0.4652 (41s)
    step 1500/6000 loss 0.1369 val MAE/spread 0.4607 (62s)
    step 2000/6000 loss 0.1276 val MAE/spread 0.4614 (83s)
    step 2500/6000 loss 0.1195 val MAE/spread 0.4639 (103s)
    step 3000/6000 loss 0.1152 val MAE/spread 0.4671 (124s)
    step 3500/6000 loss 0.1054 val MAE/spread 0.4684 (145s)
    step 4000/6000 loss 0.1047 val MAE/spread 0.4700 (165s)
    step 4500/6000 loss 0.1056 val MAE/spread 0.4719 (186s)
    step 5000/6000 loss 0.1049 val MAE/spread 0.4741 (207s)
    step 5500/6000 loss 0.1019 val MAE/spread 0.4752 (227s)
    step 6000/6000 loss 0.1016 val MAE/spread 0.4759 (248s)
    step 500/6000 loss 0.1496 val MAE/spread 0.4958 (21s)
    step 1000/6000 loss 0.1491 val MAE/spread 0.4998 (42s)
    step 1500/6000 loss 0.1332 val MAE/spread 0.4987 (62s)
    step 2000/6000 loss 0.1255 val MAE/spread 0.5032 (83s)
    step 2500/6000 loss 0.1183 val MAE/spread 0.5019 (104s)
    step 3000/6000 loss 0.1134 val MAE/spread 0.5115 (125s)
    step 3500/6000 loss 0.1047 val MAE/spread 0.5199 (146s)
    step 4000/6000 loss 0.1047 val MAE/spread 0.5279 (167s)
    step 4500/6000 loss 0.1049 val MAE/spread 0.5340 (187s)
    step 5000/6000 loss 0.1046 val MAE/spread 0.5380 (208s)
    step 5500/6000 loss 0.1015 val MAE/spread 0.5430 (229s)
    step 6000/6000 loss 0.1006 val MAE/spread 0.5479 (250s)
hybrid validation: H1 0.4506, H2 0.4607, H3 0.4958 (2 sigma = 0.0077) -> H1
    step 500/6000 loss 0.1589 val MAE/spread 0.4687 (21s)
    step 1000/6000 loss 0.1387 val MAE/spread 0.4525 (41s)
    step 1500/6000 loss 0.1286 val MAE/spread 0.4464 (62s)
    step 2000/6000 loss 0.1255 val MAE/spread 0.4464 (83s)
    step 2500/6000 loss 0.1095 val MAE/spread 0.4487 (103s)
    step 3000/6000 loss 0.1135 val MAE/spread 0.4528 (124s)
    step 3500/6000 loss 0.1021 val MAE/spread 0.4567 (145s)
    step 4000/6000 loss 0.1018 val MAE/spread 0.4601 (165s)
    step 4500/6000 loss 0.1076 val MAE/spread 0.4623 (185s)
    step 5000/6000 loss 0.1033 val MAE/spread 0.4665 (205s)
    step 5500/6000 loss 0.1031 val MAE/spread 0.4690 (224s)
    step 6000/6000 loss 0.0982 val MAE/spread 0.4715 (244s)
    step 500/6000 loss 0.1562 val MAE/spread 0.4782 (20s)
    step 1000/6000 loss 0.1495 val MAE/spread 0.4588 (41s)
    step 1500/6000 loss 0.1298 val MAE/spread 0.4523 (62s)
    step 2000/6000 loss 0.1223 val MAE/spread 0.4546 (82s)
    step 2500/6000 loss 0.1202 val MAE/spread 0.4550 (103s)
    step 3000/6000 loss 0.1050 val MAE/spread 0.4556 (124s)
    step 3500/6000 loss 0.1109 val MAE/spread 0.4602 (145s)
    step 4000/6000 loss 0.1045 val MAE/spread 0.4621 (165s)
    step 4500/6000 loss 0.1016 val MAE/spread 0.4655 (186s)
    step 5000/6000 loss 0.1050 val MAE/spread 0.4686 (206s)
    step 5500/6000 loss 0.1012 val MAE/spread 0.4707 (227s)
    step 6000/6000 loss 0.1045 val MAE/spread 0.4719 (248s)
    step 500/6000 loss 0.1536 val MAE/spread 0.4706 (21s)
    step 1000/6000 loss 0.1422 val MAE/spread 0.4596 (41s)
    step 1500/6000 loss 0.1305 val MAE/spread 0.4547 (62s)
    step 2000/6000 loss 0.1169 val MAE/spread 0.4521 (83s)
    step 2500/6000 loss 0.1212 val MAE/spread 0.4525 (103s)
    step 3000/6000 loss 0.1114 val MAE/spread 0.4529 (124s)
    step 3500/6000 loss 0.1010 val MAE/spread 0.4537 (145s)
    step 4000/6000 loss 0.1050 val MAE/spread 0.4543 (166s)
    step 4500/6000 loss 0.0996 val MAE/spread 0.4567 (186s)
    step 5000/6000 loss 0.1007 val MAE/spread 0.4593 (207s)
    step 5500/6000 loss 0.0992 val MAE/spread 0.4609 (228s)
    step 6000/6000 loss 0.1016 val MAE/spread 0.4623 (249s)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -57.1% vs raw, -28.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -62.1% vs raw, -35.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on RH: BEATS (MAE -47.5% vs raw, -9.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on RH: BEATS (MAE -51.2% vs raw, -25.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -49.5% vs raw, -30.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -55.1% vs raw, -36.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -54.1% vs raw, -24.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -56.2% vs raw, -30.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on RH: BEATS (MAE -42.3% vs raw, -8.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on RH: BEATS (MAE -40.8% vs raw, -10.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -63.9% vs raw, -46.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -68.1% vs raw, -51.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -55.7% vs raw, -27.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -60.9% vs raw, -35.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -40.2% vs raw, -19.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -48.8% vs raw, -27.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -63.6% vs raw, -46.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -63.1% vs raw, -46.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -57.2% vs raw, -34.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -66.5% vs raw, -49.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -49.2% vs raw, -28.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -61.4% vs raw, -37.7% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -60.6% vs raw, -43.1% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -70.2% vs raw, -57.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -71.0% vs raw, -40.4% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -74.1% vs raw, -48.1% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -84.7% vs raw, -43.9% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -85.3% vs raw, -47.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -77.2% vs raw, -55.0% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -77.6% vs raw, -56.6% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on AT: TIE (MAE +0.6%, p=0.69, 95% CI -2.1..+3.8%)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on RH: TIE (MAE +0.4%, p=0.81, 95% CI -2.7..+4.0%)
RESULT CPCB PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on WS: LOSS (MAE +6.4%, p=3e-07, 95% CI +4.6..+8.8%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -20.2%, p=4.5e-30, 95% CI -23.0..-17.5%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -19.2%, p=7e-39, 95% CI -21.7..-16.9%)
RESULT CPCB PWM-W (pure) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -17.2%, p=3.9e-39, 95% CI -19.3..-15.2%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -40.1%, p=3.2e-17, 95% CI -45.3..-34.8%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -30.3%, p=1.9e-23, 95% CI -34.4..-26.0%)
RESULT CPCB PWM-W (pure) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -13.8%, p=1.2e-17, 95% CI -16.3..-11.3%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on AT: WIN (MAE -17.6%, p=8.2e-14, 95% CI -20.9..-14.0%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on RH: WIN (MAE -18.5%, p=5e-18, 95% CI -21.7..-15.5%)
RESULT CPCB PWM-W (pure) vs Baseline: same hour yesterday on WS: WIN (MAE -18.5%, p=4.2e-16, 95% CI -21.6..-15.4%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -29.9%, p=7.4e-18, 95% CI -35.1..-24.3%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -14.2%, p=6.7e-06, 95% CI -19.4..-8.4%)
RESULT CPCB PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -38.9%, p=6.7e-70, 95% CI -42.0..-35.9%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on AT: LOSS (MAE +3.4%, p=0.0054, 95% CI +1.0..+5.9%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on RH: TIE (MAE +0.3%, p=0.79, 95% CI -1.9..+2.4%)
RESULT CPCB PWM-W (pure) vs Chronos-2 (Amazon, 120M) on WS: LOSS (MAE +3.2%, p=0.00042, 95% CI +1.4..+5.0%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on AT: TIE (MAE -2.5%, p=0.069, 95% CI -5.0..+0.1%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on RH: TIE (MAE -2.3%, p=0.072, 95% CI -4.9..-0.2%)
RESULT CPCB PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on WS: LOSS (MAE +2.9%, p=0.00057, 95% CI +1.2..+4.6%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on AT: TIE (MAE +1.0%, p=0.47, 95% CI -1.6..+3.6%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on RH: TIE (MAE +0.2%, p=0.85, 95% CI -2.0..+2.2%)
RESULT CPCB PWM-W (pure) vs TimesFM 3.0 (Google) on WS: LOSS (MAE +3.8%, p=0.0013, 95% CI +1.0..+5.9%)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -57.3% vs raw, -28.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -62.3% vs raw, -35.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -47.7% vs raw, -9.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -51.4% vs raw, -25.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -52.6% vs raw, -34.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -57.8% vs raw, -39.8% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -54.4% vs raw, -25.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -56.5% vs raw, -30.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -42.6% vs raw, -8.5% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -41.0% vs raw, -10.5% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -66.1% vs raw, -49.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -70.0% vs raw, -54.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -56.0% vs raw, -28.3% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -61.1% vs raw, -36.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -40.5% vs raw, -19.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -49.0% vs raw, -28.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -65.8% vs raw, -49.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -65.4% vs raw, -49.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -57.4% vs raw, -34.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -65.5% vs raw, -48.2% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -49.4% vs raw, -29.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -60.4% vs raw, -36.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -63.0% vs raw, -46.6% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -70.9% vs raw, -58.0% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -71.2% vs raw, -40.8% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -74.2% vs raw, -48.4% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -84.8% vs raw, -44.2% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -85.4% vs raw, -47.3% vs bias-corrected)
RESULT CPCB [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -78.6% vs raw, -57.7% vs bias-corrected)
RESULT CPCB [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -78.9% vs raw, -59.2% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on AT: TIE (MAE -0.6%, p=0.69, 95% CI -3.7..+2.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on RH: TIE (MAE -0.4%, p=0.81, 95% CI -3.8..+2.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on WS: WIN (MAE -6.0%, p=3e-07, 95% CI -8.0..-4.4%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -20.7%, p=1.6e-25, 95% CI -23.6..-17.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -19.5%, p=5.7e-30, 95% CI -22.4..-16.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -22.2%, p=2.1e-46, 95% CI -24.2..-20.6%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -40.5%, p=1.1e-17, 95% CI -45.6..-35.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -30.6%, p=5e-28, 95% CI -34.4..-26.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -19.0%, p=3.5e-22, 95% CI -21.7..-16.5%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on AT: WIN (MAE -18.1%, p=3.3e-10, 95% CI -22.1..-13.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on RH: WIN (MAE -18.7%, p=2.9e-12, 95% CI -22.9..-14.7%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on WS: WIN (MAE -23.9%, p=2.6e-19, 95% CI -27.3..-20.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -30.3%, p=1.8e-22, 95% CI -34.9..-25.6%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -14.5%, p=1.3e-07, 95% CI -19.1..-9.8%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -42.6%, p=1.1e-78, 95% CI -45.3..-40.1%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on AT: TIE (MAE +2.8%, p=0.14, 95% CI -0.9..+6.3%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on RH: TIE (MAE -0.1%, p=0.94, 95% CI -3.8..+3.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on WS: WIN (MAE -3.0%, p=0.046, 95% CI -5.8..-0.6%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on AT: TIE (MAE -3.1%, p=0.098, 95% CI -6.5..+0.2%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on RH: TIE (MAE -2.8%, p=0.13, 95% CI -6.3..+0.4%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on WS: WIN (MAE -3.4%, p=0.031, 95% CI -6.2..-0.9%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on AT: TIE (MAE +0.3%, p=0.87, 95% CI -3.4..+4.0%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on RH: TIE (MAE -0.2%, p=0.89, 95% CI -3.7..+2.8%)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on WS: TIE (MAE -2.5%, p=0.18, 95% CI -6.0..+0.3%)
no Earth-2 runs found (E2 file missing)
no Earth-2 runs found (E2 file missing)
```