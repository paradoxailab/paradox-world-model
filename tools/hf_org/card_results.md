---
license: cc-by-4.0
pretty_name: Atlas benchmark results (ParadoxAI Lab)
language:
- en
tags:
- weather-forecasting
- air-quality
- traffic-forecasting
- benchmark
- pre-registration
- paradoxailab
size_categories:
- n<1K
---

# Atlas benchmark results

Every score behind the Atlas-100M study by **ParadoxAI Lab**: paired tests (Diebold–Mariano and station-block
bootstrap, Holm-corrected), MAE tables, training logs, the pre-registration documents and their dated deviations.
Wins, ties and losses are all here. Code: [github.com/paradoxailab/paradox-world-model](https://github.com/paradoxailab/paradox-world-model).
Models: [PARADOXAIlabs/atlas-100m](https://huggingface.co/PARADOXAIlabs/atlas-100m).

| Path | What |
|---|---|
| `STANDINGS.md` | one-page scoreboard (final / pending) |
| `RESULTS.md` | the full report |
| `PREREG.md`, `PREREG_TRAFFIC.md` | plans committed before each run, predictions with probabilities, deviations 1–9 |
| `results/*paired*.json`, `results/*_results*.json` | weather, air-quality and traffic tests (one record per opponent and variable / network) |
| `results/india/` | the 68 Indian WEATHER-5K stations against ten foundation models (2023 test, 2024–25 live) |
| `results/hybrid/` | the hybrid (Atlas reading ECMWF IFS / AIFS and NOAA GFS forecasts) — corrected scoring |
| `results/interim_no_graphcast/` | the first, pre-correction hybrid score, kept for transparency (deviation 8) |
| `results/*log.jsonl`, `*summary.json`, `*.txt` | training logs and run logs |
| `india_stations.json` | the Indian station list (WMO blocks 42–43, id, latitude, longitude) |

A WIN needs lower error, Holm-adjusted p < 0.01 and a 95% interval that excludes zero; a LOSS is the mirror image.
No third-party model forecasts are redistributed here, only scores.

Licence: CC-BY-4.0. Cite: Kumar, A. and Singh, A. (2026). *Atlas-100M: one compact world model for weather, air quality
and traffic.* ParadoxAI Lab.
