# PWM-W v0.3 weather league: CPCB

Stations: 25. Chosen setting: P0 (validation only). Test origins every 6 h, 24 h ahead.

## AT (deg C)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| Chronos-2 (Amazon, 120M) | tsfm | 0.862 | 0.619 | 0.890 | 0.969 | 1.469 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 0.883 | 0.623 | 0.909 | 0.999 | 1.488 | 1.00 |
| PWM-W (pure) | ours | 0.942 | 0.672 | 0.997 | 1.049 | 1.537 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 0.952 | 0.693 | 1.034 | 1.041 | 1.514 | 1.00 |
| Baseline: same hour yesterday | baseline | 1.068 | 1.065 | 1.065 | 1.070 | 1.789 | 0.98 |
| Baseline: daily cycle + latest anomaly | baseline | 1.117 | 0.774 | 1.254 | 1.221 | 1.758 | 1.00 |
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 1.186 | 1.184 | 1.185 | 1.187 | 1.741 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 1.236 | 1.234 | 1.235 | 1.237 | 1.795 | 1.00 |
| DWD ICON (physics) [latest run] + local bias correction | global | 1.239 | 1.239 | 1.239 | 1.239 | 1.799 | 1.00 |
| ECMWF AIFS (AI) [issued 24 h before] + local bias correction | global | 1.278 | 1.277 | 1.278 | 1.278 | 1.835 | 1.00 |
| DWD ICON (physics) [issued 24 h before] + local bias correction | global | 1.352 | 1.349 | 1.351 | 1.354 | 1.902 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 1.359 | 1.358 | 1.359 | 1.360 | 1.948 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued 24 h before] + local bias correction | global | 1.383 | 1.383 | 1.383 | 1.384 | 1.961 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 1.488 | 1.483 | 1.486 | 1.491 | 2.160 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 1.495 | 1.494 | 1.494 | 1.497 | 2.090 | 1.00 |
| ECMWF IFS 9 km (physics) [issued 24 h before] + local bias correction | global | 1.555 | 1.552 | 1.553 | 1.558 | 2.178 | 0.51 |
| NOAA GFS (physics) [issued 24 h before] + local bias correction | global | 1.710 | 1.707 | 1.709 | 1.712 | 2.385 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 1.942 | 1.941 | 1.941 | 1.943 | 2.556 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 2.013 | 2.012 | 2.012 | 2.015 | 2.612 | 1.00 |
| ECMWF AIFS (AI) [issued 24 h before] | global | 2.043 | 2.043 | 2.043 | 2.043 | 2.681 | 1.00 |
| DWD ICON (physics) [latest run] | global | 2.075 | 2.076 | 2.076 | 2.075 | 2.704 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] | global | 2.080 | 2.078 | 2.079 | 2.083 | 2.688 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued 24 h before] | global | 2.257 | 2.256 | 2.257 | 2.258 | 2.881 | 1.00 |
| DWD ICON (physics) [issued 24 h before] | global | 2.302 | 2.301 | 2.301 | 2.303 | 2.922 | 1.00 |
| ECMWF IFS 9 km (physics) [issued 24 h before] | global | 2.330 | 2.325 | 2.327 | 2.335 | 2.961 | 0.51 |
| NOAA GFS (physics) [latest run] | global | 3.075 | 3.068 | 3.070 | 3.081 | 3.793 | 1.00 |
| NOAA GFS (physics) [issued 24 h before] | global | 3.419 | 3.413 | 3.413 | 3.424 | 4.167 | 1.00 |

## RH (%)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| Chronos-2 (Amazon, 120M) | tsfm | 4.648 | 3.338 | 4.750 | 5.252 | 6.935 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 4.653 | 3.304 | 4.766 | 5.271 | 6.901 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 4.660 | 3.549 | 5.027 | 5.033 | 6.598 | 1.00 |
| PWM-W (pure) | ours | 4.970 | 3.550 | 5.154 | 5.587 | 7.084 | 1.00 |
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 5.071 | 5.067 | 5.070 | 5.074 | 6.838 | 1.00 |
| DWD ICON (physics) [latest run] + local bias correction | global | 5.136 | 5.131 | 5.136 | 5.139 | 6.998 | 1.00 |
| ECMWF AIFS (AI) [issued 24 h before] + local bias correction | global | 5.181 | 5.177 | 5.180 | 5.183 | 7.014 | 1.00 |
| Baseline: same hour yesterday | baseline | 5.667 | 5.651 | 5.653 | 5.682 | 8.332 | 0.98 |
| Baseline: daily cycle + latest anomaly | baseline | 5.769 | 3.975 | 6.380 | 6.362 | 8.037 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 5.771 | 5.768 | 5.769 | 5.774 | 7.699 | 1.00 |
| DWD ICON (physics) [issued 24 h before] + local bias correction | global | 6.093 | 6.083 | 6.092 | 6.098 | 8.086 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued 24 h before] + local bias correction | global | 6.430 | 6.431 | 6.433 | 6.427 | 8.573 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 6.560 | 6.557 | 6.557 | 6.562 | 8.777 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 6.693 | 6.670 | 6.680 | 6.711 | 8.922 | 1.00 |
| ECMWF IFS 9 km (physics) [issued 24 h before] + local bias correction | global | 6.910 | 6.898 | 6.903 | 6.918 | 9.080 | 0.51 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 7.796 | 7.798 | 7.793 | 7.797 | 10.267 | 1.00 |
| ECMWF AIFS (AI) [issued 24 h before] | global | 7.851 | 7.861 | 7.856 | 7.843 | 10.180 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 8.081 | 8.096 | 8.085 | 8.071 | 10.365 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 8.315 | 8.293 | 8.304 | 8.332 | 10.715 | 1.00 |
| NOAA GFS (physics) [issued 24 h before] + local bias correction | global | 8.782 | 8.756 | 8.771 | 8.800 | 11.349 | 1.00 |
| DWD ICON (physics) [latest run] | global | 8.876 | 8.890 | 8.881 | 8.867 | 11.197 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued 24 h before] | global | 8.924 | 8.930 | 8.926 | 8.920 | 11.549 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] | global | 9.178 | 9.174 | 9.171 | 9.183 | 12.007 | 1.00 |
| DWD ICON (physics) [issued 24 h before] | global | 9.440 | 9.453 | 9.443 | 9.432 | 11.894 | 1.00 |
| ECMWF IFS 9 km (physics) [issued 24 h before] | global | 10.964 | 10.949 | 10.954 | 10.977 | 14.038 | 0.51 |
| NOAA GFS (physics) [latest run] | global | 30.535 | 30.439 | 30.502 | 30.600 | 35.495 | 1.00 |
| NOAA GFS (physics) [issued 24 h before] | global | 31.659 | 31.577 | 31.622 | 31.717 | 36.599 | 1.00 |

## WS (m/s)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| TimesFM 3.0 (Google) | tsfm | 0.393 | 0.328 | 0.399 | 0.422 | 0.801 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 0.395 | 0.345 | 0.407 | 0.413 | 0.693 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 0.395 | 0.329 | 0.403 | 0.424 | 0.719 | 1.00 |
| PWM-W (pure) | ours | 0.421 | 0.353 | 0.431 | 0.450 | 0.749 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 0.473 | 0.471 | 0.472 | 0.475 | 0.822 | 1.00 |
| Baseline: daily cycle + latest anomaly | baseline | 0.492 | 0.390 | 0.521 | 0.529 | 0.847 | 1.00 |
| Baseline: same hour yesterday | baseline | 0.499 | 0.499 | 0.499 | 0.500 | 0.857 | 0.92 |
| DWD ICON (physics) [latest run] + local bias correction | global | 0.586 | 0.585 | 0.585 | 0.586 | 0.962 | 1.00 |
| DWD ICON (physics) [issued 24 h before] + local bias correction | global | 0.622 | 0.622 | 0.622 | 0.622 | 1.002 | 1.00 |
| ECMWF IFS 9 km (physics) [issued 24 h before] + local bias correction | global | 0.705 | 0.703 | 0.705 | 0.707 | 1.212 | 0.45 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 0.717 | 0.716 | 0.716 | 0.717 | 1.072 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued 24 h before] + local bias correction | global | 0.752 | 0.750 | 0.752 | 0.753 | 1.107 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 0.754 | 0.753 | 0.754 | 0.755 | 1.109 | 1.00 |
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 0.760 | 0.759 | 0.760 | 0.761 | 1.109 | 1.00 |
| DWD ICON (physics) [latest run] | global | 0.807 | 0.807 | 0.807 | 0.807 | 1.157 | 1.00 |
| ECMWF AIFS (AI) [issued 24 h before] + local bias correction | global | 0.835 | 0.835 | 0.835 | 0.835 | 1.184 | 1.00 |
| DWD ICON (physics) [issued 24 h before] | global | 0.889 | 0.889 | 0.889 | 0.889 | 1.231 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 0.906 | 0.904 | 0.905 | 0.907 | 1.283 | 1.00 |
| NOAA GFS (physics) [issued 24 h before] + local bias correction | global | 0.929 | 0.928 | 0.928 | 0.930 | 1.311 | 1.00 |
| ECMWF IFS 9 km (physics) [issued 24 h before] | global | 1.017 | 1.016 | 1.016 | 1.017 | 1.442 | 0.45 |
| ECMWF IFS 9 km (physics) [latest run] | global | 1.034 | 1.034 | 1.034 | 1.035 | 1.375 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued 24 h before] | global | 1.098 | 1.098 | 1.098 | 1.099 | 1.428 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 1.120 | 1.120 | 1.120 | 1.121 | 1.467 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 1.130 | 1.129 | 1.129 | 1.130 | 1.478 | 1.00 |
| ECMWF AIFS (AI) [issued 24 h before] | global | 1.281 | 1.281 | 1.281 | 1.281 | 1.626 | 1.00 |
| NOAA GFS (physics) [latest run] | global | 1.789 | 1.792 | 1.789 | 1.787 | 2.162 | 1.00 |
| NOAA GFS (physics) [issued 24 h before] | global | 1.817 | 1.817 | 1.817 | 1.817 | 2.194 | 1.00 |

## Verdicts against the global weather models

BEATS = significantly lower MAE than both the latest run and the bias-corrected latest run.

- PWM-W (pure) vs DWD ICON (physics): AT BEATS (-54.6% / -24.0%); RH TIES / MIXED (-44.0% / -3.2%); WS BEATS (-47.9% / -28.1%)
- PWM-W (pure) vs ECMWF AIFS (AI): AT BEATS (-51.5% / -20.6%); RH TIES / MIXED (-38.5% / -2.0%); WS BEATS (-62.7% / -44.6%)
- PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT BEATS (-53.2% / -23.8%); RH BEATS (-36.3% / -13.9%); WS BEATS (-62.4% / -44.2%)
- PWM-W (pure) vs ECMWF IFS 9 km (physics): AT BEATS (-54.7% / -30.7%); RH BEATS (-45.9% / -24.2%); WS BEATS (-59.3% / -41.3%)
- PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-69.4% / -37.0%); RH BEATS (-83.7% / -40.2%); WS BEATS (-76.5% / -53.5%)
- PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-54.1% / -23.1%); RH BEATS (-47.5% / -9.3%); WS BEATS (-51.1% / -32.6%)
- PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-51.0% / -19.7%); RH BEATS (-42.3% / -8.1%); WS BEATS (-65.1% / -48.1%)
- PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-52.7% / -22.9%); RH BEATS (-40.2% / -19.3%); WS BEATS (-64.8% / -47.7%)
- PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-54.2% / -29.9%); RH BEATS (-49.2% / -29.0%); WS BEATS (-61.8% / -44.9%)
- PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-69.0% / -36.3%); RH BEATS (-84.7% / -44.0%); WS BEATS (-77.9% / -56.4%)

Not tested: GenCast and WeatherNext (no public forecast archive; data needs a Google Cloud access request).

## Log

```
WX_CPCB: 17544 hours x 25 stations, targets ['AT', 'RH', 'WS'] (missing 2.9%, 3.5%, 19.6%), 5 other channels, spreads [3.609999895095825, 13.479999542236328, 0.9300000071525574], 184 graph links, 5 regions; splits {'train': ('2024-01-01T00', '2025-05-02T23'), 'val': ('2025-05-03T00', '2025-07-02T23'), 'test': ('2025-07-03T00', '2025-12-31T23')}
origins: train 11281, validation 241, test 725 (every 6 h); device cuda
variant P0 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1144 val MAE/spread 0.5141 (13s)
    step 1000/6000 loss 0.1267 val MAE/spread 0.5021 (24s)
    step 1500/6000 loss 0.1178 val MAE/spread 0.4864 (36s)
    step 2000/6000 loss 0.1086 val MAE/spread 0.4852 (48s)
    step 2500/6000 loss 0.1003 val MAE/spread 0.4844 (59s)
    step 3000/6000 loss 0.1008 val MAE/spread 0.4783 (71s)
    step 3500/6000 loss 0.0911 val MAE/spread 0.4761 (83s)
    step 4000/6000 loss 0.0911 val MAE/spread 0.4786 (95s)
    step 4500/6000 loss 0.0908 val MAE/spread 0.4767 (106s)
    step 5000/6000 loss 0.0858 val MAE/spread 0.4856 (118s)
    step 5500/6000 loss 0.0804 val MAE/spread 0.4834 (130s)
    step 6000/6000 loss 0.0825 val MAE/spread 0.4859 (142s)
variant P0 seed 1: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1302 val MAE/spread 0.5201 (12s)
    step 1000/6000 loss 0.1140 val MAE/spread 0.4984 (24s)
    step 1500/6000 loss 0.1233 val MAE/spread 0.4917 (35s)
    step 2000/6000 loss 0.1065 val MAE/spread 0.4943 (47s)
    step 2500/6000 loss 0.1119 val MAE/spread 0.4908 (59s)
    step 3000/6000 loss 0.0933 val MAE/spread 0.4941 (71s)
    step 3500/6000 loss 0.0897 val MAE/spread 0.4934 (82s)
    step 4000/6000 loss 0.0939 val MAE/spread 0.4960 (94s)
    step 4500/6000 loss 0.0861 val MAE/spread 0.4945 (106s)
    step 5000/6000 loss 0.0850 val MAE/spread 0.4990 (118s)
    step 5500/6000 loss 0.0811 val MAE/spread 0.4985 (130s)
    step 6000/6000 loss 0.0875 val MAE/spread 0.4950 (142s)
variant P0 seed 2: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1274 val MAE/spread 0.5193 (12s)
    step 1000/6000 loss 0.1197 val MAE/spread 0.5122 (24s)
    step 1500/6000 loss 0.1158 val MAE/spread 0.5061 (36s)
    step 2000/6000 loss 0.1214 val MAE/spread 0.5120 (48s)
    step 2500/6000 loss 0.0990 val MAE/spread 0.5028 (60s)
    step 3000/6000 loss 0.0928 val MAE/spread 0.5052 (72s)
    step 3500/6000 loss 0.0885 val MAE/spread 0.5045 (84s)
    step 4000/6000 loss 0.0948 val MAE/spread 0.5073 (96s)
    step 4500/6000 loss 0.1013 val MAE/spread 0.5043 (108s)
    step 5000/6000 loss 0.0872 val MAE/spread 0.5049 (120s)
    step 5500/6000 loss 0.0953 val MAE/spread 0.4995 (131s)
    step 6000/6000 loss 0.0841 val MAE/spread 0.5058 (143s)
variant P1 seed 0: {'d': 192, 'layers': 4, 'heads': 6, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1151 val MAE/spread 0.5172 (15s)
    step 1000/6000 loss 0.1275 val MAE/spread 0.4989 (29s)
    step 1500/6000 loss 0.1179 val MAE/spread 0.4931 (44s)
    step 2000/6000 loss 0.1099 val MAE/spread 0.4908 (58s)
    step 2500/6000 loss 0.0993 val MAE/spread 0.4862 (72s)
    step 3000/6000 loss 0.1024 val MAE/spread 0.4941 (86s)
    step 3500/6000 loss 0.0888 val MAE/spread 0.4929 (101s)
    step 4000/6000 loss 0.0895 val MAE/spread 0.4935 (115s)
    step 4500/6000 loss 0.0901 val MAE/spread 0.4940 (129s)
    step 5000/6000 loss 0.0836 val MAE/spread 0.5021 (144s)
    step 5500/6000 loss 0.0791 val MAE/spread 0.4995 (158s)
    step 6000/6000 loss 0.0802 val MAE/spread 0.4986 (172s)
variant P2 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': False}
    step 500/6000 loss 0.1166 val MAE/spread 0.5142 (7s)
    step 1000/6000 loss 0.1334 val MAE/spread 0.4979 (14s)
    step 1500/6000 loss 0.1248 val MAE/spread 0.4872 (21s)
    step 2000/6000 loss 0.1171 val MAE/spread 0.4927 (28s)
    step 2500/6000 loss 0.1081 val MAE/spread 0.4874 (36s)
    step 3000/6000 loss 0.1112 val MAE/spread 0.4891 (43s)
    step 3500/6000 loss 0.1017 val MAE/spread 0.4954 (50s)
    step 4000/6000 loss 0.1009 val MAE/spread 0.4953 (57s)
    step 4500/6000 loss 0.1062 val MAE/spread 0.4975 (64s)
    step 5000/6000 loss 0.0989 val MAE/spread 0.4970 (71s)
    step 5500/6000 loss 0.0918 val MAE/spread 0.5003 (78s)
    step 6000/6000 loss 0.0948 val MAE/spread 0.5041 (85s)
variant P3 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 4, 'use_graph': True}
    step 500/6000 loss 0.1479 val MAE/spread 0.5244 (24s)
    step 1000/6000 loss 0.1607 val MAE/spread 0.5014 (49s)
    step 1500/6000 loss 0.1492 val MAE/spread 0.4997 (73s)
    step 2000/6000 loss 0.1426 val MAE/spread 0.4930 (98s)
    step 2500/6000 loss 0.1337 val MAE/spread 0.4899 (122s)
    step 3000/6000 loss 0.1345 val MAE/spread 0.4936 (147s)
    step 3500/6000 loss 0.1218 val MAE/spread 0.4860 (171s)
    step 4000/6000 loss 0.1231 val MAE/spread 0.4895 (195s)
    step 4500/6000 loss 0.1242 val MAE/spread 0.4924 (220s)
    step 5000/6000 loss 0.1188 val MAE/spread 0.4951 (244s)
    step 5500/6000 loss 0.1136 val MAE/spread 0.4952 (268s)
    step 6000/6000 loss 0.1153 val MAE/spread 0.4955 (293s)
validation (MAE / spread): P0 0.4888 +- 0.0118; P1 0.4862, P2 0.4872, P3 0.4860 -> chosen P0
    step 500/6000 loss 0.1318 val MAE/spread 0.5211 (12s)
    step 1000/6000 loss 0.1191 val MAE/spread 0.4972 (24s)
    step 1500/6000 loss 0.1155 val MAE/spread 0.4980 (36s)
    step 2000/6000 loss 0.1115 val MAE/spread 0.4999 (48s)
    step 2500/6000 loss 0.0932 val MAE/spread 0.4909 (60s)
    step 3000/6000 loss 0.0969 val MAE/spread 0.4936 (73s)
    step 3500/6000 loss 0.0861 val MAE/spread 0.4929 (85s)
    step 4000/6000 loss 0.0918 val MAE/spread 0.4915 (96s)
    step 4500/6000 loss 0.0922 val MAE/spread 0.4912 (108s)
    step 5000/6000 loss 0.0899 val MAE/spread 0.4943 (120s)
    step 5500/6000 loss 0.0931 val MAE/spread 0.4926 (132s)
    step 6000/6000 loss 0.0854 val MAE/spread 0.4954 (144s)
    step 500/6000 loss 0.1317 val MAE/spread 0.5256 (12s)
    step 1000/6000 loss 0.1326 val MAE/spread 0.5024 (24s)
    step 1500/6000 loss 0.1128 val MAE/spread 0.4913 (36s)
    step 2000/6000 loss 0.1095 val MAE/spread 0.4925 (47s)
    step 2500/6000 loss 0.1081 val MAE/spread 0.4899 (59s)
    step 3000/6000 loss 0.0918 val MAE/spread 0.4944 (71s)
    step 3500/6000 loss 0.1006 val MAE/spread 0.4970 (83s)
    step 4000/6000 loss 0.0927 val MAE/spread 0.4977 (95s)
    step 4500/6000 loss 0.0830 val MAE/spread 0.4980 (107s)
    step 5000/6000 loss 0.0921 val MAE/spread 0.4967 (118s)
    step 5500/6000 loss 0.0902 val MAE/spread 0.4996 (130s)
    step 6000/6000 loss 0.0893 val MAE/spread 0.5023 (142s)
    step 500/6000 loss 0.1308 val MAE/spread 0.5196 (12s)
    step 1000/6000 loss 0.1183 val MAE/spread 0.5008 (24s)
    step 1500/6000 loss 0.1143 val MAE/spread 0.5005 (36s)
    step 2000/6000 loss 0.1006 val MAE/spread 0.4923 (47s)
    step 2500/6000 loss 0.1025 val MAE/spread 0.4963 (59s)
    step 3000/6000 loss 0.0925 val MAE/spread 0.4967 (71s)
    step 3500/6000 loss 0.0878 val MAE/spread 0.5027 (83s)
    step 4000/6000 loss 0.0914 val MAE/spread 0.5000 (95s)
    step 4500/6000 loss 0.0886 val MAE/spread 0.4993 (107s)
    step 5000/6000 loss 0.0890 val MAE/spread 0.4995 (119s)
    step 5500/6000 loss 0.0818 val MAE/spread 0.5037 (131s)
    step 6000/6000 loss 0.0890 val MAE/spread 0.5069 (143s)
hybrid: 6 global-forecast channels (issued >= 48 h earlier), 11281 training origins from 2024
    step 500/6000 loss 0.1279 val MAE/spread 0.5242 (12s)
    step 1000/6000 loss 0.1110 val MAE/spread 0.5032 (24s)
    step 1500/6000 loss 0.1008 val MAE/spread 0.4908 (36s)
    step 2000/6000 loss 0.1012 val MAE/spread 0.4781 (49s)
    step 2500/6000 loss 0.0867 val MAE/spread 0.4724 (61s)
    step 3000/6000 loss 0.0900 val MAE/spread 0.4783 (73s)
    step 3500/6000 loss 0.0817 val MAE/spread 0.4878 (85s)
    step 4000/6000 loss 0.0848 val MAE/spread 0.4918 (97s)
    step 4500/6000 loss 0.0870 val MAE/spread 0.4938 (109s)
    step 5000/6000 loss 0.0837 val MAE/spread 0.4948 (121s)
    step 5500/6000 loss 0.0840 val MAE/spread 0.4943 (134s)
    step 6000/6000 loss 0.0797 val MAE/spread 0.4990 (146s)
    step 500/6000 loss 0.1228 val MAE/spread 0.5099 (12s)
    step 1000/6000 loss 0.1197 val MAE/spread 0.5208 (24s)
    step 1500/6000 loss 0.1035 val MAE/spread 0.4731 (36s)
    step 2000/6000 loss 0.0981 val MAE/spread 0.4810 (48s)
    step 2500/6000 loss 0.0983 val MAE/spread 0.4856 (60s)
    step 3000/6000 loss 0.0848 val MAE/spread 0.4888 (72s)
    step 3500/6000 loss 0.0925 val MAE/spread 0.4886 (84s)
    step 4000/6000 loss 0.0849 val MAE/spread 0.4961 (97s)
    step 4500/6000 loss 0.0788 val MAE/spread 0.5009 (109s)
    step 5000/6000 loss 0.0845 val MAE/spread 0.4987 (121s)
    step 5500/6000 loss 0.0831 val MAE/spread 0.5007 (133s)
    step 6000/6000 loss 0.0833 val MAE/spread 0.5026 (145s)
    step 500/6000 loss 0.1240 val MAE/spread 0.5160 (12s)
    step 1000/6000 loss 0.1092 val MAE/spread 0.4945 (24s)
    step 1500/6000 loss 0.1033 val MAE/spread 0.4806 (36s)
    step 2000/6000 loss 0.0916 val MAE/spread 0.4710 (48s)
    step 2500/6000 loss 0.0966 val MAE/spread 0.4907 (60s)
    step 3000/6000 loss 0.0864 val MAE/spread 0.4934 (72s)
    step 3500/6000 loss 0.0798 val MAE/spread 0.4893 (84s)
    step 4000/6000 loss 0.0854 val MAE/spread 0.4910 (96s)
    step 4500/6000 loss 0.0830 val MAE/spread 0.5004 (109s)
    step 5000/6000 loss 0.0814 val MAE/spread 0.4936 (121s)
    step 5500/6000 loss 0.0778 val MAE/spread 0.4961 (133s)
    step 6000/6000 loss 0.0836 val MAE/spread 0.5026 (145s)
    Chronos-2 (Amazon, 120M): first 4096 of 18125 series in 21s
    Chronos-2 (Amazon, 120M): first 4096 of 18125 series in 14s
    Chronos-2 (Amazon, 120M): first 4096 of 18125 series in 14s
    TimesFM 2.5 (Google, 200M): first 4096 of 18125 series in 25s
    TimesFM 2.5 (Google, 200M): first 4096 of 18125 series in 25s
opponent tfm25: NOT RUN (CUDA out of memory. Tried to allocate 1.25 GiB. GPU 0 has a total capacity of 14.56 GiB of which 222.81 MiB is free. Including non-PyTorch memory, this process has 14.34 GiB memory in use. Of the allo)
    TimesFM 3.0 (Google): first 4096 of 18125 series in 50s
    TimesFM 3.0 (Google): first 4096 of 18125 series in 49s
    TimesFM 3.0 (Google): first 4096 of 18125 series in 49s
RESULT CPCB PWM-W (pure) vs DWD ICON (physics) on AT: BEATS (MAE -54.6% vs latest run, -24.0% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs DWD ICON (physics) on RH: TIES / MIXED (MAE -44.0% vs latest run, -3.2% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs DWD ICON (physics) on WS: BEATS (MAE -47.9% vs latest run, -28.1% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF AIFS (AI) on AT: BEATS (MAE -51.5% vs latest run, -20.6% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF AIFS (AI) on RH: TIES / MIXED (MAE -38.5% vs latest run, -2.0% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF AIFS (AI) on WS: BEATS (MAE -62.7% vs latest run, -44.6% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -53.2% vs latest run, -23.8% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -36.3% vs latest run, -13.9% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -62.4% vs latest run, -44.2% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -54.7% vs latest run, -30.7% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -45.9% vs latest run, -24.2% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -59.3% vs latest run, -41.3% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -69.4% vs latest run, -37.0% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -83.7% vs latest run, -40.2% vs bias-corrected)
RESULT CPCB PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -76.5% vs latest run, -53.5% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -54.1% vs latest run, -23.1% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -47.5% vs latest run, -9.3% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -51.1% vs latest run, -32.6% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -51.0% vs latest run, -19.7% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -42.3% vs latest run, -8.1% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -65.1% vs latest run, -48.1% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -52.7% vs latest run, -22.9% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -40.2% vs latest run, -19.3% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -64.8% vs latest run, -47.7% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -54.2% vs latest run, -29.9% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -49.2% vs latest run, -29.0% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -61.8% vs latest run, -44.9% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -69.0% vs latest run, -36.3% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -84.7% vs latest run, -44.0% vs bias-corrected)
RESULT CPCB PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -77.9% vs latest run, -56.4% vs bias-corrected)
no Earth-2 runs found (E2 file missing)
```