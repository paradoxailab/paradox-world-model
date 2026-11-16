# Raw outputs of the Atlas runs (Kaggle)

Copied unchanged on 2026-11-17 from each run's output folder (Kaggle session id in brackets). These are the files the
results in `../../README.md`, `../../MODELS.md` and `../../THRESHOLD_FUNCTIONS.md` were read from. Weights are in
`../../models/`; forecast arrays (`.npz`) and the 5 GB WEATHER-5K array are not copied (too large; the scripts rebuild them).

| Folder | What it is | Section of `atlas/README.md` |
|---|---|---|
| `atlas-w5k-fetch` (370241076) | WEATHER-5K download and conversion: 5,672 stations × 87,648 hours × 5 variables, no missing values (check C1) | World benchmarks plan; C1 passed |
| `atlas-w5k-check` (370251849) | DLinear and persistence on WEATHER-5K at 24 / 72 / 120 / 168 h: the pipeline check against published numbers (C2) | WB1 results |
| `atlas-w5k-atlas1m-h24` (370257952) | Atlas-5K v1, 0.97M, 24 h: training log, validation 2022 and the single test 2023 | WB1 results |
| `atlas-w5k-v2a` (370284708) | Atlas-5K v2a (150,000 steps), validation only | Atlas-5K v2 rules; v2a result |
| `atlas-w5k-thr-a` (370285030) | WB1-T data shares 1/64, 1/16, 1/4 (validation only) | WB1-T |
| `atlas-wa-score` (370108354) | T-A: all-India test with ERA5 weather (upper bound): W1, Atlas-F2, TimesFM 2.5, Atlas-India | T-A results |
| `atlas-tb-score` (370236062) | T-B: Delhi winter 2024–25 with real day-before forecasts; B5 paired test | T-B results |
| `atlas-i1-score` (369668704) | I1: Atlas (no weather) against published operational Day-1 numbers, Delhi winter 2024–25 | I1 results |
| `atlas-india-score` (369103190) | All-India league (14 networks, 263 stations) | Atlas-India v1.0 against TimesFM 2.5 |
| `atlas-league2-score` (369221889) | Delhi league v2 | Atlas League v2.0 results |
| `atlas-lono-score` (369556323) | Leave-one-network-out (Uttar Pradesh, Haryana, Maharashtra, Karnataka) | L1 results: leave one network out |
| `atlas-thr-score-t1` (370236705) | T1 transfer threshold function: scratch and transfer laws, n* per network | T1 results |
| `atlas-w1-s400` / `s401` / `s402` | Atlas W1 training logs, three seeds (weights in `../../models/`) | W1 seeds |

Still running when copied: Atlas-5K v2c and the WB1-T shares 1/32, 1/8, 1/2; they will be added when they finish.
