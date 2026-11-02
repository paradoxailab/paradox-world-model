# Paradox World Model (PWM) — PWM-Dyn and ParadoxBench

**Paradox AI Lab** · [paradoxailab.com](https://paradoxailab.com) · contact.paradoxailab@gmail.com
Authors: Aditya Kumar, Anupam Singh

PWM-Dyn is a small (≈0.3 M parameters) physical-dynamics model that forecasts how traffic and rainfall
evolve and spread over real networks — California highway sensors and the India Meteorological
Department rainfall grid — with calibrated uncertainty and robustness to dead sensors. It is trained
from random initialisation on public data, benchmarked head-to-head against Google's TimesFM 2.5 and
3.0 foundation models on identical test windows, and provenance-audited (no external model code or
weights inside PWM).

**ParadoxBench** is the open benchmark released with it: four tasks, four tracks (standard, open
context, dead-sensor robustness, zero-shot transfer), one scorer, frozen test windows, and a
submission format anyone can use.

## Headline: ParadoxBench-1, open-context track (MAE, lower is better)

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
| [`v0.4-paradoxbench/`](v0.4-paradoxbench) | PWM-Dyn v0.4/v0.4.1 and the **ParadoxBench-1** benchmark (`paradoxbench/`, spec in [`SPEC.md`](v0.4-paradoxbench/paradoxbench/SPEC.md)); Kaggle notebooks for the v0.4 study, the v0.4.1 recipe check and the stopped v0.5 sweep |
| [`results/`](results) | ParadoxBench-1 leaderboard (`LEADERBOARD.md`) and every scored row as JSON, transcribed from the Kaggle run logs |
| [`paper/`](paper) | The research paper: LaTeX source (arXiv-ready), bibliography, vector figure, compiled PDF |
| [`DATA_SOURCES.md`](DATA_SOURCES.md) | Every dataset used, where it comes from, licence/terms, and how it is downloaded |

## Reproduce

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
