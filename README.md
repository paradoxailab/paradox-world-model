# Paradox World Model (PWM) — PWM-Dyn and ParadoxBench

**Paradox AI Lab** · [paradoxailab.com](https://paradoxailab.com) · contact.paradoxailab@gmail.com
Authors: Aditya Kumar, Anupam Singh

**Current version: PWM-Dyn v0.7 · ParadoxBench-1.2 (2026-11-04)**, built for real operating conditions (sensor outages);
see [`v0.7-realworld/`](v0.7-realworld). v0.6 (2026-11-03) remains the best model on clean data. Paper: [`paper-conference/named/PWM-Dyn_ParadoxBench_v0.6.pdf`](paper-conference/named/PWM-Dyn_ParadoxBench_v0.6.pdf)
(an anonymous build for double-blind review is in [`paper-conference/`](paper-conference)).

PWM-Dyn is a small (0.3–0.4 M parameters) physical-dynamics model that forecasts how traffic and rainfall
evolve and spread over real networks — California highway sensors and the India Meteorological
Department rainfall grid — with calibrated uncertainty and robustness to dead sensors. It is trained
from random initialisation on public data, benchmarked head-to-head against Google's TimesFM 2.5 and
3.0 foundation models on identical test windows, and provenance-audited (no external model code or
weights inside PWM).

**ParadoxBench** is the open benchmark released with it: eight tasks (six traffic networks, two
Indian rainfall regions), four tracks (standard, open context, dead-sensor robustness, zero-shot
transfer), one scorer, frozen test windows, saved forecasts, paired significance tests, and a
submission format anyone can use.

## Headline: v0.7 under real operating conditions (ParadoxBench-1.2)

Real detector networks lose readings in bursts: in METR-LA's own training data, 53% of outage windows are fully
dark and 69% include the latest reading. v0.7 forecasts from the last reading that actually arrived (or the
sensor's own usual pattern) and is trained on burst outages. The new **Track G** replays real METR-LA outage
patterns on 30% of sensors in every test window. Test MAE, v0.7 vs v0.6, scored on the affected sensors:

| Network | v0.7 | v0.6 | Change | Per-sensor climatology |
|---|---|---|---|---|
| PEMS08 | **18.09** | 23.03 | −21.5% | 22.26 |
| PEMS04 | **21.05** | 24.89 | −15.4% | 25.02 |
| PEMS03 | **18.39** | 22.04 | −16.6% | 26.07 |
| PEMS07 | **25.01** | 31.72 | −21.2% | 30.03 |
| METR-LA | 3.147 | **3.101** | +1.5% | 3.894 |
| PEMS-BAY | **1.959** | 2.196 | −10.8% | 2.531 |

All six differences are significant. Under real outages v0.6 was worse than climatology on PEMS08 and PEMS07; v0.7
beats it everywhere, and on fully dark sensors it now beats climatology on PEMS07 as well. The cost is 0.4–1.8% higher
MAE on clean data (Track A), so v0.6 stays the clean-data entry. With online error correction (Track B), v0.7 beats
TimesFM 3.0 zero-shot on 28 of 36 traffic metric pairs; it still loses PEMS03 and MAPE on PEMS08 / PEMS04. Full
tables: [`v0.7-realworld/README.md`](v0.7-realworld/README.md#results-kaggle-2026-11-04-notebook8ffe55b5c8-232-min-on-gpu-t4-x2-commit-b0f6a08) ·
leaderboard: [`results/LEADERBOARD_1.2.md`](results/LEADERBOARD_1.2.md).

## v0.6 on ParadoxBench-1.1 (clean data) (test MAE, lower is better)

Track A (12-step context, every model trained on the network). STID, Graph WaveNet and STAEformer were
trained with their authors' official code on our exact windows; † = stopped by its wall-clock budget
before its authors' schedule ended. TimesFM 3.0 is zero-shot with 512 steps of history (Track B).

| Network | PWM-Dyn v0.6 (3 seeds) | STID | Graph WaveNet | STAEformer | TimesFM 3.0 |
|---|---|---|---|---|---|
| PEMS08 | 14.12 | 14.18 | 14.77 | **13.93**† | 14.55 |
| PEMS04 | **18.46** | 18.49 | 19.37† | 19.21† | 19.13 |
| PEMS03 (new in 1.1) | 14.34 | 15.50 | 14.70† | 15.45† | **14.15** |
| PEMS07 (new) | **19.56** | 19.62† | 23.39† | out of memory | 20.27 |
| METR-LA (new) | **2.92** | 3.12 | 3.05† | 3.09† | 3.40 |
| PEMS-BAY (new) | **1.52** | 1.56† | 1.57† | 1.60† | 1.66 |

- Statistically tied with STID on PEMS08 and PEMS04; significantly better on PEMS03, METR-LA and
  PEMS-BAY. STAEformer's PEMS08 lead is significant. Single PWM-Dyn seeds are slightly worse than single
  STID runs on PEMS08, PEMS04 and PEMS07 — part of the margin is ensembling.
- The v0.4 accuracy loss is explained (the climatology input) and fixed: PEMS08 14.12, PEMS04 18.46,
  better than v0.3 (14.18 / 18.50).
- With 30 % of sensors dark, PWM-Dyn beats per-sensor climatology on 7 of 8 tasks (not PEMS07);
  specialists without a missing-data mechanism fail.

Full leaderboard: [`results/LEADERBOARD_1.1.md`](results/LEADERBOARD_1.1.md) · every row and test:
[`v0.6-conference/results/`](v0.6-conference/results) · code and how to re-run:
[`v0.6-conference/README.md`](v0.6-conference/README.md).

## Previous version: ParadoxBench-1, open-context track (MAE, lower is better)

| Task | PWM-Dyn (0.3 M) | TimesFM 3.0 multivariate | TimesFM 2.5 (200 M) | Climatology |
|---|---|---|---|---|
| PEMS08 traffic, 1 h ahead | **14.15** (v0.4.1) | 14.55 | 15.04 | 22.18 |
| PEMS04 traffic, 1 h ahead | **19.02** (v0.4.1) | 19.13 | 19.70 | 25.02 |
| IMD rainfall, central India, 7 days | **2.84** (v0.4) | 2.92 | 2.96 | 2.89 |
| IMD rainfall, Konkan / Western Ghats, 7 days | **3.41** (v0.4) | 3.62 | 3.67 | 3.65 |

PWM-Dyn also has the lowest pinball loss and interval score on all four tasks, with 80 % intervals
covering 79.5–84.7 %. TimesFM 3.0 keeps a lower RMSE on PEMS04, where point accuracy is a tie, and it
beats PWM's zero-shot transfer to an unseen network. All four tracks, uncertainty scores and honest
notes: [RESULTS.md](RESULTS.md) §2.

## Earlier study: PWM-Dyn v0.3 vs TimesFM (MAE)

All rows scored by the same function on the same held-out test windows. PWM-Dyn v0.3 is a 3-seed
ensemble; TimesFM is run zero-shot with a 512-step (traffic) / 365-day (rainfall) history versus
PWM's 12 steps / 30 days.

| Dataset | PWM-Dyn v0.3 (0.3 M) | TimesFM 2.5 (200 M) | TimesFM 3.0 univariate | TimesFM 3.0 multivariate |
|---|---|---|---|---|
| PEMS08 traffic, 1 h ahead | **14.18** | 15.04 | 14.63 | 14.55 |
| PEMS04 traffic, 1 h ahead | **18.50** | 19.70 | — | 19.14 |
| IMD rainfall, central India, 7 days ahead | **2.85** | 2.96 | — | 2.92 |

PWM-Dyn has lower point error in all 7 opponent rounds. TimesFM is better calibrated on rainfall
(80 % interval coverage 84–86 % vs PWM v0.3's 55 %); v0.4's conformal calibration fixed this (84.7 %).
Full tables, interval coverage and run provenance: [RESULTS.md](RESULTS.md).

## Repository layout

| Folder | What it is |
|---|---|
| [`v0.3-colab/`](v0.3-colab) | The original study: PWM-Dyn v0.3, Google Colab notebook (`PWM_Colab.ipynb`), TimesFM opponent harness, gpt-oss explanation layer, provenance audit; plus the Kaggle notebook that completed the opponent rounds |
| [`v0.7-realworld/`](v0.7-realworld) | **Current.** PWM-Dyn v0.7 (fallback base, burst-outage training, online correction), ParadoxBench-1.2 Track G (real-outage replay), validation-only ablation, results |
| [`v0.6-conference/`](v0.6-conference) | PWM-Dyn v0.6, ParadoxBench-1.1 (adds PEMS03, PEMS07, METR-LA, PEMS-BAY), opponent harness for STID / Graph WaveNet / STAEformer, validation ablation, Diebold–Mariano and block-bootstrap tests, results |
| [`paper-conference/`](paper-conference) | Conference paper (ACM sigconf): anonymous review build, and the named version in `named/` |
| [`v0.4-paradoxbench/`](v0.4-paradoxbench) | PWM-Dyn v0.4/v0.4.1 and the **ParadoxBench-1** benchmark (`paradoxbench/`, spec in [`SPEC.md`](v0.4-paradoxbench/paradoxbench/SPEC.md)); Kaggle notebooks for the v0.4 study, the v0.4.1 recipe check and the stopped v0.5 sweep |
| [`results/`](results) | ParadoxBench-1 leaderboard (`LEADERBOARD.md`) and every scored row as JSON, transcribed from the Kaggle run logs |
| [`paper/`](paper) | The research paper: LaTeX source (arXiv-ready), bibliography, vector figure, compiled PDF |
| [`DATA_SOURCES.md`](DATA_SOURCES.md) | Every dataset used, where it comes from, licence/terms, and how it is downloaded |

## Reproduce

- **v0.7 / ParadoxBench-1.2 (Kaggle):** see [`v0.7-realworld/README.md`](v0.7-realworld/README.md#run).
- **v0.6 / ParadoxBench-1.1 (Kaggle):** see [`v0.6-conference/README.md`](v0.6-conference/README.md): `tools/fetch_all.py --opponents`, `tools/prepare_traffic_data.py`, then `run_v06_pwm.py --frozen`, `run_v06_opponents.py` and `run_v06_analysis.py` on GPU T4 x2.
- **v0.3 (Colab):** open `v0.3-colab/PWM_Colab.ipynb` in Google Colab with a T4 GPU and run top to bottom.
- **ParadoxBench / v0.4–v0.5 (Kaggle):** import `v0.4-paradoxbench/notebooks/kaggle_paradoxbench_v04.ipynb`
  (or `kaggle_pwm_v041.ipynb` for the v0.4.1 traffic run) into Kaggle, set Accelerator = GPU T4 x2 and Internet on, then Save & Run All.
- **Locally:** see `v0.4-paradoxbench/README.md`; `python run_paradoxbench.py --quick` checks the whole
  pipeline on CPU in about 12 minutes.

No data is redistributed here: every script downloads the public source data itself.

## Provenance

`check_provenance.py` (in each study folder) proves that every PWM checkpoint contains only PWM-Dyn's own
parameters and that PWM's code imports no external model library (`timesfm`, `transformers`,
`huggingface_hub`, `openai`, …). TimesFM is used only as an opponent, zero-shot, in a separate step.

## Licence and citation

Code: Apache-2.0 (see [LICENSE](LICENSE)). Data keep their original terms (see DATA_SOURCES.md). TimesFM 3.0
weights are non-commercial research-only and are used here for evaluation only.
If you use PWM-Dyn or ParadoxBench, please cite it using [CITATION.cff](CITATION.cff).
