"""Method check for run_lockdown.py on MADE-UP data with a planted effect (not a result about Delhi).

Writes a fake DELHI_LONG.npz: 12 stations, 2017-06 .. 2020-12, PM2.5 = station level x season x hour-of-day /
(0.4 + wind) x noise, with every pollutant multiplied by 0.6 from 2020-03-25 to 2020-05-31 (a planted -40%).
The weather is random with multi-day persistence, so 2019 and 2020 differ and a plain year-on-year comparison is off.

  PW_RAW=/tmp/fake python tools/planted_lockdown_check.py && PW_RAW=/tmp/fake python run_lockdown.py --steps 1600 --size 60000

Recorded on 2026-11-13 (2 CPU cores, 2 minutes): recovered -39.4%, -40.8%, -40.9%, -41.0% for the four phases and
-40.3% overall; placebo bias +5.0%; "just before" -0.1% (-2.0% .. +2.8%). The plain comparisons on the same data
gave -34.7% (phase 1 against 2019) and -47.0% (all lockdown against 2019).
"""
import os

import numpy as np

RAW = os.environ.get("PW_RAW", "data/raw")


def main(seed=3, n=12):
    rng = np.random.default_rng(seed)
    start, end = np.datetime64("2017-06-01T00"), np.datetime64("2021-01-01T00")
    T = int((end - start).astype(int))
    t = start + np.arange(T)
    h = t.astype(int) % 24
    doy = (t - t.astype("datetime64[Y]")).astype("timedelta64[D]").astype(int)
    w, x = np.zeros(T), 0.0
    for i in range(T):
        x = 0.98 * x + rng.normal(0, 0.2); w[i] = x
    ws_city = np.exp(0.6 * w) * 1.2
    at_city = 25 + 10 * np.sin(2 * np.pi * (doy - 110) / 365.25) + 5 * np.sin(2 * np.pi * (h - 9) / 24)
    season = 1 + 0.6 * np.cos(2 * np.pi * (doy - 10) / 365.25)
    diurnal = 1 + 0.25 * np.cos(2 * np.pi * (h - 8) / 24)
    lock = np.where((t >= np.datetime64("2020-03-25T00")) & (t < np.datetime64("2020-06-01T00")), 0.6, 1.0)
    level = rng.uniform(60, 140, n)
    pm = level[None] * (season * diurnal * lock / (0.4 + ws_city))[:, None] * np.exp(rng.normal(0, 0.25, (T, n)))
    ws = ws_city[:, None] * np.exp(rng.normal(0, 0.15, (T, n)))
    at = at_city[:, None] + rng.normal(0, 0.7, (T, n))
    names = ["PM2.5", "PM10", "NO2", "Ozone", "CO", "SO2", "NH3", "NO", "AT", "RH", "WS", "WD", "SR", "BP"]
    X = np.stack([pm, pm * 1.9, pm * 0.4, 30 + rng.normal(0, 5, (T, n)), pm / 80, 10 + rng.normal(0, 2, (T, n)),
                  20 + rng.normal(0, 4, (T, n)), pm * 0.1, at, 60 + rng.normal(0, 10, (T, n)), ws, rng.uniform(0, 360, (T, n)),
                  np.maximum(0, 600 * np.sin(2 * np.pi * (h - 6) / 24))[:, None] + 0 * pm, 982 + rng.normal(0, 2, (T, n))], -1).astype(np.float32)
    X[rng.random(X.shape) < 0.12] = np.nan
    os.makedirs(RAW, exist_ok=True)
    np.savez_compressed(os.path.join(RAW, "DELHI_LONG.npz"), X=X, vars=np.array(names), stations=np.array([f"S{j}" for j in range(n)]),
                        start=np.array("2017-06-01 00:00:00"), league_offset=np.array(T - 17544))
    print("made-up DELHI_LONG.npz with a planted -40% from 2020-03-25 to 2020-05-31:", X.shape)


if __name__ == "__main__":
    main()
