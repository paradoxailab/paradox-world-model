"""Real-time data for PWM-W (v0.9): the METAR league's Indian airport stations from 2021-01-01 up to the latest
report, from the Iowa Environmental Mesonet (free, no key), plus 24 empty hours to forecast.

It starts from the archived league file (WX_METAR.npz) and appends IEM reports from 3 days before its end up to now,
with exactly the same hourly rule and quality limits (tools/fetch_metar.hourly). Where the two overlap, the archived
value is kept.

  python tools/fetch_live_metar.py          # -> $PW_RAW/WX_LIVE.npz
"""
import datetime as dt, io, os, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.fetch_metar import IEM, VARS, get, hourly

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))


def fetch_range(sid, d0, d1):
    import pandas as pd
    p = [("station", sid)] + [("data", v) for v in ("tmpf", "dwpf", "relh", "sknt", "drct", "alti", "mslp", "vsby")]
    p += [("year1", d0.year), ("month1", d0.month), ("day1", d0.day), ("year2", d1.year), ("month2", d1.month),
          ("day2", d1.day), ("tz", "Etc/UTC"), ("format", "onlycomma"), ("latlon", "no"), ("missing", "M"),
          ("trace", "T"), ("direct", "no"), ("report_type", "3"), ("report_type", "4")]
    txt = get(f"{IEM}/cgi-bin/request/asos.py", p)
    df = pd.read_csv(io.StringIO(txt), na_values=["M", "T", ""], low_memory=False)
    return df if len(df) else None


def main():
    z = np.load(os.path.join(RAW, "WX_METAR.npz"), allow_pickle=False)
    assert [str(v) for v in z["vars"]] == VARS
    start = np.datetime64(str(z["start"])).astype("datetime64[h]")
    Xh = z["X"]
    now = np.datetime64(dt.datetime.now(dt.timezone.utc).replace(tzinfo=None), "h")
    T = int((now - start).astype(int)) + 1 + 24                      # up to the current hour, then 24 h to forecast
    X = np.full((T, Xh.shape[1], Xh.shape[2]), np.nan, np.float32)
    X[:min(len(Xh), T)] = Xh[:T]
    d0 = (start + np.timedelta64(len(Xh), "h") - np.timedelta64(72, "h")).astype("datetime64[D]").astype(object)
    d1 = (now.astype("datetime64[D]") + np.timedelta64(1, "D")).astype(object)
    s_iso = str(start.astype("datetime64[D]"))
    for j, sid in enumerate([str(s) for s in z["ids"]]):
        df = fetch_range(sid, d0, d1)
        if df is None:
            print(f"  {sid}: no recent reports", flush=True)
            continue
        Xn = hourly(df, s_iso, T)
        fill = np.isnan(X[:, j]) & np.isfinite(Xn)
        X[:, j][fill] = Xn[fill]
        last = np.where(np.isfinite(Xn[:, 0]))[0]
        print(f"  {sid}: {len(df)} recent reports, latest hourly temperature at "
              f"{start + np.timedelta64(int(last[-1]), 'h') if len(last) else 'none'} UTC", flush=True)
        time.sleep(1)
    np.savez_compressed(os.path.join(RAW, "WX_LIVE.npz"), X=X, vars=z["vars"], stations=z["stations"], ids=z["ids"],
                        lat=z["lat"], lon=z["lon"], elev=z["elev"], start=z["start"], tz=z["tz"],
                        fetched_utc=np.array(str(now)))
    print(f"WX_LIVE: {T} hours from {start} to {start + np.timedelta64(T - 1, 'h')} UTC (last 24 h = forecast "
          f"window), {X.shape[1]} stations", flush=True)


if __name__ == "__main__":
    main()
