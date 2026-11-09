# PWM-India v2.0: a 10-million-parameter India weather model, pretrained on every Indian station

ParadoxAI Lab (Aditya Kumar, Anupam Singh). v2.0 = v1.0 + India-wide data. The v0.9 data-threshold study showed that
PWM-W needs about 24 months of a network's own history to stop losing to TimesFM / Chronos and 48 months to beat all
three; architecture changes gained 0.6–1.6 points. v2.0 therefore adds data, not tricks.

## What is new

1. **India-wide corpus** (`tools/fetch_india.py` → `WX_INDIA.npz`): every Indian NOAA ISD station whose record overlaps
   2024, 2015-01-01 to 2024-11-30, same parser and quality rules as the WMO league, kept if ≥10% of hours have a
   temperature (at most 400). **It ends before the earliest validation period of any league (WMO, 2024-12-01)**, so
   nothing from any league's validation or test period is in it, for any station.
2. **P11** = P10 (1.26M) + the corpus as an extra joint-training partner: isolates the effect of data.
3. **P12** = a 10,142,065-parameter PWM-X (width 288, 6 graph layers, 8 heads, 4 patch layers), pretrained on the
   corpus (`pretrain_india.py`; each batch a 48-station neighbourhood; masked-patch reconstruction; weight averaging),
   then fine-tuned on each league with the corpus as partner. When the network's other channels differ from the
   corpus's, the input weights are moved by channel name.
4. Everything else unchanged: P0 seed noise and the 2σ validation rule, v1.0's ensemble and self-correction steps,
   splits, opponents (TimesFM 2.5 / 3.0, Chronos-2, global models), both rules, significance tests.

## Run (Kaggle, free)

    # CPU notebook (no GPU quota):  python tools/fetch_india.py
    # GPU notebook:                 LEAGUES="CPCB" VARIANTS="P10,P11,P12" bash kaggle_v20.sh

## Results

Pending: reported here exactly as logged, losses included.
