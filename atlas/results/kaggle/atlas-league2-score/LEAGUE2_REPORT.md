# Atlas League v2.0: Atlas v1.3 against every scorable model (Delhi PM2.5, next 24 h)

Check: Atlas v1.3 reproduced 28.91 / 25.56 (recorded 28.91 / 25.56).

| Entry | Trained: MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | Never trained: MAE | cells covered S / U | Atlas v1.3 against it (trained / never trained) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Atlas v1.3 (ours, 967,632 parameters) | 28.91 | 52.82 | 9.55 | 79 | 13.59 | 26.23 | 30.85 | 33.22 | 25.56 | 100% / 100% | – | – |
| Moirai 2.0 R small (Salesforce), zero-shot | 30.50 | 54.99 | 10.10 | 79 | 14.15 | 29.27 | 32.48 | 34.40 | 26.84 | 100% / 100% | WIN -5.2% (p=0.00011) / WIN -4.8% (p=0.0009) | Atlas BEATS it |
| TiRex (NX-AI), zero-shot | 30.73 | 55.34 | 10.10 | 79 | 13.77 | 29.38 | 32.69 | 35.09 | 27.09 | 100% / 100% | WIN -5.9% (p=2.8e-05) / WIN -5.7% (p=0.00012) | Atlas BEATS it |
| TimesFM 2.5 (Google, zero-shot) | 30.83 | 55.52 | 10.15 | 78 | 13.95 | 29.17 | 32.91 | 35.34 | 27.10 | 100% / 100% | WIN -6.2% (p=1.5e-05) / WIN -5.7% (p=0.00011) | Atlas BEATS it |
| Chronos-2 (Amazon, zero-shot) | 31.17 | 55.81 | 10.23 | 79 | 14.10 | 29.29 | 32.93 | 35.99 | 27.41 | 100% / 100% | WIN -7.3% (p=1.5e-06) / WIN -6.8% (p=2.5e-05) | Atlas BEATS it |
| Chronos-Bolt (Amazon, zero-shot) | 31.35 | 56.00 | 10.26 | 79 | 14.21 | 29.33 | 33.35 | 36.26 | 27.94 | 100% / 100% | WIN -7.8% (p=3.9e-08) / WIN -8.5% (p=1.6e-07) | Atlas BEATS it |
| Granite TTM r2 (IBM), zero-shot | 31.63 | 55.12 | 12.14 | 69 | 16.50 | 30.73 | 33.42 | 34.92 | 27.79 | 100% / 100% | WIN -8.6% (p=3.1e-06) / WIN -8.0% (p=1.4e-06) | Atlas BEATS it |
| Atlas-W v0 (14,043 parameters, 3 seeds, 16 months of Delhi) | 31.97 | 56.81 | 10.51 | 79 | 14.89 | 30.47 | 34.42 | 35.34 | 27.43 | 100% / 100% | WIN -9.6% (p=1.7e-12) / WIN -6.8% (p=9.6e-11) | Atlas BEATS it |
| CAMS global + 30-day local bias correction | 41.03 | 65.54 | 14.35 | 76 | 40.10 | 40.77 | 40.85 | 40.97 | 38.32 | 97% / 88% | WIN -29.0% (p=7.2e-22) / WIN -32.5% (p=2.7e-21) | Atlas BEATS it |
| CAMS global (ECMWF Copernicus), archived forecast | 62.86 | 97.71 | 22.66 | 70 | 61.32 | 62.54 | 62.57 | 62.89 | 53.53 | 97% / 88% | WIN -53.7% (p=4.1e-33) / WIN -51.7% (p=1.8e-35) | Atlas BEATS it |

## How each trained opponent ran

- CAMS global (ECMWF Copernicus), archived forecast: {"source": "Open-Meteo air-quality archive, domain cams_global (0.4 deg); most recent run for each hour", "placed": 37}
- CAMS global + 30-day local bias correction: {"source": "Open-Meteo air-quality archive, domain cams_global (0.4 deg); most recent run for each hour", "placed": 37}
- Moirai 2.0 R small (Salesforce), zero-shot: {"name": "Moirai 2.0 R small (Salesforce)", "licence": "CC-BY-NC-4.0 (evaluation only)", "params": 11000000.0, "context_steps": 512, "minutes": 5.8, "device": "cpu"}
- TiRex (NX-AI), zero-shot: {"name": "TiRex (NX-AI)", "licence": "NXAI community licence (evaluation only)", "params": 35000000.0, "context_steps": 512, "minutes": 284.9, "device": "cpu"}
- Granite TTM r2 (IBM), zero-shot: {"name": "Granite TTM r2 (IBM)", "licence": "Apache-2.0", "params": 799756, "context_steps": 512, "minutes": 0.8, "device": "cpu"}
- Atlas-W v0 (14,043 parameters, 3 seeds, 16 months of Delhi): {"params": 14043, "width": 32, "seeds": 3, "data": "DELHI.npz, 16 months"}
