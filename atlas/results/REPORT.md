# Atlas threshold experiments: measured results

342 training runs, all from random initialisation, CPU only.

## A. Model size x data amount (damped oscillator)

Test error (normalised MSE on 2,000 fresh trajectories; mean ± spread over seeds where more than one seed ran). Persistence 1.101; ridge regression at N=10,000: 0.425; equation-aware oracle 0.029.

| params \ N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| 8,468 | 0.906 ±0.072 | 0.564 ±0.002 | 0.418 ±0.005 | 0.289 ±0.033 | 0.252 ±0.003 | 0.238 ±0.029 |
| 48,596 | 0.920 ±0.072 | 0.538 ±0.034 | 0.370 ±0.006 | 0.262 ±0.084 | 0.175 ±0.003 | 0.128 ±0.019 |
| 90,316 | 0.854 ±0.039 | 0.543 ±0.018 | 0.392 ±0.021 | 0.281 ±0.031 | 0.145 ±0.020 | 0.110 ±0.020 |
| 242,668 | 0.850 ±0.044 | 0.531 ±0.015 | 0.379 ±0.015 | 0.240 ±0.063 | 0.151 ±0.006 | 0.137 ±0.022 |
| 490,916 | 0.880 ±0.084 | 0.576 ±0.019 | 0.378 ±0.001 | 0.265 ±0.062 | 0.118 ±0.009 | 0.091 ±0.014 |
| 977,492 | 0.885 ±0.141 | 0.513 ±0.011 | 0.382 ±0.007 | 0.241 ±0.100 | 0.149 ±0.021 | 0.114 ±0.015 |
| 1,973,188 | – | 0.587 | – | 0.300 | – | 0.104 |
| 4,931,596 | – | 0.453 | – | 0.275 | – | 0.101 |
| 7,467,788 | – | 0.606 | – | 0.292 | – | 0.092 |
| 9,914,492 | – | 0.593 | – | 0.340 | – | 0.100 |

Training-set error for the same cells (how much is memorised):

| params \ N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| 8,468 | 0.175 | 0.183 | 0.053 | 0.124 | 0.170 | 0.191 |
| 48,596 | 0.220 | 0.129 | 0.038 | 0.039 | 0.057 | 0.064 |
| 90,316 | 0.162 | 0.325 | 0.031 | 0.071 | 0.031 | 0.044 |
| 242,668 | 0.390 | 0.056 | 0.027 | 0.025 | 0.022 | 0.071 |
| 490,916 | 0.075 | 0.349 | 0.073 | 0.050 | 0.011 | 0.024 |
| 977,492 | 0.087 | 0.093 | 0.057 | 0.041 | 0.028 | 0.055 |
| 1,973,188 | – | 0.176 | – | 0.056 | – | 0.020 |
| 4,931,596 | – | 0.0088 | – | 0.040 | – | 0.018 |
| 7,467,788 | – | 0.412 | – | 0.024 | – | 0.017 |
| 9,914,492 | – | 0.349 | – | 0.041 | – | 0.020 |

Runs that stopped at the step limit (training compute, not data, may be the limit there): P=8,468 N=300 seed 0, P=8,468 N=3000 seed 0, P=8,468 N=10000 seed 0, P=48,596 N=3000 seed 0, P=48,596 N=10000 seed 0, P=90,316 N=10000 seed 0, P=242,668 N=3000 seed 0, P=242,668 N=10000 seed 0, P=490,916 N=3000 seed 0, P=490,916 N=10000 seed 0, P=977,492 N=3000 seed 0, P=977,492 N=10000 seed 0, P=8,468 N=3000 seed 1, P=8,468 N=10000 seed 1, P=48,596 N=10000 seed 1, P=90,316 N=3000 seed 1, P=90,316 N=10000 seed 1, P=490,916 N=3000 seed 1, P=490,916 N=10000 seed 1, P=1,973,188 N=10000 seed 0, P=4,931,596 N=10000 seed 0, P=7,467,788 N=10000 seed 0, P=9,914,492 N=10000 seed 0

Training time per run, CPU seconds (mean over that size's runs): 8,468: 10s, 48,596: 10s, 90,316: 14s, 242,668: 10s, 490,916: 17s, 977,492: 24s, 1,973,188: 49s, 4,931,596: 141s, 7,467,788: 200s, 9,914,492: 240s

## B. Threshold function

`error(N, P) = floor + a·N^-alpha + b·P^-beta`, fitted to all 90 runs of table A:

floor = 0.0109, a = 3.039, alpha = 0.377, b = 674, beta = 0.981; typical misfit ×1.16 (RMS of log error 0.145).

**Does it predict runs it has not seen?** Fitted only on runs with N ≤ 3,000 and size ≤ 1M (65 runs), then asked to predict the 25 runs with N = 10,000 or size ≥ 2M: typical error ×1.24 (mean bias ×0.87; above 1 = predicts too high an error). Naive reference (reuse the nearest measured cell): ×1.31.

Small-range fit: floor 0.0000, alpha 0.384, beta 0.723.

| held-out cell (P, N) | measured | predicted from the small runs |
|---|---|---|
| 8,468, 10,000 | 0.238 | 0.174 |
| 48,596, 10,000 | 0.128 | 0.115 |
| 90,316, 10,000 | 0.110 | 0.107 |
| 242,668, 10,000 | 0.137 | 0.099 |
| 490,916, 10,000 | 0.091 | 0.097 |
| 977,492, 10,000 | 0.114 | 0.095 |
| 1,973,188, 100 | 0.587 | 0.543 |
| 1,973,188, 1,000 | 0.300 | 0.225 |
| 1,973,188, 10,000 | 0.104 | 0.094 |
| 4,931,596, 100 | 0.453 | 0.542 |
| 4,931,596, 1,000 | 0.275 | 0.224 |
| 4,931,596, 10,000 | 0.101 | 0.093 |
| 7,467,788, 100 | 0.606 | 0.542 |
| 7,467,788, 1,000 | 0.292 | 0.224 |
| 7,467,788, 10,000 | 0.092 | 0.093 |
| 9,914,492, 100 | 0.593 | 0.542 |
| 9,914,492, 1,000 | 0.340 | 0.224 |
| 9,914,492, 10,000 | 0.100 | 0.093 |

### Minimum data for a target error (inverting the fit; 10–90% bootstrap interval)

| target error | model size | fitted minimum N | interval | measured crossing | inside measured range? |
|---|---|---|---|---|---|
| 0.4 | 242,668 | 239 | 220 – 253 | 252 | yes |
| 0.4 | 977,492 | 234 | 213 – 248 | 252 | yes |
| 0.4 | 9,914,492 | 233 | 211 – 247 | 508 | yes |
| 0.3 | 242,668 | 529 | 472 – 567 | 556 | yes |
| 0.3 | 977,492 | 516 | 458 – 553 | 564 | yes |
| 0.3 | 9,914,492 | 513 | 451 – 549 | 1,263 | yes |
| 0.2 | 242,668 | 1,659 | 1,452 – 1,805 | 1,538 | yes |
| 0.2 | 977,492 | 1,599 | 1,373 – 1,726 | 1,527 | yes |
| 0.2 | 9,914,492 | 1,581 | 1,339 – 1,719 | 2,709 | yes |
| 0.15 | 242,668 | 3,814 | 3,410 – 4,205 | 3,160 | yes |
| 0.15 | 977,492 | 3,626 | 3,146 – 4,106 | 2,936 | yes |
| 0.15 | 9,914,492 | 3,571 | 3,018 – 4,077 | 4,657 | yes |
| 0.1 | 242,668 | 12,918 | 11,076 – 16,526 | not reached | no (extrapolated) |
| 0.1 | 977,492 | 11,930 | 10,184 – 14,887 | not reached | no (extrapolated) |
| 0.1 | 9,914,492 | 11,648 | 9,844 – 14,518 | 9,990 | no (extrapolated) |
| 0.05 | 242,668 | 132,275 | 83,913 – 945,169 | not reached | no (extrapolated) |
| 0.05 | 977,492 | 109,663 | 75,418 – 542,723 | not reached | no (extrapolated) |
| 0.05 | 9,914,492 | 103,800 | 72,007 – 294,567 | not reached | no (extrapolated) |

### What to add next (adaptive advice from the fit)

Seed-to-seed spread of a single run is 0.032, so a gain smaller than that needs several seeds to confirm.

| you have (N, P) | predicted error | gain from 2× data | gain from 2× parameters | share of the excess error due to data | advice |
|---|---|---|---|---|---|
| 100, 8,468 | 0.640 | 0.123 | 0.0465 | 85% | more data |
| 100, 977,492 | 0.547 | 0.123 | 0.0004 | 100% | more data |
| 1,000, 8,468 | 0.330 | 0.052 | 0.0465 | 70% | more data |
| 1,000, 242,668 | 0.239 | 0.052 | 0.0017 | 98% | more data |
| 10,000, 8,468 | 0.199 | 0.022 | 0.0465 | 50% | bigger model |
| 10,000, 242,668 | 0.109 | 0.022 | 0.0017 | 96% | more data |
| 10,000, 9,914,492 | 0.105 | 0.022 | 0.0000 | 100% | more data |
| 100,000, 9,914,492 | 0.051 | 0.009 | 0.0000 | 100% | more data |
| 1,000,000, 9,914,492 | 0.028 | 0.004 | 0.0000 | 99% | more data |

## C. Is there a sudden threshold in data? (damped oscillator, 250K-parameter model, 13 data amounts)

| N | 10 | 18 | 30 | 55 | 100 | 180 | 300 | 550 | 1000 | 1800 | 3000 | 5500 | 10000 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| test error | 1.066 | 1.163 | 0.850 | 0.660 | 0.531 | 0.440 | 0.379 | 0.280 | 0.240 | 0.191 | 0.151 | 0.123 | 0.137 |
| seed spread | 0.224 | 0.431 | 0.044 | 0.151 | 0.015 | 0.039 | 0.015 | 0.034 | 0.063 | 0.018 | 0.006 | 0.021 | 0.022 |
| training error | 0.241 | 0.233 | 0.390 | 0.017 | 0.056 | 0.076 | 0.027 | 0.058 | 0.025 | 0.032 | 0.022 | 0.061 | 0.071 |

Power law: error ∝ N^-0.35 (AICc -55.6). Step (logistic in log N) centred at N ≈ 226: AICc -54.4. Largest local slope 0.61 against an average of 0.30. Lower AICc fits better; a difference under about 4 is not decisive.

## D. Four systems (sizes up to 1M here)

**harmonic** — persistence 1.325, ridge at N=10,000 0.497, oracle 0.0095; bits to state its parameters for error 0.1 / 0.03 / 0.01: 2.8 / 3.7 / 4.5

| params \ N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| 8,468 | 0.894 ±0.132 | 0.529 ±0.053 | 0.338 ±0.069 | 0.209 ±0.018 | 0.156 ±0.001 | 0.143 ±0.003 |
| 48,596 | 0.876 ±0.069 | 0.592 ±0.213 | 0.245 ±0.037 | 0.143 ±0.021 | 0.063 ±0.007 | 0.045 ±0.004 |
| 90,316 | 0.858 ±0.080 | 0.505 ±0.083 | 0.284 ±0.044 | 0.138 ±0.013 | 0.055 ±0.001 | 0.029 ±0.005 |
| 242,668 | 0.842 ±0.021 | 0.479 ±0.056 | 0.240 ±0.024 | 0.128 ±0.002 | 0.065 ±0.023 | 0.024 ±0.000 |
| 490,916 | 0.817 ±0.017 | 0.471 ±0.065 | 0.256 ±0.008 | 0.147 ±0.014 | 0.062 ±0.022 | 0.030 ±0.012 |
| 977,492 | 0.890 ±0.061 | 0.534 ±0.083 | 0.251 ±0.032 | 0.138 ±0.000 | 0.046 ±0.008 | 0.019 ±0.004 |

**damped** — persistence 1.101, ridge at N=10,000 0.425, oracle 0.029; bits to state its parameters for error 0.1 / 0.03 / 0.01: 2.5 / 3.5 / 5.3

| params \ N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| 8,468 | 0.906 ±0.072 | 0.564 ±0.002 | 0.418 ±0.005 | 0.289 ±0.033 | 0.252 ±0.003 | 0.238 ±0.029 |
| 48,596 | 0.920 ±0.072 | 0.538 ±0.034 | 0.370 ±0.006 | 0.262 ±0.084 | 0.175 ±0.003 | 0.128 ±0.019 |
| 90,316 | 0.854 ±0.039 | 0.543 ±0.018 | 0.392 ±0.021 | 0.281 ±0.031 | 0.145 ±0.020 | 0.110 ±0.020 |
| 242,668 | 0.850 ±0.044 | 0.531 ±0.015 | 0.379 ±0.015 | 0.240 ±0.063 | 0.151 ±0.006 | 0.137 ±0.022 |
| 490,916 | 0.880 ±0.084 | 0.576 ±0.019 | 0.378 ±0.001 | 0.265 ±0.062 | 0.118 ±0.009 | 0.091 ±0.014 |
| 977,492 | 0.885 ±0.141 | 0.513 ±0.011 | 0.382 ±0.007 | 0.241 ±0.100 | 0.149 ±0.021 | 0.114 ±0.015 |

**diffusion** — persistence 0.254, ridge at N=10,000 0.021, oracle 0.0008; bits to state its parameters for error 0.1 / 0.03 / 0.01: 0.0 / 0.7 / 1.8

| params \ N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| 7,008 | 0.093 ±0.060 | 0.037 ±0.001 | 0.033 ±0.000 | 0.030 ±0.002 | 0.029 ±0.002 | 0.029 ±0.002 |
| 43,632 | 0.081 ±0.046 | 0.035 ±0.005 | 0.020 ±0.004 | 0.012 ±0.001 | 0.010 ±0.001 | 0.010 ±0.000 |
| 245,104 | 0.085 ±0.055 | 0.027 ±0.005 | 0.017 ±0.003 | 0.0054 ±0.000 | 0.0042 ±0.000 | 0.0037 ±0.000 |

**advdiff** — persistence 0.440, ridge at N=10,000 0.123, oracle 0.0081; bits to state its parameters for error 0.1 / 0.03 / 0.01: 1.9 / 3.1 / 5.0

| params \ N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| 7,008 | 0.228 ±0.064 | 0.152 ±0.040 | 0.093 ±0.007 | 0.078 ±0.008 | 0.076 ±0.012 | 0.076 ±0.010 |
| 43,632 | 0.203 ±0.046 | 0.105 ±0.009 | 0.051 ±0.001 | 0.033 ±0.005 | 0.026 ±0.000 | 0.026 ±0.000 |
| 245,104 | 0.195 ±0.044 | 0.101 ±0.013 | 0.045 ±0.003 | 0.022 ±0.001 | 0.014 ±0.000 | 0.013 ±0.001 |
| 991,920 | – | 0.086 | – | 0.020 | – | 0.0093 |

Measured data threshold (trajectories needed by the best size ≤ 1M to reach a test error), next to the system's complexity in bits:

| system | bits for 0.1 | N for error 0.3 | N for 0.1 | N for 0.03 | best error at N=10,000 | bits captured / available per value |
|---|---|---|---|---|---|---|
| harmonic | 2.8 | 231 | 1,379 | 5,373 | 0.019 | 2.86 / 3.36 |
| damped | 2.5 | 658 | 6,490 | not reached | 0.091 | 1.73 / 2.56 |
| diffusion | 0.0 | at or below the smallest N tested | at or below the smallest N tested | 88 | 0.0037 | 4.04 / 5.15 |
| advdiff | 1.9 | at or below the smallest N tested | at or below the smallest N tested | 534 | 0.0093 | 3.37 / 3.48 |

## E. Data quality, diversity and training compute (damped oscillator, 250K parameters)

| setting | 30 | 100 | 300 | 1000 | 3000 | 10000 | oracle floor |
|---|---|---|---|---|---|---|---|
| noise 0.0 | 0.881 | 0.529 | 0.361 | 0.242 | 0.139 | 0.097 | 0.017 |
| noise 0.05 | 0.850 | 0.531 | 0.379 | 0.240 | 0.151 | 0.137 | 0.029 |
| noise 0.2 | 0.816 | 0.562 | 0.414 | 0.314 | 0.212 | 0.179 | 0.121 |
| noise 0.5 | 1.013 | 0.689 | 0.561 | 0.443 | 0.339 | 0.291 | 0.331 |

**Is the threshold a fixed number of Shannon bits?** One noisy observation can carry at most ½·log2(1 + signal variance / noise variance) bits (signal variance 0.78). If a fixed amount of information were what matters, the data needed for one target error, counted in bits, would be the same at every noise level.

| noise | bits per observation (upper bound) | N to reach error 0.4 | total bits at that N | N to reach error 0.3 | total bits at that N |
|---|---|---|---|---|---|
| 0.05 | 4.14 | 252 | 13,338 | 556 | 29,463 |
| 0.2 | 2.18 | 350 | 9,737 | 1,134 | 31,571 |
| 0.5 | 1.02 | 1,521 | 19,829 | 7,849 | 102,344 |

| narrow diversity (¼ of the parameter range), tested on the full range | 0.708 | 0.606 | 0.521 | 0.494 | 0.467 | 0.435 | |

| training steps allowed | N = 1,000 | N = 10,000 |
|---|---|---|
| 300 | 0.372 (used 300) | 0.361 (used 300) |
| 1,000 | 0.272 (used 975) | 0.162 (used 1000) |
| 3,000 | 0.240 (used 1683) | 0.137 (used 1917) |
| 10,000 | 0.242 (used 1575) | 0.141 (used 1925) |

## F. Hard conservation rule on / off (ring systems, 250K parameters)

| system | rule | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|---|
| diffusion | off | 0.085 ±0.055 | 0.027 ±0.005 | 0.017 ±0.003 | 0.0054 ±0.000 | 0.0042 ±0.000 | 0.0037 ±0.000 |
| diffusion | on | 0.064 ±0.037 | 0.028 ±0.009 | 0.017 ±0.003 | 0.0050 ±0.000 | 0.0039 ±0.000 | 0.0036 ±0.000 |
| advdiff | off | 0.195 ±0.044 | 0.101 ±0.013 | 0.045 ±0.003 | 0.022 ±0.001 | 0.014 ±0.000 | 0.013 ±0.001 |
| advdiff | on | 0.169 ±0.035 | 0.108 ±0.020 | 0.049 ±0.011 | 0.023 ±0.003 | 0.013 ±0.000 | 0.011 ±0.000 |

## G. Other abilities at N = 10,000 (largest size run per system)

| system | params | forecast error | unseen parameter range (model / oracle) | 30% of inputs missing | intervention error | 80% interval coverage | width–error rank correlation | AUROC: width flags unseen range |
|---|---|---|---|---|---|---|---|---|
| harmonic | 977,492 | 0.019 | 0.932 / 0.0048 | 0.052 | 0.025 | 78% | 0.52 | 0.65 |
| damped | 9,914,492 | 0.100 | 0.981 / 0.016 | 0.138 | 0.038 | 78% | 0.75 | 0.34 |
| diffusion | 245,104 | 0.0037 | 0.0075 / 0.0003 | 0.0066 | 0.024 | 79% | 0.82 | 0.44 |
| advdiff | 991,920 | 0.0093 | 0.051 / 0.0011 | 0.016 | 0.053 | 80% | 0.88 | 0.69 |

