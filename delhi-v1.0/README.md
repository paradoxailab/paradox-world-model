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

## Run (Kaggle, GPU)

    LEAGUES="CPCB METAR WMO" VARIANTS="P8,P9,P10" bash kaggle_v10.sh

## Results

Pending: the run's verdicts will be reported here exactly as logged, including losses.
