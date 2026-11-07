# PWM-W Delhi v0.7: rolling weekly updates

ParadoxAI Lab. v0.7 = v0.6 plus one change, decided before any v0.7 score was seen.

**Why.** On the CPCB sensors, v0.6 pure PWM-W still loses to Chronos-2 and TimesFM 3.0, by 4–7%. Those models
read each sensor's latest 512 hours at every forecast. PWM-W was frozen at the end of its training period (May
2025) and then tested on July–December.

**Change: rolling updates.**
- Before each test week, each of the three final models is fine-tuned from its own trained weights.
- It trains only on origins whose 24 target hours were all observed before that week starts.
- Half of the batches come from the last 30 days.
- Settings: 500 steps, learning rate 3e-4, no checkpoint selection, since nothing after the update time may be
  looked at.
- This is how operational model-output-statistics systems are run.

**Rule.** The same procedure is first simulated on the validation period. Rolling updates are adopted only if they
improve the validation score by more than 2 sigma over the frozen models. The frozen models' checkpoints were
chosen on that same validation period, so the comparison is tilted against the rolling updates.

  LEAGUES="CPCB" bash kaggle_v07.sh      (attach pwm-weather-data and pwm-weather-v06-fm)

## Earth-2 results: models we ran ourselves (METAR league)

Setup:
- Each model starts from the real NOAA GFS analysis at 00 UTC on each test day (2026-02-01 to 2026-10-31).
- Forecasts are read at the six airports at +6, +12 and +18 h.
- The PWM-W entry is v0.4's pure model (station observations only), on the same hours.
- Every model is also scored after a bias correction, in two ways:
  - **oracle:** its mean error over the test period itself is removed. This is generous to the model.
  - **operational:** a trailing 30-day correction from its own earlier days.

| Model (days) | Variable | PWM-W | Model raw | Model, trailing bias-corrected | Verdict (operational) |
|---|---|---|---|---|---|
| NVIDIA FourCastNet SFNO (273) | Temp °C | 1.446 | 1.832 | **1.278** | PWM-W **loses** |
| NVIDIA FourCastNet SFNO (273) | Wind m/s | 1.055 | 1.204 | 1.052 | tie |
| GenCast Mini, 1°, one member (88) | Temp °C | 1.813 | 2.953 | **1.202** | PWM-W **loses** |
| GenCast Mini, 1°, one member (88) | Wind m/s | 1.036 | 1.219 | 1.067 | tie (beats it after oracle correction) |

**Plain reading:**
- Pure PWM-W beats both models' raw forecasts on temperature and wind.
- Once each model's local bias is removed, both beat pure PWM-W on temperature, and wind is a tie.
- The fair test for these models is the hybrid, which already beats the bias-corrected ECMWF AIFS and IFS under the
  issued-before-start rule. v0.7 saves the hybrid's forecasts so it can be scored against them too.
- GenCast Mini's days are spread across the test period, so its trailing correction uses fewer days.

**Models that could not be run on Kaggle's free T4 GPU (15 GB):**
- GraphCast Operational (0.25°), FourCastNet 3 and Aurora: out of memory, even in half precision.
- GraphCast Small (1°): ran for 273 days, but every stored value is missing. Probably it needs a 6-hour
  precipitation input that GFS analyses do not provide; not verified.

---

# PWM-W Delhi v0.6: learning from a larger station network

ParadoxAI Lab. v0.6 = v0.5 plus one change and one fix, both decided before any v0.6 score was seen.

## Why: the CPCB league result in v0.4

On Delhi's CPCB/DPCC station sensors (25 stations, test 2025-07-03 to 2025-12-31), v0.4 found:
- **Pure PWM-W beats the global models.** Under both rules it beats IFS 0.25, IFS 9 km and GFS on all three
  variables, and AIFS and ICON on temperature and wind. On humidity it ties AIFS under both rules, and ties ICON
  under the strict rule. It also beats the bias-corrected 4-model ensemble (−26.6% / −8.5% / −37.2%).
- **But it loses to the time-series foundation models.**
  - Chronos-2 is better by 8.3% (temperature), 6.9% (humidity) and 6.0% (wind).
  - TimesFM 3.0 is better by 5.7%, 6.8% and 6.7%.
  - TimesFM 2.5 ties on temperature and is better on humidity (+4.1%).
  - All losses are significant.
- **The hybrid** (global forecasts as inputs) beats every global model on every variable under both rules, and ties
  all three foundation models.

These are rooftop air-quality-station sensors with only 16 months of training data. That is the setting where
models pre-trained on very large corpora help most.

**Invalid number withdrawn:** v0.4's "PWM-W beats TimesFM 2.5 on CPCB wind by 99%" is invalid. TimesFM 2.5 ran out
of GPU memory on wind at every batch size. The code then silently reused that model's humidity forecast as its
wind forecast. v0.6 fixes this (see below). The WMO and METAR TimesFM 2.5 numbers are unaffected: they completed.

## What is new in v0.6

1. **Cross-network training (P4, P5).** The CPCB model may also train on the 20-station WMO network
   (2021 to 2025). Safeguards:
   - It uses only WMO hours before CPCB's validation period, and WMO's normalisation statistics come from those
     hours alone.
   - Other channels are matched by name: wind direction and pressure are shared. Channels a network lacks (solar
     radiation and PM2.5 for WMO; dew point and visibility for CPCB) are masked.
   - Hour-of-day inputs are moved to IST (+6 h). Sun elevation is exact for every station.
   - P4 is P0's size plus the partner and P5 is P1's size plus the partner. Either replaces the current choice only
     if it beats P0 on validation by more than 2 sigma.
   - This is our own technique: the foundation models pre-train on generic series, while PWM-W learns from real
     neighbouring weather stations under the same physics.
2. **Fix to the foundation-model runner:**
   - A forecast is never reused across variables; a model that cannot run is reported as NOT RUN.
   - The model's own batch size now follows the chunk size, so smaller chunks actually use less memory.
   - All foundation-model forecasts are recomputed.
   - The first v0.6 CPCB run hit a bug in this new runner code: it read the model's name after freeing the model.
     All three foundation models therefore show as NOT RUN in that log. PWM-W's own results were unaffected and
     saved. `kaggle_v06_fm.sh` re-scores those saved forecasts against the three models, so the comparison does
     not need a full retrain.

## v0.6 results: CPCB league

**Validation choice:**
- P4 (P0 plus training on the WMO stations) scored 0.4735, against P0's 0.4922 ± 0.0038. That is about 5 sigma
  better, so P4 is adopted. P5 scored 0.4774 and v0.4's choice, P1, scored 0.4797.
- The hybrid stays H1: H1 scored 0.4586, H2 0.4788 and H3 0.4932.

**Pure PWM-W against the global models** (test 2025-07-03 to 2025-12-31). Values are MAE differences against the
bias-corrected forecast; negative means PWM-W is better.

| Opponent | Temp | RH | Wind |
|---|---|---|---|
| ECMWF AIFS | BEATS −27.7% | **BEATS −7.1%** (was a tie in v0.4) | BEATS −50.2% |
| ECMWF IFS 9 km | BEATS −49.3% | BEATS −36.8% | BEATS −56.2% |
| ECMWF IFS 0.25 | BEATS −33.6% | BEATS −25.2% | BEATS −45.1% |
| DWD ICON | BEATS −33.3% | BEATS −22.4% | BEATS −34.9% |
| NOAA GFS | BEATS −46.3% | BEATS −45.3% | BEATS −55.9% |

- These verdicts use the issued-before-start rule.
- Under the strict rule (the latest run, often issued after our start) every cell is also BEATS, except humidity
  against AIFS, which ties (−5.0%, not significant).
- PWM-W also beats the bias-corrected 4-model ensemble by −27.6% / −11.3% / −37.9%.
- The hybrid beats every global model on every variable under both rules.
- Caveat: these are rooftop air-quality-station sensors, which sit far from the global models' grid-box averages.
  That is why the raw global forecasts do so badly here.

**Against the foundation models:** pending; `kaggle_v06_fm.sh` is re-scoring them now.

## v0.5 result (negative)

Adding cloud cover, radiation, dew point, pressure and wind direction to the learned-correction hybrid (H3) scored
0.3539 on METAR validation, against 0.3481 for v0.4's design. It was **not adopted**. The v0.5 run then retrained
v0.4's design from scratch, and its test results reproduced v0.4's numbers exactly, a useful check that the pipeline
is deterministic.

  LEAGUES="CPCB" bash kaggle_v06.sh

---

# PWM-W Delhi v0.5: more predictors for the learned correction

v0.5 = v0.4 plus one change, decided before any v0.5 score was seen. The hybrid may also read further output from
the same global runs:
- cloud cover;
- shortwave radiation;
- dew point;
- sea-level pressure;
- wind direction.

These come from ECMWF IFS 0.25, AIFS, DWD ICON and NOAA GFS, using only the run published before the forecast
start. Classic model output statistics use such predictors because cloud and radiation errors drive temperature
errors.

The new design H3 replaces v0.4's choice (H2) only if its validation score is better by more than 2 sigma (the seed
noise of the pure model). Everything else, including the rules, opponents and splits, is unchanged from v0.4.

  LEAGUES="METAR" bash kaggle_v05.sh

---

# PWM-W Delhi v0.4: learned-correction hybrid and a fair comparison

ParadoxAI Lab. v0.4 builds on v0.3 (the weather league against the global models). The question: can learned local
correction beat the global AI weather models at stations, using only forecasts that exist when our forecast is made?

## What is new in v0.4

1. **Learned-correction hybrid (H2).** The base forecast is the bias-corrected mean of ECMWF IFS 0.25, ECMWF AIFS,
   DWD ICON and NOAA GFS. Each uses its newest run published before the forecast start: the 24 h-old run for hours
   0–16, the 48 h-old run after that. PWM-W then learns the correction from the station network's own
   observations. Validation picked this design over v0.3's inputs-only hybrid (validation 0.348 vs 0.372; the pure
   model scores 0.393).
2. **A fair comparison, reported alongside the strict one.**
   - ISSUED-BEFORE-START scores each global model on its newest run published before our forecast start.
   - STRICT, as in v0.3, scores it on its latest run, which is often issued after our start (generous to it).
   - Both rules require significance against the raw forecast and against the bias-corrected one.
3. **A strong new opponent:** the bias-corrected 4-model ensemble on its own.
4. **Joint training across station networks (P4).** Validation improved from 0.3934 to 0.3920, which is below the
   2-sigma bar, so it was not adopted.
5. **Fixes:** GPU memory is freed before the foundation-model opponents (TimesFM 2.5 had run out of memory in v0.3).

## Results: METAR league

Six airports, including Delhi Palam. Test period 2026-02-01 to 2026-10-31, 1,089 origins. Differences are MAE
(negative means PWM-W is better); every verdict passed significance.

**Hybrid under the ISSUED-BEFORE-START rule** (newest run published before the start, bias-corrected)

| Opponent | Temp | RH | Wind |
|---|---|---|---|
| **ECMWF AIFS** | **BEATS −4.4%** | **BEATS −11.8%** | **BEATS −7.4%** |
| ECMWF IFS 9 km | BEATS −21.0% | BEATS −24.2% | BEATS −13.4% |
| ECMWF IFS 0.25 | BEATS −19.4% | BEATS −22.0% | BEATS −12.7% |
| DWD ICON | BEATS −22.1% | BEATS −23.6% | BEATS −11.0% |
| NOAA AIGFS (GraphCast-based) | BEATS −21.0% | – | BEATS −17.7% |
| NOAA GFS | BEATS −37.2% | BEATS −41.4% | BEATS −29.3% |
| Bias-corrected 4-model ensemble | WIN −6.9% | WIN −11.5% | WIN −3.6% |

**Hybrid under the STRICT rule** (latest run + bias correction)

| Opponent | Verdict |
|---|---|
| Wind | **BEATS** AIFS, IFS 9 km, IFS 0.25, ICON, AIGFS and GFS |
| Humidity | **BEATS** IFS and ICON; **loses** to AIFS (+3.3%) |
| Temperature | **Loses** to AIFS (+15.6%) and IFS 0.25 (+3.3%); ties IFS 9 km and ICON; **BEATS** AIGFS and GFS |

**Pure PWM-W** (station observations only) against the time-series foundation models, each forecasting from a
station's own last 512 hours. PWM-W wins everywhere, p < 0.01.

| Opponent | Temp | RH | Wind |
|---|---|---|---|
| TimesFM 3.0 | −5.8% | −4.3% | −1.5% |
| TimesFM 2.5 | −10.0% | −7.3% | −2.4% |
| Chronos-2 | −6.9% | −5.6% | −1.8% |

**Bottom line:** with the forecasts that actually exist at forecast time, the hybrid beats ECMWF AIFS, IFS, ICON,
AIGFS and GFS at these airports. Against AIFS's freshest run, often issued after our forecast start, it still loses
on temperature and humidity.

The WMO and CPCB leagues are running (`kaggle_v04.sh`).

## Entries

**Ours**
- **PWM-W (pure):** inductive graph world model over the station network. Its inputs are past observations only;
  nothing from any global model goes in. The model setting is chosen on validation data alone, and the entry is
  the mean of 3 seeds.
- **PWM-W hybrid:** the same model, plus ECMWF IFS (0.25°) and AIFS forecasts issued at least 48 hours earlier as extra
  inputs. It is reported separately and never counted as the pure model.

**Global weather models.** These are the real operational forecasts, archived by the Open-Meteo Previous Runs API:
- ECMWF AIFS (AI)
- NOAA AIGFS (AI, GraphCast-based)
- DWD AICON (AI)
- ECMWF IFS 9 km and 0.25°
- NOAA GFS
- DWD ICON

Each is scored in several versions:
- its latest run (generous to the global model: often issued after our forecast's origin);
- its run from 24 h before the valid time;
- each of the above, after a trailing 30-day local bias correction.

**Models we run ourselves.** NVIDIA Earth2Studio runs FourCastNet 3 / SFNO and, if it fits in the GPU's memory,
GraphCast Operational. Each run starts from the real NOAA GFS analysis at 00 UTC of each test day, and the
forecasts are read at each station at +6, +12 and +18 h.

**Time-series foundation models.** TimesFM 2.5, TimesFM 3.0 (evaluation only, non-commercial licence) and
Chronos-2, each on each station's own last 512 hours.

**Baselines**
- same hour yesterday;
- the last 14 days' daily cycle;
- the daily cycle plus the latest anomaly.

**Not tested:** GenCast and WeatherNext. They have no public forecast archive, and their data needs a Google
Cloud access request.

## Leagues (`pw/leagues.py`)

| League | Stations | Period | Test |
|---|---|---|---|
| METAR | Delhi Palam and Safdarjung airports, plus nearby north-Indian airports below 1,000 m (up to 16; WMO-grade reports, IEM archive) | 2021-01 to 2026-11 (UTC) | 2026-02-01 to 2026-10-31 |
| CPCB | Delhi's CPCB/DPCC/IMD stations' own weather sensors (located by name with OpenStreetMap) | 2024-01 to 2025-12 (IST) | last 182 days |

Targets are 2 m temperature (°C), relative humidity (%) and 10 m wind speed (m/s), forecast for the next 24
hours. Origins are every 6 hours.

## Rule for "beats"

A global model counts as beaten on a variable only if PWM-W's MAE is significantly lower than both:
- its latest run, and
- its bias-corrected latest run.

"Significantly lower" means Diebold–Mariano p < 0.05 and a day-block bootstrap 95% interval below zero. Each
comparison uses only the hours where both forecasts exist. Results are also broken down by lead time
(1–6 h, 7–12 h, 13–24 h).

## Run (Kaggle)

```
pip install -q timesfm chronos-forecasting
python tools/fetch_metar.py                 # WX_METAR.npz
python tools/fetch_nwp.py --league METAR    # NWP_METAR.npz (global models' archived forecasts)
python tools/fetch_delhi.py && python tools/fetch_cpcb_wx.py && python tools/fetch_nwp.py --league CPCB
python tools/earth2_run.py --league METAR --budget_h 7      # GPU: FourCastNet / GraphCast runs
python run_weather.py --league METAR && python run_weather.py --league CPCB
```

## Data licences

- METAR: Iowa Environmental Mesonet archive of public airport reports.
- Global forecasts: Open-Meteo (CC BY 4.0, non-commercial free tier). The underlying models are © ECMWF, NOAA
  and DWD.
- CPCB: OpenCity, public domain.
- Station positions: © OpenStreetMap contributors (ODbL).

No data or weights are stored in this repository.
