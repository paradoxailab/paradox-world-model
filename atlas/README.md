# Paradox Atlas v0.2: how much information does a world model need?

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

Runs are deterministic for a given seed on the same machine (the same configuration run twice gave identical numbers).
