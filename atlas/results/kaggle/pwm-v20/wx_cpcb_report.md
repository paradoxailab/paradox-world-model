# PWM-W v0.3 weather league: CPCB

Stations: 25. Chosen setting: P10 (validation only). Test origins every 6 h, 24 h ahead.

## AT (deg C)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| Chronos-2 (Amazon, 120M) | tsfm | 0.862 | 0.619 | 0.890 | 0.969 | 1.469 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.883 | 0.623 | 0.909 | 0.999 | 1.488 | 1.00 |
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
    step 1500/6000 loss 0.1180 val MAE/spread 0.4968 (40s)
    step 2000/6000 loss 0.1096 val MAE/spread 0.4921 (53s)
    step 2500/6000 loss 0.1007 val MAE/spread 0.4940 (66s)
    step 3000/6000 loss 0.1012 val MAE/spread 0.4930 (79s)
    step 3500/6000 loss 0.0902 val MAE/spread 0.4905 (92s)
    step 4000/6000 loss 0.0894 val MAE/spread 0.4886 (105s)
    step 4500/6000 loss 0.0908 val MAE/spread 0.4916 (118s)
    step 5000/6000 loss 0.0863 val MAE/spread 0.4966 (132s)
    step 5500/6000 loss 0.0819 val MAE/spread 0.4973 (145s)
    step 6000/6000 loss 0.0828 val MAE/spread 0.4978 (158s)
variant P0 seed 1: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1304 val MAE/spread 0.5194 (14s)
    step 1000/6000 loss 0.1150 val MAE/spread 0.4979 (27s)
    step 1500/6000 loss 0.1256 val MAE/spread 0.4955 (40s)
    step 2000/6000 loss 0.1055 val MAE/spread 0.4991 (54s)
    step 2500/6000 loss 0.1132 val MAE/spread 0.5038 (67s)
    step 3000/6000 loss 0.0945 val MAE/spread 0.5050 (80s)
    step 3500/6000 loss 0.0888 val MAE/spread 0.4918 (93s)
    step 4000/6000 loss 0.0971 val MAE/spread 0.4936 (106s)
    step 4500/6000 loss 0.0857 val MAE/spread 0.4960 (119s)
    step 5000/6000 loss 0.0854 val MAE/spread 0.4969 (132s)
    step 5500/6000 loss 0.0814 val MAE/spread 0.4968 (146s)
    step 6000/6000 loss 0.0881 val MAE/spread 0.4941 (159s)
variant P0 seed 2: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1305 val MAE/spread 0.5206 (13s)
    step 1000/6000 loss 0.1212 val MAE/spread 0.5081 (27s)
    step 1500/6000 loss 0.1177 val MAE/spread 0.4963 (40s)
    step 2000/6000 loss 0.1221 val MAE/spread 0.5011 (53s)
    step 2500/6000 loss 0.1003 val MAE/spread 0.4997 (67s)
    step 3000/6000 loss 0.0941 val MAE/spread 0.4971 (80s)
    step 3500/6000 loss 0.0883 val MAE/spread 0.4988 (93s)
    step 4000/6000 loss 0.0969 val MAE/spread 0.4969 (106s)
    step 4500/6000 loss 0.1026 val MAE/spread 0.5003 (119s)
    step 5000/6000 loss 0.0880 val MAE/spread 0.4973 (132s)
    step 5500/6000 loss 0.0978 val MAE/spread 0.4989 (145s)
    step 6000/6000 loss 0.0848 val MAE/spread 0.5025 (158s)
variant P10 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'xarch': True, 'ssl': True, 'ema': True}
    step 500/6000 loss 0.1971 val MAE/spread 0.5033 (21s)
    step 1000/6000 loss 0.1944 val MAE/spread 0.4829 (42s)
    step 1500/6000 loss 0.1863 val MAE/spread 0.4715 (63s)
    step 2000/6000 loss 0.1516 val MAE/spread 0.4658 (84s)
    step 2500/6000 loss 0.1339 val MAE/spread 0.4614 (105s)
    step 3000/6000 loss 0.1757 val MAE/spread 0.4608 (126s)
    step 3500/6000 loss 0.1336 val MAE/spread 0.4597 (146s)
    step 4000/6000 loss 0.1367 val MAE/spread 0.4622 (167s)
    step 4500/6000 loss 0.1737 val MAE/spread 0.4643 (188s)
    step 5000/6000 loss 0.1680 val MAE/spread 0.4656 (209s)
    step 5500/6000 loss 0.1645 val MAE/spread 0.4687 (230s)
    step 6000/6000 loss 0.1669 val MAE/spread 0.4709 (250s)
variant P11 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'longctx': True, 'ema': True, 'fenc': '/kaggle/working/out/fenc.pt'}
    step 500/6000 loss 0.1375 val MAE/spread 0.4828 (128s)
    step 1000/6000 loss 0.1343 val MAE/spread 0.4665 (257s)
    step 1500/6000 loss 0.1304 val MAE/spread 0.4620 (386s)
    step 2000/6000 loss 0.0940 val MAE/spread 0.4646 (515s)
    step 2500/6000 loss 0.0858 val MAE/spread 0.4691 (644s)
    step 3000/6000 loss 0.1264 val MAE/spread 0.4702 (773s)
    step 3500/6000 loss 0.0838 val MAE/spread 0.4724 (901s)
    step 4000/6000 loss 0.0864 val MAE/spread 0.4736 (1030s)
    step 4500/6000 loss 0.1230 val MAE/spread 0.4757 (1159s)
    step 5000/6000 loss 0.1223 val MAE/spread 0.4768 (1289s)
    step 5500/6000 loss 0.1176 val MAE/spread 0.4784 (1418s)
    step 6000/6000 loss 0.1181 val MAE/spread 0.4805 (1547s)
variant P12 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True, 'xarch': True, 'ssl': True, 'ema': True, 'fenc': '/kaggle/working/out/fenc.pt'}
    step 500/6000 loss 0.1887 val MAE/spread 0.4826 (136s)
    step 1000/6000 loss 0.1821 val MAE/spread 0.4669 (273s)
    step 1500/6000 loss 0.1731 val MAE/spread 0.4617 (409s)
    step 2000/6000 loss 0.1318 val MAE/spread 0.4632 (545s)
    step 2500/6000 loss 0.1159 val MAE/spread 0.4673 (682s)
    step 3000/6000 loss 0.1635 val MAE/spread 0.4689 (818s)
    step 3500/6000 loss 0.1138 val MAE/spread 0.4730 (955s)
    step 4000/6000 loss 0.1173 val MAE/spread 0.4729 (1091s)
    step 4500/6000 loss 0.1593 val MAE/spread 0.4763 (1227s)
    step 5000/6000 loss 0.1601 val MAE/spread 0.4776 (1365s)
    step 5500/6000 loss 0.1536 val MAE/spread 0.4788 (1501s)
    step 6000/6000 loss 0.1537 val MAE/spread 0.4796 (1638s)
validation (MAE / spread): P0 0.4922 +- 0.0038; P10 0.4597, P11 0.4620, P12 0.4617 -> chosen P10
    step 500/6000 loss 0.2029 val MAE/spread 0.5031 (21s)
    step 1000/6000 loss 0.1550 val MAE/spread 0.4816 (42s)
    step 1500/6000 loss 0.1728 val MAE/spread 0.4736 (63s)
    step 2000/6000 loss 0.1656 val MAE/spread 0.4658 (84s)
    step 2500/6000 loss 0.1303 val MAE/spread 0.4632 (105s)
    step 3000/6000 loss 0.1337 val MAE/spread 0.4648 (125s)
    step 3500/6000 loss 0.1339 val MAE/spread 0.4670 (146s)
    step 4000/6000 loss 0.1714 val MAE/spread 0.4668 (167s)
    step 4500/6000 loss 0.1673 val MAE/spread 0.4685 (188s)
    step 5000/6000 loss 0.1716 val MAE/spread 0.4712 (209s)
    step 5500/6000 loss 0.1697 val MAE/spread 0.4742 (230s)
    step 6000/6000 loss 0.1122 val MAE/spread 0.4760 (251s)
    step 500/6000 loss 0.1511 val MAE/spread 0.5033 (21s)
    step 1000/6000 loss 0.1894 val MAE/spread 0.4803 (42s)
    step 1500/6000 loss 0.1855 val MAE/spread 0.4697 (63s)
    step 2000/6000 loss 0.1532 val MAE/spread 0.4636 (84s)
    step 2500/6000 loss 0.1787 val MAE/spread 0.4605 (104s)
    step 3000/6000 loss 0.1301 val MAE/spread 0.4574 (125s)
    step 3500/6000 loss 0.1792 val MAE/spread 0.4589 (146s)
    step 4000/6000 loss 0.1227 val MAE/spread 0.4617 (166s)
    step 4500/6000 loss 0.1265 val MAE/spread 0.4643 (187s)
    step 5000/6000 loss 0.1617 val MAE/spread 0.4673 (208s)
    step 5500/6000 loss 0.1163 val MAE/spread 0.4704 (229s)
    step 6000/6000 loss 0.1750 val MAE/spread 0.4717 (250s)
    step 500/6000 loss 0.1593 val MAE/spread 0.5027 (21s)
    step 1000/6000 loss 0.1499 val MAE/spread 0.4817 (42s)
    step 1500/6000 loss 0.1931 val MAE/spread 0.4711 (63s)
    step 2000/6000 loss 0.1741 val MAE/spread 0.4658 (84s)
    step 2500/6000 loss 0.1373 val MAE/spread 0.4611 (105s)
    step 3000/6000 loss 0.1391 val MAE/spread 0.4607 (126s)
    step 3500/6000 loss 0.1215 val MAE/spread 0.4612 (147s)
    step 4000/6000 loss 0.1227 val MAE/spread 0.4619 (168s)
    step 4500/6000 loss 0.1765 val MAE/spread 0.4623 (190s)
    step 5000/6000 loss 0.1191 val MAE/spread 0.4640 (211s)
    step 5500/6000 loss 0.1235 val MAE/spread 0.4661 (231s)
    step 6000/6000 loss 0.1235 val MAE/spread 0.4672 (252s)
    step 500/6000 loss 0.1407 val MAE/spread 0.4841 (128s)
    step 1000/6000 loss 0.1024 val MAE/spread 0.4706 (257s)
    step 1500/6000 loss 0.1190 val MAE/spread 0.4695 (385s)
    step 2000/6000 loss 0.1148 val MAE/spread 0.4682 (514s)
    step 2500/6000 loss 0.0833 val MAE/spread 0.4682 (643s)
    step 3000/6000 loss 0.0861 val MAE/spread 0.4716 (774s)
    step 3500/6000 loss 0.0843 val MAE/spread 0.4740 (903s)
    step 4000/6000 loss 0.1226 val MAE/spread 0.4768 (1032s)
    step 4500/6000 loss 0.1191 val MAE/spread 0.4781 (1161s)
    step 5000/6000 loss 0.1264 val MAE/spread 0.4794 (1290s)
    step 5500/6000 loss 0.1233 val MAE/spread 0.4803 (1419s)
    step 6000/6000 loss 0.0686 val MAE/spread 0.4816 (1548s)
    step 500/6000 loss 0.0995 val MAE/spread 0.4852 (127s)
    step 1000/6000 loss 0.1334 val MAE/spread 0.4683 (256s)
    step 1500/6000 loss 0.1308 val MAE/spread 0.4650 (385s)
    step 2000/6000 loss 0.0959 val MAE/spread 0.4643 (515s)
    step 2500/6000 loss 0.1269 val MAE/spread 0.4671 (644s)
    step 3000/6000 loss 0.0823 val MAE/spread 0.4715 (774s)
    step 3500/6000 loss 0.1269 val MAE/spread 0.4745 (902s)
    step 4000/6000 loss 0.0775 val MAE/spread 0.4786 (1031s)
    step 4500/6000 loss 0.0754 val MAE/spread 0.4802 (1160s)
    step 5000/6000 loss 0.1155 val MAE/spread 0.4825 (1289s)
    step 5500/6000 loss 0.0747 val MAE/spread 0.4835 (1418s)
    step 6000/6000 loss 0.1227 val MAE/spread 0.4853 (1547s)
    step 500/6000 loss 0.1098 val MAE/spread 0.4825 (128s)
    step 1000/6000 loss 0.1018 val MAE/spread 0.4671 (257s)
    step 1500/6000 loss 0.1377 val MAE/spread 0.4672 (386s)
    step 2000/6000 loss 0.1227 val MAE/spread 0.4689 (516s)
    step 2500/6000 loss 0.0880 val MAE/spread 0.4743 (645s)
    step 3000/6000 loss 0.0848 val MAE/spread 0.4752 (774s)
    step 3500/6000 loss 0.0766 val MAE/spread 0.4774 (904s)
    step 4000/6000 loss 0.0770 val MAE/spread 0.4773 (1033s)
    step 4500/6000 loss 0.1254 val MAE/spread 0.4796 (1162s)
    step 5000/6000 loss 0.0743 val MAE/spread 0.4807 (1291s)
    step 5500/6000 loss 0.0796 val MAE/spread 0.4830 (1419s)
    step 6000/6000 loss 0.0779 val MAE/spread 0.4859 (1548s)
v1.0 ensemble validation: P10 alone 0.4561, P10+P11 0.4509 (2 sigma = 0.0077) -> not adopted
v1.0 self-correction validation: raw 0.4561, corrected 0.4686 (2 sigma = 0.0077) -> not adopted
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
no Earth-2 runs found (E2 file missing)
```