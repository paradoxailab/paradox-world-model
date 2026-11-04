# PWM-Dyn v0.8 (prepared, not yet run): close the remaining gaps to TimesFM 3.0, with no extra data

v0.7 beats TimesFM 3.0 zero-shot on 28 of 36 traffic metric pairs (Track B). It still loses all of PEMS03, where our
model reads 12 steps and TimesFM reads 512, and MAPE on PEMS08 / PEMS04. v0.8 keeps v0.7's frozen real-condition
recipe and adds:

- the long-context input (the same series' own history, 300 steps, inside TimesFM's 512) on every network, with the
  online correction window cut so the total look-back stays within 512;
- a relative-error loss term (`--rel_w`), kept only if validation MAPE falls by at least 2% while validation MAE rises
  by at most 0.3% and RMSE by at most 0.5% (rule in `run_v08.py`);
- rainfall re-trained with the v0.7 recipe (standard and long context).

Every model still trains only on its own network's training split. Track B picks, per network on validation,
between the v0.7 standard ensemble and the v0.8 long-context ensemble. Run it with the v0.7 session's output attached:

```
!git clone -q -b v0.8 https://github.com/paradoxailab/paradox-world-model /kaggle/working/repo
%cd /kaggle/working/repo/v0.8-longcontext
!pip install -q imdlib 2>&1 | tail -1
!python tools/fetch_all.py 2>&1 | tail -2
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
