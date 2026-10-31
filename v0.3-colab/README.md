# Paradox World Model — PWM-Dyn kit (v0.3)

PWM-Dyn is Paradox's physical-world dynamics model. It is trained from scratch on real observations laid out on a physical graph: road-sensor networks, or the IMD rainfall grid over India. It forecasts how conditions evolve, with an 80% uncertainty interval, and handles missing sensors. gpt-oss sits on top as a language layer that explains PWM's numbers.

This kit trains PWM, benchmarks it head-to-head against **Google TimesFM 2.5 and 3.0** (zero-shot) on identical test windows, proves provenance, and writes `RESULTS.md`.

## Run it

Open `PWM_Colab.ipynb` in Google Colab with a GPU runtime and run it top to bottom. It takes about 2–3 hours on a free T4. Everything is saved to your Google Drive, so a disconnect only means re-running and skipping finished steps.

## Layout

| Path | What it is |
|---|---|
| `pwm/model.py` | PWM-Dyn architecture |
| `pwm/data.py` | Real-data loaders: PeMS traffic, IMD rainfall (`central_india`, `north_india`, `west_coast`) |
| `pwm/evaluation.py` | The one scoring function every model is graded with |
| `train.py` | Train one seed; promote only if validation improves |
| `evaluate_pwm.py` | Score the seed ensemble on the test period |
| `opponents/run_timesfm.py` | Google TimesFM, zero-shot, separate environment |
| `reason/gptoss_layer.py` | gpt-oss explanations and what-if scenarios grounded in PWM's numbers |
| `check_provenance.py` | Proves PWM's weights and code contain nothing external |
| `compare.py` | Builds `RESULTS.md` (refuses stub or synthetic runs) |
| `PROVENANCE.md` | What is Paradox's and what is not |
| `tests/make_synthetic_imd.py` | Test-only fake rainfall file for checking the pipeline offline |

## Benchmark protocol

- **PeMS:** 12 steps (1 h) in → 12 steps out, chronological 60/20/20 split, zero values excluded. This is the standard protocol, so PEMS08 numbers are comparable with the published leaderboard.
- **IMD rainfall:** 30 days in → next 7 days, last 3 years held out for test, 3 before that for validation. Dry days count.
- **TimesFM** gets a much longer history (512 steps / 365 days). TimesFM 3.0 also runs in multivariate mode, letting it see other locations.

## Tested so far

Every script was run end-to-end on real PEMS08 data in a CPU workspace, with short training and a stub opponent. The real TimesFM and gpt-oss weights could not be downloaded there, so their numbers come only from your Colab run. Earlier full CPU training of PWM-Dyn (v0.1) scored 14.37 MAE on PEMS08.
