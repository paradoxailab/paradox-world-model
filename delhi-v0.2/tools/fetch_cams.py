"""CAMS (ECMWF's Copernicus Atmosphere Monitoring Service) global air-quality forecasts of PM2.5 at every Delhi
station: the operational model the air-quality league must beat. Source: Open-Meteo Air Quality API, domain
cams_global (0.4 deg, archived forecasts from August 2022; free for non-commercial use, no key).

Open-Meteo's archive keeps the most recent forecast for each hour, so this opponent mostly uses runs issued close to
the hour it predicts. That is generous to CAMS, and it is labelled so in the results.
Station positions: located by name with OpenStreetMap's Nominatim (same rule as delhi-v0.3/tools/fetch_cpcb_wx.py);
a station that cannot be placed is left out of this comparison.

  python tools/fetch_cams.py      # -> data/raw/DELHI_cams.npz  (hourly PM2.5, Indian time, [T, N])
"""
import datetime as dt, json, os, re, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
API = "https://air-quality-api.open-meteo.com/v1/air-quality"
UA = {"User-Agent": "paradox-world-model-data-builder"}
BOX = (28.35, 28.95, 76.80, 77.45)


def get(url, params, tries=10):
    import requests
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=300, headers=UA)
            if r.status_code == 429:
                time.sleep(65)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"    retry {k + 1}: {str(e)[:150]}", flush=True)
            time.sleep(min(60, 5 * (k + 1)))
    return None


def clean(name):
    n = re.split(r"\s+-\s+", str(name))[0]
    return re.sub(r",?\s*(New\s+)?Delhi\b.*$", "", n, flags=re.I).strip(" ,")


def geocode(name):
    base = clean(name)
    for q in dict.fromkeys([f"{base}, Delhi, India", f"{base.split(',')[0].split('(')[0].strip()}, Delhi, India",
                            f"{' '.join(base.split()[:2])}, Delhi, India"]):
        j = get("https://nominatim.openstreetmap.org/search", dict(q=q, format="json", limit=5, countrycodes="in"))
        time.sleep(1.1)
        for h in j or []:
            la, lo = float(h["lat"]), float(h["lon"])
            if BOX[0] <= la <= BOX[1] and BOX[2] <= lo <= BOX[3]:
                return la, lo
    return None


def main():
    z = np.load(os.path.join(RAW, "DELHI.npz"))
    st = [str(s) for s in z["stations"]]
    start = str(z["start"])[:10]
    T = z["X"].shape[0]
    end = (dt.date.fromisoformat(start) + dt.timedelta(hours=T + 48)).isoformat()
    s0 = dt.datetime.fromisoformat(start)
    P = np.full((T + 48, len(st)), np.nan, np.float32)
    coords = {}
    for i, s in enumerate(st):
        g = geocode(s)
        coords[s] = g
        if not g:
            print(f"  {s}: not placed", flush=True)
            continue
        j = get(API, dict(latitude=round(g[0], 3), longitude=round(g[1], 3), hourly="pm2_5", domains="cams_global",
                          start_date=start, end_date=end, timezone="Asia/Kolkata"))
        if not j:
            continue
        h = j.get("hourly", {})
        for ts, v in zip(h.get("time", []), h.get("pm2_5", [])):
            k = int((dt.datetime.fromisoformat(ts) - s0).total_seconds() // 3600)
            if 0 <= k < len(P) and v is not None:
                P[k, i] = v
        print(f"  {s}: {g[0]:.4f}, {g[1]:.4f}; CAMS PM2.5 coverage {100 * np.isfinite(P[:T, i]).mean():.0f}%", flush=True)
    np.savez_compressed(os.path.join(RAW, "DELHI_cams.npz"), pm25=P, stations=np.array(st),
                        start=np.array(start + " 00:00:00"), coords=np.array(json.dumps(coords)))
    print(f"DELHI_cams: {P.shape} written", flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main()
