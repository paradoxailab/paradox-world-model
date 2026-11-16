# ICML T1: the transfer threshold function (generated)

r = calibrated test MAE / TimesFM 2.5's, trained stations (unseen in brackets); mean over seeds.

| Network | arm | 0 mo | 0.5 mo | 1 mo | 2 mo | 4 mo | 8 mo | 16 mo | all | n* |
|---|---|---|---|---|---|---|---|---|---|---|
| Uttar Pradesh | pre | 1.021 (0.992) | 1.020 (0.993) | 1.020 (0.992) | 0.983 (0.974) | 0.969 (0.974) | 0.956 (0.956) | 0.954 (0.961) | 0.938 (0.945) | 2 |
| Uttar Pradesh | scratch | – | 1.554 (1.502) | 1.597 (1.518) | 1.329 (1.323) | 1.319 (1.298) | 1.095 (1.075) | 1.052 (1.033) | 1.004 (1.001) | not reached |
| Haryana | pre | 1.015 (1.241) | 1.014 (1.243) | 1.015 (1.238) | 1.008 (1.187) | 1.005 (1.149) | 0.985 (1.077) | 0.981 (1.001) | 0.968 (0.979) | 8 |
| Haryana | scratch | – | 1.347 (1.322) | 1.547 (4.282) | 1.402 (1.470) | 1.305 (1.514) | 1.143 (1.230) | 1.136 (1.125) | 1.054 (1.065) | not reached |
| Maharashtra | pre | 1.051 (1.204) | 1.048 (1.192) | 1.048 (1.184) | 1.053 (1.181) | 1.040 (1.128) | 1.040 (1.124) | 1.043 (1.124) | 1.015 (1.242) | not reached |
| Maharashtra | scratch | – | 1.415 (1.484) | 1.415 (1.484) | 1.536 (2.826) | 1.383 (2.024) | 1.276 (1.633) | 1.218 (1.603) | 1.175 (1.626) | not reached |
| Karnataka | pre | 1.048 (1.009) | 1.049 (1.008) | 1.051 (1.011) | 1.107 (1.118) | 1.071 (1.105) | 1.007 (1.012) | 1.008 (1.023) | 0.996 (1.007) | all |
| Karnataka | scratch | – | 1.475 (1.566) | 1.478 (1.706) | 1.419 (1.531) | 1.302 (1.448) | 1.190 (1.260) | 1.162 (1.272) | 1.093 (1.149) | not reached |

Scratch law: r = c_X + 2.18 n^-0.080 (misfit x1.057); c[Haryana] = 0.012, c[Karnataka] = 0.041, c[Maharashtra] = 0.087, c[Uttar Pradesh] = 0.001
Transfer law: D_T = 1.04e+04 n^0.094 (28 points; 0 pre-trained runs below every scratch floor)

Rule: confirmed if pre-training lowers n* (the smallest budget at TimesFM 2.5's level on trained stations) on at least 3 of the 4 networks; a network where neither arm reaches it does not count as support. Support: ['Uttar Pradesh', 'Haryana', 'Karnataka']. Result: CONFIRMED
