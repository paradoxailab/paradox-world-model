# Atlas v0.2: fixing the three failures — measured results

103 training runs (250K-parameter models unless stated; 2 seeds; both variants trained with the same protocol, early-stopping patience 10).

*plain* = Atlas v0.1. *ID* = Atlas with in-context identification of the dynamics.

## harmonic

References: oracle 0.0095 (seen range), 0.0048 (unseen range); identification with no training 0.661 (seen), 0.044 (unseen).

| trajectories N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| seen range, plain | 0.842 ±0.021 | 0.479 ±0.056 | 0.240 ±0.024 | 0.130 ±0.000 | 0.050 ±0.002 | 0.024 ±0.000 |
| seen range, ID | 0.246 ±0.005 | 0.226 ±0.126 | 0.138 ±0.003 | 0.091 ±0.023 | 0.065 ±0.002 | 0.048 ±0.004 |
| unseen range, plain | 2.427 | 2.373 | 2.016 | 1.327 | 1.111 | 0.929 |
| unseen range, ID | 0.182 | 0.058 | 0.074 | 0.040 | 0.080 | 0.038 |
| unseen range, ID + fallback when flagged | 0.082 | 0.038 | 0.038 | 0.039 | 0.037 | 0.038 |
| seen range, ID + fallback when flagged | 0.362 | 0.254 | 0.277 | 0.158 | 0.158 | 0.175 |
| intervention error, plain | 0.733 | 0.471 | 0.262 | 0.160 | 0.080 | 0.029 |
| intervention error, ID | 0.184 | 0.082 | 0.078 | 0.049 | 0.039 | 0.032 |
| 30% inputs missing, plain | 0.926 | 0.564 | 0.330 | 0.170 | 0.088 | 0.063 |
| 30% inputs missing, ID | 0.985 | 0.907 | 0.739 | 0.627 | 0.422 | 0.439 |
| flag AUROC: interval width, plain | 0.433 | 0.509 | 0.538 | 0.603 | 0.645 | 0.704 |
| flag AUROC: latent distance, plain | 0.440 | 0.532 | 0.574 | 0.648 | 0.704 | 0.743 |
| flag AUROC: identified dynamics, ID | 0.792 | 0.883 | 0.883 | 0.925 | 0.940 | 0.951 |
| unseen cases flagged, ID | 0.422 | 0.338 | 0.571 | 0.632 | 0.701 | 0.762 |
| false alarms on seen cases, ID | 0.164 | 0.059 | 0.087 | 0.040 | 0.039 | 0.040 |
| seen-range error of flagged cases, ID | 0.846 | 2.489 | 0.731 | 0.478 | 0.719 | 0.373 |
| seen-range error of unflagged cases, ID | 0.153 | 0.093 | 0.086 | 0.076 | 0.039 | 0.034 |
| 80% interval coverage, ID | 0.627 | 0.686 | 0.786 | 0.794 | 0.758 | 0.781 |
| training steps used, plain | 575.000 | 925.000 | 1525.000 | 2500.000 | 2975.000 | 3000.000 |
| training steps used, ID | 950.000 | 1325.000 | 1325.000 | 1625.000 | 3000.000 | 2925.000 |
| CPU seconds per run, plain | 4.300 | 8.300 | 14.400 | 24.100 | 26.950 | 28.700 |
| CPU seconds per run, ID | 30.800 | 46.250 | 48.800 | 54.500 | 113.450 | 111.650 |

## damped

References: oracle 0.029 (seen range), 0.016 (unseen range); identification with no training 0.486 (seen), 0.109 (unseen).

| trajectories N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| seen range, plain | 0.852 ±0.062 | 0.529 ±0.021 | 0.378 ±0.021 | 0.237 ±0.086 | 0.149 ±0.007 | 0.107 ±0.018 |
| seen range, ID | 0.395 ±0.072 | 0.449 ±0.106 | 0.196 ±0.018 | 0.192 ±0.084 | 0.115 ±0.028 | 0.098 ±0.043 |
| unseen range, plain | 5.049 | 3.569 | 3.024 | 1.718 | 1.290 | 1.181 |
| unseen range, ID | 0.573 | 0.158 | 0.557 | 0.155 | 0.071 | 0.090 |
| unseen range, ID + fallback when flagged | 0.248 | 0.114 | 0.091 | 0.101 | 0.084 | 0.090 |
| seen range, ID + fallback when flagged | 0.368 | 0.351 | 0.233 | 0.164 | 0.125 | 0.169 |
| intervention error, plain | 0.632 | 0.503 | 0.317 | 0.216 | 0.082 | 0.046 |
| intervention error, ID | 0.137 | 0.084 | 0.067 | 0.062 | 0.038 | 0.043 |
| 30% inputs missing, plain | 0.934 | 0.566 | 0.423 | 0.266 | 0.190 | 0.166 |
| 30% inputs missing, ID | 1.297 | 1.138 | 1.232 | 0.894 | 0.499 | 0.656 |
| flag AUROC: interval width, plain | 0.359 | 0.349 | 0.396 | 0.333 | 0.346 | 0.381 |
| flag AUROC: latent distance, plain | 0.403 | 0.409 | 0.442 | 0.504 | 0.539 | 0.584 |
| flag AUROC: identified dynamics, ID | 0.802 | 0.876 | 0.906 | 0.922 | 0.928 | 0.937 |
| unseen cases flagged, ID | 0.347 | 0.326 | 0.617 | 0.562 | 0.596 | 0.680 |
| false alarms on seen cases, ID | 0.148 | 0.069 | 0.082 | 0.045 | 0.048 | 0.053 |
| seen-range error of flagged cases, ID | 0.617 | 4.076 | 1.042 | 2.666 | 0.540 | 0.276 |
| seen-range error of unflagged cases, ID | 0.239 | 0.176 | 0.125 | 0.081 | 0.094 | 0.088 |
| 80% interval coverage, ID | 0.596 | 0.693 | 0.695 | 0.748 | 0.794 | 0.815 |
| training steps used, plain | 575.000 | 925.000 | 1050.000 | 2150.000 | 3000.000 | 3000.000 |
| training steps used, ID | 925.000 | 950.000 | 1500.000 | 1150.000 | 2350.000 | 2175.000 |
| CPU seconds per run, plain | 4.400 | 8.550 | 9.750 | 20.150 | 27.250 | 28.300 |
| CPU seconds per run, ID | 30.400 | 36.000 | 53.550 | 41.450 | 88.250 | 80.050 |

## diffusion

References: oracle 0.0008 (seen range), 0.0003 (unseen range); identification with no training 1.598 (seen), 0.089 (unseen).

| trajectories N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| seen range, plain | 0.080 ±0.062 | 0.027 ±0.005 | 0.014 ±0.003 | 0.0054 ±0.000 | 0.0042 ±0.000 | 0.0037 ±0.000 |
| seen range, ID | 0.031 ±0.007 | 0.137 ±0.103 | 0.045 ±0.009 | 0.011 ±0.001 | 0.0093 ±0.001 | 0.0096 ±0.001 |
| unseen range, plain | 0.163 | 0.044 | 0.023 | 0.0086 | 0.0081 | 0.0075 |
| unseen range, ID | 0.043 | 0.137 | 0.035 | 0.010 | 0.0077 | 0.0083 |
| unseen range, ID + fallback when flagged | 0.057 | 0.128 | 0.023 | 0.019 | 0.017 | 0.016 |
| seen range, ID + fallback when flagged | 0.053 | 0.138 | 0.040 | 0.020 | 0.014 | 0.015 |
| intervention error, plain | 0.214 | 0.087 | 0.081 | 0.044 | 0.027 | 0.024 |
| intervention error, ID | 0.067 | 0.046 | 0.035 | 0.025 | 0.024 | 0.024 |
| 30% inputs missing, plain | 0.087 | 0.032 | 0.017 | 0.0082 | 0.0071 | 0.0066 |
| 30% inputs missing, ID | 0.194 | 0.073 | 0.052 | 0.203 | 0.023 | 0.050 |
| flag AUROC: interval width, plain | 0.569 | 0.515 | 0.394 | 0.408 | 0.437 | 0.436 |
| flag AUROC: latent distance, plain | 0.495 | 0.469 | 0.481 | 0.475 | 0.467 | 0.490 |
| flag AUROC: identified dynamics, ID | 0.583 | 0.637 | 0.619 | 0.632 | 0.653 | 0.662 |
| unseen cases flagged, ID | 0.252 | 0.011 | 0.110 | 0.123 | 0.099 | 0.096 |
| false alarms on seen cases, ID | 0.207 | 0.0050 | 0.067 | 0.069 | 0.040 | 0.045 |
| seen-range error of flagged cases, ID | 0.025 | 0.016 | 0.205 | 0.016 | 0.011 | 0.011 |
| seen-range error of unflagged cases, ID | 0.032 | 0.137 | 0.033 | 0.011 | 0.0093 | 0.0095 |
| 80% interval coverage, ID | 0.731 | 0.790 | 0.789 | 0.780 | 0.778 | 0.786 |
| training steps used, plain | 1450.000 | 1425.000 | 2000.000 | 2000.000 | 2000.000 | 2000.000 |
| training steps used, ID | 675.000 | 875.000 | 1200.000 | 2000.000 | 2000.000 | 1850.000 |
| CPU seconds per run, plain | 35.250 | 67.200 | 92.400 | 92.050 | 96.350 | 99.850 |
| CPU seconds per run, ID | 46.500 | 107.550 | 146.550 | 245.400 | 250.800 | 242.200 |

## advdiff

References: oracle 0.0081 (seen range), 0.0011 (unseen range); identification with no training 0.106 (seen), 0.081 (unseen).

| trajectories N | 30 | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|---|
| seen range, plain | 0.195 ±0.044 | 0.089 ±0.003 | 0.044 ±0.001 | 0.022 ±0.001 | 0.014 ±0.000 | 0.013 ±0.001 |
| seen range, ID | 0.152 ±0.119 | 0.023 ±0.001 | 0.016 ±0.001 | 0.013 ±0.000 | 0.042 ±0.040 | 0.019 ±0.010 |
| unseen range, plain | 0.312 | 0.176 | 0.117 | 0.096 | 0.085 | 0.066 |
| unseen range, ID | 0.039 | 0.020 | 0.014 | 0.010 | 0.012 | 0.0086 |
| unseen range, ID + fallback when flagged | 0.050 | 0.044 | 0.036 | 0.024 | 0.028 | 0.024 |
| seen range, ID + fallback when flagged | 0.047 | 0.035 | 0.022 | 0.018 | 0.023 | 0.018 |
| intervention error, plain | 0.462 | 0.331 | 0.182 | 0.107 | 0.069 | 0.058 |
| intervention error, ID | 0.091 | 0.054 | 0.043 | 0.039 | 0.046 | 0.035 |
| 30% inputs missing, plain | 0.219 | 0.099 | 0.055 | 0.033 | 0.023 | 0.021 |
| 30% inputs missing, ID | 0.172 | 0.078 | 0.054 | 0.033 | 0.077 | 0.030 |
| flag AUROC: interval width, plain | 0.523 | 0.646 | 0.737 | 0.711 | 0.698 | 0.682 |
| flag AUROC: latent distance, plain | 0.491 | 0.530 | 0.536 | 0.545 | 0.567 | 0.558 |
| flag AUROC: identified dynamics, ID | 0.813 | 0.749 | 0.770 | 0.763 | 0.761 | 0.769 |
| unseen cases flagged, ID | 0.440 | 0.417 | 0.287 | 0.214 | 0.247 | 0.234 |
| false alarms on seen cases, ID | 0.114 | 0.145 | 0.070 | 0.050 | 0.061 | 0.053 |
| seen-range error of flagged cases, ID | 0.943 | 0.038 | 0.031 | 0.037 | 0.495 | 0.155 |
| seen-range error of unflagged cases, ID | 0.038 | 0.021 | 0.014 | 0.012 | 0.015 | 0.011 |
| 80% interval coverage, ID | 0.733 | 0.668 | 0.768 | 0.765 | 0.776 | 0.785 |
| training steps used, plain | 650.000 | 1600.000 | 1850.000 | 2000.000 | 2000.000 | 2000.000 |
| training steps used, ID | 1075.000 | 1325.000 | 1450.000 | 1900.000 | 1025.000 | 2000.000 |
| CPU seconds per run, plain | 14.050 | 68.650 | 76.800 | 85.700 | 91.050 | 102.400 |
| CPU seconds per run, ID | 72.550 | 156.400 | 184.800 | 225.350 | 123.600 | 262.400 |

## Does the structural prior lower the data needed?

Trajectories needed to reach a test error in the seen range (log-log interpolation of the mean curve).

| system | target error | plain | ID | ratio |
|---|---|---|---|---|
| harmonic | 0.3 | 210 | ≤ 30 | – |
| harmonic | 0.1 | 1,356 | 765 | 1.8× |
| harmonic | 0.03 | 6,887 | not reached by 10,000 | – |
| damped | 0.3 | 545 | 171 | 3.2× |
| damped | 0.1 | not reached by 10,000 | 8,473 | – |
| diffusion | 0.3 | ≤ 30 | ≤ 30 | – |
| diffusion | 0.1 | ≤ 30 | ≤ 30 | – |
| diffusion | 0.03 | 88 | 427 | 0.2× |
| diffusion | 0.01 | 449 | 2,017 | 0.2× |
| advdiff | 0.3 | ≤ 30 | ≤ 30 | – |
| advdiff | 0.1 | 83 | 39 | 2.1× |
| advdiff | 0.03 | 587 | 85 | 6.9× |

## Model size with identification (damped oscillator, seed 0)

| parameters | N=100 seen / unseen | N=1,000 seen / unseen | N=10,000 seen / unseen |
|---|---|---|---|
| 43,516 | 0.431 / 0.125 | 0.125 / 0.076 | 0.088 / 0.060 |
| 245,980 | 0.524 / 0.180 | 0.133 / 0.218 | 0.128 / 0.099 |
| 983,532 | 0.664 / 0.253 | 0.288 / 0.114 | 0.089 / 0.101 |
| 9,932,412 | – | – | 0.098 / 0.089 |

