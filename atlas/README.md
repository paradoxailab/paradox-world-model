# Paradox Atlas v0.3: how much information does a world model need?

ParadoxAI Lab (Aditya Kumar, Anupam Singh).

**Question.** Is there a minimum amount of useful information a model needs before it can predict a physical system,
and can it be worked out before training? This version builds the model and the measuring apparatus, and answers the
question on four systems whose equations are known. It uses numbers only: no images, video or text, and no
pretrained weights from anyone.

Everything below was measured, on a 2-core CPU, from random initialisation: 342 training runs for v0.1 (full tables
in [`results/REPORT.md`](results/REPORT.md)) and 103 for v0.2 ([`results/REPORT_v02.md`](results/REPORT_v02.md)).
Raw runs: `results/runs_*.jsonl`. v0.2 (the section "v0.2: working on the three failures") changes the answer to
findings 8 and part of 7; the v0.1 findings are kept as they were measured.

## What was built

| Part | File | What it does |
|---|---|---|
| Exact simulators | `atlas/systems.py` | Harmonic oscillator, damped oscillator, diffusion and advection-diffusion on a ring of 8 nodes. Solved exactly (checked against the analytic solutions to 1e-14), with a forcing input (a force, or an emission source at one node). Every trajectory has its own parameters, start and forcing. |
| Equation-aware oracle | `atlas/systems.py: oracle` | Knows the equation but not its parameters or state; fits them to the noisy window and forecasts. This is the floor a perfect learner could reach. |
| Atlas model | `atlas/model.py` | Eight modules: numerical encoder, per-node state, spatial engine (attention biased by geometry), one transition network iterated in time, future forcing fed into the transition (interventions), hard physics rules (bounds, conservation of total amount), 10/50/90% quantiles that cannot cross. One width setting scales it from 8,468 to 9,914,492 parameters (ring version: 9,988,512). The code refuses to build above 10M. |
| Trainer | `atlas/train.py` | Quantile loss on the next 16 steps plus reconstruction of 15% hidden inputs. 80% of the N trajectories train, 20% decide early stopping. Test sets are fixed: 2,000 fresh trajectories, 1,000 from parameter ranges never seen, and counterfactual forcings. |
| In-context identification (v0.2) | `atlas/sysid.py` | Works out each system's dynamics from the one window being forecast (ridge least squares over fixed geometric operators), fits the starting state to all observed values, and runs the dynamics forward. Assumes only that the dynamics do not change during the window; it is not told the equation or its parameters. |
| Threshold function | `atlas/threshold.py` | Fits `error(N, P) = floor + a·N^-alpha + b·P^-beta` to runs, inverts it for the minimum data or model size, gives bootstrap intervals, tests "sudden or gradual", and advises what to add next. |
| Experiment runner | `grid.py`, `baselines.py`, `analyze.py` | Resumable grid, simple baselines, report. |

Task in every experiment: see 16 noisy steps, forecast the next 16. Error = mean squared error against the true
(noise-free) future, divided by its variance. N = number of independent training trajectories; P = trainable parameters.

## Findings

**1. No sudden threshold was found; error falls gradually with data.** On the damped oscillator (13 data amounts
from 10 to 10,000, 3 seeds) a power law, error ∝ N^-0.35, fits as well as a step: AICc −55.6 against −54.4, a
difference too small to prefer either. The largest local slope is 0.61 against an average of 0.30. So for these
systems "the threshold" is a point on a smooth curve that depends on the error you ask for, not a critical value.

**2. Data, not model size, set the error here.** Damped oscillator, test error:

| parameters | N=100 | N=1,000 | N=10,000 |
|---|---|---|---|
| 8,468 | 0.564 | 0.289 | 0.238 |
| 48,596 | 0.538 | 0.262 | 0.128 |
| 490,916 | 0.576 | 0.265 | 0.091 |
| 977,492 | 0.513 | 0.241 | 0.114 |
| 4,931,596 (1 seed) | 0.453 | 0.275 | 0.101 |
| 9,914,492 (1 seed) | 0.593 | 0.340 | 0.100 |

(Seed-to-seed spread of one run is about 0.03.) Beyond roughly 50K–500K parameters, more parameters did nothing;
the 10M model was no better than the 0.5M one (0.100 against 0.091). Ten times more data cut the error by about
2.4×. The transport systems still gained from size up to the largest run (advection-diffusion at N=10,000: 0.076 at
7K, 0.026 at 44K, 0.013 at 245K, 0.0093 at 1M).

**3. The fitted threshold function** (damped oscillator, 90 runs): floor 0.011, alpha 0.377, beta 0.981; typical
misfit ×1.16. Tested honestly: fitted only on runs with N ≤ 3,000 and size ≤ 1M (65 runs), it predicted the 25
unseen runs (N = 10,000 or size ≥ 2M) within a typical factor of ×1.24, against ×1.31 for simply reusing the nearest
measured cell. That is a small advantage, not a strong one. Minimum data it gives for a 1M-parameter model:

| target error | fitted minimum N (10–90% interval) | measured |
|---|---|---|
| 0.4 | 234 (213–248) | 252 |
| 0.3 | 516 (458–553) | 564 |
| 0.2 | 1,599 (1,373–1,726) | 1,527 |
| 0.15 | 3,626 (3,146–4,106) | 2,936 |
| 0.1 | 11,930 (10,184–14,887) | not reached by N = 10,000 (extrapolated) |
| 0.05 | 109,663 (75,418–542,723) | extrapolated; interval is very wide |

**4. The threshold is not a fixed number of Shannon bits.** Counting each noisy observation at its channel capacity,
the data needed to reach error 0.3 was 29,463 bits at noise 0.05, 31,571 at noise 0.2 and 102,344 at noise 0.5;
for error 0.4 it was 13,338, 9,737 and 19,829. Noise-free data (unlimited bits per observation) needed almost the
same N as noise 0.05. What counted was the number of independent trajectories, and their spread:

**5. Diversity matters more than volume.** Trained on a quarter of the parameter range and tested on the full range,
10,000 trajectories gave 0.435, worse than 300 trajectories drawn from the full range (0.379).

**6. Training compute saturates.** At N = 10,000: 300 steps 0.361, 1,000 steps 0.162, 3,000 allowed 0.137,
10,000 allowed 0.141 (early stopping used about 1,900).

**7. Different abilities need different amounts.** Trajectories needed by the best model up to 1M parameters:

| system | bits to state its parameters (for error 0.03) | N for error 0.3 | N for 0.1 | N for 0.03 | error at N=10,000 | ridge regression | oracle |
|---|---|---|---|---|---|---|---|
| diffusion | 0.7 | ≤ 30 | ≤ 30 | 88 | 0.0037 | 0.021 | 0.0008 |
| advection-diffusion | 3.1 | ≤ 30 | ≤ 30 | 534 | 0.0093 | 0.123 | 0.0081 |
| harmonic | 3.7 | 231 | 1,379 | 5,373 | 0.019 | 0.497 | 0.0095 |
| damped | 3.5 | 658 | 6,490 | not reached | 0.091 | 0.425 | 0.029 |

Systems that take more bits to specify broadly needed more data (the two oscillators are close in bits and far apart in data), so with four systems this is a pattern, not a law. The oracle searches a parameter grid, so its own error is slightly above the true floor.
Atlas beat ridge regression on every system by 5–26×, and got within 1.2× of the oracle on advection-diffusion,
but stayed 2× (harmonic), 3× (damped) and 5× (diffusion) above it.

**8. Where it failed.**
* **It did not learn the equations.** On parameter ranges it never saw, the oscillator error was 0.93–0.98 (the
  oracle gets 0.005–0.016). It learned to interpolate inside the training range, not the law. Transport systems
  transferred better (advection-diffusion 0.051, oracle 0.0011).
* **Its uncertainty does not flag the unseen range.** Interval width separated unseen from seen trajectories with
  AUROC 0.34–0.69 (0.5 is chance). Inside the training range the intervals are good: 78–80% coverage for a nominal
  80%, and width tracks error (rank correlation 0.52–0.88).
* **The hard conservation rule did not lower the data need.** With it on or off the errors were within the seed
  spread at every N (advection-diffusion at N=10,000: 0.011 on, 0.013 off).

**9. Interventions work inside the training range.** Changing the future forcing and comparing with the exact
counterfactual: error of the predicted effect 0.024–0.053 (relative to the size of the true effect) at N = 10,000.
This is a simulated system with a known answer, not evidence about any real policy.

## v0.2: working on the three failures

v0.1 failed in three ways: it did not extrapolate to unseen parameter ranges, its uncertainty did not flag them,
and the conservation rule did not reduce the data needed. v0.2 makes one change. Instead of mapping the window
straight to a forecast, the model first **identifies the dynamics from the window itself** (`atlas/sysid.py`), runs
them forward, and lets the network add a correction. The network supplies what one window cannot show: a prior for
the coefficients, a denoising correction, and the response to a forcing that has not acted yet. The identified
coefficients also give a new warning signal: how far they lie from anything seen in training.

Both variants below have about 250K parameters, 2 seeds, and the same training protocol. *plain* = v0.1 Atlas.
*ID* = with identification. Error at N = 10,000 training trajectories unless stated:

| | harmonic | damped | diffusion | advection-diffusion |
|---|---|---|---|---|
| **Unseen range**, plain | 0.929 | 1.181 | 0.0075 | 0.066 |
| **Unseen range**, ID | **0.038** | **0.090** | 0.0083 | **0.0086** |
| Unseen range, identification with no training at all | 0.044 | 0.109 | 0.089 | 0.081 |
| Unseen range, oracle | 0.0048 | 0.016 | 0.0003 | 0.0011 |
| **Warning flag** AUROC, plain (interval width) | 0.70 | 0.38 | 0.44 | 0.68 |
| **Warning flag** AUROC, ID (distance of identified dynamics) | **0.95** | **0.94** | 0.66 | 0.77 |
| Unseen cases flagged, ID (false alarms on seen cases) | 76% (4%) | 68% (5%) | 10% (5%) | 23% (5%) |
| Seen range, plain | **0.024** | 0.107 | **0.0037** | **0.013** |
| Seen range, ID | 0.048 | 0.098 | 0.0096 | 0.019 |
| Seen range with 30% of inputs missing, plain | **0.063** | **0.166** | **0.0066** | **0.021** |
| Seen range with 30% of inputs missing, ID | 0.439 | 0.656 | 0.050 | 0.030 |

**Failure 1, extrapolation: largely fixed on three of four systems.** Unseen-range error fell 24× (harmonic), 13×
(damped) and 8× (advection-diffusion). Diffusion did not change (it was already close). Two limits: the result is
still 5–8× above the oracle (28× on diffusion), and on the two oscillators it is only slightly better than
identification with no training at all (0.038 against 0.044; 0.090 against 0.109). On the transport systems
training adds a great deal (0.0086 against 0.081).

**Failure 2, knowing when it is out of its depth: fixed for the oscillators, partly for transport.** The new flag
separates unseen from seen cases with AUROC 0.94–0.95 on the oscillators (v0.1: 0.38–0.70), 0.77 on
advection-diffusion and 0.66 on diffusion. It is also useful inside the seen range: flagged harmonic cases had error
0.37, unflagged ones 0.034. Replacing flagged forecasts by training-free identification was tested and is not
recommended: it helped unseen cases only at small N and made the seen range worse (harmonic 0.048 → 0.175).

**Failure 3, a physics prior that lowers the data needed: yes for coarse targets, no for fine ones.**
Trajectories needed in the seen range:

| system | target error | plain | ID |
|---|---|---|---|
| harmonic | 0.3 | 210 | ≤ 30 |
| harmonic | 0.1 | 1,356 | 765 |
| harmonic | 0.03 | 6,887 | not reached by 10,000 |
| damped | 0.3 | 545 | 171 |
| damped | 0.1 | not reached by 10,000 | 8,473 |
| advection-diffusion | 0.1 | 83 | 39 |
| advection-diffusion | 0.03 | 587 | 85 |
| diffusion | 0.03 | 88 | 427 |
| diffusion | 0.01 | 449 | 2,017 |

With little data the prior is worth 2–7× less data (and at N = 100 it cuts intervention error from 0.33–0.50 to
0.05–0.08). With plenty of data the plain network is better on harmonic and diffusion, and on diffusion the prior
costs about 5× more data at both targets measured. So the prior moves the threshold; it does not remove it, and it can move
it the wrong way.

**What v0.2 made worse.**
* **Missing inputs.** With 30% of the window hidden, ID is far worse than plain on the oscillators (0.439 against
  0.063; 0.656 against 0.166). Identification from a gappy 16-step window is fragile; not fixed.
* **Seen-range accuracy at high N** on harmonic and diffusion (table above).
* **Stability.** One of two advection-diffusion runs at N = 3,000 stopped early at error 0.070 (the other: 0.014),
  and unseen-range error is uneven from one N to the next (damped: 0.158, 0.557, 0.155 at N = 100, 300, 1,000).
* **Cost.** About 3× the CPU time per training step.

Model size still does not matter: with identification, a 44K-parameter model did as well as 250K, 1M and 10M on the
damped oscillator (seen / unseen at N = 10,000: 0.088 / 0.060, 0.128 / 0.099, 0.089 / 0.101, 0.098 / 0.089; one seed).

How the design was reached: three variants (plain roll-out, a learned gate between the two paths, the final one)
were each tried on one or two single runs while looking at seen- and unseen-range test error. An iterative
refinement and a noise-bias correction were tried on the untrained identification and dropped because they were
unstable. The design was then frozen and the 103-run grid was run once; the tables are from that grid.

## v0.3: missing inputs, and the move to real data

**Missing inputs.** v0.2's identification broke when part of the window was hidden. v0.3 changes two things: hidden
values are filled by linear interpolation in time before identification (instead of the network's reconstruction
plus a re-fit), and both variants are trained with 0–40% of inputs hidden per trajectory (instead of a fixed 15%).
48 runs, 250K parameters, 2 seeds (`results/runs_gaps.jsonl`). Error with 30% of inputs hidden:

| | N | plain | ID v0.2 | ID v0.3 |
|---|---|---|---|---|
| harmonic | 1,000 | 0.156 | 0.627 | **0.161** |
| harmonic | 10,000 | 0.053 | 0.439 | **0.159** |
| damped | 1,000 | 0.316 | 0.894 | **0.330** |
| damped | 10,000 | 0.132 | 0.656 | **0.148** |
| diffusion | 1,000 | 0.0075 | 0.203 | 0.105 |
| diffusion | 10,000 | 0.0055 | 0.050 | 0.041 |
| advection-diffusion | 1,000 | 0.028 | 0.033 | 0.076 |
| advection-diffusion | 10,000 | 0.018 | 0.030 | 0.035 |

* **Oscillators: mostly repaired.** 3–4× better than v0.2 and level with the plain model, except harmonic at
  N = 10,000 where plain is still 3× better.
* **Transport systems: not repaired.** Identification is still 2–14× worse than plain with gaps, and on
  advection-diffusion v0.3 is worse than v0.2 at N ≤ 1,000.
* **Beyond what it was trained on, it collapses.** With 50% hidden (training went up to 40%), ID error is 0.46–1.9
  on every system; plain degrades gently (0.010–0.52).
* **Side effects with nothing hidden.** Seen-range error improved (harmonic at N = 10,000: 0.048 → 0.035; damped
  0.098 → 0.069, now better than plain's 0.110; advection-diffusion 0.019 → 0.012, level with plain and no failed
  run this time). Unseen-range error on the oscillators got worse (harmonic 0.038 → 0.110, damped 0.090 → 0.146),
  still 8–10× better than plain (1.04, 1.21).

So identification remains a trade: better with little data, on unseen ranges and for interventions; worse when the
window has many gaps. On real data the choice between plain and ID is therefore made on validation, not assumed.

**Real data (stage 7).** `delhi/run_atlas_delhi.py` runs Atlas on Delhi's CPCB stations with the same data file,
splits, test windows and scoring as the PWM-W Delhi league (branch `delhi-v0.2`): next-24-hour PM2.5 at every
station, from the last 72 h of 15 measured variables. Observations only. It compares plain and ID at two sizes on
validation, scores the chosen one once on test against TimesFM 2.5 / 3.0 and Chronos, measures which inputs matter,
and repeats training on the last 0.5–4 months to measure the data threshold. Results follow.

### Stage 7 results (Kaggle run atlas-delhi v2, 2026-11-12, CPU, 666 minutes)

39 Delhi stations (31 trained on, 8 never trained on), 2024-01-01 to 2025-12-31; train to 2025-05-02, validation
to 2025-07-02, test 2025-07-03 to 2025-12-31. PM2.5, next 24 h, MAE in µg/m³. The foundation models' scores match
the earlier Delhi league on the same windows (Chronos-2: 31.17 / 27.41 in both runs).

| Model | Trained stations | Unseen stations | Atlas against it (trained / unseen) |
|---|---|---|---|
| TimesFM 2.5 (200M, zero-shot) | **30.83** | **27.10** | loses +8.4% (p=0.0006) / loses +7.3% (p=0.0009) |
| Chronos-2 (120M, zero-shot) | 31.17 | 27.41 | loses +7.2% (p=0.003) / loses +6.1% (p=0.007) |
| Chronos-Bolt base (205M, zero-shot) | 31.35 | 27.94 | loses +6.6% (p=0.005) / tie +4.0% (p=0.08) |
| **Atlas plain, 967,632 parameters, 3 seeds** | 33.42 | 29.07 | – |
| Atlas plain, 231,312 parameters, 1 seed | 34.73 | 30.34 | wins −3.8% / −4.2% |
| Atlas ID, 984,749 parameters, 1 seed | 34.97 | 30.48 | wins −4.4% / −4.6% |
| Atlas ID, 238,637 parameters, 1 seed | 35.79 | 31.78 | wins −6.6% / −8.5% |
| Same hour yesterday | 40.30 | 35.39 | wins −17.1% / −17.9% |
| Last observed value | 46.01 | 38.69 | wins −27.4% / −24.9% |

* **Atlas does not beat the foundation models on Delhi PM2.5.** A 1M-parameter model trained from zero on 16 months
  of one city is 6.6–8.4% behind three zero-shot models of 120–205M parameters on trained stations, significantly
  in every case, and behind two of three on unseen stations. It beats both simple baselines by 17–27%.
* **Identification did not help on real data.** Validation MAE: plain 22.60 (250K) and 22.02 (1M); ID 22.70 and
  22.91. Both ID runs hit the 50-minute cap (they are 5–7× slower per step on CPU). ID is much worse one hour
  ahead (23.3 against 14.9 µg/m³ on trained stations) and about level from six hours on: its forecast starts from a
  smoothed state rather than from the last reading.
* **The validation rule was weaker than it looked.** The noise floor came from three seeds of the 250K model
  (sigma 0.107). The 1M model's own seeds spread far more (validation 21.83, 22.02, 22.62, 22.89), so "1M beats
  250K" rests on one seed; the 3-seed ensemble is what was scored.
* **What the final model uses** (trained-station MAE with inputs hidden at test time; all inputs 33.42): other
  pollutants hidden 37.96 (+13.6%); meteorology hidden 36.37 (+8.8%); only the last 24 h visible 36.47 (+9.1%);
  30% of all inputs hidden at random 34.40 (+2.9%). The foundation models see none of the other variables but read
  512 h of PM2.5 history; Atlas reads 72 h.
* **Not run:** TimesFM 3.0 and the data-threshold study were skipped for time (TimesFM 2.5 alone took about 7 of
  the 11 hours on CPU). The 10M model needs a GPU.

### Stage 8 results (Kaggle run atlas-delhi-threshold, 2026-11-12, CPU, 353 minutes)

**A. Longer history.** Validation MAE over 3 seeds: 72 h 21.98 / 22.22 / 22.18 (mean 22.128); 336 h of PM2.5 history
22.28 / 21.90 / 22.29 (mean 22.155). Difference −0.027 ± 0.148 (standard error): not adopted, 72 h kept. On test the two
tie (trained stations 32.93 against 32.90, p = 0.92; unseen 28.84 against 28.95, p = 0.65). **A longer history is not
what separates Atlas from the foundation models.**

Adopted Atlas (72 h, 1M parameters, 3 fresh seeds) against the cached foundation-model forecasts, PM2.5 MAE µg/m³:

| | trained stations | unseen stations |
|---|---|---|
| Atlas, 3 seeds | 32.93 | 28.84 |
| TimesFM 2.5 | 30.83 (Atlas loses +6.8%, p = 0.003) | 27.10 (loses +6.4%, p = 0.002) |
| Chronos-2 | 31.17 (loses +5.6%, p = 0.012) | 27.41 (loses +5.2%, p = 0.02) |
| Chronos-Bolt base | 31.35 (loses +5.0%, p = 0.024) | 27.94 (tie +3.2%, p = 0.16) |

**B. Data and size on Delhi** (single models, median forecast, trained stations, test MAE, mean of 2 seeds):

| parameters | 0.5 mo | 1 mo | 2 mo | 4 mo | 8 mo | 15 mo (all) |
|---|---|---|---|---|---|---|
| 50,232 | 47.3 | 48.3 | 50.6 | 43.1 | 38.0 | 35.1 |
| 231,312 | 43.5 | 47.1 | 51.9 | 43.6 | 36.9 | 34.9 |
| 967,632 | 42.7 | 42.8 | 44.2 | 40.0 | 35.4 | 34.3 |
| 3,972,192 (1 seed) | – | – | 42.4 | – | – | 36.6 |

More data helps strongly here (about 44–52 with 2 months, 34–35 with 15), unlike the all-India regions in ATF v1.0.
Size helps a little from 8 months on (1M best); 4M was worse than 1M with all data (36.6 against 34.3, one seed).
Single models with few months vary a lot between seeds (for example 41.7 and 55.0 at 1 month, 50K).

Threshold function fitted to these 38 runs: misfit ×1.09; fitted without the largest data amount it predicted those
7 runs within ×1.10 (biased 8% high). The fitted floor sits at its bound (0), so the floor is not identified and the
decay is slow (α = 0.087, β = 0.308). **Extrapolation, not measurement:** to reach each foundation model a single 4M
model would need about 12,200 training windows for Chronos-Bolt (10–90%: 8,100–22,400), 13,000 for Chronos-2
(8,700–24,200) and 14,900 for TimesFM 2.5 (10,000–28,300), against 3,673 measured (15 months); that is roughly 4–5 years
of Delhi history at this sampling. These are single uncalibrated models; the 3-seed ensemble above (32.93) already
does better than any single model, so the true requirement for an ensemble is likely lower.

## Atlas Threshold Function (ATF): plan and rules, written before any result

**Question.** Before collecting more data or training on it, can we predict how accurate a model will become on a
*real* station network, and from how many months of data it will beat the foundation models (TimesFM, Chronos)? And
can that prediction be used to build a forecasting system that beats every single model?

**v1.0: real-data learning curves** (`bench/curves.py`). 13 networks, fixed in advance: 6 regions of India's NOAA ISD
airport/synoptic stations (k-means on position, seed 0, up to 32 stations each; temperature, humidity, wind; up to 9
years of training data), the CPCB rooftop stations of 6 cities (PM2.5, temperature, humidity, wind; up to 11 months)
and Delhi (same four; up to 16 months). On each network Atlas (plain, about 250K parameters, from random weights) is
trained on the most recent 0.5, 1, 2, 4, 8, 16, 32, 64 months and all data (as far as the network has them), 2 seeds
each, and scored on a fixed test period (ISD and Delhi: last 182 days; cities: last 90 days). Forecasts are saved.

**v1.1: the threshold function, tested on networks it has not seen.** For each network in turn, the function is
fitted on the *other* 12 networks and then predicts this network's error at every data amount from its own **2-month
pilot** runs only (about 15 CPU-minutes). Candidates, all fixed now:
* M0 no improvement: error(N) = pilot error.
* M1 per-network power law fitted to the 0.5-, 1- and 2-month pilots (standard learning-curve extrapolation).
* M2 **ATF**: error(N) = e_p · [φ + (1 − φ)(N / N_p)^−α], with α and φ pooled from the other networks' curves
  (each curve relative to its own 2-month error e_p).
* M3 ATF with α and φ pooled per variable (temperature, humidity, wind, PM2.5).

Primary measure: median absolute log error of the predicted test MAE at the largest data amount (lower is better), over
all held-out network-targets. **ATF counts as working only if M2 or M3 beats both M0 and M1 on that measure and a
paired sign test over network-targets gives p < 0.05.** Also reported: error over all amounts above 2 months, and
whether the 80% intervals cover the measured errors.

**v1.2: decide before training whether, and how, to use our model.** TimesFM 2.5 / 3.0 and Chronos run zero-shot on the
same windows. (a) Does ATF predict, from the 2-month pilot, whether Atlas trained on all data will beat the best
foundation model (accuracy against always-yes and always-no), and the months needed? (b) Combination: for every
network-target, the weight between Atlas and the best foundation model (0, 0.25, 0.5, 0.75, 1) is chosen on
validation only, then scored once on test. **The combination counts as beating a model only where it is lower on test
MAE with p < 0.05 (Diebold-Mariano on daily errors and a day-block bootstrap), and the overall claim needs this
against every foundation model on a majority of network-targets.**

Known limits, stated in advance: one model family (Atlas) and one size; "more months" also means other seasons, so a
data amount is not a count of identical samples; the 6 city networks share coordinates within a city (no geometry).

### ATF v1.1 results (Kaggle runs atf-curves-s0..s3 and atf-analysis, 2026-11-12)

All 192 planned training runs finished (13 networks, 46 network-targets; about 9 CPU-hours in 4 parallel sessions).
Curves: [`results/atf/curves_v10.txt`](results/atf/curves_v10.txt) (test MAE per data amount, mean of 2 seeds, with
persistence and same-hour-yesterday baselines). The analysis was run on Kaggle (`bench/atf.py`) and reproduced exactly
here from that file.

**Predicting an unseen network's error from its 2-month pilot** (leave-one-network-out; error of the prediction as
median |log(predicted / measured)|, lower is better):

| method | at the largest data amount (46) | within 10% | all amounts above 2 months (192) |
|---|---|---|---|
| M0 no improvement | 0.200 (off by ×1.22) | 24% | 0.122 |
| M1 per-network power law (standard extrapolation) | 0.156 (×1.17) | 39% | 0.093 |
| M2 ATF, pooled | 0.098 (×1.10) | 50% | 0.092 |
| **M3 ATF, pooled per variable** | **0.093 (×1.10)** | 50% | **0.070** |

Sign tests at the largest amount: M3 beats M0 on 36 of 46 (p = 0.0002) and M1 on 32 of 46 (p = 0.011); M2 beats M0
34/46 (p = 0.002) and M1 31/46 (p = 0.026). **The pre-registered rule is met by both M2 and M3: ATF works.** The 80%
intervals covered 74% (largest amount) and 78% (all amounts) of measured errors.

Robustness check, not pre-registered: the 46 targets come from 13 networks, so they are not independent. Counting one
vote per network (mean error over its targets): M3 beats M0 and M1 on 11 of 13 networks (sign p = 0.022; Wilcoxon
p = 0.006 and 0.001). M2 beats M1 on 10 of 13 (sign p = 0.09, Wilcoxon p = 0.013), so M2's lead over M1 is weaker.

**What the fitted law says** (all 13 networks, e(N) = e(2 mo)·[φ + (1 − φ)(N/2)^−α]): going from 2 months to all data
cuts error by about 36% for temperature, 27% for humidity, 17% for PM2.5 and 16% for wind. PM2.5 gains early and then
flattens (φ = 0.83); wind gains slowly at every scale.

**Two findings that limit what this means:**
* **More data did not reliably help.** On all 6 all-India regions, training on the last 32 or 64 months was worse than
  on the last 16 months, for every target (18 of 18), while all 111 months was about as good as 16. The seeds agree,
  so this is systematic, not noise. Possible causes, unresolved: data-quality changes in the 2018–2022 ISD records,
  early stopping on a pre-monsoon validation period that differs from the June–November test, or both. ATF wins partly
  because it learns that gains are modest; M1 extrapolates noisy pilots.
* **Atlas itself is weak on the small city networks.** With all its data it beats "same hour yesterday" on 18 of 18
  all-India targets but only 9 of 24 city targets and 2 of 4 Delhi targets. Chennai has a single usable station.
  ATF predicts Atlas's errors well; that does not make those errors small.

### ATF v2.0: does the law hold outside weather and air quality? (plan and rules, written before any result)

The law is **frozen** as fitted on the 46 Indian curves (`bench/atf_law.json`: α = 0.179, φ = 0.474, 80% interval from
the Indian residuals), committed before any v2.0 curve was trained. It is then applied, unchanged, to four public
forecasting benchmarks from other domains (`bench/fetch_bench.py`), each split into networks fixed now:
electricity use of 256 customers (8 groups of 32, 2012–2014), road occupancy of 256 sensors (8 groups of 32,
2015–2016), output of 128 solar plants (4 groups of 32, 2006, averaged to hourly), and the two ETT transformers (oil
temperature, with 6 load readings as inputs). 22 networks, one target each. Each series is put in fixed units
(mean and spread before validation) so errors are comparable. Same Atlas, same training, data amounts 0.5–16 months
and all data, 2 seeds; test = last 182 days (electricity), 91 (traffic, ETT), 61 (solar).

**Rule.** For each network the frozen law predicts the test MAE with all data from that network's own 2-month pilot.
It "transfers" only if its median |log(predicted / measured)| at the largest amount is lower than both M0 (no
improvement) and M1 (power law fitted to the network's own 0.5/1/2-month pilots) and a two-sided sign test over the
22 networks gives p < 0.05 against each. Reported also: all amounts above 2 months, interval coverage, results per
dataset. Groups within one dataset are not independent; with 22 networks the test needs about 16 wins of 22.

**Diagnostic for the 32–64-month dip** (not part of the rule). Hypothesis: early stopping on the pre-monsoon validation
period caused it. Test: the 6 all-India regions at 16, 32, 64 months and all data, trained a fixed 4,000 steps with
the final weights kept, 1 seed; plus per-year missing data and level of each variable. The hypothesis is supported if
the dip (32 or 64 months worse than 16 by more than 3%) disappears in at least 5 of 6 regions.

**The tool** (`bench/atf_tool.py`). Any hourly multi-series data (CSV with one column per series, or npz): it trains
the 0.5/1/2-month pilots, applies the frozen law, and prints the predicted error for more data with an 80% interval,
the months needed for a target error (or that more data alone will not reach it), and the gain from doubling the
data; `--verify` also trains on all the data and prints measured against predicted.

*Tool demo (real, `results/atf/tool_demo_electricity_65.txt`).* The 65 electricity customers that are in none of the
v2.0 networks, on this machine's 2 CPU cores (about 70 minutes, mostly the `--verify` training). Pilots: 0.370 (0.5
month), 0.358 (1), 0.346 (2) in standardised MAE; persistence 0.841. The tool predicted 0.275 with all 31.8 months
(80% interval 0.228–0.321); training on all of it measured **0.252**: off by ×1.09 and inside the interval. The pilot
alone (M0) was off by ×1.37 and the power law on the pilots (M1) by ×1.20. One network, so an illustration, not
a test; the test is the 22 networks above.

### ATF v2.0 results, part 1: the 32–64-month diagnostic (Kaggle run atf2-diag, 2026-11-12, 137 minutes)

Each all-India region trained for a fixed 4,000 steps with the final weights kept (no early stopping), 1 seed; test MAE
(temperature °C, humidity %, wind m/s):

| region | AT 16 / 32 / 64 / all | RH 16 / 32 / 64 / all | WS 16 / 32 / 64 / all | 32 ÷ 16 | 64 ÷ 16 | all ÷ 16 |
|---|---|---|---|---|---|---|
| isd-r0 | 1.27 / 1.77 / 1.89 / 1.25 | 5.61 / 8.01 / 7.94 / 5.54 | 0.691 / 0.812 / 0.804 / 0.699 | 1.33 | 1.36 | 0.99 |
| isd-r1 | 1.10 / 2.99 / 1.46 / 1.08 | 5.47 / 8.79 / 7.06 / 5.49 | 0.809 / 1.068 / 0.908 / 0.802 | 1.88 | 1.24 | 0.99 |
| isd-r2 | 1.08 / 3.18 / 1.49 / 1.06 | 5.57 / 9.76 / 7.00 / 5.43 | 0.900 / 1.115 / 1.070 / 0.887 | 1.98 | 1.27 | 0.98 |
| isd-r3 | 1.18 / 1.33 / 1.54 / 1.15 | 5.71 / 6.32 / 7.09 / 5.65 | 0.819 / 0.874 / 0.922 / 0.822 | 1.10 | 1.22 | 0.99 |
| isd-r4 | 1.35 / 2.89 / 2.17 / 1.32 | 6.00 / 11.36 / 8.50 / 5.80 | 0.601 / 0.680 / 0.652 / 0.604 | 1.72 | 1.37 | 0.98 |
| isd-r5 | 0.99 / 1.16 / 1.24 / 0.98 | 5.13 / 5.92 / 6.57 / 5.08 | 0.930 / 1.016 / 1.042 / 0.934 | 1.14 | 1.21 | 0.99 |

**Verdict: the early-stopping hypothesis is NOT supported.** The dip is present in 6 of 6 regions (pre-registered
test needed it to vanish in 5), and fixed-length training made it slightly larger, not smaller (for example isd-r1:
32 months is 2.7× worse than 16 on temperature). All data is again as good as or slightly better than 16 months.

The per-year check found no obvious data break: across the six regions, missing data is 54–57% every year from 2016
to 2023 (74% in 2015), the number of reporting stations is 138–146, and yearly mean temperature (26.1–26.9 °C),
humidity (66.5–70.6%) and wind (1.6–1.8 m/s) are steady. So the cause is still open. Two candidates remain: a
problem in the input variables that were not checked (dew point, pressure, visibility, wind direction) in parts of
2018–2022, or something about where the window starts rather than how long it is. The test that separates them
is to train on 16-month windows that end earlier (for example ending November 2022) and see whether those alone are
bad.

## Atlas-Delhi league: against the models on the master list (plan and rules, written before any result)

The master list (weather, traffic, flood, wildfire, landslide, earthquake, Earth-observation, urban, digital-twin,
Indian and Sarvam systems) holds several hundred names. A model can be an opponent here only if it produces a
forecast of something Delhi's stations measure, for hours that can be scored. Sorted by that test:

| Group on the list | Can it be scored on Delhi / Indian station data? | Where it stands |
|---|---|---|
| Time-series foundation models (TimesFM 2.5 and 3.0, Chronos-2, Chronos-Bolt; not on the list, but the strongest opponents found so far) | Yes: zero-shot on the same windows | PM2.5: Atlas alone loses by 5–8% (stage 8). Earlier PWM-W hybrid: ties; loses to TimesFM 3.0 multivariate on unseen stations (branch `delhi-v0.2`). **Not beaten.** |
| Air-quality forecast systems: CAMS global (ECMWF/Copernicus) | Yes (PM2.5) | Beaten: −50% raw, −25% after local bias correction (`delhi-v0.2`) |
| Operational global models with a public forecast archive: ECMWF IFS / HRES, ECMWF AIFS, DWD ICON, NOAA GFS, NOAA AIGFS (GraphCast-based) | Yes: temperature, humidity, wind at stations | Delhi's CPCB stations: PWM-W beats IFS, AIFS, ICON and GFS on all three variables. Six airports: the hybrid beats all six under the issued-before-start rule; under the strict rule it loses temperature to AIFS and IFS 0.25 and humidity to AIFS (`delhi-v0.4` … `india-v2.0`) |
| AI weather models with open weights and no archive: FourCastNet (SFNO), GenCast, GraphCast, FourCastNet 3, Aurora, Pangu-Weather, FuXi, FengWu, NeuralGCM, Stormer, … | Only by running them ourselves from real analyses (GPU) | SFNO and GenCast Mini ran: after their local bias correction PWM-W loses temperature, ties wind. GraphCast Operational, FourCastNet 3, Aurora: out of memory on the free GPU. The rest: not run |
| WeatherNext, GenCast (full), MetNet-3, Aardvark and other closed or archive-less systems | No public forecasts for these stations and dates | Not scored (not publicly available) |
| Traffic forecasting architectures: DCRNN, STGCN, Graph WaveNet, AGCRN, MTGNN, GMAN, STID, PDFormer, STAEformer, … | Yes as architectures: trained on Delhi's station graph with their authors' code (GPU) | Not yet on Delhi. On the standard traffic benchmarks PWM-Dyn v0.6 was level with or ahead of STID, Graph WaveNet and STAEformer on 5 of 6 networks; STAEformer led on PEMS08, and several specialist runs were stopped by the time budget (`main`, RESULTS.md §3) |
| Traffic and urban foundation models: UniST, UrbanGPT, GPT-ST, STEP, … | Only where weights are public and accept an irregular station graph | Not checked yet |
| Radar nowcasting (DGMR, NowcastNet, MetNet), climate and Earth-system models (CESM, E3SM, …) | No: no public Indian radar archive; decadal climate is a different question from the next 24 h | Out of scope |
| Traffic-signal control, traffic simulators, commercial traffic systems, digital twins, city platforms | No: they do not publish forecasts of station measurements, and there is no open Delhi traffic feed | Out of scope |
| Flood, wildfire, landslide, earthquake, tsunami, damage-assessment models | No: different tasks and data from station air quality and weather | Out of scope until that hazard's Indian data is collected |
| Indian systems: BharatFS, Mithuna, IMD and NCMRWF forecasts, SAFAR / air-quality early warning | Only if archived forecasts at station points are published; none found | Not scored (not publicly disclosed) |
| Sarvam models and other language models | They are not physical forecasters and are not used as one | Not opponents |

So the open target is the first row: **no Paradox model has beaten the time-series foundation models on Delhi PM2.5.**
The steps below go after that, one change per version.

(That was the position before the runs below. For where it stands now, see "Atlas-Delhi v1.1 results".)

### Atlas-Delhi Fusion v1.0 (rules)

Atlas and the open-licence foundation models forecast together (`delhi/fuse.py`). Members: the saved Atlas 3-seed
ensemble (stage 7: 33.42 / 29.07), TimesFM 2.5, Chronos-2, Chronos-Bolt (their cached forecasts on the same windows).
TimesFM 3.0 is never a member. The fused forecast is a weighted average of the members' quantiles, weights
non-negative, summing to 1, on a 0.05 grid, chosen on training stations only:

* **static:** once, on the validation period; equal weights, one set, or one set per lead block (1–6, 7–12, 13–24 h),
  whichever has the lowest 5-fold blocked cross-validated MAE on validation;
* **online (the primary entry):** one set per lead block, re-chosen at the start of every test day from the previous
  30 days of forecasts whose 24 target hours were all observed before that day began; the 80% band is calibrated on
  the same trailing windows. Reason, fixed before the run: validation is May–July and the test runs July–December
  (monsoon, then the smog season), so weights fitted once in summer may not suit winter. Nothing later than a
  forecast's start is used.

Both entries are reported whatever they score. Controls: the same two procedures with the three foundation models
only. Rules for the words used:

* the fusion **beats** a model only with a significant MAE win (Diebold–Mariano p < 0.05 and a day-block bootstrap
  95% interval excluding zero) on **both** the trained stations and the unseen stations;
* **Atlas adds information** only if the fusion significantly beats the foundation-models-only fusion (same procedure)
  on the trained stations; otherwise any gain is credited to combining the foundation models, not to Atlas;
* a fusion that contains a model has not beaten it as an independent model: every statement says "Atlas together
  with …". Atlas alone stays in the table;
* TimesFM 3.0 (30.31 / 26.84; multivariate 29.95 / 26.16 in `delhi-v0.2`) is compared by number only until its
  forecasts on these windows are re-made on a GPU; no verdict against it before that.

Known weaknesses: Atlas's training stopped on a superset of the validation windows used to fit the static weights
(a small bias towards Atlas in the static entry; the online entry does not have it after the first month); the
online entry reads 30 days of past forecast errors that a single zero-shot model does not use, which is part of
the system and is stated wherever it is reported.

### Atlas-Delhi Fusion v1.0 results (Kaggle run atlas-delhi-fusion, 2026-11-13, CPU, 3.7 minutes)

Checks first: each member alone reproduces its earlier score to two decimals (Atlas 33.42 / 29.07, TimesFM 2.5
30.83 / 27.10, Chronos-2 31.17 / 27.41, Chronos-Bolt 31.35 / 27.94). PM2.5, next 24 h, MAE in µg/m³, 725 test windows.

| Entry | Trained stations | Unseen stations | Fusion (online) against it: trained / unseen |
|---|---|---|---|
| **Atlas-Delhi Fusion, online (primary)** | **30.13** | **26.50** | – |
| Atlas-Delhi Fusion, static | 30.16 | 26.58 | tie −0.1% (p=0.90) / tie −0.3% (p=0.59) |
| Foundation models only, online (control) | 30.43 | 26.82 | tie −1.0% (p=0.17) / tie −1.2% (p=0.077) |
| Foundation models only, static (control) | 30.55 | 26.94 | tie −1.4% (p=0.13) / tie −1.6% (p=0.073) |
| TimesFM 2.5 (200M) | 30.83 | 27.10 | **wins −2.3% (p=0.017) / wins −2.2% (p=0.024)** |
| Chronos-2 (120M) | 31.17 | 27.41 | **wins −3.3% (p=0.0001) / wins −3.3% (p=0.0002)** |
| Chronos-Bolt base (205M) | 31.35 | 27.94 | **wins −3.9% (p<0.0001) / wins −5.1% (p<0.0001)** |
| Atlas alone (1M, 3 seeds) | 33.42 | 29.07 | wins −9.8% / wins −8.8% (p<0.0001) |
| TimesFM 3.0, earlier league, not re-run | 30.31 | 26.84 | by number only: fusion 0.6% / 1.3% lower |
| TimesFM 3.0 multivariate, earlier league, not re-run | 29.95 | 26.16 | by number only: fusion 0.6% / 1.3% **higher** |

Verdicts under the rules above:

* **The fusion beats TimesFM 2.5, Chronos-2 and Chronos-Bolt**: significant MAE wins on both the trained and the
  unseen stations, for the online entry and for the static one (static: −2.2% / −1.9%, −3.3% / −3.0%, −3.8% / −4.8%;
  p from 0.018 down). The pinball loss of the quantiles agrees (−1.7% to −4.1%, all significant). This is the first
  significant win over these models on Delhi PM2.5 in this project, and it is **Atlas together with them**, not an
  independent model: Atlas alone still loses to all three.
* **Whether Atlas adds information is not settled.** Against the same procedure without Atlas, the online entry is
  1.0% / 1.2% better but not significantly (p = 0.17 / 0.077): by the rule, **not shown** for the primary entry. The
  static entry is 1.3% / 1.3% better and passes (p = 0.046 / 0.041), barely. Of the 2.3% gained on TimesFM 2.5,
  about 1.3 points come from combining the three foundation models and about 1 from adding Atlas. Whether the
  foundation-models-only fusion itself beats TimesFM 2.5 was not tested.
* **TimesFM 3.0 is not beaten.** By number the fusion is slightly ahead of univariate TimesFM 3.0 and slightly behind
  the multivariate one; no test until its forecasts are re-made on these windows (GPU).
* **Online against static: no difference** (p = 0.90 / 0.59). The reason given for making online the primary entry
  (summer weights may not suit winter) was not borne out in the score.
* **Where Atlas earns its weight.** Static weights from validation: hours 1–6 Atlas 0.55, Chronos-Bolt 0.45; hours
  7–12 Atlas 0.45, TimesFM 2.5 0.35, Chronos-Bolt 0.20; hours 13–24 Atlas 0.15, TimesFM 2.5 0.65, Chronos-Bolt 0.20.
  Online, Atlas's weight was 0.19–0.22 in July–September and 0.36–0.38 in October–November (the smog season), 0.26
  in December; mean 0.27 (TimesFM 2.5 0.39, Chronos-2 0.24, Chronos-Bolt 0.10).
* By lead time on trained stations (fusion online / TimesFM 2.5 / Atlas): 1 h 13.5 / 14.0 / 14.9; 6 h 27.9 / 29.2 /
  30.0; 12 h 32.2 / 32.9 / 36.3; 24 h 34.7 / 35.3 / 37.7. The 80% band covers 79%.

### Atlas-Delhi v1.1: all of Delhi's history (data, rules and predictions, written before any score)

**Data (Kaggle run atlas-delhi-long v2, 2026-11-13).** The league file has 16 months because OpenCity's earlier Delhi
files hold only the AQI index. `delhi/tools/build_delhi_long.py` joins the earlier measurements from a public copy of
CPCB's station exports (Kaggle dataset "Time Series Air Quality Data of India (2010-2023)", 453 stations, 40 in
Delhi) to the league file, with the league's own reader and cleaning rules:

* all 39 league stations matched by name and agency (the agency separates Pusa IMD from Pusa DPCC and Lodhi Road IMD
  from Lodhi Road IITM);
* 140,256 hours, 2010-01-01 to 2025-12-31; the last 17,544 are the league file unchanged, so stations, the seen /
  unseen split and every validation and test window are identical (checked in code on a copy);
* stations reporting PM2.5 on at least half the hours: 1–9 a year in 2010–2017, 32 in 2018, 36–38 in 2019–2022; the
  copy ends on 2023-03-31, so April–December 2023 is a gap;
* units agree across the join (median 2019–2022 against 2024–25: PM2.5 ×1.02, PM10 ×0.99, CO ×1.03, pressure ×1.00,
  temperature ×0.97; NO2 ×0.83, NO ×0.78, solar radiation ×0.70 are the largest shifts);
* 8 of the earlier files were stamped in UTC (solar-radiation peak at 04–07 h) and were moved to Indian time; on
  an hourly clock that leaves those stations half an hour off in the earlier years.

**What changes.** Only the training data. `delhi/run_atlas_long.py` trains the same 1M-parameter Atlas (inputs, loss,
masking, 72 h context as stage 7) on every valid window since 2018-01-01 (at least 8 training stations with 12 or more
observed PM2.5 hours in the last 24 h and in the 24 target hours). Per seed, two models: **B** all history, checkpoint
= best validation; **C** = B fine-tuned on the league's own 16 months at a fifth of the learning rate (C = B if
fine-tuning never improves validation). Three fresh seeds (300–302), one Kaggle CPU notebook each.

**Rules.**

1. The recipe (B or C) with the lower mean validation MAE over the three seeds is the v1.1 candidate; its three models
   are averaged and calibrated on validation exactly as before.
2. v1.1 is **adopted** only if that mean is lower than the 16-month Atlas's (stage 8: 21.98, 22.22, 22.18 on the same
   validation windows) by more than 2 standard errors of the difference. Its test scores are reported either way,
   and so are the other recipe's.
3. Atlas v1.1 **alone beats** a foundation model only with significant MAE wins on both the trained and the unseen
   stations. The fusion (same code and rules as v1.0, with v1.1 as the Atlas member) is reported beside it.
4. Validation is May–July and cannot see winter skill; no second look at the test is allowed to fix that.

**Predictions for a single model's test MAE on trained stations** (16 months: 34.3; about five times the windows):

| Source | Prediction |
|---|---|
| Stage-8 threshold fit on Delhi (error falls as windows^−0.087) | about 29.8 |
| The last measured doubling on Delhi only (8 → 15 months, slope −0.05) | about 31.6 |
| ATF-1.1 law for PM2.5, frozen from the six-city curves (α = 0.763, floor 0.826) | about 33.2 |

TimesFM 2.5 scores 30.83. The three predictions straddle it, so the run also says which of the lab's own laws to
trust on Delhi.

### Atlas-Delhi v1.1 results (Kaggle runs atlas-long-s300 / s301 / s302 and atlas-delhi-fusion-v11 v2, 2026-11-13, CPU)

**Training.** 19,082 valid windows since 2018 (2018: 2,784; 2019–2022: about 2,920 a year; 2023: 717; 2024: 2,924;
2025: 969), against 3,673 in stage 8. Same 967,632-parameter Atlas. Each run took 19–44 minutes; recipe B stopped
early at 8,400–14,400 of its 24,000 steps (ten validation checks without improvement).

| Seed | B: validation | B: test, one model (trained / unseen) | C: validation | C: test, one model |
|---|---|---|---|---|
| 300 | 20.980 | 31.96 / 27.89 | 20.733 | 31.66 / 27.66 |
| 301 | 21.016 | 31.39 / 27.37 | 20.686 | 31.43 / 27.41 |
| 302 | 21.002 | 31.74 / 27.86 | 21.002 (fine-tuning never improved: C = B) | 31.74 / 27.86 |

**Decision (rule 1 and 2).** C has the lower mean validation MAE (20.807 against 20.999). Against the 16-month Atlas
(mean 22.127) the difference is 1.320 with standard error 0.123: **v1.1 is adopted**.

**The predictions.** One model, trained stations: measured 31.70 for B (the pure "all history" recipe) and 31.61
for C. The last measured doubling (31.6) was right; the stage-8 threshold fit (29.8) was 6% too optimistic; the
ATF-1.1 PM2.5 law (33.2) was 5% too pessimistic. From 3,673 to 19,082 windows the error fell as windows^−0.048.

**Test, PM2.5, next 24 h, MAE µg/m³, 725 windows** (the three models averaged and calibrated on validation):

| Entry | Trained stations | Unseen stations | Atlas v1.1 alone against it | Fusion (online) against it |
|---|---|---|---|---|
| **Atlas-Delhi Fusion with v1.1, online (primary)** | **29.22** | **25.68** | loses +3.6% / +3.7% | – |
| Atlas-Delhi Fusion with v1.1, static | 29.21 | 25.75 | loses +3.6% / +3.4% | tie |
| **Atlas v1.1 alone (1M parameters, 3 seeds, no other model inside)** | **30.26** | **26.62** | – | wins −3.4% / −3.5% |
| Atlas v1.1, recipe B (not chosen) | 30.20 | 26.64 | tie +0.2% / −0.1% | wins −3.2% / −3.6% |
| Foundation models only, online (control) | 30.43 | 26.82 | tie −0.6% / −0.7% | **wins −4.0% (p<0.0001) / −4.3% (p<0.0001)** |
| Foundation models only, static (control) | 30.55 | 26.94 | tie −1.0% / −1.2% | wins −4.4% / −4.7% |
| TimesFM 2.5 (200M) | 30.83 | 27.10 | **tie −1.8% (p=0.29) / −1.7% (p=0.27)** | **wins −5.2% / −5.2% (p<0.0001)** |
| Chronos-2 (120M) | 31.17 | 27.41 | **tie −2.9% (p=0.069) / −2.9% (p=0.050)** | **wins −6.3% / −6.3% (p<0.0001)** |
| Chronos-Bolt base (205M) | 31.35 | 27.94 | **wins −3.5% (p=0.031) / −4.7% (p=0.004)** | **wins −6.8% / −8.1% (p<0.0001)** |
| Atlas v1.0 (16 months) | 33.42 | 29.07 | wins −9.4% / −8.4% (p<0.0001) | wins −12.6% / −11.6% |
| TimesFM 3.0, earlier league, not re-run | 30.31 | 26.84 | by number: 0.2% / 0.8% lower | by number: 3.6% / 4.3% lower |
| TimesFM 3.0 multivariate, earlier league, not re-run | 29.95 | 26.16 | by number: 1.0% / 1.8% **higher** | by number: 2.4% / 1.8% lower |

Verdicts under the rules written before the run:

* **Atlas alone no longer loses to the foundation models, and has not yet beaten the two best of them.** With all
  of Delhi's history it beats Chronos-Bolt on both tracks and is level with TimesFM 2.5 and Chronos-2 (ahead by number
  on both tracks, not significantly). In stage 8, on 16 months, it lost significantly to TimesFM 2.5 and Chronos-2 on
  both tracks. A 1M-parameter model trained from zero is now level with zero-shot models of 120–205M parameters.
* **More data was the lever, as the threshold work said.** Five times the windows cut the three-model error from
  33.42 / 29.07 to 30.26 / 26.62 (−9.4% / −8.4%), with the model, its inputs and its loss unchanged (the training
  schedule is longer, as five times the data needs).
* **The fusion beats TimesFM 2.5, Chronos-2 and Chronos-Bolt by 5–8%** on both tracks (p < 0.0001 everywhere), in
  both the online and the static form, and **Atlas adds information**: against the same procedure without Atlas the
  fusion is 4.0% / 4.3% better online and 4.4% / 4.4% better static (p < 0.0001). In v1.0 that contribution was about
  1% and not settled.
* **TimesFM 3.0: no verdict.** By number the fusion is now below both of its earlier scores, including the
  multivariate one that every earlier Paradox entry trailed; Atlas alone is level with the univariate and behind the
  multivariate. A test needs its forecasts on these windows (GPU).
* **B against C:** a tie on test (30.20 / 26.64 against 30.26 / 26.62). Fine-tuning on the last 16 months improved
  validation in two of three seeds and changed nothing that the test can see.
* **By lead time on trained stations** (Atlas v1.1 alone / TimesFM 2.5 / fusion online): 1 h 14.5 / 14.0 / 13.5; 6 h
  27.7 / 29.2 / 27.1; 12 h 32.3 / 32.9 / 31.1; 24 h 34.6 / 35.3 / 33.8. Atlas alone is behind in the first hour and
  ahead from six hours on. The 80% bands cover 78–80%.
* **Weights.** Static (one set, from validation): Atlas 0.40, TimesFM 2.5 0.40, Chronos-Bolt 0.20, Chronos-2 0.
  Online: Atlas 0.49 on average, 0.34–0.47 in July–September and 0.57–0.58 in October–November (the smog season).
* **What this does not show.** One city and one variable; three seeds; training stopped early on a summer
  validation at 35–60% of its planned steps, so the model may be under-trained; the comparison with TimesFM 3.0 is by
  number only; whether Atlas alone can pass TimesFM 2.5 with more seeds, a longer schedule or a larger model is open.

### Atlas-Delhi v1.2: the whole schedule and more seeds (rules, written before any score)

**Why.** In v1.1 every run stopped at 8,400–14,400 of its 24,000 steps, because a noisy summer validation went ten
checks without a new best; and with three seeds Atlas alone is 1.8% ahead of TimesFM 2.5 with p = 0.29.

**What changes.** Eight fresh seeds (310–317) instead of three, and every run trains the whole schedule
(`run_atlas_long.py --full`). Each run yields two models: **E**, the checkpoint v1.1's early-stopping rule keeps
(v1.1's recipe B), and **F**, the weights after the last step, which validation never chose. No fine-tuning step (B
and C tied in v1.1). Data, model, inputs and loss are v1.1's.

**Rules.**

1. F replaces E only if its validation MAE is lower by more than 2 standard errors, paired by seed. E's validation
   score is flattered by having been selected on it and F's is not, so the test leans against F.
2. The eight models of the chosen recipe are averaged: Atlas v1.2. It replaces v1.1 only if its validation MAE on the
   fusion's validation windows is lower than that of v1.1's three models. Test scores of both recipes are reported
   either way.
3. Atlas alone **beats** a model only with significant MAE wins on both tracks, as before; the fusion is reported
   beside it with the same code.
4. Delhi's test windows have now been scored by v1.0 and v1.1. Both v1.2 changes come from validation-side facts
   (where training stopped; how many seeds), not from test scores, but any Delhi gain from here on counts as
   provisional until the all-India league, whose test no Atlas model has touched, confirms it.

### India first: the all-India league (plan; its rules are fixed after the data is inspected and before any score)

Delhi is one city. To hold India, the same model has to work at every Indian station, and Atlas needs more data of
the kind it is tested on. The public copy of CPCB's exports used for Delhi's history covers 453 stations across the
country.

* **Data step** (`delhi/tools/build_india_long.py`, notebook `atlas_india_long.ipynb`): every station, hourly,
  2017-01-01 to 2023-03-31, the league's reader and cleaning rules; prints stations by state and city, coverage by
  year, unit checks, and how many stations per city could carry a test.
* **League sketch:** test = the last 182 days (October 2022 to March 2023, which includes north India's smog season),
  validation = the 61 days before, training = everything earlier; each city with enough stations is its own network;
  a fifth of the stations are never trained on.
* **What the data holds (Kaggle run atlas-india-long, 2026-11-13, 3.3 minutes):** 453 of 453 station files read;
  54,744 hours (2017-01-01 to 2023-03-31) x 453 stations x 14 variables. Stations reporting PM2.5 on at least half
  the hours: 39 in 2017, 114 in 2018, 174 in 2019, 213 in 2020, 267 in 2021, 318 in 2022. With the sketch above (train
  to 2022-07-31, validation to 2022-09-30, test 2022-10-01 to 2023-03-31), **259 stations** can carry a test (PM2.5 on
  at least 50% of test hours, 25% of validation hours and 12.5% of training hours); they have a median of 38 months
  of PM2.5 before validation (10–90%: 13–57). By state: Uttar Pradesh 40, Delhi 36, Haryana 29, Maharashtra 27,
  Karnataka 23, Madhya Pradesh 14, West Bengal 14, Bihar 12, Rajasthan 10, Gujarat 9, Tamil Nadu 9, Punjab 8, Kerala 7,
  Telangana 5, Andhra Pradesh 4, eleven others 1–2. Thirteen cities have 4 or more: Delhi 36, Mumbai 18, Chennai 7,
  Kolkata 7, Bengaluru 6, Lucknow 6, Patna 6, Agra 5, Hyderabad 5, Faridabad 4, Ghaziabad 4, Varanasi 4, Noida 4;
  the other 147 usable stations are spread over 228 smaller cities.
* **Two things the rules must handle:** pressure is in mixed units across stations (median 753, 99th percentile
  1,015), so each station's variables need their own scaling; and 15 files were moved from UTC by the solar-peak
  rule, but some stations' solar sensors peak at impossible hours (0, 19–22 h), so their clocks cannot be checked
  that way.
* **Opponents:** TimesFM 2.5, Chronos-2, Chronos-Bolt and TimesFM 3.0 (evaluation only), zero-shot on the same
  windows (GPU), and CAMS, whose public archive starts in August 2022 and so covers the test.
* **Order:** the Delhi v1.1 result decides the recipe. If all of Delhi's history lets Atlas alone reach the
  foundation models, the same recipe is trained on all of India. If it does not, the design changes first.
* **After that, the test a pure forecaster cannot take:** the national lockdown from 25 March 2020 is inside this
  history. Atlas is asked what the weeks after it would have looked like without the lockdown, and the gap to what was
  measured is compared with published estimates of the drop in emissions.

**Rules of the all-India league (Atlas-India v1.0), fixed before any model is scored on this data:**

1. **Stations.** PM2.5 on at least 50% of test hours and 12.5% of training hours: the Delhi league's rule with a lower
   training floor, because many Indian stations are young. (The sketch's validation condition is dropped to keep it
   to that one rule; the run prints the count.)
2. **Networks.** Every state with 6 or more league stations is one network; all other stations are pooled as "other
   states". In each network a fifth of the stations is never trained on (same seeded rule as Delhi); graphs and
   scaling come from each network's own training period; pressure is centred on each station's own training median.
3. **Model.** The Delhi v1.1 Atlas unchanged (967,632 parameters, same inputs and loss), **one set of weights for
   all of India**: each training step draws a network in proportion to its valid training windows and 16 windows
   from it. 60,000 steps, three seeds (400–402), `delhi/run_atlas_india.py`. As in Delhi v1.2 each run keeps E (early
   stopping on pooled validation) and F (the last step); F replaces E only if its pooled validation MAE is lower by
   more than 2 standard errors, paired by seed.
4. **Scoring** (`delhi/score_india.py`). The three models are averaged; the 80% band is calibrated on each network's
   validation windows; the test (2022-10-01 to 2023-03-31, every 6 h) is scored once: all networks pooled, trained
   stations and never-trained stations separately, and each network on its own.
5. **Words.** Atlas-India **beats** an entry across India only with significant pooled MAE wins on both tracks
   (Diebold–Mariano p < 0.05 and a day-block bootstrap interval excluding zero). Each network's win, tie or loss is
   listed; Delhi's row is reported like any other.
6. **Foundation models.** Until TimesFM and Chronos have forecast these same windows (GPU), the league holds only
   the two simple baselines, and nothing is said from it about foundation models.
7. The Delhi models (v1.1, v1.2) were trained on hours that are test hours here and are never scored in this league.

## Atlas what-if test 1: the 2020 lockdown in Delhi (rules, written before any result)

Forecasting the next 24 hours well does not make a world model. A world model has to answer a question no
forecaster can: **what would have happened otherwise?** India's national lockdown began on 25 March 2020 and is
inside the history joined for Delhi v1.1. The question put to Atlas: what would Delhi's PM2.5 have been in those
weeks if emissions had gone on as usual?

**Why a forecaster cannot answer.** Atlas, TimesFM and Chronos all read recent pollution. During the lockdown
those readings already contain the lockdown, so their forecasts follow it. The model for this test, **Atlas-BAU**
("business as usual", `delhi/run_lockdown.py`), is the Atlas architecture with every pollutant reading removed from
its inputs. It is given only what the lockdown did not change: each station's weather for the last 72 h and for the
24 h being simulated (temperature, humidity, wind speed and direction, solar radiation, pressure), the city-mean
weather for the same hours, the hour, weekday and season, and each station's usual PM2.5 level. The weather enters as
forcing of the transition, the route the design reserves for interventions.

**Rules.**

1. **Training** on 2018-01-15 to 2020-02-29, to reproduce measured PM2.5. Never trained on: the **placebo window**,
   25 March to 31 May 2019 (the same dates a year earlier, no lockdown), or anything from 1 March 2020. The data file
   is cut at 2020-06-01 before loading, and the loader's scaling and station graph use data up to October 2019 only.
2. **Model.** Atlas, about 250K parameters, 8,000 steps, seeds 500–502; the checkpoint is chosen on every tenth
   training-period day, held out; the three models are averaged.
3. **Number reported.** Measured ÷ simulated − 1 over the measured station-hours of the trained stations: the change
   that weather and season do not explain. The same number on the placebo window is the method's own bias. The
   **effect** is the lockdown ratio divided by the placebo ratio, minus 1 (phase 1 against the same dates in 2019,
   the later phases and the total against the whole placebo window), with a 95% interval from a 3-day block bootstrap.
4. **Validity gate.** The lockdown numbers count only if the placebo bias is within ±15% and the three weeks just
   before the lockdown (1–21 March 2020) show no effect (interval includes zero, or below 15%).
5. **"Atlas detects the lockdown"** only if the phase-1 interval excludes zero and the effect is larger than the
   one measured just before.
6. **Published numbers are context, not a target.** Mahato, Pal and Ghosh (2020, Science of the Total Environment):
   PM2.5 about 53% lower in 25 March–14 April than in 2–21 March 2020, 39% lower than the same period of 2019 at one
   station; meteorology not considered. Sahoo et al. (2021, Int. J. Environ. Sci. Technol., 34 stations): phase 1
   62.6% lower than before the lockdown and 51.7% lower than the same dates in 2019; no weather adjustment. A 2021
   preprint that does weather-normalise reports a small reduction (no figure on its abstract page). The plain
   year-on-year comparisons are printed from our own data beside the weather-adjusted effect.
7. **Known limits, stated now.** One spring (2018) is in training for the season simulated, and many stations came
   online during it. The weather is the stations' own sensors: no boundary-layer height, no regional transport, no
   fire counts. So "not explained by weather" includes any change in regional sources between years, not only the
   lockdown; the placebo measures how large that was from 2018 to 2019.

**Method check on made-up data** (`delhi/tools/planted_lockdown_check.py`; not a result about Delhi). Twelve fake
stations whose PM2.5 depends on season, hour and wind, with a planted −40% from 25 March to 31 May 2020. The method
recovered −39.4%, −40.8%, −40.9% and −41.0% for the four phases (−40.3% overall), with a placebo bias of +5.0% and
−0.1% (−2.0% to +2.8%) just before. Plain year-on-year comparison on the same made-up data gave −34.7% for phase 1
and −47.0% overall, because the weather of the two years differed.

### What-if test 1 results (Colab run colab_lockdown_india, 2026-11-13, Tesla T4, 12.0 minutes)

Run on Google Colab because Kaggle's five CPU sessions were in use; the Kaggle run of the same script will follow as
a replication. The data was rebuilt on Colab from the public sources and matched the Kaggle build in every printed
statistic (39 of 39 stations matched, the same by-year coverage and unit check). After the cut at 2020-06-01:
21,168 hours, 36 stations (29 trained on, 7 never trained on), 4,489 training windows, 72 held-out days. The three
models reached 35.41, 36.04 and 34.70 µg/m³ mean absolute error on the held-out days.

| Window | days | measured PM2.5 | simulated, business as usual | measured ÷ simulated − 1 | 95% interval | effect after removing the placebo bias | 95% interval | day-to-day correlation |
|---|---|---|---|---|---|---|---|---|
| placebo: 25 Mar – 31 May 2019 | 68 | 88.1 | 88.1 | +0.1% | −7.9% .. +8.6% | – | – | 0.62 |
| placebo, phase-1 dates: 25 Mar – 14 Apr 2019 | 21 | 90.6 | 89.3 | +1.4% | −7.0% .. +12.1% | – | – | 0.80 |
| just before: 1 – 21 Mar 2020 | 21 | 67.1 | 84.6 | −20.7% | −24.7% .. −16.9% | −20.8% | −28.0% .. −13.0% | 0.92 |
| lockdown 1: 25 Mar – 14 Apr 2020 | 21 | 39.4 | 82.3 | −52.1% | −56.0% .. −48.5% | −52.8% | −58.5% .. −46.9% | 0.80 |
| lockdown 2: 15 Apr – 3 May 2020 | 19 | 44.6 | 85.1 | −47.6% | −54.5% .. −40.8% | −47.6% | −55.5% .. −39.7% | 0.72 |
| lockdown 3: 4 – 17 May 2020 | 14 | 53.6 | 73.4 | −27.0% | −37.7% .. −18.8% | −27.0% | −39.3% .. −17.0% | 0.70 |
| lockdown 4: 18 – 31 May 2020 | 14 | 56.6 | 90.4 | −37.5% | −53.1% .. −25.3% | −37.5% | −53.8% .. −24.1% | 0.64 |
| all lockdown: 25 Mar – 31 May 2020 | 68 | 47.5 | 83.0 | −42.8% | −48.3% .. −35.9% | −42.9% | −49.5% .. −33.8% | 0.61 |

Without any weather adjustment, from the same data: phase 1 against the same dates in 2019 −54.3%; phase 1 against
2–21 March 2020 −39.7%; all lockdown against the same dates in 2019 −43.2%.

**Validity gate (rule 4): FAILED. Lockdown detected in phase 1 (rule 5): YES.**

What this means, by the rules written before the run:

1. **The placebo half of the gate passed.** On the same dates in 2019, which the models never saw, the simulation
   matched measured PM2.5 with no bias (+0.1%, interval −7.9% to +8.6%) and followed its day-to-day changes
   (correlation 0.62 over the 68 days, 0.80 over the first three weeks).
2. **The other half failed.** In the three weeks before the lockdown, measured PM2.5 was already 20.7% below the
   simulation (interval −24.7% to −16.9%). Rule 4 required no effect there. So the lockdown rows are **not** a
   valid measurement of the lockdown, and "the lockdown lowered Delhi's PM2.5 by 52.8%" is not claimed.
3. **What the run does show.** The drop on 25 March is far larger than the gap that was already there (−52.8%
   against −20.8%; the two intervals do not overlap), which is what rule 5 calls detected. Dividing the two ratios
   gives about −40% for phase 1 relative to the weeks before. This last number was computed after seeing the table;
   it is not one of the rules, and it equals the plain before-and-after comparison (−39.7%).
4. **The weather adjustment changed little.** Against 2019 the adjusted number is −52.8% and the plain one −54.3%.
   On the made-up data the same method moved the plain number 5 points towards the truth. Here the test gives no
   evidence that Atlas-BAU knows more about this episode than a plain year-on-year comparison does.

Why the weeks before the lockdown may have been cleaner than simulated (not tested, so not conclusions):

* **Rain.** March 2020 was Delhi's wettest March on record: 109.6 mm against a normal of 15.9 mm (India
  Meteorological Department). Rain washes particles out, and Atlas-BAU has no rainfall input.
* **Restrictions began before 25 March.** Closures in Delhi started in mid-March, inside the 1–21 March window.
* **Drift.** March 2020 is the first month after the training period ends.

**Next (test 1b; its rules will be written before it runs):** add rainfall and boundary-layer height from a
reanalysis as forcing, and hold 1–21 March 2019 out of training as a second placebo, so that the test can tell a
March bias of the method from something that happened in March 2020. The gate stays as it is.

### What-if test 1b: rain, mixing height and a second placebo (rules, written before any run on Delhi data)

Test 1 failed because the three weeks before the lockdown were already cleaner than simulated. Test 1b asks whether
weather that the stations' own sensors do not measure explains that gap. It is the **second look at the same
episode**, so a pass here is weaker evidence than a first-time pass would have been; rule 6 deals with that.

1. **Same as test 1:** the training period, the cut at 2020-06-01, the model (about 250K parameters, 8,000 steps,
   seeds 500–502, checkpoint on every tenth training-period day), the number reported, the bootstrap, rule 5.
2. **New inputs.** ERA5 reanalysis at Delhi's centre (one cell of about 25 km; `delhi/tools/fetch_era5_delhi.py`,
   through Open-Meteo's archive, no key; free for non-commercial use, data CC BY 4.0, ERA5 from the Copernicus
   Climate Change Service; used for this research test only): rain in the hour, in the last 24 h and in the last
   72 h, boundary-layer height, wind at 100 m, cloud cover and top-layer soil moisture, for the 72 past hours and
   the 24 simulated hours. If the archive does not serve rain the test is not run; any other variable it does not
   serve is left out and named in the result.
3. **A second placebo.** 1–21 March 2019 is also never trained on. The effect "just before" is now the 2020 ratio
   divided by the ratio on those same dates in 2019, as phase 1 already is.
4. **Validity gate.** Both placebo biases (25 March–31 May 2019 and 1–21 March 2019) within ±15%, and no effect
   just before the lockdown (interval includes zero, or below 15%). Otherwise the lockdown rows do not count.
5. **Either outcome is reported.** If the gap closes, rain and mixing explain early March 2020 and the lockdown
   rows count. If it stays, the weather we can obtain does not explain it, and the candidates left are a real fall
   in emissions before 25 March or sources outside Delhi.
6. **After 1b the method is frozen** (inputs, sizes, gate) and goes to an episode it has not been run on, with
   rules written first: Delhi's 2021 lockdown, and the 2020 lockdown in the other Indian networks.

**Method check on made-up data** (`delhi/tools/planted_lockdown_check.py --hidden-rain`; not a result about Delhi).
The made-up world of test 1 with rain spells added that wash particles out, a wet 1–24 March 2020 (129 mm against
17 mm on the same dates of 2019), a planted −40% from 25 March, and station sensors that do not show the rain.

| Method | gap just before the lockdown | gate | phase 1 | all lockdown |
|---|---|---|---|---|
| Test 1 (no reanalysis) | −36.0% (−50.3% .. −20.0%) | FAILED | −33.1% | −40.5% |
| Test 1b (reanalysis) | −2.8% (−5.9% .. +0.8%) | PASSED | −39.7% (−42.0% .. −37.1%) | −40.3% (−41.8% .. −38.9%) |
| Plain comparison, no model | – | – | −28.0% against 2019; +6.5% against 2–21 March 2020 | −46.6% against 2019 |

So when hidden rain is the cause, test 1 fails in the way it failed on Delhi, and test 1b repairs it and recovers the
planted effect (four phases: −39.7%, −40.2%, −40.8%, −42.3%). In a second made-up world where the stations' humidity
sensor does show the rain (`--rain`), test 1 already passed its gate (gap −9.1%, interval −14.7% to −0.8%) and 1b
gave −2.4% and −40.5% overall. This shows the method can separate rain from a lockdown. It does not show that rain
is what happened in Delhi.

## What has not been done

* Sizes of 2M and above ran on the damped oscillator only, with one seed and three data amounts. The 10M ring
  model was built and counted but not trained (CPU time).
* No real data yet: the pollution stage (CPCB, weather, PM2.5), the comparison with TimesFM and Chronos, and the
  "which variable or station to collect next" advisor on real data are the next stage. The design asks for the
  known-equation stage first; this is it.
* Long autoregressive roll-outs, non-linear systems (Burgers, shallow water), and information-bottleneck /
  mutual-information estimates of the learned state are not measured.
* All four systems are linear in their state. The findings above may not carry to chaotic or non-linear systems.

## Run

    cd atlas
    python baselines.py                               # oracle, persistence, ridge, complexity bits
    python grid.py results/runs_ladder.jsonl ladder   # size x data on the damped oscillator (about 50 min, 1 core)
    python grid.py results/runs_systems.jsonl systems # other systems and sweeps (about 100 min, 1 core)
    python analyze.py                                 # -> results/REPORT.md, results/summary.json
    python baselines_sysid.py                         # identification with no training
    python grid.py results/runs_fix.jsonl fix         # v0.2: plain against identification (about 170 min, 1 core)
    python analyze_fix.py                             # -> results/REPORT_v02.md
    python grid.py results/runs_gaps.jsonl gaps       # v0.3: missing inputs (about 90 min, 1 core)
    cd delhi && bash kaggle_atlas_delhi.sh            # stage 7 on Kaggle (CPU is enough up to 1M parameters)

Runs are deterministic for a given seed on the same machine (the same configuration run twice gave identical numbers).
