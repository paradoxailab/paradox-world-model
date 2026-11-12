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
