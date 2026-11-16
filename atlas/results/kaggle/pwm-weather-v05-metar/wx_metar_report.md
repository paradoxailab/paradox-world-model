# PWM-W v0.3 weather league: METAR

Stations: 6. Chosen setting: P0 (validation only). Test origins every 6 h, 24 h ahead.

## AT (deg C)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 0.872 | 0.872 | 0.872 | 0.872 | 1.229 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 0.976 | 0.976 | 0.976 | 0.975 | 1.366 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 0.986 | 0.986 | 0.986 | 0.985 | 1.388 | 1.00 |
| DWD ICON (physics) [latest run] + local bias correction | global | 1.005 | 1.005 | 1.005 | 1.005 | 1.420 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 1.008 | 0.921 | 1.002 | 1.054 | 1.449 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] + local bias correction | global | 1.054 | 1.034 | 1.034 | 1.074 | 1.461 | 1.00 |
| Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) | global-ensemble | 1.083 | 1.059 | 1.059 | 1.107 | 1.526 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] | global | 1.146 | 1.146 | 1.146 | 1.146 | 1.558 | 1.00 |
| DWD ICON (physics) [latest run] | global | 1.159 | 1.159 | 1.159 | 1.160 | 1.590 | 1.00 |
| NOAA AIGFS (AI, GraphCast-based) [latest run] + local bias correction | global | 1.216 | 1.216 | 1.216 | 1.216 | 1.671 | 1.00 |
| NOAA AIGFS (AI, GraphCast-based) [issued before forecast start] + local bias correction | global | 1.236 | 1.232 | 1.232 | 1.240 | 1.689 | 0.75 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 1.239 | 1.239 | 1.239 | 1.239 | 1.675 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 1.242 | 1.242 | 1.242 | 1.242 | 1.681 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] + local bias correction | global | 1.251 | 1.223 | 1.223 | 1.278 | 1.745 | 1.00 |
| PWM-W (pure) | ours | 1.263 | 0.950 | 1.272 | 1.414 | 1.865 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] + local bias correction | global | 1.268 | 1.243 | 1.243 | 1.293 | 1.772 | 0.95 |
| DWD ICON (physics) [issued before forecast start] + local bias correction | global | 1.295 | 1.261 | 1.261 | 1.329 | 1.815 | 0.99 |
| TimesFM 3.0 (Google) | tsfm | 1.341 | 0.993 | 1.355 | 1.507 | 1.982 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 1.354 | 1.355 | 1.354 | 1.354 | 1.879 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 1.357 | 0.999 | 1.369 | 1.529 | 2.023 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 1.403 | 1.032 | 1.415 | 1.583 | 2.024 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] | global | 1.423 | 1.398 | 1.398 | 1.448 | 1.918 | 0.95 |
| DWD ICON (physics) [issued before forecast start] | global | 1.444 | 1.409 | 1.409 | 1.480 | 1.957 | 0.99 |
| ECMWF AIFS (AI) [issued before forecast start] | global | 1.493 | 1.486 | 1.485 | 1.501 | 1.975 | 1.00 |
| NOAA AIGFS (AI, GraphCast-based) [issued before forecast start] | global | 1.550 | 1.577 | 1.575 | 1.526 | 2.116 | 0.75 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] | global | 1.578 | 1.553 | 1.553 | 1.603 | 2.071 | 1.00 |
| Baseline: same hour yesterday | baseline | 1.600 | 1.599 | 1.600 | 1.600 | 2.333 | 0.97 |
| NOAA GFS (physics) [issued before forecast start] + local bias correction | global | 1.605 | 1.568 | 1.568 | 1.641 | 2.217 | 1.00 |
| Baseline: daily cycle + latest anomaly | baseline | 1.631 | 1.157 | 1.751 | 1.808 | 2.302 | 1.00 |
| NOAA AIGFS (AI, GraphCast-based) [latest run] | global | 1.812 | 1.813 | 1.811 | 1.812 | 2.412 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 2.183 | 2.183 | 2.183 | 2.183 | 2.884 | 1.00 |
| NOAA GFS (physics) [latest run] | global | 2.296 | 2.296 | 2.296 | 2.296 | 2.991 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] | global | 2.792 | 2.739 | 2.738 | 2.845 | 3.616 | 1.00 |

## RH (%)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 5.311 | 5.316 | 5.314 | 5.307 | 7.344 | 1.00 |
| PWM-W hybrid (uses global forecasts) | hybrid | 5.487 | 4.906 | 5.484 | 5.779 | 7.708 | 1.00 |
| DWD ICON (physics) [latest run] + local bias correction | global | 5.743 | 5.746 | 5.745 | 5.740 | 7.868 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 5.884 | 5.888 | 5.888 | 5.881 | 7.982 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 6.043 | 6.049 | 6.048 | 6.038 | 8.218 | 1.00 |
| Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) | global-ensemble | 6.202 | 6.079 | 6.076 | 6.326 | 8.458 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] + local bias correction | global | 6.229 | 6.099 | 6.098 | 6.364 | 8.475 | 0.99 |
| PWM-W (pure) | ours | 6.245 | 4.871 | 6.317 | 6.896 | 8.897 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 6.523 | 4.962 | 6.559 | 7.286 | 9.493 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] | global | 6.590 | 6.594 | 6.595 | 6.586 | 8.899 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 6.615 | 5.030 | 6.645 | 7.392 | 9.638 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 6.618 | 6.623 | 6.623 | 6.613 | 8.862 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 6.737 | 5.093 | 6.779 | 7.539 | 9.725 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 6.790 | 6.799 | 6.797 | 6.781 | 8.875 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] + local bias correction | global | 7.060 | 6.960 | 6.958 | 7.159 | 9.599 | 0.99 |
| DWD ICON (physics) [latest run] | global | 7.096 | 7.103 | 7.100 | 7.090 | 9.333 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] + local bias correction | global | 7.162 | 7.033 | 7.031 | 7.292 | 9.792 | 0.95 |
| DWD ICON (physics) [issued before forecast start] + local bias correction | global | 7.190 | 7.006 | 7.005 | 7.376 | 9.759 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] | global | 7.690 | 7.557 | 7.555 | 7.824 | 10.436 | 0.95 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] | global | 7.748 | 7.653 | 7.652 | 7.842 | 10.413 | 0.99 |
| Baseline: daily cycle + latest anomaly | baseline | 7.776 | 5.715 | 8.206 | 8.592 | 10.781 | 1.00 |
| Baseline: same hour yesterday | baseline | 7.954 | 7.950 | 7.957 | 7.954 | 11.540 | 0.97 |
| ECMWF AIFS (AI) [issued before forecast start] | global | 8.070 | 7.962 | 7.962 | 8.182 | 10.418 | 0.99 |
| DWD ICON (physics) [issued before forecast start] | global | 8.264 | 8.147 | 8.146 | 8.383 | 10.880 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 8.542 | 8.554 | 8.543 | 8.535 | 11.390 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] + local bias correction | global | 9.358 | 9.208 | 9.203 | 9.511 | 12.387 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 10.230 | 10.211 | 10.228 | 10.241 | 13.475 | 1.00 |
| NOAA GFS (physics) [latest run] | global | 19.132 | 19.137 | 19.125 | 19.133 | 23.470 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] | global | 20.754 | 20.679 | 20.662 | 20.838 | 25.385 | 1.00 |

## WS (m/s)

| entry | kind | MAE | 1-6h | 7-12h | 13-24h | RMSE | coverage |
|---|---|---|---|---|---|---|---|
| PWM-W hybrid (uses global forecasts) | hybrid | 0.889 | 0.863 | 0.889 | 0.903 | 1.232 | 1.00 |
| ECMWF AIFS (AI) [latest run] + local bias correction | global | 0.910 | 0.911 | 0.910 | 0.910 | 1.244 | 1.00 |
| ECMWF IFS 0.25 (physics) [latest run] + local bias correction | global | 0.913 | 0.913 | 0.913 | 0.913 | 1.244 | 1.00 |
| Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) | global-ensemble | 0.923 | 0.916 | 0.915 | 0.930 | 1.266 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] + local bias correction | global | 0.924 | 0.924 | 0.924 | 0.924 | 1.259 | 1.00 |
| DWD ICON (physics) [latest run] + local bias correction | global | 0.926 | 0.926 | 0.926 | 0.926 | 1.266 | 1.00 |
| ECMWF AIFS (AI) [issued before forecast start] + local bias correction | global | 0.961 | 0.957 | 0.957 | 0.965 | 1.317 | 1.00 |
| DWD ICON (physics) [issued before forecast start] + local bias correction | global | 0.999 | 0.987 | 0.987 | 1.010 | 1.353 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] + local bias correction | global | 1.014 | 1.002 | 1.001 | 1.027 | 1.376 | 0.95 |
| PWM-W (pure) | ours | 1.017 | 0.930 | 1.027 | 1.054 | 1.405 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] + local bias correction | global | 1.019 | 1.010 | 1.010 | 1.028 | 1.387 | 1.00 |
| NOAA AIGFS (AI, GraphCast-based) [latest run] + local bias correction | global | 1.025 | 1.025 | 1.026 | 1.025 | 1.389 | 1.00 |
| TimesFM 3.0 (Google) | tsfm | 1.032 | 0.950 | 1.047 | 1.065 | 1.406 | 1.00 |
| Chronos-2 (Amazon, 120M) | tsfm | 1.036 | 0.951 | 1.050 | 1.070 | 1.409 | 1.00 |
| TimesFM 2.5 (Google, 200M) | tsfm | 1.042 | 0.955 | 1.058 | 1.078 | 1.416 | 1.00 |
| NOAA AIGFS (AI, GraphCast-based) [issued before forecast start] + local bias correction | global | 1.058 | 1.051 | 1.051 | 1.064 | 1.405 | 0.73 |
| ECMWF IFS 0.25 (physics) [latest run] | global | 1.078 | 1.078 | 1.078 | 1.078 | 1.433 | 1.00 |
| NOAA GFS (physics) [latest run] + local bias correction | global | 1.108 | 1.108 | 1.108 | 1.108 | 1.511 | 1.00 |
| ECMWF IFS 9 km (physics) [latest run] | global | 1.112 | 1.112 | 1.112 | 1.112 | 1.470 | 1.00 |
| ECMWF AIFS (AI) [latest run] | global | 1.118 | 1.118 | 1.118 | 1.118 | 1.488 | 1.00 |
| Baseline: last 14 days' daily cycle | baseline | 1.124 | 1.124 | 1.124 | 1.124 | 1.489 | 1.00 |
| NOAA AIGFS (AI, GraphCast-based) [latest run] | global | 1.178 | 1.178 | 1.178 | 1.178 | 1.557 | 1.00 |
| NOAA AIGFS (AI, GraphCast-based) [issued before forecast start] | global | 1.178 | 1.166 | 1.166 | 1.190 | 1.537 | 0.73 |
| ECMWF AIFS (AI) [issued before forecast start] | global | 1.193 | 1.185 | 1.185 | 1.202 | 1.594 | 1.00 |
| ECMWF IFS 0.25 (physics) [issued before forecast start] | global | 1.198 | 1.192 | 1.191 | 1.204 | 1.593 | 1.00 |
| ECMWF IFS 9 km (physics) [issued before forecast start] | global | 1.213 | 1.202 | 1.202 | 1.225 | 1.605 | 0.95 |
| DWD ICON (physics) [latest run] | global | 1.218 | 1.219 | 1.219 | 1.218 | 1.607 | 1.00 |
| DWD ICON (physics) [issued before forecast start] | global | 1.235 | 1.231 | 1.231 | 1.239 | 1.641 | 1.00 |
| NOAA GFS (physics) [latest run] | global | 1.243 | 1.243 | 1.243 | 1.243 | 1.641 | 1.00 |
| NOAA GFS (physics) [issued before forecast start] + local bias correction | global | 1.257 | 1.244 | 1.244 | 1.270 | 1.699 | 1.00 |
| Baseline: daily cycle + latest anomaly | baseline | 1.302 | 1.145 | 1.348 | 1.357 | 1.795 | 1.00 |
| Baseline: same hour yesterday | baseline | 1.312 | 1.312 | 1.312 | 1.312 | 1.807 | 0.97 |
| NOAA GFS (physics) [issued before forecast start] | global | 1.531 | 1.498 | 1.498 | 1.563 | 1.993 | 1.00 |

## Verdicts against the global weather models

BEATS = significantly lower MAE than both the raw and the bias-corrected forecast. STRICT uses the latest run (often issued after our forecast start); ISSUED-BEFORE-START uses the newest run published before it.

- [STRICT] PWM-W (pure) vs DWD ICON (physics): AT LOSES TO (+8.9% / +25.6%); RH LOSES TO (-12.0% / +8.7%); WS LOSES TO (-16.6% / +9.8%)
- [STRICT] PWM-W (pure) vs ECMWF AIFS (AI): AT LOSES TO (+1.7% / +44.8%); RH LOSES TO (-8.0% / +17.6%); WS LOSES TO (-9.1% / +11.7%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT LOSES TO (+1.9% / +29.4%); RH LOSES TO (-5.6% / +6.1%); WS LOSES TO (-5.7% / +11.3%)
- [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT LOSES TO (+10.2% / +28.1%); RH LOSES TO (-5.2% / +3.3%); WS LOSES TO (-8.6% / +10.0%)
- [STRICT] PWM-W (pure) vs NOAA AIGFS (AI, GraphCast-based): AT LOSES TO (-30.3% / +3.8%); WS TIES / MIXED (-13.7% / -0.9%)
- [STRICT] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-45.0% / -6.8%); RH BEATS (-67.4% / -26.9%); WS BEATS (-18.2% / -8.3%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics): AT TIES / MIXED (-12.6% / -2.5%); RH BEATS (-24.4% / -13.1%); WS LOSES TO (-17.7% / +1.8%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI): AT LOSES TO (-15.5% / +19.8%); RH TIES / MIXED (-22.6% / +0.3%); WS LOSES TO (-14.8% / +5.8%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics): AT TIES / MIXED (-20.0% / +1.0%); RH BEATS (-19.2% / -11.3%); WS TIES / MIXED (-15.1% / -0.2%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics): AT TIES / MIXED (-13.0% / -2.3%); RH BEATS (-20.4% / -14.5%); WS TIES / MIXED (-17.2% / -1.0%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA AIGFS (AI, GraphCast-based): AT BEATS (-22.9% / -3.3%); WS BEATS (-15.1% / -5.4%)
- [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics): AT BEATS (-54.8% / -21.3%); RH BEATS (-69.9% / -33.3%); WS BEATS (-33.6% / -19.1%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT TIES / MIXED (-13.1% / +0.3%); RH BEATS (-22.7% / -4.5%); WS BEATS (-27.0% / -4.0%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT LOSES TO (-18.9% / +15.6%); RH LOSES TO (-19.2% / +3.3%); WS BEATS (-20.5% / -2.3%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT LOSES TO (-18.7% / +3.3%); RH BEATS (-17.1% / -6.8%); WS BEATS (-17.5% / -2.6%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT TIES / MIXED (-12.1% / +2.2%); RH BEATS (-16.7% / -9.2%); WS BEATS (-20.0% / -3.7%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA AIGFS (AI, GraphCast-based): AT BEATS (-44.4% / -17.1%); WS BEATS (-24.5% / -13.3%)
- [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-56.1% / -25.6%); RH BEATS (-71.3% / -35.8%); WS BEATS (-28.5% / -19.7%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics): AT BEATS (-30.2% / -22.1%); RH BEATS (-33.6% / -23.6%); WS BEATS (-28.0% / -11.0%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI): AT BEATS (-32.5% / -4.4%); RH BEATS (-32.0% / -11.8%); WS BEATS (-25.5% / -7.4%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics): AT BEATS (-36.1% / -19.4%); RH BEATS (-29.0% / -22.0%); WS BEATS (-25.7% / -12.7%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics): AT BEATS (-29.6% / -21.0%); RH BEATS (-29.4% / -24.2%); WS BEATS (-27.6% / -13.4%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA AIGFS (AI, GraphCast-based): AT BEATS (-37.0% / -21.0%); WS BEATS (-26.1% / -17.7%)
- [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics): AT BEATS (-63.9% / -37.2%); RH BEATS (-73.6% / -41.4%); WS BEATS (-41.9% / -29.3%)

Not tested: GenCast and WeatherNext (no public forecast archive; data needs a Google Cloud access request).

## Log

```
WX_METAR: 51240 hours x 6 stations, targets ['AT', 'RH', 'WS'] (missing 15.1%, 15.1%, 15.1%), 5 other channels, spreads [4.269999980926514, 16.670000076293945, 1.5], 30 graph links, 2 regions; splits {'train': ('2021-01-01T00', '2025-10-31T23'), 'val': ('2025-11-01T00', '2026-01-31T23'), 'test': ('2026-02-01T00', '2026-10-31T23')}
origins: train 41929, validation 365, test 1089 (every 6 h); device cpu
joint-training partner WMO: 20 stations, 40155 origins ending before 2025-11-01T00
variant P0 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1675 val MAE/spread 0.4423 (23s)
    step 1000/6000 loss 0.1591 val MAE/spread 0.4238 (47s)
    step 1500/6000 loss 0.1529 val MAE/spread 0.4102 (70s)
    step 2000/6000 loss 0.1495 val MAE/spread 0.4051 (93s)
    step 2500/6000 loss 0.1430 val MAE/spread 0.4059 (116s)
    step 3000/6000 loss 0.1412 val MAE/spread 0.4054 (139s)
    step 3500/6000 loss 0.1442 val MAE/spread 0.3976 (162s)
    step 4000/6000 loss 0.1480 val MAE/spread 0.3971 (185s)
    step 4500/6000 loss 0.1316 val MAE/spread 0.3958 (208s)
    step 5000/6000 loss 0.1487 val MAE/spread 0.3969 (230s)
    step 5500/6000 loss 0.1340 val MAE/spread 0.3955 (253s)
    step 6000/6000 loss 0.1309 val MAE/spread 0.3946 (276s)
variant P0 seed 1: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1854 val MAE/spread 0.4374 (23s)
    step 1000/6000 loss 0.1506 val MAE/spread 0.4306 (46s)
    step 1500/6000 loss 0.1494 val MAE/spread 0.4131 (69s)
    step 2000/6000 loss 0.1423 val MAE/spread 0.4152 (92s)
    step 2500/6000 loss 0.1672 val MAE/spread 0.4019 (115s)
    step 3000/6000 loss 0.1565 val MAE/spread 0.3999 (137s)
    step 3500/6000 loss 0.1524 val MAE/spread 0.3973 (160s)
    step 4000/6000 loss 0.1369 val MAE/spread 0.3950 (184s)
    step 4500/6000 loss 0.1393 val MAE/spread 0.3935 (206s)
    step 5000/6000 loss 0.1443 val MAE/spread 0.3945 (229s)
    step 5500/6000 loss 0.1488 val MAE/spread 0.3935 (252s)
    step 6000/6000 loss 0.1453 val MAE/spread 0.3952 (275s)
variant P0 seed 2: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1758 val MAE/spread 0.4368 (23s)
    step 1000/6000 loss 0.1579 val MAE/spread 0.4198 (45s)
    step 1500/6000 loss 0.1597 val MAE/spread 0.4147 (68s)
    step 2000/6000 loss 0.1583 val MAE/spread 0.4056 (91s)
    step 2500/6000 loss 0.1453 val MAE/spread 0.4036 (114s)
    step 3000/6000 loss 0.1481 val MAE/spread 0.4034 (138s)
    step 3500/6000 loss 0.1446 val MAE/spread 0.3985 (160s)
    step 4000/6000 loss 0.1465 val MAE/spread 0.3979 (183s)
    step 4500/6000 loss 0.1453 val MAE/spread 0.3941 (206s)
    step 5000/6000 loss 0.1534 val MAE/spread 0.3944 (229s)
    step 5500/6000 loss 0.1401 val MAE/spread 0.3932 (251s)
    step 6000/6000 loss 0.1370 val MAE/spread 0.3922 (274s)
variant P1 seed 0: {'d': 192, 'layers': 4, 'heads': 6, 'ff': 2, 'experts': 0, 'use_graph': True}
    step 500/6000 loss 0.1664 val MAE/spread 0.4352 (36s)
    step 1000/6000 loss 0.1575 val MAE/spread 0.4266 (72s)
    step 1500/6000 loss 0.1521 val MAE/spread 0.4116 (109s)
    step 2000/6000 loss 0.1526 val MAE/spread 0.4066 (146s)
    step 2500/6000 loss 0.1471 val MAE/spread 0.4051 (183s)
    step 3000/6000 loss 0.1399 val MAE/spread 0.4026 (221s)
    step 3500/6000 loss 0.1429 val MAE/spread 0.3969 (258s)
    step 4000/6000 loss 0.1460 val MAE/spread 0.3952 (295s)
    step 4500/6000 loss 0.1347 val MAE/spread 0.3955 (331s)
    step 5000/6000 loss 0.1449 val MAE/spread 0.3929 (368s)
    step 5500/6000 loss 0.1304 val MAE/spread 0.3930 (405s)
    step 6000/6000 loss 0.1260 val MAE/spread 0.3942 (442s)
variant P2 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': False}
    step 500/6000 loss 0.1684 val MAE/spread 0.4382 (18s)
    step 1000/6000 loss 0.1568 val MAE/spread 0.4253 (36s)
    step 1500/6000 loss 0.1524 val MAE/spread 0.4148 (54s)
    step 2000/6000 loss 0.1509 val MAE/spread 0.4149 (71s)
    step 2500/6000 loss 0.1433 val MAE/spread 0.4116 (90s)
    step 3000/6000 loss 0.1427 val MAE/spread 0.4066 (107s)
    step 3500/6000 loss 0.1455 val MAE/spread 0.4004 (125s)
    step 4000/6000 loss 0.1497 val MAE/spread 0.3991 (143s)
    step 4500/6000 loss 0.1337 val MAE/spread 0.3970 (161s)
    step 5000/6000 loss 0.1481 val MAE/spread 0.3964 (179s)
    step 5500/6000 loss 0.1383 val MAE/spread 0.3955 (196s)
    step 6000/6000 loss 0.1322 val MAE/spread 0.3954 (214s)
variant P3 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 4, 'use_graph': True}
    step 500/6000 loss 0.1994 val MAE/spread 0.4437 (31s)
    step 1000/6000 loss 0.1900 val MAE/spread 0.4272 (62s)
    step 1500/6000 loss 0.1885 val MAE/spread 0.4158 (93s)
    step 2000/6000 loss 0.1801 val MAE/spread 0.4099 (124s)
    step 2500/6000 loss 0.1765 val MAE/spread 0.4140 (155s)
    step 3000/6000 loss 0.1703 val MAE/spread 0.4066 (186s)
    step 3500/6000 loss 0.1740 val MAE/spread 0.3974 (217s)
    step 4000/6000 loss 0.1773 val MAE/spread 0.3986 (248s)
    step 4500/6000 loss 0.1636 val MAE/spread 0.3975 (279s)
    step 5000/6000 loss 0.1773 val MAE/spread 0.3967 (311s)
    step 5500/6000 loss 0.1656 val MAE/spread 0.3955 (342s)
    step 6000/6000 loss 0.1633 val MAE/spread 0.3957 (373s)
variant P4 seed 0: {'d': 128, 'layers': 3, 'heads': 4, 'ff': 2, 'experts': 0, 'use_graph': True, 'joint': True}
    step 500/6000 loss 0.1643 val MAE/spread 0.4451 (32s)
    step 1000/6000 loss 0.1440 val MAE/spread 0.4229 (66s)
    step 1500/6000 loss 0.1431 val MAE/spread 0.4177 (99s)
    step 2000/6000 loss 0.1436 val MAE/spread 0.4085 (133s)
    step 2500/6000 loss 0.1477 val MAE/spread 0.4054 (165s)
    step 3000/6000 loss 0.1343 val MAE/spread 0.4041 (198s)
    step 3500/6000 loss 0.1520 val MAE/spread 0.3982 (231s)
    step 4000/6000 loss 0.1377 val MAE/spread 0.3970 (263s)
    step 4500/6000 loss 0.1349 val MAE/spread 0.3960 (296s)
    step 5000/6000 loss 0.1388 val MAE/spread 0.3953 (329s)
    step 5500/6000 loss 0.1386 val MAE/spread 0.3934 (363s)
    step 6000/6000 loss 0.1356 val MAE/spread 0.3920 (396s)
validation (MAE / spread): P0 0.3934 +- 0.0012; P1 0.3929, P2 0.3954, P3 0.3955, P4 0.3920 -> chosen P0
    step 500/6000 loss 0.1642 val MAE/spread 0.4321 (23s)
    step 1000/6000 loss 0.1476 val MAE/spread 0.4168 (46s)
    step 1500/6000 loss 0.1466 val MAE/spread 0.4124 (70s)
    step 2000/6000 loss 0.1519 val MAE/spread 0.4077 (93s)
    step 2500/6000 loss 0.1509 val MAE/spread 0.4066 (116s)
    step 3000/6000 loss 0.1555 val MAE/spread 0.4014 (139s)
    step 3500/6000 loss 0.1414 val MAE/spread 0.3969 (162s)
    step 4000/6000 loss 0.1383 val MAE/spread 0.3953 (186s)
    step 4500/6000 loss 0.1525 val MAE/spread 0.3961 (209s)
    step 5000/6000 loss 0.1539 val MAE/spread 0.3964 (233s)
    step 5500/6000 loss 0.1501 val MAE/spread 0.3951 (256s)
    step 6000/6000 loss 0.1493 val MAE/spread 0.3945 (279s)
    step 500/6000 loss 0.1517 val MAE/spread 0.4378 (23s)
    step 1000/6000 loss 0.1537 val MAE/spread 0.4223 (47s)
    step 1500/6000 loss 0.1606 val MAE/spread 0.4190 (70s)
    step 2000/6000 loss 0.1542 val MAE/spread 0.4041 (93s)
    step 2500/6000 loss 0.1582 val MAE/spread 0.4052 (116s)
    step 3000/6000 loss 0.1490 val MAE/spread 0.4013 (139s)
    step 3500/6000 loss 0.1573 val MAE/spread 0.3999 (163s)
    step 4000/6000 loss 0.1569 val MAE/spread 0.3979 (186s)
    step 4500/6000 loss 0.1375 val MAE/spread 0.3943 (210s)
    step 5000/6000 loss 0.1359 val MAE/spread 0.3961 (233s)
    step 5500/6000 loss 0.1330 val MAE/spread 0.3958 (257s)
    step 6000/6000 loss 0.1394 val MAE/spread 0.3953 (280s)
    step 500/6000 loss 0.1609 val MAE/spread 0.4443 (23s)
    step 1000/6000 loss 0.1716 val MAE/spread 0.4184 (47s)
    step 1500/6000 loss 0.1712 val MAE/spread 0.4119 (71s)
    step 2000/6000 loss 0.1620 val MAE/spread 0.4107 (94s)
    step 2500/6000 loss 0.1569 val MAE/spread 0.4023 (117s)
    step 3000/6000 loss 0.1482 val MAE/spread 0.4016 (141s)
    step 3500/6000 loss 0.1456 val MAE/spread 0.4020 (164s)
    step 4000/6000 loss 0.1397 val MAE/spread 0.3982 (187s)
    step 4500/6000 loss 0.1578 val MAE/spread 0.3956 (210s)
    step 5000/6000 loss 0.1476 val MAE/spread 0.3936 (234s)
    step 5500/6000 loss 0.1420 val MAE/spread 0.3936 (257s)
    step 6000/6000 loss 0.1361 val MAE/spread 0.3938 (280s)
hybrid: 12 global-forecast channels from ['ECMWF IFS 0.25 (physics)', 'ECMWF AIFS (AI)', 'DWD ICON (physics)', 'NOAA GFS (physics)'], 16056 training origins from 2024
    step 500/6000 loss 0.1509 val MAE/spread 0.4081 (26s)
    step 1000/6000 loss 0.1340 val MAE/spread 0.3901 (52s)
    step 1500/6000 loss 0.1286 val MAE/spread 0.3775 (78s)
    step 2000/6000 loss 0.1244 val MAE/spread 0.3816 (104s)
    step 2500/6000 loss 0.1324 val MAE/spread 0.3717 (131s)
    step 3000/6000 loss 0.1231 val MAE/spread 0.3739 (157s)
    step 3500/6000 loss 0.1228 val MAE/spread 0.3754 (184s)
    step 4000/6000 loss 0.1206 val MAE/spread 0.3734 (210s)
    step 4500/6000 loss 0.1142 val MAE/spread 0.3737 (236s)
    step 5000/6000 loss 0.1196 val MAE/spread 0.3802 (263s)
    step 5500/6000 loss 0.1099 val MAE/spread 0.3773 (289s)
    step 6000/6000 loss 0.1152 val MAE/spread 0.3752 (315s)
    step 500/6000 loss 0.1279 val MAE/spread 0.3481 (27s)
    step 1000/6000 loss 0.1235 val MAE/spread 0.3509 (53s)
    step 1500/6000 loss 0.1102 val MAE/spread 0.3513 (80s)
    step 2000/6000 loss 0.1030 val MAE/spread 0.3559 (107s)
    step 2500/6000 loss 0.1100 val MAE/spread 0.3544 (133s)
    step 3000/6000 loss 0.0998 val MAE/spread 0.3577 (160s)
    step 3500/6000 loss 0.1030 val MAE/spread 0.3625 (186s)
    step 4000/6000 loss 0.0969 val MAE/spread 0.3631 (212s)
    step 4500/6000 loss 0.0926 val MAE/spread 0.3679 (239s)
    step 5000/6000 loss 0.0960 val MAE/spread 0.3691 (265s)
    step 5500/6000 loss 0.0875 val MAE/spread 0.3717 (291s)
    step 6000/6000 loss 0.0935 val MAE/spread 0.3718 (318s)
    step 500/6000 loss 0.1254 val MAE/spread 0.3539 (28s)
    step 1000/6000 loss 0.1193 val MAE/spread 0.3577 (56s)
    step 1500/6000 loss 0.1077 val MAE/spread 0.3692 (84s)
    step 2000/6000 loss 0.1007 val MAE/spread 0.3656 (112s)
    step 2500/6000 loss 0.1041 val MAE/spread 0.3676 (141s)
    step 3000/6000 loss 0.0963 val MAE/spread 0.3738 (169s)
    step 3500/6000 loss 0.0965 val MAE/spread 0.3809 (198s)
    step 4000/6000 loss 0.0922 val MAE/spread 0.3806 (226s)
    step 4500/6000 loss 0.0897 val MAE/spread 0.3833 (255s)
    step 5000/6000 loss 0.0926 val MAE/spread 0.3834 (283s)
    step 5500/6000 loss 0.0844 val MAE/spread 0.3852 (311s)
    step 6000/6000 loss 0.0898 val MAE/spread 0.3860 (339s)
hybrid validation: H1 0.3717, H2 0.3481, H3 0.3539 (2 sigma = 0.0024) -> H2
    step 500/6000 loss 0.1248 val MAE/spread 0.3505 (26s)
    step 1000/6000 loss 0.1259 val MAE/spread 0.3507 (53s)
    step 1500/6000 loss 0.1134 val MAE/spread 0.3478 (79s)
    step 2000/6000 loss 0.1127 val MAE/spread 0.3520 (106s)
    step 2500/6000 loss 0.1130 val MAE/spread 0.3537 (132s)
    step 3000/6000 loss 0.1052 val MAE/spread 0.3553 (159s)
    step 3500/6000 loss 0.0984 val MAE/spread 0.3580 (185s)
    step 4000/6000 loss 0.0966 val MAE/spread 0.3633 (212s)
    step 4500/6000 loss 0.0933 val MAE/spread 0.3654 (238s)
    step 5000/6000 loss 0.0892 val MAE/spread 0.3652 (265s)
    step 5500/6000 loss 0.0929 val MAE/spread 0.3693 (291s)
    step 6000/6000 loss 0.0931 val MAE/spread 0.3691 (318s)
    step 500/6000 loss 0.1314 val MAE/spread 0.3543 (27s)
    step 1000/6000 loss 0.1292 val MAE/spread 0.3504 (53s)
    step 1500/6000 loss 0.1172 val MAE/spread 0.3496 (79s)
    step 2000/6000 loss 0.1109 val MAE/spread 0.3512 (106s)
    step 2500/6000 loss 0.1102 val MAE/spread 0.3590 (132s)
    step 3000/6000 loss 0.1063 val MAE/spread 0.3629 (158s)
    step 3500/6000 loss 0.0979 val MAE/spread 0.3652 (185s)
    step 4000/6000 loss 0.0918 val MAE/spread 0.3686 (211s)
    step 4500/6000 loss 0.0895 val MAE/spread 0.3700 (238s)
    step 5000/6000 loss 0.0929 val MAE/spread 0.3725 (265s)
    step 5500/6000 loss 0.0984 val MAE/spread 0.3740 (291s)
    step 6000/6000 loss 0.0914 val MAE/spread 0.3759 (318s)
    step 500/6000 loss 0.1298 val MAE/spread 0.3498 (27s)
    step 1000/6000 loss 0.1210 val MAE/spread 0.3492 (53s)
    step 1500/6000 loss 0.1153 val MAE/spread 0.3557 (80s)
    step 2000/6000 loss 0.1079 val MAE/spread 0.3551 (107s)
    step 2500/6000 loss 0.1048 val MAE/spread 0.3599 (133s)
    step 3000/6000 loss 0.1020 val MAE/spread 0.3596 (160s)
    step 3500/6000 loss 0.1038 val MAE/spread 0.3629 (187s)
    step 4000/6000 loss 0.0968 val MAE/spread 0.3654 (214s)
    step 4500/6000 loss 0.0963 val MAE/spread 0.3701 (240s)
    step 5000/6000 loss 0.0978 val MAE/spread 0.3712 (267s)
    step 5500/6000 loss 0.0945 val MAE/spread 0.3727 (294s)
    step 6000/6000 loss 0.0920 val MAE/spread 0.3733 (320s)
RESULT METAR [STRICT] PWM-W (pure) vs DWD ICON (physics) on AT: LOSES TO (MAE +8.9% vs raw, +25.6% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on AT: TIES / MIXED (MAE -12.6% vs raw, -2.5% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs DWD ICON (physics) on RH: LOSES TO (MAE -12.0% vs raw, +8.7% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on RH: BEATS (MAE -24.4% vs raw, -13.1% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs DWD ICON (physics) on WS: LOSES TO (MAE -16.6% vs raw, +9.8% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs DWD ICON (physics) on WS: LOSES TO (MAE -17.7% vs raw, +1.8% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on AT: LOSES TO (MAE +1.7% vs raw, +44.8% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on AT: LOSES TO (MAE -15.5% vs raw, +19.8% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on RH: LOSES TO (MAE -8.0% vs raw, +17.6% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on RH: TIES / MIXED (MAE -22.6% vs raw, +0.3% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF AIFS (AI) on WS: LOSES TO (MAE -9.1% vs raw, +11.7% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF AIFS (AI) on WS: LOSES TO (MAE -14.8% vs raw, +5.8% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: LOSES TO (MAE +1.9% vs raw, +29.4% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on AT: TIES / MIXED (MAE -20.0% vs raw, +1.0% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: LOSES TO (MAE -5.6% vs raw, +6.1% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -19.2% vs raw, -11.3% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: LOSES TO (MAE -5.7% vs raw, +11.3% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 0.25 (physics) on WS: TIES / MIXED (MAE -15.1% vs raw, -0.2% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: LOSES TO (MAE +10.2% vs raw, +28.1% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on AT: TIES / MIXED (MAE -13.0% vs raw, -2.3% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: LOSES TO (MAE -5.2% vs raw, +3.3% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -20.4% vs raw, -14.5% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: LOSES TO (MAE -8.6% vs raw, +10.0% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs ECMWF IFS 9 km (physics) on WS: TIES / MIXED (MAE -17.2% vs raw, -1.0% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs NOAA AIGFS (AI, GraphCast-based) on AT: LOSES TO (MAE -30.3% vs raw, +3.8% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA AIGFS (AI, GraphCast-based) on AT: BEATS (MAE -22.9% vs raw, -3.3% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs NOAA AIGFS (AI, GraphCast-based) on WS: TIES / MIXED (MAE -13.7% vs raw, -0.9% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA AIGFS (AI, GraphCast-based) on WS: BEATS (MAE -15.1% vs raw, -5.4% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -45.0% vs raw, -6.8% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on AT: BEATS (MAE -54.8% vs raw, -21.3% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -67.4% vs raw, -26.9% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on RH: BEATS (MAE -69.9% vs raw, -33.3% vs bias-corrected)
RESULT METAR [STRICT] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -18.2% vs raw, -8.3% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W (pure) vs NOAA GFS (physics) on WS: BEATS (MAE -33.6% vs raw, -19.1% vs bias-corrected)
RESULT METAR PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on AT: LOSS (MAE +25.3%, p=1.8e-61, 95% CI +22.6..+28.2%)
RESULT METAR PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on RH: LOSS (MAE +13.8%, p=9.4e-31, 95% CI +11.5..+16.1%)
RESULT METAR PWM-W (pure) vs PWM-W hybrid (uses global forecasts) on WS: LOSS (MAE +14.3%, p=2.3e-80, 95% CI +12.9..+15.9%)
RESULT METAR PWM-W (pure) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -22.6%, p=2.8e-110, 95% CI -24.1..-20.9%)
RESULT METAR PWM-W (pure) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -19.7%, p=3.2e-137, 95% CI -20.9..-18.3%)
RESULT METAR PWM-W (pure) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -21.9%, p=7.9e-182, 95% CI -22.9..-20.8%)
RESULT METAR PWM-W (pure) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -42.2%, p=1.3e-59, 95% CI -45.1..-39.3%)
RESULT METAR PWM-W (pure) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -39.0%, p=3.5e-75, 95% CI -41.4..-36.3%)
RESULT METAR PWM-W (pure) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -9.6%, p=3.7e-29, 95% CI -11.1..-8.2%)
RESULT METAR PWM-W (pure) vs Baseline: same hour yesterday on AT: WIN (MAE -22.0%, p=6.9e-54, 95% CI -23.8..-20.0%)
RESULT METAR PWM-W (pure) vs Baseline: same hour yesterday on RH: WIN (MAE -22.2%, p=2.2e-61, 95% CI -23.8..-20.4%)
RESULT METAR PWM-W (pure) vs Baseline: same hour yesterday on WS: WIN (MAE -22.9%, p=1.8e-146, 95% CI -24.1..-21.6%)
RESULT METAR PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: LOSS (MAE +16.6%, p=3.7e-27, 95% CI +13.7..+19.6%)
RESULT METAR PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: TIE (MAE +0.7%, p=0.6, 95% CI -1.8..+3.2%)
RESULT METAR PWM-W (pure) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: LOSS (MAE +10.2%, p=3.9e-39, 95% CI +8.7..+11.7%)
RESULT METAR PWM-W (pure) vs Chronos-2 (Amazon, 120M) on AT: WIN (MAE -6.9%, p=2.3e-12, 95% CI -8.6..-5.1%)
RESULT METAR PWM-W (pure) vs Chronos-2 (Amazon, 120M) on RH: WIN (MAE -5.6%, p=6.1e-09, 95% CI -7.3..-3.9%)
RESULT METAR PWM-W (pure) vs Chronos-2 (Amazon, 120M) on WS: WIN (MAE -1.8%, p=0.0015, 95% CI -2.9..-0.7%)
RESULT METAR PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on AT: WIN (MAE -10.0%, p=1.5e-21, 95% CI -11.9..-8.2%)
RESULT METAR PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on RH: WIN (MAE -7.3%, p=8.5e-14, 95% CI -9.0..-5.7%)
RESULT METAR PWM-W (pure) vs TimesFM 2.5 (Google, 200M) on WS: WIN (MAE -2.4%, p=1.2e-05, 95% CI -3.4..-1.4%)
RESULT METAR PWM-W (pure) vs TimesFM 3.0 (Google) on AT: WIN (MAE -5.8%, p=1.1e-10, 95% CI -7.4..-4.2%)
RESULT METAR PWM-W (pure) vs TimesFM 3.0 (Google) on RH: WIN (MAE -4.3%, p=1.1e-06, 95% CI -5.8..-2.8%)
RESULT METAR PWM-W (pure) vs TimesFM 3.0 (Google) on WS: WIN (MAE -1.5%, p=0.008, 95% CI -2.4..-0.4%)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: TIES / MIXED (MAE -13.1% vs raw, +0.3% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on AT: BEATS (MAE -30.2% vs raw, -22.1% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -22.7% vs raw, -4.5% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on RH: BEATS (MAE -33.6% vs raw, -23.6% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -27.0% vs raw, -4.0% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs DWD ICON (physics) on WS: BEATS (MAE -28.0% vs raw, -11.0% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: LOSES TO (MAE -18.9% vs raw, +15.6% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on AT: BEATS (MAE -32.5% vs raw, -4.4% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: LOSES TO (MAE -19.2% vs raw, +3.3% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on RH: BEATS (MAE -32.0% vs raw, -11.8% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -20.5% vs raw, -2.3% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF AIFS (AI) on WS: BEATS (MAE -25.5% vs raw, -7.4% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: LOSES TO (MAE -18.7% vs raw, +3.3% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on AT: BEATS (MAE -36.1% vs raw, -19.4% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -17.1% vs raw, -6.8% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on RH: BEATS (MAE -29.0% vs raw, -22.0% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -17.5% vs raw, -2.6% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 0.25 (physics) on WS: BEATS (MAE -25.7% vs raw, -12.7% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: TIES / MIXED (MAE -12.1% vs raw, +2.2% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on AT: BEATS (MAE -29.6% vs raw, -21.0% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -16.7% vs raw, -9.2% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on RH: BEATS (MAE -29.4% vs raw, -24.2% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -20.0% vs raw, -3.7% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs ECMWF IFS 9 km (physics) on WS: BEATS (MAE -27.6% vs raw, -13.4% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA AIGFS (AI, GraphCast-based) on AT: BEATS (MAE -44.4% vs raw, -17.1% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA AIGFS (AI, GraphCast-based) on AT: BEATS (MAE -37.0% vs raw, -21.0% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA AIGFS (AI, GraphCast-based) on WS: BEATS (MAE -24.5% vs raw, -13.3% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA AIGFS (AI, GraphCast-based) on WS: BEATS (MAE -26.1% vs raw, -17.7% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -56.1% vs raw, -25.6% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on AT: BEATS (MAE -63.9% vs raw, -37.2% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -71.3% vs raw, -35.8% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on RH: BEATS (MAE -73.6% vs raw, -41.4% vs bias-corrected)
RESULT METAR [STRICT] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -28.5% vs raw, -19.7% vs bias-corrected)
RESULT METAR [ISSUED-BEFORE-START] PWM-W hybrid (uses global forecasts) vs NOAA GFS (physics) on WS: BEATS (MAE -41.9% vs raw, -29.3% vs bias-corrected)
RESULT METAR PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on AT: WIN (MAE -20.2%, p=1.8e-61, 95% CI -22.0..-18.4%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on RH: WIN (MAE -12.1%, p=9.4e-31, 95% CI -13.9..-10.3%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs PWM-W (pure) on WS: WIN (MAE -12.5%, p=2.3e-80, 95% CI -13.7..-11.4%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on AT: WIN (MAE -38.2%, p=4.4e-177, 95% CI -39.8..-36.6%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on RH: WIN (MAE -29.4%, p=1.6e-154, 95% CI -30.8..-27.9%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: daily cycle + latest anomaly on WS: WIN (MAE -31.7%, p=3.5e-283, 95% CI -32.7..-30.6%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on AT: WIN (MAE -53.8%, p=1.4e-87, 95% CI -56.1..-51.5%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on RH: WIN (MAE -46.4%, p=4.9e-103, 95% CI -48.4..-44.0%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: last 14 days' daily cycle on WS: WIN (MAE -20.9%, p=6.6e-117, 95% CI -22.3..-19.6%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on AT: WIN (MAE -37.2%, p=5.4e-92, 95% CI -39.0..-35.2%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on RH: WIN (MAE -31.2%, p=4.5e-75, 95% CI -33.1..-29.2%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Baseline: same hour yesterday on WS: WIN (MAE -32.4%, p=1.2e-240, 95% CI -33.5..-31.2%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on AT: WIN (MAE -6.9%, p=2.5e-30, 95% CI -7.9..-5.9%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on RH: WIN (MAE -11.5%, p=7.2e-53, 95% CI -12.8..-10.3%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Global-model ensemble (IFS+AIFS+ICON+GFS, bias-corrected, issued before forecast start) on WS: WIN (MAE -3.6%, p=3.3e-48, 95% CI -4.1..-3.2%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on AT: WIN (MAE -25.7%, p=5.2e-64, 95% CI -27.7..-23.7%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on RH: WIN (MAE -17.1%, p=7.3e-32, 95% CI -19.2..-14.7%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs Chronos-2 (Amazon, 120M) on WS: WIN (MAE -14.1%, p=1.3e-88, 95% CI -15.3..-13.0%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on AT: WIN (MAE -28.2%, p=7.9e-88, 95% CI -30.0..-26.2%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on RH: WIN (MAE -18.6%, p=1.9e-40, 95% CI -20.6..-16.4%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs TimesFM 2.5 (Google, 200M) on WS: WIN (MAE -14.7%, p=8e-93, 95% CI -15.8..-13.5%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on AT: WIN (MAE -24.8%, p=3.1e-67, 95% CI -26.7..-22.9%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on RH: WIN (MAE -15.9%, p=6.2e-31, 95% CI -18.0..-13.6%)
RESULT METAR PWM-W hybrid (uses global forecasts) vs TimesFM 3.0 (Google) on WS: WIN (MAE -13.8%, p=6.7e-86, 95% CI -15.0..-12.7%)
no Earth-2 runs found (E2 file missing)
```