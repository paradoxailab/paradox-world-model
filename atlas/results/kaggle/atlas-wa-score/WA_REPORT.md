# Atlas v2-W, T-A: all-India test with perfect weather (generated)

| Entry | trained MAE | unseen MAE |
|---|---|---|
| W1 (1M + weather) | 19.86 | 19.92 |
| Atlas-India | 20.99 | 20.86 |
| TimesFM 2.5 | 22.35 | 21.93 |
| Atlas-F | 20.75 | 20.44 |
| Atlas-F2 (W1 + TimesFM 2.5) | 19.66 | 19.52 |

| Pair | trained | unseen | verdict |
|---|---|---|---|
| W1 (1M + weather) vs Atlas-India | -5.38% (p=1.4e-27) | -4.53% (p=4.5e-22) | BEATS |
| W1 (1M + weather) vs TimesFM 2.5 | -11.12% (p=9.3e-47) | -9.15% (p=6.9e-26) | BEATS |
| W1 (1M + weather) vs Atlas-F | -4.27% (p=6.2e-16) | -2.53% (p=2e-06) | BEATS |
| Atlas-F2 (W1 + TimesFM 2.5) vs Atlas-F | -5.23% (p=1e-28) | -4.47% (p=2.7e-23) | BEATS |
| Atlas-F2 (W1 + TimesFM 2.5) vs Atlas-India | -6.33% (p=7.8e-43) | -6.43% (p=7.5e-47) | BEATS |
| Atlas-F2 (W1 + TimesFM 2.5) vs TimesFM 2.5 | -12.02% (p=4.7e-63) | -10.97% (p=3.5e-43) | BEATS |

| Criterion (with perfect weather) | result |
|---|---|
| B1 W1 beats Atlas-India | PASS |
| B2 W1 never loses to TimesFM 2.5 (28 network-tracks) and beats it pooled | FAIL |
| B3 W1 level with or better than Atlas-F | PASS |
| B4 Atlas-F2 beats Atlas-F | PASS |
| network-tracks W1 loses to TimesFM 2.5 | ['Maharashtra U', 'Kerala S'] |
