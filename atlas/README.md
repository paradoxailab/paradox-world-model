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

### ATF v2.0 results, part 2: the out-of-domain test (Kaggle runs atf2-bench-s0 .. s3 and atf2-analysis, 2026-11-13)

22 networks, 296 training runs (80 + 80 + 68 + 68 over the four notebooks; every network at 6 or 7 data amounts,
2 seeds). The law frozen on the 46 Indian
curves (α = 0.179, φ = 0.474) was applied unchanged; each network's own 2-month pilot is its only input.

**Verdict under the rule written before the run: the law does NOT transfer.** It missed by one network. At the
largest amount it beat M1 in 16 of 22 networks, which gives p = 0.0525 on the two-sided sign test; the rule needed
p < 0.05, that is 17 of 22. Every other part of the rule was met.

*Largest amount of data (22 predictions; the rule's measure):*

| Method | median abs log error | within 10% of measured | mean abs log error |
|---|---|---|---|
| M0: no improvement beyond the pilot | 0.221 (×1.247) | 9% | 0.208 |
| M1: power law fitted to the network's own pilots | 0.115 (×1.122) | 41% | 0.111 |
| **M2: the frozen law** | **0.037 (×1.038)** | **91%** | **0.046** |

Sign tests (wins / losses): frozen law against M0 20 / 2, p = 0.00012; against M1 **16 / 6, p = 0.0525**. Its 80%
interval contained the measured error in 95% of cases (so the interval is too wide).

*All amounts above 2 months (82 predictions; reported, not part of the rule):* M0 0.157, M1 0.086, frozen law
0.047 (×1.048), within 10% in 87% of cases; sign tests 63 / 19 against M0 (p = 0.000001) and 57 / 25 against M1
(p = 0.0005); interval coverage 98%.

*By dataset (median abs log error at the largest amount; measured gain from 2 months to all data, and the law's):*

| Dataset | networks | M0 | M1 | frozen law | measured gain | law predicted |
|---|---|---|---|---|---|---|
| Electricity | 8 | 0.255 | 0.065 | 0.034 | 22.5% | 19.8% |
| Traffic | 8 | 0.225 | 0.123 | 0.032 | 20.2% | 17.6% |
| Solar | 4 | 0.167 | 0.143 | 0.069 | 15.3% | 12.3% |
| ETTh2 | 1 | 0.161 | 0.118 | 0.032 | 14.9% | 17.5% |
| ETTh1 | 1 | 0.012 | 0.036 | 0.181 | 1.2% | 17.5% |

**Reading.**

1. **The rule's verdict stands: not shown.** The threshold was fixed in advance, and 16 of 22 is under it. Groups
   inside one dataset are also not independent, so even 17 would have been weaker evidence than it looks.
2. **What was measured is still worth stating.** A law fitted only on Indian weather and air-quality curves predicted
   the error of electricity, traffic and solar networks at full data to within 4% in the median, three times closer
   than a power law fitted to each network's own pilots and six times closer than assuming no improvement.
3. **Where it failed.** ETTh1 gained 1.2% from more data and the law predicted 17.5%; the law has no way to know
   that a series has stopped improving. And the 80% interval covered 95–98% of cases, so it is too wide to be useful
   as stated.
4. **Next for this line** (not started): a tighter interval fitted on the Indian curves alone, and a second
   out-of-domain test with independent datasets rather than groups of one dataset, with the rule written first.

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

### Atlas-Delhi v1.2 results (Kaggle runs atlas-long2-a .. d and atlas-delhi-fusion-v12, 2026-11-13, CPU)

Eight seeds, about 67 minutes each; the assembly took 2.4 minutes. Neither change improved the test score.

**Decision on validation (rules 1 and 2).**

| Seed | 310 | 311 | 312 | 313 | 314 | 315 | 316 | 317 |
|---|---|---|---|---|---|---|---|---|
| E: validation MAE (early stopping) | 21.118 | 20.720 | 21.154 | 21.143 | 21.246 | 21.180 | 21.129 | 21.150 |
| E: steps | 10,000 | 17,600 | 10,000 | 9,600 | 12,400 | 12,000 | 9,200 | 9,200 |
| F: validation MAE (whole schedule, 24,000 steps) | 21.760 | 21.186 | 21.365 | 21.766 | 21.356 | 21.298 | 21.362 | 21.707 |
| E: test MAE, trained / unseen | 31.42 / 27.73 | 33.46 / 29.09 | 32.34 / 27.88 | 32.22 / 28.02 | 33.67 / 28.70 | 32.82 / 28.17 | 33.87 / 29.11 | 31.37 / 27.43 |
| F: test MAE, trained / unseen | 32.28 / 28.07 | 33.41 / 28.80 | 32.27 / 27.52 | 31.79 / 28.08 | 34.31 / 28.79 | 32.61 / 28.17 | 31.07 / 26.99 | 31.28 / 27.73 |

* Rule 1: F was worse than E on validation in all eight seeds (paired difference E − F −0.370, standard error
  0.080). **Recipe E.** Training the whole schedule did not help.
* Rule 2: the eight E models averaged score 20.162 on the fusion's validation windows against 20.453 for v1.1's
  three. **Atlas v1.2 is adopted** and replaces v1.1 as the Atlas entry.

**Test (PM2.5 MAE, µg/m³; 725 windows; trained stations / never-trained stations).**

| Entry | Trained | Never trained |
|---|---|---|
| Atlas-Delhi Fusion with v1.2 (static) | 29.33 | 25.83 |
| Atlas-Delhi Fusion with v1.2 (online, primary) | 29.34 | 25.75 |
| Atlas v1.2, recipe F (not chosen) | 30.23 | 26.48 |
| Atlas v1.1 (3 seeds) | 30.26 | 26.62 |
| **Atlas v1.2 alone (8 seeds)** | **30.39** | **26.59** |
| Foundation models only (online) | 30.43 | 26.82 |
| Foundation models only (static) | 30.55 | 26.94 |
| TimesFM 2.5 | 30.83 | 27.10 |
| Chronos-2 | 31.17 | 27.41 |
| Chronos-Bolt | 31.35 | 27.94 |
| Atlas v1.0 (16 months) | 33.42 | 29.07 |

**Verdicts under the rules.**

* **Atlas v1.2 alone** is level with TimesFM 2.5 (−1.41%, p = 0.41 / −1.86%, p = 0.21) and with Chronos-2
  (−2.50%, p = 0.16 / −2.97%, p = 0.085). Against Chronos-Bolt it wins on never-trained stations (−4.81%,
  p = 0.0061) but only ties on trained ones (−3.06%, p = 0.073), so the verdict is **level**; v1.1 had beaten
  Chronos-Bolt on both. It beats v1.0 (−9.06% / −8.51%) and is level with v1.1 (+0.44%, p = 0.58 / −0.12%,
  p = 0.88) and with recipe F.
* **The fusion with v1.2** beats all three foundation models on both tracks: online −4.84% / −4.96% against
  TimesFM 2.5, −5.90% / −6.03% against Chronos-2, −6.43% / −7.81% against Chronos-Bolt (every p below 0.0001);
  static −4.86% / −4.69%, −5.91% / −5.76%, −6.45% / −7.55%. **Atlas adds information beyond the foundation
  models: YES** (online −3.60%, p = 0.00027 / −3.99%, p = 0.00003; static −4.00% / −4.14%).
* Weights: static Atlas 0.45, TimesFM 2.5 0.40, Chronos-Bolt 0.15; online, on average, Atlas 0.50, TimesFM 2.5
  0.25, Chronos-2 0.18, Chronos-Bolt 0.07.

**What this means.**

1. **The adopted version is not better on test.** Validation chose v1.2, so by the rule its numbers are now the
   league's: Atlas alone 30.39 / 26.59 and the fusion 29.34 / 25.75. v1.1 had 30.26 / 26.62 and 29.22 / 25.68.
   The two versions are statistically level, and the slightly better-looking v1.1 numbers are not kept.
2. **One model's test score depends heavily on its seed.** The eight E models range from 31.37 to 33.87 on
   trained stations (mean 32.65, standard deviation 0.97), while their validation scores sit within 0.5 of each
   other and do not predict the test score (correlation −0.21). Validation is May and June; the test runs from July
   to December, which includes the winter peak. So choosing between recipes on validation has little power here, and differences of a few tenths
   between Atlas versions are noise.
3. **v1.1's three seeds were at the lucky end.** Their single models averaged 31.70; all eleven seeds of this
   recipe average 32.39. The v1.1 "prediction against measurement" check (31.6 predicted, 31.7 measured) therefore
   looked closer than it is: on eleven seeds the measured value is 32.4, between the "law holds" and "no gain"
   predictions.
4. **Atlas alone stays level with TimesFM 2.5.** Three versions of the same recipe (v1.1, v1.2 E, v1.2 F) land
   between 30.2 and 30.4. More seeds and longer training do not move it; v1.3 changes the data instead.

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

**Correction to the all-India league, made on 2026-11-13 after the first seed and before the league was scored.**

*What was seen.* The first seed's log (Colab, seed 400; one model, all networks pooled) gave 21.42 and 21.53 µg/m³
on trained stations for the two saved models, but 44.43 and 23.75 on never-trained stations. Two models that agree
on trained stations should not differ by a factor of two on the others.

*Cause.* A fault in the loader, not in the weights. Each weather variable is scaled with the statistics of the
network's trained stations. In Gujarat and in Kerala the only station that reports pressure is a never-trained one
(Maninagar, Ahmedabad; Plammoodu, Thiruvananthapuram). With no trained station to scale it, the pressure went in
unscaled: about 1000 where the model expects values near zero (and Maninagar's sensor also drops from about 1000 to
800 hPa in the test period). The forecasts at those two stations averaged 846 and 410 µg/m³ from one saved model and
10 and 20 from the other. The cause was found from the forecasts and the inputs; no test measurement was used to
find it. The Delhi league is not affected: every variable there is reported by trained stations.

*Fix* (`delhi/pw/ddata.py`). A weather variable that no trained station of a network reports is not an input in
that network. Nothing else changes. Nothing is retrained: training reads trained stations only, so the weights are
the ones the rules produced. The forecasts are made again from the saved weights
(`delhi/run_atlas_india.py --reforecast`). Forecasts for trained stations do not read never-trained stations, so
they must come out unchanged; the largest change is printed as a check.

*How it is reported.* The league is scored twice and both are recorded: as first run, and with the fix. Verdicts
are read from the fixed version. This correction was made after one seed's pooled test numbers had been printed,
so it is not blind; what limits it is that it was chosen from the inputs and cannot move a trained-station result.

### Atlas-India v1.0 results, as first run (Colab run colab_lockdown_india, 2026-11-13, Tesla T4)

Three seeds (400–402), about 31 minutes each on the T4; the scoring took 0.5 minutes. The data rebuilt on Colab gave
the same 14 networks, 263 stations and 158,893 training windows as the Kaggle build. This is the league **before**
the input fix described above; the never-trained-station numbers of Gujarat and Kerala are the fault, not the model.
The scoring with the fix follows below when it has run.

*Recipe decision on pooled validation:* E 9.084, 9.103, 9.053; F 9.150, 9.124, 9.053; paired difference E − F
−0.029, standard error 0.019: **recipe E** (in seed 402 the last step was also the best, so E and F are the same
model). Single models on test, trained / never trained: E 21.42 / 44.43, 21.43 / 23.71, 21.29 / 24.96; F 21.53 /
23.75, 21.50 / 23.46, 21.29 / 24.96. *Cross-check on other hardware* (Kaggle CPU, seed 400): E 21.47 / 23.60,
F 21.70 / 23.64.

*All 14 networks pooled (PM2.5, µg/m³, next 24 h; three models averaged, calibrated on each network's validation):*

| Entry | Trained: MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | Never trained: MAE | Atlas-India against it (trained / never trained) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Atlas-India** (recipe E) | **21.00** | 38.87 | 6.91 | 80 | 9.56 | 19.08 | 21.83 | 23.89 | 29.05 | – |
| Atlas-India, recipe F (not chosen) | 21.00 | 38.70 | 6.92 | 80 | 9.53 | 19.06 | 21.86 | 23.95 | 22.57 | TIE +0.0% / LOSS +28.7% |
| Same hour yesterday | 29.86 | 53.86 | 11.83 | 54 | 29.48 | 29.66 | 29.66 | 29.68 | 29.30 | WIN −29.7% (p = 2e-118) / TIE −0.9% (p = 0.62) |
| Last observed value | 32.01 | 57.63 | 12.95 | 49 | 11.65 | 32.15 | 35.64 | 28.36 | 31.13 | WIN −34.4% (p = 3e-140) / WIN −6.7% (p = 0.00013) |

*Each network (MAE):*

| Network | stations (never trained) | mean PM2.5 in test | Atlas-India: trained / never trained | Same hour yesterday (trained) | Last observed value (trained) |
|---|---|---|---|---|---|
| Uttar Pradesh | 40 (8) | 77 | 20.87 / 22.47 | 30.15 (WIN −30.8%) | 33.40 (WIN −37.5%) |
| Delhi | 37 (7) | 140 | 37.46 / 35.81 | 54.74 (WIN −31.6%) | 59.63 (WIN −37.2%) |
| Haryana | 30 (6) | 86 | 24.40 / 22.45 | 35.81 (WIN −31.9%) | 34.76 (WIN −29.8%) |
| Maharashtra | 27 (5) | 74 | 19.59 / 24.94 | 26.38 (WIN −25.7%) | 27.83 (WIN −29.6%) |
| Karnataka | 24 (5) | 34 | 8.87 / 9.15 | 12.49 (WIN −29.0%) | 11.66 (WIN −23.9%) |
| other states | 22 (4) | 55 | 15.09 / 9.25 | 20.01 (WIN −24.6%) | 22.37 (WIN −32.5%) |
| Madhya Pradesh | 14 (3) | 57 | 16.18 / 13.88 | 21.80 (WIN −25.8%) | 26.92 (WIN −39.9%) |
| West Bengal | 14 (3) | 75 | 14.69 / 14.80 | 21.41 (WIN −31.4%) | 22.87 (WIN −35.8%) |
| Bihar | 12 (2) | 121 | 27.57 / 24.84 | 39.71 (WIN −30.6%) | 43.96 (WIN −37.3%) |
| Rajasthan | 10 (2) | 63 | 18.96 / 15.31 | 26.71 (WIN −29.0%) | 29.40 (WIN −35.5%) |
| Gujarat | 9 (2) | 67 | 18.43 / **156.49** | 23.66 (WIN −22.1%) | 27.83 (WIN −33.8%) |
| Tamil Nadu | 9 (2) | 42 | 12.69 / 16.46 | 17.37 (WIN −26.9%) | 17.25 (WIN −26.4%) |
| Punjab | 8 (2) | 65 | 17.38 / 35.09 | 23.86 (WIN −27.2%) | 24.30 (WIN −28.5%) |
| Kerala | 7 (1) | 43 | 8.52 / **149.88** | 12.44 (WIN −31.6%) | 10.91 (WIN −21.9%) |

*Verdicts as first run.* On trained stations Atlas-India beats both simple forecasts in **14 of 14 networks**, by
22% to 40%. Under the rule (a win on both tracks) it **beats** "last observed value" and is only **level** with
"same hour yesterday", because the two faulty stations put the never-trained error at 29.05. No foundation model has
been run on these windows yet, so this says nothing yet about TimesFM or Chronos on all-India data. Punjab's
never-trained error (35.09 against 17.38 on trained stations) is also high and is not explained yet.

### Atlas-India v1.0 results with the input fix (Colab, same session and weights, 2026-11-13)

The forecasts were made again from the three saved models (`run_atlas_india.py --reforecast`). The loader found
three variables that no trained station of a network reports and dropped them as inputs there: pressure in Gujarat
and in Kerala, and **temperature in Punjab**, which had not been noticed and explains part of Punjab's high
never-trained error. The largest change of any trained-station forecast was 0.0000 µg/m³, as it had to be.

*Single models on test, trained / never trained:* E 21.42 / 21.29, 21.43 / 21.76, 21.29 / 21.15 (as first run
21.42 / 44.43, 21.43 / 23.71, 21.29 / 24.96). So the fault had inflated every seed's never-trained error, not only
the one that blew up.

*All 14 networks pooled:*

| Entry | Trained: MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | Never trained: MAE | QL | COV80 % | Atlas-India against it (trained / never trained) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Atlas-India** (recipe E) | **21.00** | 38.87 | 6.91 | 80 | 9.56 | 19.08 | 21.83 | 23.89 | **20.91** | 6.88 | 79 | – |
| Atlas-India, recipe F (not chosen) | 21.00 | 38.70 | 6.92 | 80 | 9.53 | 19.06 | 21.86 | 23.95 | 21.00 | 6.91 | 79 | TIE +0.0% (p = 0.95) / WIN −0.4% (p = 0.0012) |
| Same hour yesterday | 29.86 | 53.86 | 11.83 | 54 | 29.48 | 29.66 | 29.66 | 29.68 | 29.30 | 11.53 | 53 | WIN −29.7% (p = 2e-118) / WIN −28.6% (p = 3e-102) |
| Last observed value | 32.01 | 57.63 | 12.95 | 49 | 11.65 | 32.15 | 35.64 | 28.36 | 31.13 | 12.50 | 47 | WIN −34.4% (p = 3e-140) / WIN −32.8% (p = 2e-104) |

*Never-trained stations by network, where the fix changed them:* Gujarat 18.35 (as first run 156.49), Kerala 12.21
(149.88), Punjab 28.09 (35.09). Every other number in the per-network table above is unchanged.

**Verdicts with the fix.** Atlas-India **beats** "same hour yesterday" and "last observed value" on both tracks,
pooled, and on trained stations in 14 of 14 networks. Its error on stations it never trained on (20.91) is the same
as on the stations it did train on (21.00), and its 80% intervals contain 79–80% of the measurements.

**What this does not show yet.** No foundation model has been scored on these windows; that run is next, and
until it is done the all-India league says nothing about TimesFM or Chronos. Punjab's never-trained stations (28.09
against 17.38) and Maharashtra's (24.94 against 19.59) remain clearly worse than the trained ones.

### Atlas-India v1.0 against TimesFM 2.5 (Kaggle runs atlas-india-opp-gpu v2 and atlas-india-score, 2026-11-13)

TimesFM 2.5 forecast all 14 networks' windows zero-shot on a Kaggle T4 (512 h of each station's PM2.5, 44 minutes),
and the league was scored under its rules (above), once. The three Atlas-India seeds here are the Kaggle runs:
seed 400 (re-forecast with the input fix, weights unchanged; largest change of any trained-station forecast 0.0000
µg/m³) and seeds 401 and 402 (trained on Kaggle with the fixed loader). They are not bit-identical to the Colab seeds
scored above, so Atlas-India's pooled MAE is 20.99 / 20.86 here against 21.00 / 20.91 there. Recipe decision: E
(validation 9.104, 9.070, 9.059 against F 9.116, 9.093, 9.059; paired difference −0.011, standard error 0.007).

*All 14 networks pooled (PM2.5, µg/m³, next 24 h; every entry calibrated on each network's validation windows):*

| Entry | Trained: MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | Never trained: MAE | Atlas-India against it (trained / never trained) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Atlas-India** (recipe E) | **20.99** | 38.89 | 6.91 | 79 | 9.55 | 19.09 | 21.75 | 23.88 | **20.86** | – |
| TimesFM 2.5 (Google, 200M), zero-shot | 22.35 | 41.30 | 7.37 | 80 | 9.54 | 20.67 | 23.46 | 25.16 | 21.93 | **WIN −6.07% (p = 2.1e-20) / WIN −4.84% (p = 3.8e-11)** |
| Same hour yesterday | 29.86 | 53.86 | 11.83 | 54 | 29.48 | 29.66 | 29.66 | 29.68 | 29.30 | WIN −29.7% / WIN −28.8% |
| Last observed value | 32.01 | 57.63 | 12.95 | 49 | 11.65 | 32.15 | 35.64 | 28.36 | 31.13 | WIN −34.4% / WIN −33.0% |

*Each network, trained stations (Atlas-India against TimesFM 2.5; Diebold–Mariano, p < 0.05):* Uttar Pradesh 20.89 vs
22.78 (WIN −8.3%), Delhi 37.34 vs 41.87 (WIN −10.8%), Haryana 24.32 vs 25.72 (WIN −5.5%), Maharashtra 19.68 vs 19.45
(TIE +1.2%), Karnataka 8.87 vs 8.98 (TIE −1.2%), other states 15.12 vs 15.19 (TIE −0.5%), Madhya Pradesh 16.23 vs
17.07 (WIN −4.9%), West Bengal 14.65 vs 15.79 (WIN −7.2%), Bihar 27.74 vs 29.35 (WIN −5.5%), Rajasthan 19.07 vs
19.67 (WIN −3.1%), Gujarat 18.47 vs 18.20 (TIE +1.5%), Tamil Nadu 12.64 vs 13.39 (WIN −5.6%), Punjab 17.31 vs 18.20
(WIN −4.9%), Kerala 8.51 vs 7.96 (**LOSS +6.9%**).

**Verdict under the rules: Atlas-India BEATS TimesFM 2.5 across India**, with significant pooled wins on both tracks;
network by network it wins 9, ties 4 and loses 1 (Kerala, mean PM2.5 43 µg/m³).

**What this adds to the Delhi result.** This test period (October 2022 – March 2023) had been scored once before, by
these same weights against simple forecasts only; no Atlas version was chosen or tuned on it. So it is the first
foundation-model comparison on data that is not reused. It is not the leave-one-network-out repetition of the v1.3
recipe (Atlas-India is trained on all networks at once), and Chronos-2 and Chronos-Bolt have not been scored on these
windows yet (their CPU run will not finish within Kaggle's 12-hour limit; they need the GPU). TimesFM 2.5 is level
with or slightly ahead of Atlas-India one hour ahead (9.54 against 9.55); Atlas-India's lead comes from 6 to 24 hours.

### Atlas-Delhi v1.3: pre-trained on the rest of India (rules and predictions, written before any score)

v1.1 showed that more of Delhi's own history made Atlas 9% better, along the line the scaling law drew. Delhi has
no more history to give. The rest of India has: 13 networks, 226 stations and 144,671 valid training windows,
against Delhi's 19,082. v1.3 asks whether other cities' history counts for Delhi.

1. **Pre-training.** The Atlas-India recipe unchanged (one model for all networks, 60,000 steps, the checkpoint with
   the best pooled validation), on 13 networks. **The Delhi network is left out entirely**, so the model has seen no
   Delhi station and the Delhi league's never-trained stations stay never trained (`delhi/run_atlas_india.py --skip
   Delhi --pretrain-only`; the fine-tuning script refuses weights that have seen Delhi). The pre-training data ends
   on 2022-07-31, almost three years before the Delhi league's validation period. Only weights are saved; no test
   window of any league is forecast.
2. **Then v1.1's two stages, from those weights.** B: all of Delhi's history since 2018, training stations only, at
   0.3 of the learning rate, up to 12,000 steps, the same early stopping. C: the league's own 16 months at 0.2 of
   the learning rate, as in v1.1.
3. **Seeds 320–322**, one Kaggle notebook each (pre-training and both stages; `delhi/kaggle_v13.sh`).
4. **Decided on validation only.** B or C by the lower mean validation error. v1.3 replaces v1.1 as the Atlas entry
   only if its three-model ensemble has a lower validation error than v1.1's on the fusion's validation windows.
5. **Scored as v1.1 was** (`fuse.py --v13`): the same 725 test windows, calibration, tests and verdict words. Entries:
   Atlas v1.3 alone, the fusion with v1.3, and **P, the pre-trained model before any Delhi training**. P is
   zero-shot on Delhi in the sense the foundation models are: its weights have never seen a Delhi station. Its inputs
   are scaled with Delhi's training-period statistics and it uses Delhi's station graph.
6. **Predictions** from the v1.1 law (single-model test error on trained stations falls as windows^-0.048; v1.1
   measured 31.61 µg/m³): **28.5** if a window from another state counts like a Delhi window, **30.8** if it counts
   a tenth, **31.6** if it does not count. v1.1's ensemble was 1.35 below its single models. TimesFM 2.5 scored
   30.83; the smallest margin that has been significant in this league is about 3.5%, so Atlas alone needs an
   ensemble near 29.7, which means single models near 31.1.
7. **Provisional by construction.** Delhi's test period has now been scored by v1.0, the fusion, v1.1 and v1.2. A
   v1.3 gain counts as confirmed only when the same recipe (leave one network out, pre-train on the rest, adapt)
   also gains on another network of the all-India league.

*Note added after the v1.2 result and before any v1.3 score.* The predictions in rule 6 start from v1.1's 31.61,
which three seeds gave. Eleven seeds of the same recipe average 32.39. Starting from that, the same three
predictions are **29.2 / 31.5 / 32.4**. Both sets are kept; the threshold for beating TimesFM 2.5 (single models
near 31.1 for a three-model ensemble) does not change.

### Atlas-Delhi v1.3 results (Kaggle runs atlas-v13-s320 / s321 / s322 and atlas-delhi-fusion-v13, 2026-11-13, CPU)

Each seed: pre-training on 13 networks without Delhi (144,671 windows, about 100 minutes), then stage B on all of
Delhi's history and stage C on the league's 16 months. The assembly ran on the same 725 test windows as every
earlier version.

**Decision on validation (rules 4 and 6).**

| Seed | 320 | 321 | 322 |
|---|---|---|---|
| Pre-training: pooled validation MAE on the 13 networks | 8.507 | 8.540 | 8.484 |
| P (no Delhi training): Delhi validation MAE | 20.506 | 20.579 | 20.413 |
| B (then all of Delhi's history): validation MAE, steps | 19.922, 5,200 | 19.651, 11,200 | 19.802, 5,200 |
| C (then the league's 16 months) | no gain: C = B | no gain: C = B | no gain: C = B |
| Single models on test, trained / never trained: P | 30.67 / 26.62 | 30.66 / 26.64 | 30.22 / 26.35 |
| Single models on test, trained / never trained: B | 29.76 / 26.19 | 29.93 / 26.35 | 29.74 / 26.17 |

Recipe **B**. Its three-model ensemble scores 19.273 on the fusion's validation windows against 20.453 for v1.1:
**Atlas v1.3 is adopted.**

**Predictions written before the run (rule 6), against the measurement.** Single-model test MAE on trained
stations, mean of three: **29.81**. Predicted 28.5 / 30.8 / 31.6 from v1.1's three seeds, or 29.2 / 31.5 / 32.4
from the eleven-seed baseline (a window from another state counting as fully as a Delhi window / a tenth / not at
all). The measurement lies between the first two predictions, nearer the first. The spread between seeds fell from
31.37–33.87 (v1.2, eight seeds) to 29.74–29.93.

**Test (PM2.5 MAE, µg/m³, 725 windows; trained stations / never-trained stations).**

| Entry | Trained | Never trained | 80% coverage |
|---|---|---|---|
| Atlas-Delhi Fusion with v1.3 (static) | 28.55 | 25.21 | 79 / 78 |
| Atlas-Delhi Fusion with v1.3 (online, primary) | 28.57 | 25.14 | 79 / 78 |
| **Atlas v1.3 alone** | **28.91** | **25.56** | 79 / 78 |
| Atlas-India without Delhi (no Delhi training, zero-shot on Delhi) | 29.98 | 26.11 | 80 / 80 |
| Atlas v1.1 (3 seeds) | 30.26 | 26.62 | 80 / 78 |
| Foundation models only (online) | 30.43 | 26.82 | 79 / 79 |
| TimesFM 2.5 | 30.83 | 27.10 | 78 / 78 |
| Chronos-2 | 31.17 | 27.41 | 79 / 80 |
| Chronos-Bolt | 31.35 | 27.94 | 79 / 79 |
| Atlas v1.0 (16 months) | 33.42 | 29.07 | 79 / 79 |

**Verdicts under the rules.**

* **Atlas v1.3 alone BEATS all three foundation models**, with significant wins on both tracks: TimesFM 2.5
  −6.22% (p = 0.000015) / −5.69% (p = 0.00011); Chronos-2 −7.26% / −6.76%; Chronos-Bolt −7.79% / −8.52%. The
  pinball loss agrees (−5.86% / −5.43% against TimesFM 2.5). It also beats the fusion of the three foundation models
  (−4.99% / −4.73%), v1.1 (−4.46% / −4.02%) and v1.0 (−13.49% / −12.08%).
* **The zero-shot model** (never trained on a Delhi station) beats Chronos-2 and Chronos-Bolt on both tracks and is
  level with TimesFM 2.5 (−2.75%, p = 0.054 on trained stations; −3.64%, p = 0.011 on never-trained stations).
* **The fusion with v1.3** beats all three foundation models (online: TimesFM 2.5 −7.33% / −7.22%, Chronos-2
  −8.36% / −8.27%, Chronos-Bolt −8.88% / −10.00%, every p below 0.0000002) and Atlas v1.3 alone (−1.18%, p = 0.018 /
  −1.62%, p = 0.0006). Atlas adds information beyond the foundation models: YES (−6.12% / −6.27%). Online weights,
  on average: Atlas 0.63, TimesFM 2.5 0.20, Chronos-2 0.12, Chronos-Bolt 0.05.
* By number only (no significance test: its forecasts are not in this assembly), TimesFM 3.0 multivariate scored
  29.95 / 26.16 on these windows; Atlas v1.3 alone is 3.5% / 2.3% lower.

**Status: provisional, by rule 7.** Delhi's test period has been scored by every version. The gain counts as
confirmed when the same recipe (leave one network out, pre-train on the rest, adapt) also beats the foundation
models on another network of the all-India league.

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

**Replication on Kaggle CPU** (run atlas-lockdown, 2026-11-13, 35.9 minutes; same code and data, different
hardware). Placebo bias +4.8% (−3.1% to +13.4%); phase-1 placebo +5.6%; just before −21.2% (effect −24.8%,
interval −31.2% to −17.3%); lockdown phase 1 −50.9% (effect −53.5%, −59.2% to −47.5%); all lockdown −41.0% (effect
−43.7%). Held-out-day errors of the three models 36.78, 35.42, 34.55. **Validity gate FAILED; detected YES**, as on
Colab. Every window moved by under 5 points between the two machines (training on GPU and CPU is not bit-identical),
and both verdicts are the same.

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

### What-if test 1b results (Colab, 2026-11-13, Tesla T4, 11.8 minutes)

The archive served every variable asked for (rain, boundary-layer height, wind at 100 m, cloud cover, soil moisture).
Its rain agrees that March 2020 was wet: 65.2 mm against 13.6 mm in March 2019 (the India Meteorological Department
measured 109.6 mm at Safdarjung). 4,346 training windows, 70 held-out days; the three models reached 34.34, 33.78
and 34.99 µg/m³ on the held-out days (test 1: 35.41, 36.04, 34.70).

| Window | days | measured PM2.5 | simulated, business as usual | measured ÷ simulated − 1 | 95% interval | effect after removing the placebo bias | 95% interval | day-to-day correlation |
|---|---|---|---|---|---|---|---|---|
| placebo: 25 Mar – 31 May 2019 | 68 | 88.1 | 82.6 | +6.7% | −3.6% .. +18.4% | – | – | 0.56 |
| placebo, phase-1 dates: 25 Mar – 14 Apr 2019 | 21 | 90.6 | 90.9 | −0.3% | −13.2% .. +10.4% | – | – | 0.73 |
| placebo, just-before dates: 1 – 21 Mar 2019 | 21 | 91.2 | 85.3 | +6.9% | +0.1% .. +14.9% | – | – | 0.77 |
| just before: 1 – 21 Mar 2020 | 21 | 67.1 | 80.3 | −16.5% | −24.2% .. −6.2% | −21.9% | −30.7% .. −10.8% | 0.84 |
| lockdown 1: 25 Mar – 14 Apr 2020 | 21 | 39.4 | 76.9 | −48.7% | −53.9% .. −44.0% | −48.6% | −55.6% .. −38.9% | 0.75 |
| lockdown 2: 15 Apr – 3 May 2020 | 19 | 44.6 | 86.5 | −48.4% | −54.4% .. −43.5% | −51.7% | −59.1% .. −44.8% | 0.78 |
| lockdown 3: 4 – 17 May 2020 | 14 | 53.6 | 84.0 | −36.2% | −47.3% .. −27.3% | −40.2% | −52.5% .. −30.1% | 0.45 |
| lockdown 4: 18 – 31 May 2020 | 14 | 56.6 | 92.6 | −38.9% | −54.4% .. −25.7% | −42.8% | −57.6% .. −29.3% | 0.61 |
| all lockdown: 25 Mar – 31 May 2020 | 68 | 47.5 | 84.4 | −43.8% | −48.5% .. −37.0% | −47.3% | −53.7% .. −38.9% | 0.64 |

**Validity gate (rule 4): FAILED. Lockdown detected in phase 1 (rule 5 of test 1): YES.**

1. **Both placebos pass** (+6.7% and +6.9%, inside ±15%). **The weeks before the lockdown still fail**: 16.5% below
   the simulation, and 21.9% below after removing the March 2019 bias (interval −30.7% to −10.8%). Rain and mixing
   height moved the raw gap from −20.7% to −16.5%. By rule 5 the weather we can obtain does not explain early March
   2020, and the lockdown rows again do not count as a measurement.
2. **Where the gap sits** (looked at after the result; a diagnostic, not a rule). Split at 12 March, when closures
   in Delhi began:

   | Days | test 1 | test 1b |
   |---|---|---|
   | 1 – 11 March 2020 | −24.3% | −26.2% |
   | 12 – 21 March 2020 | −16.9% | −4.1% |

   The reanalysis inputs explain the second half, where the heaviest rain fell. They do not explain the first
   eleven days, which came **before** any restriction. So "restrictions began early" is not the explanation
   either.
3. **Leading candidates now** (untested): the model has no way to represent a year-on-year change in emissions, and
   March 2020 is the first month after its training data ends; or rain the reanalysis under-counts (65 mm against
   109.6 mm measured).
4. **What can honestly be said about the lockdown.** Two versions of the method put phase 1 at −48.6% and −52.8%,
   far below the −20% that was already there, and plain comparisons give −39.7% (against the weeks before) and
   −54.3% (against 2019). The method has not earned the right to choose between those numbers.

Under rule 6 the method is now frozen. Before it goes to another episode, one check that does not touch any
lockdown: the error on the held-out training-period days, by half-year, to see whether the simulation drifts above
the measurements as time goes on.

## Atlas League v2.0: Atlas v1.3 against every scorable model on the list (rules, written before any score)

Adi's request: compare the present model with every existing model on the benchmark list, by actual runs, not by
numbers carried over from older Paradox models. Earlier verdicts against CAMS, the weather models and the traffic
architectures were made with PWM-W and PWM-Dyn (sections above and branches `delhi-v0.2` … `india-v2.0`, `main`);
none of them was made with Atlas. This league makes them with Atlas.

1. **Model under test: Atlas v1.3, frozen.** The adopted 3-seed ensemble (pre-trained on 13 networks without Delhi,
   then all Delhi history), exactly the forecasts saved by the Kaggle run atlas-delhi-fusion-v13
   (`fusion_members_atlas.npz`). Nothing is retrained or re-chosen. As a check the scorer must reproduce Atlas v1.3's
   recorded 28.91 / 25.56 before it scores anyone else.
2. **Task, windows, scoring: the Delhi league, unchanged.** PM2.5 at 39 CPCB stations, the next 24 hours, from every
   6th hour of 2025-07-03 .. 2025-12-31 (725 windows); Track S = the 31 stations Atlas trained on, Track U = the 8 it
   never trained on. Every entry is calibrated on the validation windows (conformalised quantile regression on Track
   S), MAE is the headline, and each comparison is a Diebold–Mariano test with a day-block bootstrap (p < 0.05 and an
   interval excluding zero). An opponent that does not cover a station or hour is compared only on the cells it
   covers (both models restricted to them).
3. **Words.** "Atlas beats X" only with significant MAE wins on both tracks; a significant loss on either track is
   "loses to X"; anything else is "level". An opponent that cannot forecast a station it was not trained on (its
   design needs a learned embedding per station) is still scored on Track U as it is, and that is said.
4. **Opponents, fixed now.** A model that cannot be installed or run on free hardware is reported as "not run" with
   the reason; no model is added, dropped or re-configured after any score is seen.
   * **A. Time-series foundation models, zero-shot** (512 h of each station's PM2.5, gaps forward-filled, the same
     windows): already scored TimesFM 2.5, Chronos-2, Chronos-Bolt; new: TimesFM 3.0 (univariate and multivariate;
     evaluation only, non-commercial licence), Moirai 2.0 (Salesforce), Toto (Datadog), Sundial (Tsinghua), TiRex
     (NX-AI), Granite TTM r2 (IBM). These need the GPU (Kaggle quota resets 2026-11-14 00:00 UTC).
   * **B. Operational air-quality forecast: CAMS global** (ECMWF Copernicus, 0.4°), from Open-Meteo's archive at each
     station's position (located by name, as in `delhi-v0.2`). The archive keeps the most recent run for each hour,
     which is generous to CAMS; scored raw and with a trailing 30-day same-hour local bias correction (only days before
     the forecast start). Point forecasts: the MAE verdict is the one that counts.
   * **C. Spatio-temporal graph architectures, trained on Atlas's own Delhi data**: STID (CIKM 2022), Graph WaveNet
     (IJCAI 2019), STAEformer (CIKM 2023), AGCRN (NeurIPS 2020), MTGNN (KDD 2020). Each is the class from its
     authors' repository, unchanged, with their published hyper-parameters (the METR-LA configuration where the
     repository has one, because METR-LA has missing readings as Delhi does; AGCRN has only PEMS configurations, so
     PEMS04) except input length (72 h, as Atlas), output length (24 h), nodes (39) and steps per day (24). Inputs, as in their papers: PM2.5 z-scored over the
     training period plus time of day and day of week. Training windows: the same as Atlas v1.3's Delhi stage (from
     2018, every 3rd hour, at least 8 trained stations observed); targets on Track S stations only; Track U stations'
     inputs are hidden (the repositories' missing value) during training and given at test, as for Atlas. Loss,
     optimiser, schedule, batch size and early stopping from each repository's train script (MTGNN without its
     curriculum schedule); best-validation checkpoint; one seed; a wall-clock budget of 100 minutes per model on a
     Kaggle T4 GPU (on the CPU STAEformer and AGCRN would finish only an epoch or two), and the run says whether the
     budget or the authors' rule stopped it. DCRNN and STGCN are not run:
     their official code is TensorFlow 1.x, which does not run on current Kaggle images.
   * **D. Weather models: ECMWF IFS, ECMWF AIFS, DWD ICON, NOAA GFS**, and NOAA AIGFS (GraphCast-based) and DWD
     AICON where Open-Meteo's archive has them (archived runs, Open-Meteo Previous Runs API, the run issued the day
     before each forecast hour; each raw and with the same trailing 30-day local bias correction as CAMS), against
     Atlas v1.3's own forecasts of temperature, humidity and wind speed at the CPCB stations that measure them (the
     same saved weights, all output channels; MAE in physical units). Atlas was trained with a weight of 0.05 on these
     channels, so this tests a by-product, and it is said so. (AIGFS, AICON and the bias-corrected variants were added
     to this rule on 2026-11-13, before any weather score.)
   * **E. AI weather models without an archive**, run by us from real analyses on the free GPU: Pangu-Weather,
     FourCastNet (SFNO), GraphCast (1°), on the same weather variables as D. Those that do not fit the free GPU are
     reported as not run.
5. **Not comparable, and said so in the paper:** video and robot world models (Genie, Cosmos, V-JEPA, Dreamer) do
   not forecast station measurements; WeatherNext, MetNet-3, GenCast (full) and Indian operational systems (IMD,
   NCMRWF, SAFAR) publish no archived forecasts at these stations and dates; Aurora's air-pollution model needs more
   GPU memory than the free tier has (Aurora ran out of memory on the free GPU in the earlier weather league) and CAMS
   analyses behind a Copernicus account.
6. **The all-India league** gets groups A and B as well, under its own rules (above), when the GPU allows.

### Atlas League v2.0 results (each group added when it has run)

**Group B, CAMS (Kaggle run atlas-league2-cams v2, 2026-11-13, CPU, 2 minutes).** The scorer first reproduced Atlas
v1.3's recorded 28.91 / 25.56. 37 of 39 stations were placed by name; CAMS covers 97% of trained-station cells and 88%
of never-trained-station cells, and every comparison is made on the cells it covers.

| Entry | Trained: MAE | Never trained: MAE | MAE@1h | MAE@24h | Atlas v1.3 against it (trained / never trained) | Verdict |
|---|---|---|---|---|---|---|
| Atlas v1.3 | 28.91 | 25.56 | 13.59 | 33.22 | – | – |
| CAMS global + 30-day local bias correction | 41.03 | 38.32 | 40.10 | 40.97 | WIN −29.0% (p = 7.2e-22) / WIN −32.5% (p = 2.7e-21) | **Atlas beats it** |
| CAMS global, archived forecast | 62.86 | 53.53 | 61.32 | 62.89 | WIN −53.7% (p = 4.1e-33) / WIN −51.7% (p = 1.8e-35) | **Atlas beats it** |

CAMS is a 0.4° global chemistry model; at station scale in Delhi it is biased high, and the local correction removes
part of that. Even generously timed (the archive keeps the latest run for each hour), it is far behind every
station-trained or station-reading forecast here. The same scoring run reproduced the three foundation models'
recorded numbers (TimesFM 2.5 30.83 / 27.10, Chronos-2 31.17 / 27.41, Chronos-Bolt 31.35 / 27.94).

**Group D, weather models (Kaggle run atlas-league2-weather, 2026-11-13, CPU, 5 minutes).** Atlas v1.3's own
temperature, humidity and wind-speed channels, from the same three saved models (check: their PM2.5 channel equals the
saved Atlas v1.3 forecasts to 0.0002 µg/m³), against each global model's run issued the day before each forecast hour,
at the CPCB stations that measure the variable (temperature 26, humidity 31, wind 29). NOAA AIGFS and DWD AICON have
no archived runs at Open-Meteo, so they were not run. MAE in physical units, trained / never-trained stations:

| Variable | Atlas v1.3 | Best raw model | Best bias-corrected model | Atlas against the best bias-corrected model |
|---|---|---|---|---|
| Temperature (°C) | 1.14 / 1.28 | AIFS 1.99 / 2.33 | AIFS 1.28 / 1.35 | WIN −10.8% (p = 0.0012) / TIE −5.0% (p = 0.17): **level** |
| Humidity (%) | 5.64 / 6.57 | AIFS 8.69 / 8.20 | AIFS 5.70 / 5.47 | TIE −2.6% (p = 0.36) / LOSS +13.4% (p = 9.4e-06): **Atlas loses** |
| Wind speed (m/s) | 0.38 / 0.32 | ICON 0.89 / 0.76 | ICON 0.60 / 0.51 | WIN −35.8% / WIN −35.1%: **Atlas beats** |

Against every raw archived run (IFS, AIFS, ICON, GFS) Atlas wins on all three variables and both tracks. With the local
bias correction: temperature, Atlas beats IFS, ICON and GFS and is level with AIFS; humidity, it beats IFS and GFS, is
level with ICON and loses to AIFS; wind, it beats all four. Full tables: `WEATHER_REPORT.md` in the run's output.

*What this does and does not mean.* Atlas reads the station's own last hours, so most of its edge is at short leads
(temperature MAE 0.43 °C one hour ahead against 1.28 for bias-corrected AIFS; 1.10 against 1.27 at 24 h; humidity at 24
h 6.02 against AIFS's 5.65, so AIFS is better by then). The global models forecast a grid cell, not a sensor; CPCB's wind
sensors in particular read far below the 10 m wind the models forecast (Atlas's 0.38 m/s error is against readings that
are themselves low), so the wind result says more about the sensors than about the models. These are verdicts about
forecasting these stations' readings, not about global weather skill.

**Group A, the foundation models that run on a CPU (Kaggle run atlas-league2-score, 2026-11-13, CPU, 0.9 minutes of
scoring).** Forecasts from runs atlas-league2-tsfm-cpu (Moirai 2.0 5.8 minutes, TiRex 284.9 minutes) and
atlas-league2-tsfm-ttm (TTM 0.8 minutes, with the frequency-token fix), all zero-shot with 512 hours of context, each
calibrated on validation the same way as Atlas. The scorer reproduced Atlas v1.3's 28.91 / 25.56 and the earlier
opponents' recorded numbers. Atlas-W v0 is scored in the same run as an entry (its own section is below).

| Entry | Trained: MAE | Never trained: MAE | QL | MAE@1h | MAE@24h | Atlas v1.3 against it (trained / never trained) | Verdict |
|---|---|---|---|---|---|---|---|
| Atlas v1.3 (967,632 parameters) | 28.91 | 25.56 | 9.55 | 13.59 | 33.22 | – | – |
| Moirai 2.0 R small (Salesforce, 11M) | 30.50 | 26.84 | 10.10 | 14.15 | 34.40 | WIN −5.2% (p = 1.1e-04) / WIN −4.8% (p = 9.0e-04) | **Atlas beats it** |
| TiRex (NX-AI, 35M) | 30.73 | 27.09 | 10.10 | 13.77 | 35.09 | WIN −5.9% (p = 2.8e-05) / WIN −5.7% (p = 1.2e-04) | **Atlas beats it** |
| TimesFM 2.5 (Google) | 30.83 | 27.10 | 10.15 | 13.95 | 35.34 | WIN −6.2% (p = 1.5e-05) / WIN −5.7% (p = 1.1e-04) | **Atlas beats it** |
| Chronos-2 (Amazon) | 31.17 | 27.41 | 10.23 | 14.10 | 35.99 | WIN −7.3% (p = 1.5e-06) / WIN −6.8% (p = 2.5e-05) | **Atlas beats it** |
| Chronos-Bolt (Amazon) | 31.35 | 27.94 | 10.26 | 14.21 | 36.26 | WIN −7.8% (p = 3.9e-08) / WIN −8.5% (p = 1.6e-07) | **Atlas beats it** |
| Granite TTM r2 (IBM, 0.8M) | 31.63 | 27.79 | 12.14 | 16.50 | 34.92 | WIN −8.6% (p = 3.1e-06) / WIN −8.0% (p = 1.4e-06) | **Atlas beats it** |
| Atlas-W v0 (ours, 14,043 parameters) | 31.97 | 27.43 | 10.51 | 14.89 | 35.34 | WIN −9.6% (p = 1.7e-12) / WIN −6.8% (p = 9.6e-11) | Atlas v1.3 better |

Moirai 2.0 is the strongest zero-shot model found so far on Delhi, ahead of TimesFM 2.5 by 0.3, and Atlas v1.3 still
beats it on both tracks. TTM forecasts a single value (its interval comes only from calibration), which is why its QL
and 80% coverage (69%) are worse. Atlas-W v0, trained on 16 months of Delhi alone, is behind Atlas v1.3, which was
pre-trained on 13 networks and then trained on all of Delhi's history.

**Groups A (TimesFM 3.0, Sundial, Toto), C (graph architectures) and E:** waiting for the GPU quota (resets Saturday
00:00 UTC); added here when scored.

## Atlas-W: the output-first, information-efficient world model (3-day build; rules written before any score)

Adi's brief (2026-11-13): build the world model output-first — define the physical understanding wanted, find the
minimum information it needs, use efficient mathematical representations, learn with the fewest trainable parameters
— and show the best output on less training data, within three days. The full plan is in the planning document
(16 weeks, traffic included); this section fixes what the three days must deliver and how it is judged.

**Day 1. Atlas-W air core v0 (`atlas/atlas/atlasw.py`, `delhi/run_atlasw.py`).** The same task, data file, windows,
loss, optimiser and scoring as Atlas on Delhi stage 8 (16 months of Delhi, PM2.5 headline, the other pollutants and
weather as outputs with the same loss weights). What changes is the representation:

* *Minimum information.* The model does not read the flattened 72-hour window (2,526 numbers per station). It reads
  a summary: each variable's last observed value, its means over the last 6, 24 and 72 hours relative to that value,
  the share of the last 24 hours observed and whether any value was seen (90 numbers), plus Atlas's static summary
  (78 numbers).
* *Efficient representation.* The forecast is produced by an explicit hourly state update in transport form, for all
  15 variables at once: relaxation towards a learned equilibrium at a learned rate (sources, sinks and dilution),
  plus exchange with the graph neighbours at a learned rate (transport between places). Untrained, it is
  persistence. The network supplies only the equilibrium, the two rates and the spread of the quantiles.
* *Fewest parameters.* 14,043 at width 32 and 37,531 at width 64 (Atlas: 967,632).

**Rules.**
1. Data-threshold grid as in stage 8B: the last 0.5, 1, 2, 4, 8 and all 15 months of training windows, widths 32 and
   64, 2 seeds each, single models, validation-chosen checkpoint, test MAE on trained stations. Atlas's stage-8B
   numbers on the same windows are the comparison (for example 967,632 parameters: 42.7, 42.8, 44.2, 40.0, 35.4, 34.3).
2. "Atlas-W is more data-efficient" only if, at each of 0.5, 1, 2 and 4 months, the better Atlas-W width's 2-seed mean
   is below the best Atlas size's 2-seed mean at that amount. "Atlas-W needs less data for the same accuracy" is
   read off the two curves: the months at which each first goes below 36.0 and below same-hour-yesterday (40.30).
3. Full data: the width with the lower mean validation MAE, 3 seeds, ensembled and calibrated as Atlas v1.0 was
   (33.42 / 29.07), scored once on test, and tested against TimesFM 2.5, Chronos-2 and Chronos-Bolt with the league's
   test. Words as in the league: beats / level / loses.
4. The threshold function e = floor + a·N^-α + b·P^-β is refitted on Atlas's and Atlas-W's runs separately; the
   data each needs to reach each foundation model is reported as an extrapolation, labelled as such.

**Predictions (written before any run).** Atlas-W beats every Atlas size at 0.5 to 4 months (it starts at
persistence and has few parameters to fit), reaching below 40.3 by 2 months, where Atlas needed 8. At 15 months it is
level with or a little behind the 1M Atlas (about 34 to 36 single-model), because the summary discards information the
full window holds. It does not beat the foundation models on 16 months of Delhi alone. If the last prediction holds,
day 2 gives Atlas-W what moved Atlas: all of Delhi's history and pre-training on the rest of India, under v1.3's rules.

**Day 2.** Atlas-W on all Delhi history and pre-trained on the other 13 networks (the v1.3 recipe, rules unchanged),
scored against the same league; and the horizon extended to 72 hours for the five pollutants.
**Day 3.** The minimum-information table (each input group removed, each summary removed, cost measured on
validation and reported on test), the threshold function with the parameter axis, and the write-up.
**Not in the three days, and not claimed:** traffic (no Indian network-scale data in hand; corridor trajectory data
has to be obtained first) and intervention tests (the placebo gate has failed twice). They stay in the 16-week plan.

### Atlas-W air core v0 results (Kaggle run atlasw-v0, 2026-11-13, CPU, 67.9 minutes, real Delhi data)

**Data threshold** (single models, test MAE on trained stations, mean of 2 seeds; Atlas rows are stage 8B, same windows):

| model | parameters | 0.5 mo | 1 mo | 2 mo | 4 mo | 8 mo | all 15 mo |
|---|---|---|---|---|---|---|---|
| **Atlas-W width 32** | **14,043** | **37.1** | 37.4 | 39.5 | 37.3 | **33.0** | **32.1** |
| Atlas-W width 64 | 37,531 | 37.9 | 37.4 | 39.2 | 36.6 | 33.4 | 32.3 |
| Atlas | 50,232 | 47.3 | 48.3 | 50.6 | 43.1 | 38.0 | 35.1 |
| Atlas | 231,312 | 43.5 | 47.1 | 51.9 | 43.6 | 36.9 | 34.9 |
| Atlas | 967,632 | 42.7 | 42.8 | 44.2 | 40.0 | 35.4 | 34.3 |

* **Rule 2: Atlas-W is more data-efficient.** Its best width is below the best Atlas size at every amount: by 13%
  at 0.5 months, 13% at 1, 11% at 2, 9% at 4, 7% at 8 and 6% with everything. It is below same-hour-yesterday (40.30)
  from two weeks of data; Atlas needed four months. With two weeks (114 training windows) it is about where the
  1M Atlas is with eight months. Both first go below 36.0 at 8 months. Seeds agree (for example 36.2 and 37.9 at
  0.5 months, 32.0 and 32.2 with everything); the two widths are indistinguishable, so 14,043 parameters suffice.
* **Rule 3, full data (width 32 chosen on validation, 3 seeds, calibrated):** 31.97 on trained stations and 27.43 on
  never-trained stations, against 33.42 / 29.07 for the 967,632-parameter Atlas v1.0 on the same 16 months: 4.3% and
  5.6% lower with 69 times fewer parameters. Against the foundation models: **loses to TimesFM 2.5** (+3.71%,
  p = 0.015 on trained stations; tie +1.24% on never-trained), **level with Chronos-2** (+2.56%, p = 0.077 / +0.09%)
  and **level with Chronos-Bolt** (+1.98% / −1.80%). Coverage 79%. One hour ahead it is behind (14.89 against 13.95
  for TimesFM 2.5); at 24 hours it is equal (35.34 and 35.34).
* **Rule 4 (extrapolation, not measurement):** the threshold function fitted to the 24 runs (misfit ×1.05) puts the
  floor at its bound and the model-size term near zero, and says a single Atlas-W would need about 11,900 training
  windows to reach Chronos-Bolt, 13,400 for Chronos-2 and 16,900 for TimesFM 2.5, against 3,673 here. Delhi's full
  history has 19,082.

**Against the predictions.** Held: more data-efficient at 0.5 to 4 months; below 40.3 by 2 months (already at two
weeks); does not beat the foundation models on 16 months alone. Wrong: Atlas-W was predicted level with or behind the
1M Atlas at 15 months and is ahead of it, so the 168-number summary lost nothing that the full window was giving
Atlas at this data size. Not shown: that the physics form itself (relaxation and exchange) is what helps, as opposed
to the summary inputs or simply being small; the day-3 removals test that. The Delhi test period is reused, so these
are provisional like every Delhi result.

### Atlas-W days 2 and 3: rules and predictions (written 2026-11-13, before any of these runs)

**Change to the day-2 plan, made before running.** The 72-hour horizon for five pollutants is taken out of day 2.
It needs its own league (new windows, new baselines, and SO₂, which the Delhi league file does not carry), and its
rules will be written before it runs. Day 2 is now only the v1.3 recipe below, so that Atlas-W v1 can be scored in
the same league as everything else.

**Day 2: Atlas-W v1, trained the way Atlas v1.3 was** (`delhi/kaggle_atlasw13.sh`; the same scripts as v1.3, with
`ATLAS_MODEL=atlasw:32` so that they build Atlas-W instead of Atlas).
1. Model: Atlas-W v0 unchanged, width 32 (the width validation chose on day 1), 14,043 parameters.
2. Recipe: v1.3's, unchanged. (a) Pre-train one set of weights on the 13 other Indian networks, with no Delhi
   station (`run_atlas_india.py --skip Delhi --pretrain-only`, the early-stopping checkpoint E). (b) Stage B: all
   valid Delhi windows since 2018 at 0.3 × the learning rate, up to 12,000 steps. (c) Stage C: B fine-tuned on the
   league's 16 months at 0.2 × the learning rate. Seeds 320, 321 and 322, one notebook each.
3. B or C is chosen by the lower mean validation MAE over the three seeds. The three chosen models are averaged,
   calibrated on validation exactly as every league entry is, and scored once in Atlas League v2.0 against
   everything there. The forecasts of the pre-trained weights before any Delhi training (P) are scored as a separate
   entry: Atlas-W with no Delhi training at all.
4. Words as in the league: "Atlas-W v1 beats X" only with a significant win on both tracks; "level"; "loses".

*Predictions.* Atlas-W gains less from more data than Atlas did: its day-1 curve was already flatter, and Atlas went
from 33.42 to 28.91 (−13.5%) with this recipe. Atlas-W v1: about 29.5 to 31.0 on trained stations. That is level with
or better than TimesFM 2.5 (30.83) and Moirai 2.0 (30.50), and behind Atlas v1.3 (28.91). P (no Delhi training):
about 32 to 35, worse than v0, which saw Delhi.

**Day 3a: the minimum-information table** (`delhi/run_atlasw_ablate.py`). The setting is day 1's full-data model:
width 32, the league's 16 months, the same windows, steps and caps. Each variant is run with seeds 0 and 1, and the
full model is run again in the same notebook as the base. One thing is removed at a time:

| Variant | What is removed |
|---|---|
| R1 | exchange between stations in the update (κ = 0) |
| R2 | mixing of the summary between graph neighbours |
| R3 | the physics form: the median is the last value plus a direct output for each hour (no recurrence, no κ) |
| R4 | the 6, 24 and 72-hour means (the summary keeps the last value, the observed share and the any-value flag) |
| R5 | weather as an input (weather is still forecast as an output) |
| R6 | the other pollutants (PM10, NO₂, ozone) as inputs (still forecast as outputs) |
| R7 | the longer-history summary: the past days' daily PM2.5 means, PM2.5 at the same hour a week earlier, the station's scale |
| R8 | the calendar of the hours being forecast (hour of day, day of week) |

(R7's description was corrected before any run: the first version called this input a calendar summary, but the only
calendar input Atlas-W reads is R8's. R6 removes PM10, NO₂ and ozone as written; CO, SO₂, NH₃ and NO stay inputs.)

For each variant, the 2-seed average is compared with the base's. The measure is validation MAE on trained stations;
test MAE is also reported, with the league's test (day blocks, both tracks) against the base. A part "earns its place"
if removing it raises validation MAE by 1% or more, and "is not needed" if the change is under 1%. "The physics form
helps" only if R3 is at least 1% worse on validation and the base beats it significantly on trained stations.
Nothing is removed from the model on the strength of this table until a new version is written down and run again.

*Predictions.* R8 and R7 hurt most (3% or more: PM2.5 in Delhi follows the clock and the week). R4 hurts (more than 3%). R3:
2–5% worse, but this is the least certain prediction. R5 and R6: 1–2%. R1 and R2: under 1%.

**Day 3b: the threshold function with the parameter axis** (`run_atlasw.py --grid-only --widths 16,128`). The day-1
grid (the last 0.5, 1, 2, 4, 8 and 15 months, 2 seeds) is run at widths 16 and 128. e = floor + a·N^-α + b·P^-β is
fitted to all four widths together (Atlas-W runs only). Reported: the fitted numbers, the misfit, and the best width
at each data amount. *Prediction:* width 16 is close to 32 at small data; 128 is no better than 64 at full data, so
the parameter term is small and data is what limits Atlas-W.

### Atlas-W day 2 results: Atlas-W v1, trained the v1.3 way (Kaggle runs atlasw-v13-s320/s321/s322 and atlas-league2-score-w1, 2026-11-13, CPU)

Pre-training on 13 networks (144,671 windows, no Delhi station) took 41–44 minutes per seed: 20,000–42,000 steps to
the early-stopping checkpoint, pooled validation MAE 8.83–8.86. Stage B used 19,082 Delhi windows since 2018 and
stopped at 6,000–8,000 steps. Stage C never beat B on validation, so C equals B, and the rule chose B. The scorer
reproduced Atlas v1.3's 28.91 / 25.56.

| Entry | Trained: MAE | Never trained: MAE | QL | MAE@1h | MAE@24h | Atlas v1.3 against it |
|---|---|---|---|---|---|---|
| Atlas v1.3 (967,632 parameters) | **28.91** | **25.56** | 9.55 | 13.59 | 33.22 | – |
| Moirai 2.0 | 30.50 | 26.84 | 10.10 | 14.15 | 34.40 | WIN −5.2% / −4.8% |
| TimesFM 2.5 | 30.83 | 27.10 | 10.15 | 13.95 | 35.34 | WIN −6.2% / −5.7% |
| Chronos-Bolt | 31.35 | 27.94 | 10.26 | 14.21 | 36.26 | WIN −7.8% / −8.5% |
| **Atlas-W v1 (14,043 parameters, v1.3 recipe)** | **31.44** | **27.48** | 10.35 | 15.11 | 35.04 | WIN −8.0% (p = 1.7e-11) / −7.0% (p = 1.2e-11) |
| Granite TTM r2 | 31.63 | 27.79 | 12.14 | 16.50 | 34.92 | WIN −8.6% / −8.0% |
| **Atlas-W, no Delhi training at all (P)** | 31.91 | 27.63 | 10.53 | 16.24 | 35.82 | WIN −9.4% / −7.5% |
| Atlas-W v0 (16 months of Delhi) | 31.97 | 27.43 | 10.51 | 14.89 | 35.34 | WIN −9.6% / −6.8% |

*Against the predictions:* **wrong.** Atlas-W v1 is 31.44, not 29.5–31.0. All of Delhi's history and pre-training
gained only 0.53 over v0 (−1.7%), where Atlas gained 13.5% from the same recipe. So Atlas-W is not level with or
better than TimesFM 2.5 or Moirai 2.0. On trained stations it is 0.6–0.9 behind them and 0.1 behind Chronos-Bolt.
On never-trained stations it is 0.4–0.6 behind Moirai and TimesFM and ahead of Chronos-Bolt and TTM. Atlas-W was
not tested directly against those models in this run (the scorer tests Atlas v1.3 against every entry), so "level"
or "behind" here is by the numbers, not by a significance test. P was predicted at 32 to 35; it came out at 31.91, the
good end.

*What it shows.* (1) **Transfer works without any local data.** Atlas-W trained only on the other 13 networks,
which never saw a Delhi station, does as well as Atlas-W trained on 16 months of Delhi (31.91 against 31.97 on
trained stations). (2) **Atlas-W has hit a ceiling.** Its curve is flat from 8 months onward, at every width. A
14,000-parameter model with this information already uses what this information can give; more data and more
parameters do not move it. What moves it is form (day 3a). (3) Atlas v1.3 stays the best model in the league.

### Atlas-W day 3a results: the minimum-information table (Kaggle run atlasw-ablate, 2026-11-13, CPU, 75 minutes)

Two seeds per row, width 32, the league's 16 months of Delhi. The base reproduces day 1: 32.03 / 27.44 with two
seeds, against 31.97 / 27.43 with three. "Base against it" is the league's test (day blocks); WIN means the full
model is better.

| Variant | Removed | Validation MAE | Change | Test: trained | Never trained | Base against it (trained / never trained) | Words (1% rule) |
|---|---|---|---|---|---|---|---|
| base | – | 20.49 | – | 32.03 | 27.44 | – | – |
| R1 | exchange between stations (κ) | 21.16 | **+3.2%** | 32.32 | 27.78 | TIE −0.9% (p = 0.15) / WIN −1.2% (p = 0.047) | earns its place |
| R2 | summary mixing between neighbours | 20.63 | +0.7% | 32.15 | 27.66 | TIE / WIN −0.8% (p = 0.026) | not needed |
| R3 | **the physics form** (direct output for each hour) | 21.51 | **+5.0%** | 33.92 | 29.34 | **WIN −5.6% (p = 3.9e-06) / WIN −6.5% (p = 4.4e-09)** | **earns its place** |
| R4 | 6 / 24 / 72 h means | 20.67 | +0.9% | 32.10 | 27.61 | TIE / TIE | not needed |
| R5 | weather as input | 20.65 | +0.8% | 32.23 | 27.75 | TIE / WIN −1.1% (p = 0.007) | not needed |
| R6 | PM10, NO₂, ozone as inputs | 20.56 | +0.4% | 32.24 | 27.57 | WIN −0.7% (p = 0.003) / WIN −0.5% (p = 0.036) | not needed |
| R7 | longer-history summary | 20.54 | +0.2% | 31.89 | 27.42 | TIE / TIE | not needed |
| R8 | **calendar of the forecast hours** | 20.90 | **+2.0%** | 36.35 | 30.75 | **WIN −11.9% (p = 1.4e-08) / WIN −10.8% (p = 1e-08)** | **earns its place** |

**The physics form helps** by the written rule: R3 is 5.0% worse on validation, and the base beats it significantly
on both tracks (5.6% and 6.5%). R3's parameter count includes the rate and κ heads that it does not use, so its
real count is 990 lower. Three parts earn their place: the physics update, the exchange between stations, and the
calendar of the forecast hours. Five do not reach 1% on validation: summary mixing, the 6/24/72 h means, weather,
the other pollutants and the longer history. Some of them still help a little on test (R5 and R6 are significant at
0.5–1.1%), so under the rule they are "not needed", not "useless". Nothing is removed until a new version is written
down and run.

*Against the predictions:* R8 half right: it hurts most on test (−11.9%), but on validation it is +2.0%, not the
predicted 3% or more. R7 was wrong: the week-ago history adds nothing.
R4 was wrong: under 1%, not over 3%. R3 was right (5.0%, the top of the 2–5% range). R5 and R6 were roughly right
(under 1%, not 1–2%). R1 was wrong: exchange matters (3.2%), not under 1%. R2 was right.

### Atlas-W day 3b results: the parameter axis (Kaggle run atlasw-grid2, 2026-11-13, CPU, 68 minutes)

Test MAE on trained stations, 2-seed means (widths 32 and 64 from day 1):

| Width | Parameters | 0.5 mo | 1 mo | 2 mo | 4 mo | 8 mo | all (15 mo) |
|---|---|---|---|---|---|---|---|
| 16 | 6,139 | 35.8 | 38.4 | 40.6 | 35.7 | 32.8 | 32.4 |
| 32 | 14,043 | 37.1 | 37.4 | 39.5 | 37.3 | 33.0 | 32.1 |
| 64 | 37,531 | 37.9 | 37.4 | 39.2 | 36.6 | 33.4 | 32.3 |
| 128 | 115,227 | 37.6 | 37.7 | 37.7 | 35.8 | 34.9 | 32.6 |

With all the data, a 19-fold range of sizes lands within 0.5 of each other (32.1 to 32.6). The fitted function
(48 runs) puts essentially nothing on the parameter term (b = 0.0016, β = 2.9) and a weak data term (α = 0.045,
floor 0, misfit ×1.046). The fit is poorly determined. Test error does not fall smoothly with data here, because
the most recent 2 months are a hard season for the test period (every width is worst at 2 months). Validation picks
a different best width at almost every data amount (64, 64, 64, 16, 64, 128), which is another sign that the
differences are noise.

*Against the prediction:* right. Size is not what limits Atlas-W: 6,000 parameters do as well as 115,000. What
helps is the form of the model (R3, R1, R8) and the amount of data.

## Atlas-Live: the continuously updating model (rules written before any score)

Adi's brief (2026-11-13): the model must keep updating as new data arrives. `delhi/run_live.py` is the engine. Its
first test is a **replay on real data**: the Delhi test period is walked through day by day, and at every moment the
engine may use only measurements that had already arrived. Nothing is simulated; "replay" means the real measurements
are released to the engine in the order they happened.

Three layers, each added on top of the one before, all starting from the frozen Atlas v1.3 (3 saved models):
1. **Frozen.** v1.3 as scored (check: the engine must reproduce 28.91 / 25.56 with the validation calibration).
2. **Daily correction.** At 00:00 each day, from the forecasts of the previous 30 days whose 24 target hours were all
   in the past: a bias per station and lead block (hours 1-6, 7-12, 13-24; mean error shrunk by n / (n + 50)), then
   the 80% band re-calibrated on the same corrected trailing forecasts. No weights change.
3. **Weekly gated fine-tune.** Every 7 days each model continues training (same loss; learning rate 1e-4, at most
   200 steps, batch 16) on the windows of the previous 9 weeks except the last, and is checked on the last week's
   windows (trained stations). The fine-tuned weights replace the current ones only if their error on that week is
   lower; otherwise the current weights stay. Layer 2 is then applied on top.

Every forecast is written to a ledger with its issue time before its target hours are released
(`live_ledger.npz`). Scoring: the league's 725 test windows and both tracks; each layer against the one before and
against TimesFM 2.5 with the league's test. "Continuous updating helps" only if layer 2 or 3 beats layer 1 with
significant MAE wins on both tracks. The Delhi test period is reused, so any gain is provisional (rule 7).

**Prediction.** Layer 2 changes MAE by less than 1% either way (v1.3 already reads the last 72 hours, and its bias on
validation was small). Layer 3 gains 1 to 3% in November-December, when the season differs most from the training
years' average, and is level before that. **Not yet built:** the live feed. CPCB's real-time data needs a free API
key (data.gov.in or OpenAQ) that Adi creates and stores as a Kaggle secret; until then the engine runs on the public
files, which arrive in yearly batches.

### Atlas-Live results: the replay on real data (Kaggle run atlas-live-replay, 2026-11-13, CPU, 44.8 minutes)

The engine reproduced the frozen Atlas v1.3 exactly (28.91 / 25.56; largest difference from the saved forecasts
0.0002 µg/m³). 26 weekly updates ran; the gate accepted 51 of 78 fine-tunes.

| Layer | Trained: MAE | Never trained: MAE | Against layer 1 | Against TimesFM 2.5 (30.83 / 27.10) |
|---|---|---|---|---|
| 1 Frozen Atlas v1.3 | **28.91** | **25.56** | – | beats (−6.22% / −5.69%) |
| 2 + daily correction | 29.08 | 25.79 | level (+0.59%, p = 0.59 / +0.91%, p = 0.39) | beats (−5.67% / −4.83%) |
| 3 + weekly gated fine-tune | 30.39 | 26.94 | **loses** (+5.11%, p = 0.0009 / +5.43%, p = 0.0004) | level (−1.43% / −0.57%) |

**Continuous updating, as built, does not help; the weekly fine-tune makes the model significantly worse.** The
prediction for layer 2 held (a change under 1%); the prediction for layer 3 (a 1 to 3% gain in November-December) was
wrong. By month, trained stations: July to September all layers within 0.5 µg/m³; October 32.0 / 31.8 / 33.4;
November 48.6 / 49.9 / **54.2**; December 53.9 / 53.3 / 54.8 (layers 1 / 2 / 3).

*Why layer 3 fails, as far as this run shows.* The gate compares on the most recent week only, and in a season that
is changing fast (October into November) last week is a poor guide to next week: a model pulled towards the last nine
weeks' conditions loses what the pre-trained model knew about winter from other years and other cities. Accepting 51
of 78 updates on 49 gate windows each is also what noise alone would do. The frozen model already adapts through its
inputs (the last 72 hours and 14 daily means), which is the cheaper kind of updating.

*What stays.* The ledger, the daily ingest design and the frozen model reading live data. Weight updates are off
until a rule that passes this replay exists; candidates, to be written as rules before any run: update only on a
full year of new data, or with the all-India mixture kept in every batch, or a much stricter gate (several weeks,
significance required). The live feed still needs the API key.

## ICML programme, wave 1: rules and predictions (written 2026-11-14, before any of these runs)

Wave 1 answers the two objections a reviewer will raise first: that the Delhi test was reused, and that the
architecture is standard. Later waves (stronger baselines: fine-tuned foundation models, foundation models given
neighbouring stations, the five graph models; benchmarks outside India; removal tests on Atlas itself) get their own
rules before they run.

**L1. Leave one network out (the confirmation that rule 7 of v1.3 asked for).** Four networks, fixed now as the four
largest after Delhi: Uttar Pradesh, Haryana, Maharashtra, Karnataka. For each network X (`delhi/kaggle_lono.sh`):
1. Pre-train Atlas (967,632 parameters, the all-India recipe) on the 13 networks other than X (`run_atlas_india.py
   --skip X --pretrain-only`, early-stopping checkpoint E). Seed 500.
2. Adapt to X: X's own training windows only, 0.3 × the learning rate, up to 12,000 steps, a look at X's validation
   every 400 steps, stopping after 10 looks without improvement (Delhi v1.3's stage B, unchanged). The checkpoint
   with the best validation error on X is kept.
3. Score on X's all-India test windows, calibrated on X's validation exactly as in the all-India league, against
   TimesFM 2.5's forecasts of the same windows (run atlas-india-opp-gpu v2), with the league's test (day blocks, both
   tracks). The pre-trained weights before adaptation (P) are scored too.

*Rule.* The v1.3 recipe is **confirmed** if the adapted model beats TimesFM 2.5 (a significant win on both tracks) on
at least three of the four networks and loses on none. **Not confirmed** if it beats TimesFM 2.5 on two or fewer, or
loses on any. One seed is used. If a network's verdict depends on it, two more seeds are run before anything is
claimed, and the rule is applied to the three-seed average.

*Predictions.* Atlas-India (trained on all 14 networks) beat TimesFM 2.5 on Uttar Pradesh (−8.3%) and Haryana
(−5.5%) and was level on Maharashtra (+1.2%) and Karnataka (−1.2%). Leaving the network out of pre-training should
cost a little, and adaptation should give some of it back. Predicted: beats on Uttar Pradesh and Haryana; level on
Maharashtra and Karnataka. That is two of four, so **not confirmed**. P, the model never trained on X: level with
TimesFM 2.5 on all four.

**A1. Atlas-P: Atlas with a physics decoder.** Atlas unchanged up to the decoder. Then, per hour and per variable,
the decoder gives the equilibrium offset, the relaxation rate and two spreads, and the median is stepped hour by hour
as in Atlas-W: x[t+1] = x[t] + k (x* − x) + κ (neighbour mean − x). κ per station and variable comes from the
encoded state, the neighbour mean from the same station graph as the attention, and the rates start near zero, so an
untrained Atlas-P is persistence. 978,507 parameters (width 144, as Atlas).
1. Trained exactly as Atlas-India (all 14 networks, 60,000 steps, the same seeds 400, 401 and 402), with
   `ATLAS_PHYS=1`.
2. Decision on validation only: Atlas-P replaces Atlas if its pooled validation MAE, averaged over the three seeds,
   is lower than Atlas-India's three seeds by more than 2 standard errors of the paired difference.
3. The all-India test is reported once, as a second use of that period (Atlas-India's was the first), with the
   league's test against Atlas-India and TimesFM 2.5.

*Prediction.* Removing the physics update cost Atlas-W 5.0% on validation, but Atlas's latent dynamics and
attention already capture much of what it does. Atlas-P: 1% to 3% lower validation MAE than Atlas. That clears the
2-standard-error bar only if the seed spread is small.

## What has not been done (as of 2026-11-13)

* Sizes of 2M and above ran on the damped oscillator only, with one seed and three data amounts. The 10M ring
  model was built and counted but not trained (CPU time).
* Real data so far is air quality only: Delhi, then every Indian station network. The comparison with TimesFM and
  Chronos has been made on Delhi PM2.5 only; TimesFM 3.0 is compared by number only, with no significance test yet.
* The all-India league has been scored against simple forecasts only; the foundation models are running on its
  windows. Atlas-Delhi v1.3 beats them on Delhi, provisionally, until the recipe is repeated on another network.
* What-if: tests 1 and 1b both failed their validity gate (the weeks before the 2020 lockdown are 17–21% cleaner
  than the simulation). No counterfactual claim is made.
* The "which variable or station to collect next" advisor has not been tried on real data.
* Long autoregressive roll-outs, non-linear systems (Burgers, shallow water), and information-bottleneck /
  mutual-information estimates of the learned state are not measured.
* All four known-equation systems are linear in their state. The findings above may not carry to chaotic or non-linear systems.

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
