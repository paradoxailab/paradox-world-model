---
title: README
emoji: 🌍
colorFrom: indigo
colorTo: blue
sdk: static
pinned: false
---

# ParadoxAI Lab

**Compact world models for the physical world — weather, air quality, traffic — trained on real sensor data, tested in
public, with every loss reported.** Independent AI lab from India · Aditya Kumar & Anupam Singh.

### Where we stand (Nov 2026)

| | Result |
|---|---|
| 🌦️ Weather, 709 stations worldwide, 24 h | **WIN 100 / 100** against ten zero-shot foundation models (TimesFM 2.5 / 3.0, Chronos-2, Chronos-Bolt, TiRex, Sundial, Time-MoE, TTM …) |
| 🛰️ Weather + global forecasts (Atlas-100M-H2), 178 stations, 2025 | **beats raw and bias-corrected ECMWF IFS and NOAA GFS** on temperature, dewpoint and wind (11–34% lower error); loses to bias-corrected IFS on sea-level pressure; GraphCast comparison pending |
| 🇮🇳 Weather, all 68 Indian stations | level with the foundation models (WIN 19, TIE 74, LOSS 7) |
| 🌫️ PM2.5, all-India CPCB | WIN against 7 of 9 foundation models; ties TimesFM 3.0 |
| 🚦 Traffic, six road networks | Atlas-100M-TXL2: no loss to any foundation model (18 / 12 / 0); still behind the best trained specialists |

Every study is pre-registered before it runs; deviations are dated and published. Scoreboard:
[STANDINGS.md](https://github.com/paradoxailab/paradox-world-model/blob/main/atlas/m100/STANDINGS.md).

### Start here

- **[atlas-100m](https://huggingface.co/PARADOXAIlabs/atlas-100m)** — one 98.6M model for weather, air quality and traffic (+ traffic and hybrid variants)
- **[atlas-5k-25m](https://huggingface.co/PARADOXAIlabs/atlas-5k-25m)** — the 24.1M weather model it was grown from
- **[atlas-india-v1.0](https://huggingface.co/PARADOXAIlabs/atlas-india-v1.0)** — PM2.5 across India
- **[pwm-dyn](https://huggingface.co/PARADOXAIlabs/pwm-dyn-v0.7-pems08)** — compact traffic dynamics
- Datasets: **[atlas-benchmark-results](https://huggingface.co/datasets/PARADOXAIlabs/atlas-benchmark-results)** · **[atlas-station-forecast-archive](https://huggingface.co/datasets/PARADOXAIlabs/atlas-station-forecast-archive)**

### Links

🌐 [paradoxailab.com](https://paradoxailab.com) · 💻 [GitHub](https://github.com/paradoxailab/paradox-world-model) ·
📄 [Papers (Zenodo)](https://zenodo.org/records/24370660) · 🗺️ [Atlas web app](https://atlaswebapp.paradoxailab.com) ·
💼 [LinkedIn — Aditya Kumar](https://www.linkedin.com/in/aditya-kumar16/)
