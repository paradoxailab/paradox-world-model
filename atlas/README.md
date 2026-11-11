# Paradox Atlas v0.1: how much information does a world model need?

ParadoxAI Lab (Aditya Kumar, Anupam Singh).

**Question.** Is there a minimum amount of useful information a model needs before it can predict a physical system,
and can it be worked out before training? This version builds the model and the measuring apparatus, and answers the
question on four systems whose equations are known. It uses numbers only: no images, video or text, and no
pretrained weights from anyone.

Everything below was measured: 342 training runs from random initialisation, on a 2-core CPU, about 100 minutes.
Full tables: [`results/REPORT.md`](results/REPORT.md). Raw runs: `results/runs_*.jsonl`.

## What was built

| Part | File | What it does |
|---|---|---|
| Exact simulators | `atlas/systems.py` | Harmonic oscillator, damped oscillator, diffusion and advection-diffusion on a ring of 8 nodes. Solved exactly (checked against the analytic solutions to 1e-14), with a forcing input (a force, or an emission source at one node). Every trajectory has its own parameters, start and forcing. |
| Equation-aware oracle | `atlas/systems.py: oracle` | Knows the equation but not its parameters or state; fits them to the noisy window and forecasts. This is the floor a perfect learner could reach. |
| Atlas model | `atlas/model.py` | Eight modules: numerical encoder, per-node state, spatial engine (attention biased by geometry), one transition network iterated in time, future forcing fed into the transition (interventions), hard physics rules (bounds, conservation of total amount), 10/50/90% quantiles that cannot cross. One width setting scales it from 8,468 to 9,914,492 parameters (ring version: 9,988,512). The code refuses to build above 10M. |
| Trainer | `atlas/train.py` | Quantile loss on the next 16 steps plus reconstruction of 15% hidden inputs. 80% of the N trajectories train, 20% decide early stopping. Test sets are fixed: 2,000 fresh trajectories, 1,000 from parameter ranges never seen, and counterfactual forcings. |
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

Runs are deterministic for a given seed on the same machine (the same configuration run twice gave identical numbers).
