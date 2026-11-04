# PWM-Dyn v0.8 (prepared, not yet run): significant wins over TimesFM 3.0 on every metric, no extra data, present-day data

v0.7 beats TimesFM 3.0 zero-shot on 28 of 36 traffic metric pairs (Track B). It still loses all of PEMS03, where our
model reads 12 steps and TimesFM reads 512, and MAPE on PEMS08 / PEMS04. v0.8 targets those, and adds a task built
from data up to the latest published month.

**New task UK-M25 (ParadoxBench-1.3, present-day data).** National Highways' live WebTRIS API (MIDAS loop sensors,
free, Open Government Licence v3.0): 190 sensors on the M25 and the radial motorways around London, 15-minute vehicle
counts, **2025-07-01 to 2026-06-29** (WebTRIS publishes with a lag of about four months; 2026-06-29 was the latest
complete day on 2026-11-04). Real outages are kept: 6.9% of readings are missing. Splits 70/10/20 by time, so the test
period is about 5 May to 29 June 2026. Built by `tools/fetch_webtris.py` (selection rules fixed before downloading);
no data is re-hosted.

**What v0.8 changes** (every choice made on validation by rules fixed in `run_v08.py` before the run):
- long-context input (the series' own history, 300 steps on 5-minute data, inside TimesFM's 512) on every network,
  with the online-correction window cut so the total look-back stays within 512;
- width / depth chosen on validation: 96 or 128 channels, 3 or 4 blocks; a larger model is kept only if it is at
  least 0.5% better (all stay under one million parameters);
- a relative-error loss term (`--rel_w`) for MAPE, kept only if validation MAPE falls by at least 2% while MAE rises
  by at most 0.3% and RMSE by at most 0.5%;
- rainfall re-trained with the v0.7 recipe.

**Opponents.** TimesFM 3.0 multivariate zero-shot is re-run where no saved forecast exists (PEMS08, PEMS04, UK-M25,
both rainfall regions), so every metric can be tested; STID (official code) is trained on UK-M25.
**Tests on every metric.** Diebold–Mariano and day-block bootstrap on per-window losses of MAE, squared error (RMSE),
absolute percentage error (MAPE), pinball loss (QL) and interval score (IS80); significant = p < 0.05 and a 95%
interval that excludes 0.

Every model still trains only on its own network's training split. Run it on Kaggle (GPU T4 x2, Internet on), with
the v0.7 session's output (`notebook8ffe55b5c8`) and the UK-M25 data notebook's output (`notebooke7bbb29c74`) attached:

```
!pip install -q timesfm imdlib torchinfo 2>&1 | tail -1
!git clone -q -b v0.8 https://github.com/paradoxailab/paradox-world-model /kaggle/working/repo
%cd /kaggle/working/repo/v0.8-longcontext
!python tools/fetch_all.py --opponents 2>&1 | tail -2
!python run_v08.py --roots /kaggle/input 2>&1
```

The v0.7 description follows, unchanged.

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
