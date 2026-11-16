# ICML L1: leave one network out (generated)

| Network | adapted (S / U) | not adapted, P (S / U) | TimesFM 2.5 (S / U) | Atlas-India, all 14 (S / U) | adapted vs TimesFM 2.5 (S / U) | verdict |
|---|---|---|---|---|---|---|
| Uttar Pradesh | 21.45 / 23.14 | 21.76 / 23.29 | 22.78 / 24.32 | 20.89 / 22.46 | -5.8% (p=2.3e-07) / -4.8% (p=0.00025) | BEATS |
| Haryana | 24.93 / 22.85 | 25.31 / 23.17 | 25.72 / 23.20 | 24.32 / 22.31 | -3.1% (p=0.00095) / -1.5% (p=0.2) | level |
| Maharashtra | 19.86 / 28.28 | 20.39 / 25.44 | 19.45 / 22.25 | 19.68 / 24.92 | +2.1% (p=0.0027) / +27.1% (p=1.8e-19) | LOSES |
| Karnataka | 8.97 / 9.68 | 9.26 / 9.44 | 8.98 / 9.43 | 8.87 / 9.20 | -0.1% (p=0.96) / +2.7% (p=0.029) | LOSES |

Rule: confirmed if the adapted model beats TimesFM 2.5 on at least 3 of the 4 networks and loses on none. Result: NOT CONFIRMED
