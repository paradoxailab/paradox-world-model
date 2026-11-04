# PWM-Dyn v0.7: real-world conditions (ParadoxBench-1.2)

v0.6 was strong on clean benchmark data but lost to plain per-sensor climatology on PEMS07 when sensors went dark,
and its forecast for a sensor whose latest reading was missing started from the global mean. Real detector
networks look nothing like a clean benchmark: in METR-LA's own training data, 10% of 12-step sensor windows contain
an outage, 53% of those outages black out the whole window and 69% include the latest reading. v0.7 targets that.

## What changes

| Change | Switch | Why |
|---|---|---|
| Last-observed base with climatology fallback | `--fallback` | the forecast is an offset from the last reading that was actually observed, or from the sensor's own train-split time-of-week median when there is none; two cues tell the model how old the reading is |
| Burst-outage training | `--gap_p 0.2 --gap_mean 6` | besides v0.6's whole-window sensor dropout, 20% of sensor windows lose a contiguous run of readings (mean 30 min), usually up to the latest one |
| Weight averaging | `--ema 0.999` | validation and the saved checkpoint use an exponential moving average of the weights |
| Online error correction (Track B) | `paradoxbench/run_online.py` | in streaming use, past forecasts can be checked; their recent errors shift the next forecast (strength chosen on validation, zero allowed) |

Each switch is kept or dropped by rules fixed in `run_v07.py` before any run, using validation data only
(clean, a validation-only set of dark sensors, and validation-only replayed outages). Then the frozen configuration
is trained with fresh seeds 200-202 and test is scored once.

## ParadoxBench-1.2: Track G (real-outage replay)

Every 1.1 task, track and window is unchanged. Track G: in each official test window, 30% of sensors (re-drawn
per window, seed 2027) get their 12-step input replaced by a real outage pattern taken from METR-LA's training
split (a 12-step detector window with at least one missing reading). Scored on those sensors only. Baselines: the
last observed reading (climatology if none) and per-sensor climatology. See `paradoxbench/spec.py`.

## Run

Kaggle, GPU T4 x2, Internet on; attach the v0.6 session's output (File → Add input → Your Work) so v0.6 can be
re-scored on Track G and every v0.6 row is compared:

```
!git clone -q -b v0.7 https://github.com/paradoxailab/paradox-world-model /kaggle/working/repo
%cd /kaggle/working/repo/v0.7-realworld
!python tools/fetch_all.py 2>&1 | tail -2
!python run_v07.py --roots /kaggle/input 2>&1
```

`python run_v07.py --quick --tasks PEMS08 --ab_tasks PEMS08` checks the whole pipeline on a CPU in ~15 minutes.

## Results (Kaggle, 2026-11-04, notebook8ffe55b5c8, 232 min on GPU T4 x2, commit b0f6a08)

Every line below is in [`results/v07_rows_sig_valcond.txt`](results/v07_rows_sig_valcond.txt), copied from the run
log by script (not retyped). Significance: Diebold–Mariano p < 0.05 **and** a day-block bootstrap 95% interval
that excludes 0, as in v0.6.

### Which changes were kept (validation only, seed 0, PEMS08 + METR-LA)

| Configuration | Clean MAE ratio | Dark + outage MAE ratio | Decision |
|---|---|---|---|
| fallback only vs v0.6 recipe | 1.0036 | 1.0463 (worse) | not kept |
| **fallback + outage training vs v0.6 recipe** | **1.0045** | **0.9549** | **kept** |
| + weight averaging (EMA) vs the kept one | 1.0095 | 1.0061 | dropped |

The fallback base alone does not help; it works together with training on burst outages. EMA made validation
worse and was dropped. Online correction was chosen on validation for PEMS08, PEMS04, PEMS03 and PEMS07, and not
for METR-LA and PEMS-BAY (where Track B equals Track A).

### Test MAE, v0.7 (seeds 200–202) vs v0.6 (seeds 100–102)

| Network | A: clean | R: 30% dark | G: real outages (new) | G: climatology |
|---|---|---|---|---|
| PEMS08 | 14.22 vs 14.12 (+0.7%) | **18.86** vs 19.25 (−2.0%) | **18.09** vs 23.03 (−21.5%) | 22.26 |
| PEMS04 | 18.53 vs 18.46 (+0.4%) | 25.42 vs 25.33 (tie) | **21.05** vs 24.89 (−15.4%) | 25.02 |
| PEMS03 | 14.60 vs 14.34 (+1.8%) | 19.14 vs **17.71** (+8.1%) | **18.39** vs 22.04 (−16.6%) | 26.07 |
| PEMS07 | 19.78 vs 19.56 (+1.1%) | **28.35** vs 30.95 (−8.4%) | **25.01** vs 31.72 (−21.2%) | 30.03 |
| METR-LA | 2.918 vs 2.919 (tie) | 3.486 vs **3.364** (+3.6%) | 3.147 vs **3.101** (+1.5%) | 3.894 |
| PEMS-BAY | 1.533 vs 1.519 (+0.9%) | 2.390 vs **2.306** (+3.7%) | **1.959** vs 2.196 (−10.8%) | 2.531 |

Every difference marked with a percentage is significant except the two ties.

- **Real outages (Track G):** 11–22% lower error than v0.6 on five of six networks. v0.6 was worse than plain
  per-sensor climatology on PEMS08 and PEMS07 under real outages; v0.7 beats climatology on all six. On METR-LA
  (the network whose outages are replayed, and whose own data already has 8% missing readings) v0.7 is 1.5% worse.
- **Fully dark sensors (Track R):** v0.7 now beats climatology on PEMS07 (28.35 vs 29.10), the one network where v0.6
  lost. It is better than v0.6 on PEMS08 and PEMS07, and worse on PEMS03, METR-LA and PEMS-BAY.
- **Clean data (Track A):** the price is 0.4–1.8% higher MAE on five networks (a tie on METR-LA). Against STID,
  v0.7 is tied on PEMS08 and PEMS04 and significantly 0.8% worse on PEMS07 (v0.6 was 0.3% ahead there, not significant).
- **Open context (Track B) with online correction:** PEMS08 14.00 (v0.6-LC 14.18; now statistically tied with
  STAEformer, p = 0.13), PEMS04 18.33 (better than v0.6 and STID's 18.49, the STID gap not significant), PEMS03 14.27,
  PEMS07 19.61.

### Against TimesFM 3.0 (Track B, every metric)

| Network | MAE | RMSE | MAPE | QL | IS80 | COV80 closer to 80% |
|---|---|---|---|---|---|---|
| PEMS08 | **14.00** / 14.55 | **23.22** / 23.57 | 9.154 / **9.150** | **4.553** / 4.686 | **66.57** / 67.84 | **80.1%** / 80.7% |
| PEMS04 | **18.33** / 19.13 | **30.29** / 31.02 | 12.81 / **12.60** | **5.900** / 6.137 | **85.35** / 88.42 | **79.8%** / 80.7% |
| PEMS03 | 14.27 / **14.15** | 22.94 / **22.70** | 15.12 / **13.39** | 4.605 / **4.541** | 66.81 / **65.50** | 78.4% / **80.7%** |
| PEMS07 | **19.61** / 20.27 | **32.60** / 33.13 | **8.22** / 8.47 | **6.405** / 6.556 | **94.14** / 95.32 | **79.8%** / 81.0% |
| METR-LA | **2.918** / 3.401 | **5.874** / 6.972 | **7.91** / 9.75 | **0.964** / 1.146 | **14.33** / 17.37 | **80.3%** / 81.3% |
| PEMS-BAY | **1.533** / 1.661 | **3.469** / 3.947 | **3.40** / 3.77 | **0.509** / 0.553 | **7.60** / 8.29 | **79.1%** / 81.0% |

PWM-Dyn v0.7 / TimesFM 3.0 zero-shot; bold = better. v0.7 wins 28 of 36 traffic metric pairs. The PEMS03 MAE gap
shrank to +0.8% and is no longer significant (p = 0.65). Still lost: all of PEMS03 and MAPE on PEMS08 / PEMS04
(rainfall was not re-run and stays as in v0.6, where MAPE is also lost). These are the targets of v0.8, which gives every
network the long-context input (our PEMS03 model still reads 12 steps; TimesFM reads 512) and tests a
relative-error loss term, with no extra data.
