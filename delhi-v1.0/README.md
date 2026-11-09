# PWM-W Delhi v1.0: self-correction and a two-architecture ensemble

ParadoxAI Lab. v1.0 = v0.8 + PWM-X (v0.9) + two new steps aimed at the comparisons PWM-W still lost:
CPCB wind and temperature against TimesFM/Chronos, and airport/WMO temperature against ECMWF AIFS.

## What is new (each step adopted only if > 2 sigma better on validation, decided before any test score)

1. **Self-correction (S).** The global models are always scored after a trailing 30-day local bias correction.
   v1.0 gives PWM-W the same treatment on its own forecasts: for each station, lead hour and hour of day, the mean
   error of PWM-W's forecasts issued on the previous 30 days (at least 10), using only hours observed before the
   forecast start. Its purpose is to absorb seasonal drift (CPCB trains on summer, tests on monsoon to winter) and
   sensor drift. Pure and hybrid decide separately.
2. **Two-family ensemble (E).** The chosen setting averaged with the best passing setting of the other architecture
   family: the station-graph encoder (P4–P8) and the 21-day patch transformer PWM-X (P9–P10).
3. **All three leagues on the newest candidates.** v0.6–v0.9 were tested on CPCB only; v1.0 runs P8, P9, P10 (P0
   always, for the seed noise) on the airports (METAR) and WMO stations too.

Everything else (splits, opponents, the ISSUED-BEFORE and STRICT rules, significance tests) is unchanged from v0.8.

## Starting point: PWM-X (v0.9) on CPCB, test 2025-07-03 to 2025-12-31 (Kaggle run pwm-x-cpcb)

Validation (MAE / spread): P0 0.4922 ± 0.0038; P8 0.4678, P9 0.4606, **P10 0.4597 → chosen P10**.
Hybrid validation: H1 0.4506, H2 0.4607, H3 0.4958 → H1.

Pure PWM-X (P10) against the foundation models (positive = they are better; v0.8 P8 in brackets):

| Opponent | Temp | RH | Wind |
|---|---|---|---|
| Chronos-2 | +3.4% LOSS [+5.0 L] | +0.3% tie [+1.4 tie] | +3.2% LOSS [+3.8 L] |
| TimesFM 2.5 | −2.5% tie [−1.0 tie] | −2.3% tie [−1.3 tie] | +2.9% LOSS [+3.5 L] |
| TimesFM 3.0 | +1.0% tie [+2.5 tie] | +0.2% tie [+1.3 tie] | +3.8% LOSS [+4.4 L] |

Hybrid (H1 on P10): ties all three on temperature and humidity; wind WIN vs Chronos-2 (−3.0%, p=0.046) and
TimesFM 2.5 (−3.4%, p=0.031), tie vs TimesFM 3.0 (−2.5%). Both pure and hybrid beat every global model (IFS 9 km,
IFS 0.25, AIFS, ICON, GFS) on every variable under both rules, and the bias-corrected four-model ensemble
(pure: −29.9% / −14.2% / −38.9%).

PWM-X narrowed every gap but did not close the wind gap or the Chronos-2 temperature gap: v1.0's two steps target these.

## v1.0 results (Kaggle run pwm-v10, 2026-11-09)

**Validation decisions** (both v1.0 steps had to beat the chosen model by > 2 sigma; neither did, anywhere):

| League | Chosen pure | Ensemble (alone vs with partner) | Self-correction (raw vs corrected) | Hybrid design | Hybrid self-correction |
|---|---|---|---|---|---|
| CPCB | P10 (0.4597; P0 0.4922 ± 0.0038) | 0.4561 vs 0.4564: not adopted | 0.4561 vs 0.4686 (worse): not adopted | H1 | 0.4440 vs 0.4512: not adopted |
| Airports | **P10** (0.3869; P0 0.3939 ± 0.0006) | 0.3836 vs 0.3842: not adopted | 0.3836 vs 0.3919 (worse): not adopted | H2 | 0.3469 vs 0.3539: not adopted |
| WMO | P10 (0.3838; P0 0.3879 ± 0.0010) | no passing partner of the other family | 0.3816 vs 0.3922 (worse): not adopted | H1 (0.4078) | 0.4047 vs 0.4134: not adopted |

Self-correction from the model's own trailing errors made validation **worse** in every case: PWM-W's errors do not
persist over 30 days the way a global model's local bias does. It is rejected.

**Airports, test 2026-02 to 2026-10** (PWM-X, newly chosen there):

| | vs Chronos-2 (T / RH / wind) | vs TimesFM 2.5 | vs TimesFM 3.0 |
|---|---|---|---|
| Pure | −8.5 / −7.5 / −3.2 % (all WIN) | −11.5 / −9.1 / −3.8 % (all WIN) | −7.4 / −6.2 / −2.8 % (all WIN) |
| Hybrid | −26.0 / −15.6 / −13.7 % (all WIN) | −28.4 / −17.2 / −14.2 % (all WIN) | −25.1 / −14.5 / −13.4 % (all WIN) |

Pure vs the bias-corrected four-model ensemble: temperature LOSS (+14.6%), humidity tie (−1.3%), wind LOSS (+8.7%).
Hybrid vs the same ensemble: WIN on all three (−7.3 / −10.0 / −3.1%). All wins p < 1e-6.

**CPCB:** identical to the PWM-X run above (neither v1.0 step adopted).

**WMO, test 2025-03 to 2025-08** (PWM-X): the pure model beats all three foundation models on every variable —
Chronos-2 −11.0 / −7.8 / −3.4 %, TimesFM 2.5 −14.6 / −10.9 / −3.6 %, TimesFM 3.0 −10.7 / −7.4 / −2.7 % (all p < 1e-7).
Against the bias-corrected four-model ensemble: temperature LOSS (+11.6%), humidity tie, wind WIN (−11.5%).
The WMO **hybrid is not valid in this run**: the refetch of its global-forecast inputs hit Open-Meteo's daily request
limit, so it trained on 8,016 origins instead of ~34,000 and scored worse than the pure model; it must be rerun.

## Run (Kaggle, GPU)

    LEAGUES="CPCB METAR WMO" VARIANTS="P8,P9,P10" bash kaggle_v10.sh

## Results

Pending: the run's verdicts will be reported here exactly as logged, including losses.
