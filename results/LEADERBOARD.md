# ParadoxBench-1 leaderboard

Official test windows (every 2nd). Ranked by MAE. Lower is better for MAE, RMSE, QL and IS80; COV80 should be close to 80 %.
Traffic in vehicles per 5 min (zero readings excluded); rainfall in mm/day (dry days included, so MAPE is not meaningful for rain).

## PEMS08 — Track A: Standard (12 steps / 30 days of history)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4.1** | specialist (Paradox, trained from scratch) | 0.3M | 12 | 14.50 | 23.99 | 9.4% | 4.696 | 68.39 | 79.7% |
| 2 | PWM-Dyn v0.4 | specialist (Paradox, trained from scratch) | 0.3M | 12 | 14.53 | 23.91 | 9.5% | 4.719 | 68.94 | 79.7% |
| 3 | Climatology quantiles | baseline | 0 | 0 | 22.18 | 40.77 | 13.6% | 7.625 | 117.83 | 71.4% |
| 4 | Last value | baseline | 0 | 1 | 25.30 | 38.66 | 15.7% | - | - | - |

## PEMS08 — Track B: Open context (up to 512 steps / 365 days)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4.1-LC** | specialist (Paradox, trained from scratch) | 0.3M | 300 | 14.15 | 23.24 | 9.2% | 4.593 | 67.05 | 79.5% |
| 2 | PWM-Dyn v0.4-LC | specialist (Paradox, trained from scratch) | 0.3M | 300 | 14.38 | 23.48 | 9.5% | 4.660 | 67.91 | 79.7% |
| 3 | TimesFM 3.0 multivariate | foundation (Google, zero-shot) | - | 512 | 14.55 | 23.57 | 9.2% | 4.686 | 67.84 | 80.7% |
| 4 | TimesFM 2.5 | foundation (Google, zero-shot) | 200M | 512 | 15.04 | 24.09 | 9.4% | 4.857 | 70.54 | 82.4% |
| 5 | Climatology quantiles | baseline | 0 | 0 | 22.18 | 40.77 | 13.6% | 7.625 | 117.83 | 71.4% |
| 6 | Last value | baseline | 0 | 1 | 25.30 | 38.66 | 15.7% | - | - | - |
| 7 | Seasonal naive | baseline | 0 | 300 | 36.54 | 60.77 | 24.6% | - | - | - |

## PEMS08 — Track R: Robustness (30 % of locations hidden; scored on hidden only)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4-LC** | specialist (Paradox, trained from scratch) | 0.3M | 300 | 18.70 | 33.45 | 12.4% | 6.470 | 100.61 | 76.8% |
| 2 | PWM-Dyn v0.4.1-LC | specialist (Paradox, trained from scratch) | 0.3M | 300 | 18.81 | 33.49 | 12.6% | 6.468 | 99.99 | 76.4% |
| 3 | Climatology quantiles | baseline | 0 | 0 | 21.78 | 41.08 | 13.9% | 7.411 | 113.41 | 72.4% |

## PEMS08 — Track Z: Zero-shot transfer (never saw PEMS08)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4-LC inductive (PEMS04 only)** | specialist (Paradox, trained from scratch) | 0.2M | 300 | 16.36 | 25.73 | 12.8% | 5.510 | 83.47 | 86.7% |
| 2 | PWM-Dyn v0.4.1-LC inductive (PEMS04 only) | specialist (Paradox, trained from scratch) | 0.2M | 300 | 16.57 | 25.94 | 13.7% | 5.514 | 82.58 | 85.3% |

## PEMS04 — Track A: Standard (12 steps / 30 days of history)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4.1** | specialist (Paradox, trained from scratch) | 0.3M | 12 | 19.02 | 31.81 | 12.8% | 6.101 | 87.90 | 79.8% |
| 2 | PWM-Dyn v0.4 | specialist (Paradox, trained from scratch) | 0.3M | 12 | 19.21 | 31.75 | 13.1% | 6.156 | 88.65 | 79.6% |
| 3 | Climatology quantiles | baseline | 0 | 0 | 25.02 | 41.36 | 16.1% | 8.431 | 127.81 | 71.5% |
| 4 | Last value | baseline | 0 | 1 | 31.56 | 48.25 | 21.3% | - | - | - |

## PEMS04 — Track B: Open context (up to 512 steps / 365 days)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4.1** | specialist (Paradox, trained from scratch) | 0.3M | 12 | 19.02 | 31.81 | 12.8% | 6.101 | 87.90 | 79.8% |
| 2 | TimesFM 3.0 multivariate | foundation (Google, zero-shot) | - | 512 | 19.14 | 31.02 | 12.6% | 6.137 | 88.42 | 80.7% |
| 3 | PWM-Dyn v0.4-LC | specialist (Paradox, trained from scratch) | 0.3M | 300 | 19.18 | 31.52 | 13.1% | 6.135 | 88.16 | 80.0% |
| 4 | TimesFM 2.5 | foundation (Google, zero-shot) | 200M | 512 | 19.70 | 31.70 | 13.2% | 6.337 | 91.61 | 82.0% |
| 5 | Climatology quantiles | baseline | 0 | 0 | 25.02 | 41.36 | 16.1% | 8.431 | 127.81 | 71.5% |
| 6 | Last value | baseline | 0 | 1 | 31.56 | 48.25 | 21.3% | - | - | - |
| 7 | Seasonal naive | baseline | 0 | 300 | 40.67 | 66.64 | 27.1% | - | - | - |

## PEMS04 — Track R: Robustness (30 % of locations hidden; scored on hidden only)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4.1** | specialist (Paradox, trained from scratch) | 0.3M | 12 | 24.69 | 42.64 | 18.0% | 8.324 | 126.27 | 78.0% |
| 2 | PWM-Dyn v0.4-LC | specialist (Paradox, trained from scratch) | 0.3M | 300 | 24.99 | 43.03 | 18.2% | 8.484 | 129.58 | 78.1% |
| 3 | Climatology quantiles | baseline | 0 | 0 | 27.39 | 45.60 | 15.9% | 9.199 | 139.04 | 71.3% |

## IMD-CI — Track A: Standard (12 steps / 30 days of history)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4** | specialist (Paradox, trained from scratch) | 0.4M | 30 | 2.84 | 10.42 | 268.3% | 1.073 | 18.01 | 84.7% |
| 2 | Climatology quantiles | baseline | 0 | 0 | 2.89 | 10.70 | 229.0% | 1.088 | 18.21 | 91.0% |
| 3 | Last value | baseline | 0 | 1 | 4.37 | 13.55 | 1328.9% | - | - | - |

## IMD-CI — Track B: Open context (up to 512 steps / 365 days)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4** | specialist (Paradox, trained from scratch) | 0.4M | 30 | 2.84 | 10.42 | 268.3% | 1.073 | 18.01 | 84.7% |
| 2 | Climatology quantiles | baseline | 0 | 0 | 2.89 | 10.70 | 229.0% | 1.088 | 18.21 | 91.0% |
| 3 | TimesFM 3.0 multivariate | foundation (Google, zero-shot) | - | 365 | 2.92 | 10.65 | 204.0% | 1.147 | 19.79 | 86.3% |
| 4 | TimesFM 2.5 | foundation (Google, zero-shot) | 200M | 365 | 2.96 | 10.58 | 277.4% | 1.184 | 20.72 | 84.3% |
| 5 | Last value | baseline | 0 | 1 | 4.37 | 13.55 | 1328.9% | - | - | - |
| 6 | Seasonal naive | baseline | 0 | 372 | 4.68 | 14.11 | 1171.0% | - | - | - |

## IMD-CI — Track R: Robustness (30 % of locations hidden; scored on hidden only)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4** | specialist (Paradox, trained from scratch) | 0.4M | 30 | 2.84 | 10.38 | 272.2% | 1.072 | 17.99 | 85.5% |
| 2 | Climatology quantiles | baseline | 0 | 0 | 2.88 | 10.64 | 211.4% | 1.085 | 18.12 | 91.1% |

## IMD-WC — Track A: Standard (12 steps / 30 days of history)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4** | specialist (Paradox, trained from scratch) | 0.4M | 30 | 3.42 | 12.01 | 274.7% | 1.245 | 20.27 | 82.9% |
| 2 | Climatology quantiles | baseline | 0 | 0 | 3.65 | 13.01 | 289.7% | 1.312 | 21.09 | 91.0% |
| 3 | Last value | baseline | 0 | 1 | 4.88 | 14.94 | 737.4% | - | - | - |

## IMD-WC — Track B: Open context (up to 512 steps / 365 days)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4** | specialist (Paradox, trained from scratch) | 0.4M | 30 | 3.42 | 12.01 | 274.7% | 1.245 | 20.27 | 82.9% |
| 2 | TimesFM 3.0 multivariate | foundation (Google, zero-shot) | - | 365 | 3.62 | 12.78 | 208.7% | 1.332 | 21.85 | 87.2% |
| 3 | Climatology quantiles | baseline | 0 | 0 | 3.65 | 13.01 | 289.7% | 1.312 | 21.09 | 91.0% |
| 4 | TimesFM 2.5 | foundation (Google, zero-shot) | 200M | 365 | 3.67 | 12.65 | 246.9% | 1.378 | 23.00 | 85.2% |
| 5 | Last value | baseline | 0 | 1 | 4.88 | 14.94 | 737.4% | - | - | - |
| 6 | Seasonal naive | baseline | 0 | 372 | 5.69 | 17.07 | 1122.7% | - | - | - |

## IMD-WC — Track R: Robustness (30 % of locations hidden; scored on hidden only)

| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **PWM-Dyn v0.4** | specialist (Paradox, trained from scratch) | 0.4M | 30 | 3.43 | 12.07 | 288.5% | 1.263 | 20.75 | 83.2% |
| 2 | Climatology quantiles | baseline | 0 | 0 | 3.60 | 12.85 | 307.5% | 1.300 | 21.00 | 90.8% |
