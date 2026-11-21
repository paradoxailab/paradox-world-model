# Atlas-100M-T: a larger traffic adapter on the frozen Atlas-100M (pre-registration)

ParadoxAI Lab · Aditya Kumar, Anupam Singh · written 2026-11-21, after Atlas-100M v1.0 lost traffic
(`RESULTS.md`) and **before any training or scoring of this model**. The commit adding this file is the time stamp.
Changes after the first run are appended under "Deviations" with date and reason.

## 1. Question

Atlas-100M lost 22 of 24 traffic comparisons with trained specialists and PWM-Dyn. Its traffic adapter had 80,322
parameters, 12 steps of context, no sensor identity, and about 25,000 of the 100,000 training steps. **Does giving
traffic more parameters of its own, while leaving weather and air quality exactly as published, close that gap?**

This is a follow-up model, not a re-run of Atlas-100M: Atlas-100M's v1.0 results stay as published. Atlas-100M-T is
reported as a separate entry, next to Atlas-100M.

## 2. What changes and what cannot change

- **Unchanged by construction:** the shared core (94,755,808 weights) is frozen; the weather and air-quality views,
  their weights and their results are not loaded, retrained or rescored. Check W: the SHA-256 of
  `atlas100m_best.pt`, `atlas100m_weather_view.pt` and `atlas100m_aq_view.pt` after this study equals
  `results/SHA256SUMS`.
- **Added, used only by traffic** (`atlas/m100/traffic_plus.py`):
  - LoRA, rank 32 (alpha 32), on every linear layer of the frozen core (encoder and dynamics blocks, spatial
    query/key/value and output): 4,666,368 parameters; B starts at zero.
  - A learned 32-number embedding for every sensor of the six networks (2,250 sensors): 72,000 parameters, fed as
    extra static inputs whose input weights start at zero.
  - The traffic adapter (input layer, forcing embedding, decoder, reconstruction, geometry MLP) keeps training:
    105,410 parameters including the wider input layer.
  - Traffic-only trainable parameters: **4,843,778** (from 80,322). Whole system: 98,599,994 + 4,763,456 new =
    103,363,450.
- **Check T0:** before training, Atlas-100M-T's validation ratio equals Atlas-100M's traffic view's within 2e-3
  (bf16 rounding); otherwise the run stops.
- **Kept the same as Atlas-100M:** 12 steps of context (Track A protocol, the specialists' own input length), the
  traffic loss and masking of the harness, the validation metric (mean over networks of MAE / last-reading MAE).

## 3. Training (defaults of `traffic_plus.py` = the rule)

Traffic batches only, AdamW (LoRA and embeddings 1e-3, adapter 3e-4, weight decay 1e-4), 3% warm-up then cosine to
10%, bf16, gradient clip 1.0, at most 40,000 steps or 240 minutes, validation every 2,000 steps, patience 6, seed 800.
The checkpoint kept has the lowest validation ratio. No test window is read during training.

## 4. Evaluation

`score_traffic.py --plus … --name Atlas-100M-T`: same networks, official test windows (read once), conformal 80% band
from the validation windows, entered on Tracks A and B, paired tests (Diebold–Mariano, day-block bootstrap) against
every other submission on ParadoxBench — STID, Graph WaveNet, STAEformer, PWM-Dyn v0.6r, TimesFM 2.5 / 3.0
(uni- and multivariate), Chronos-2, Chronos-Bolt, **and Atlas-100M itself** — one Holm family. WIN = lower MAE,
p_holm < 0.01 and a 95% interval excluding 0; LOSS the mirror image; otherwise TIE.

## 5. Predictions

| # | Prediction | Probability |
|---|---|---|
| T1 | Check T0 holds | 0.99 |
| T2 | Check W holds (weather / air-quality files unchanged) | 0.99 |
| T3 | Best validation ratio below Atlas-100M's 0.7210 | 0.90 |
| T4 | WIN against Atlas-100M on at least 5 of 6 networks | 0.70 |
| T5 | Track A: WIN against all three specialists on at least 4 of 6 networks | 0.10 |
| T6 | Lower MAE than PWM-Dyn v0.6r on at least 3 of 6 networks | 0.15 |
| T7 | Track B: WIN against every foundation model on at least 3 of 6 networks | 0.30 |

Our expectation: sensor identity and more capacity should give most of the specialists' advantage back, but a
shared, frozen weather core with 12 steps of context is unlikely to beat models designed and trained for traffic.

## Deviations

(none yet)
