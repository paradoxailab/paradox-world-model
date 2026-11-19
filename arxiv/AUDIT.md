# Authenticity audit of the five arXiv papers (2026-11-19)

Every reference was checked against an external record, and every number against the run outputs saved in this
repository (and its development branches). Anything that could not be traced was removed or marked, not kept.

## References: 96 distinct works, 180 citations

| Check | Result |
|---|---|
| Journal and conference papers with a DOI | Matched in OpenAlex or Crossref: title, lead authors, year and venue |
| ML papers without DOIs (ICLR, ICML, arXiv) | Venue and year checked; Toto and MOMENT confirmed on arXiv / ICML 2024 with the full author list |
| Model cards (TimesFM 2.5 and 3.0, Chronos-2, Chronos-Bolt, Moirai 2.0, TiRex, Sundial, Time-MoE, TTM r2) | All exist on Hugging Face; licences as stated in the papers (Moirai 2.0 CC-BY-NC-4.0, TiRex NXAI community, TimesFM 3.0 non-commercial: evaluation only) |
| Datasets and services | WEATHER-5K (ICML 2026, PMLR), OpenCity Delhi reports, Open-Meteo (Zenodo), CEEW report, NOAA ISD; the Kaggle all-India dataset is the one the pipeline downloads (`atlas/delhi/colab_run.sh`) |

Corrected: TiRex cited as NeurIPS 2025 (arXiv:2505.23719) instead of an undated preprint; BasicTS dated 2025 (TKDE
issue), DOI added.

## Numbers

| Paper | Numbers checked | How |
|---|---|---|
| 1 PWM-Dyn + ParadoxBench | 412 | All six tables regenerate byte-identically from `rows.txt` (`make_tables.py`); all 447 logged values in `rows.txt` occur in the v0.6/v0.7 run outputs; the rest of the text traced to run outputs |
| 2 PWM-W North India weather | 485 | Traced to the run reports and the records on branches `delhi-v0.3` to `delhi-v1.0`; version-table cells checked by hand against the run that produced each |
| 3 Atlas India air quality | 492 | Traced to `atlas/results` and the record; every table row's values found together in one run output, or checked by hand; parameter breakdown recomputed from the released weights |
| 4 Atlas-F | 433 | As #3 |
| 5 Atlas-5K 10M / 25M | 1,054 | Tables 1–3 checked by `atlas/paper4/make_tables.py --check`; appendix tables generated from the result files; the rest traced |

Corrected or removed because no saved record supports them:

* **#1** METR-LA test windows: 1,139 (a value computed from the split) replaced by **1,051**, the number of windows
  every logged run scored.
* **#2** v0.4 WMO validation scores (H2 0.3732 vs H1 0.3783; P4 0.3889): the v0.4 WMO run saved its test comparisons
  but not its validation scores. The numbers are removed and the WMO choices are marked as decisions without a saved
  record.
* **#3** Atlas-W v1 RMSE (55.99) and coverage (80), and the no-Delhi model's QL (9.92): the scoring runs' output files
  were not saved. Removed and marked; the MAE and QL values that the record kept are unchanged.
* **#4** Per-seed correlations in the Delhi robustness table (0.836, 0.843, 0.844): not saved. Removed and marked.
* **#5** Validation E 0.27307 (the result file) instead of 0.27308 (the first of two validation passes).

Also fixed: "Preprint. Under review." stamp (none is under review) changed to "Preprint."; checklist lines that said
"link withheld for review" now give the repository URL in the named builds; contact email info@paradoxailab.com.

## Limits of this audit

A value that matches a number somewhere in the run outputs is strong but not absolute evidence; the row-level and
regeneration checks above guard against coincidental matches, and every flagged value was traced by hand to the run
that produced it. Values that come from a record written at the time of a run (the repository READMEs) rather than
from a saved output file are kept and are identifiable in the record.
