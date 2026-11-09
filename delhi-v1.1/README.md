# PWM-F (Delhi v1.1): a 10M-parameter Indian weather foundation model, pretrained for free

ParadoxAI Lab. v1.1 = v1.0 + **PWM-F**: the PWM-W station-graph world model scaled to ~10M parameters and pretrained
on every Indian NOAA weather station, then fine-tuned on each league. The aim is to close the remaining losses to
TimesFM and Chronos, which the v0.9 data-threshold study traced to too little local history (the airports need about
24 months to stop losing and 48 to win everywhere; the Delhi sensors have 16).

## What PWM-F is

Sensor data only: no images, video or text. Each station is a token; the model reads its last 21 days, its neighbours
on the station graph, the sun's position and the calendar, and outputs calibrated 10/50/90% quantiles for the next
24 hours.

| Idea | Where it comes from (idea only; implemented from scratch) | In PWM-F |
|---|---|---|
| Efficiency over scale | DeepSeek | 9.85M parameters in total, ~6.4M active per token (TimesFM 2.5: 200M) |
| Fine-grained experts + a shared expert | DeepSeekMoE | 21-day encoder: 12 small routed experts (top-2) + 1 always-on expert per layer (`pw/moe.py`) |
| Load balancing without an auxiliary loss | DeepSeek-V3 | a per-expert routing bias nudged towards equal load; it picks experts but never weights them |
| Large-scale self-supervised pretraining, then fine-tuning | OpenAI (GPT) | forecast + masked-patch reconstruction on all Indian stations, then per-league fine-tuning |
| Honest, calibrated, inspectable | Anthropic | conformal 10–90% intervals; a pre-registered validation rule decides every change; expert routing is logged per station |
| Physics in the structure | PWM-W | station graph, sun elevation, outputs clipped to physical ranges |

Configuration: width 256, 4 graph blocks, 8 heads, 4-layer mixture-of-experts patch encoder (P11 in `run_weather.py`).

## Data (free, no account)

- **Pretraining:** every Indian station in NOAA's Integrated Surface Database, 2015-01-01 .. **2024-11-30**, grouped
  into regional networks of ~30 (`tools/fetch_india_isd.py` → `WX_IN01.npz` …). The end date is the day before the
  earliest validation period of any league, so pretraining never sees any league's validation or test weather.
- **Fine-tuning and test:** the three leagues, unchanged (airports, WMO stations, Delhi CPCB sensors).

## Rules (unchanged)

P11 replaces P0 only if > 2σ better on validation; the v1.0 ensemble and self-correction steps follow; finals are 3
seeds; every comparison uses Diebold–Mariano + day-block bootstrap.

## Run (Kaggle)

    bash kaggle_india_data.sh                                       # CPU notebook: the pretraining networks
    STEPS=40000 LEAGUES="CPCB METAR WMO" VARIANTS="P8,P11" bash kaggle_pwmf.sh   # GPU: pretrain + leagues

## Results

Pending. They will be reported here exactly as logged, losses included.
