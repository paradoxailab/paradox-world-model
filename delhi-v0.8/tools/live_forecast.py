"""Real-time PWM-W forecast (v0.9) for the Indian airport stations, with a running, honest score.

1. The forecast starts at the hour after the latest temperature report. PWM-W gives the 10/50/90% quantiles of 2 m
   temperature, humidity and 10 m wind for the next 24 hours, from observations only (no global model inside).
2. For comparison, the global models' current forecasts for the same stations and hours come from Open-Meteo (free,
   no key): ECMWF IFS 0.25, ECMWF AIFS, NOAA GFS and DWD ICON. They are shown raw, as issued.
3. Every forecast is appended to live_log.csv. A previous log, if attached, is carried forward, and every logged
   forecast whose hour has now been observed is scored. The score covers only hours forecast before they happened.

  python tools/live_forecast.py     # -> $PW_OUT/live_forecast.json, live_log.csv, live_scores.json
"""
import csv, json, os, sys

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pw.leagues import TARGETS
from pw.wdata import Wx, H
from pw.wmodel import WxModel
from pw import wtrain as WT

OUT = os.environ.get("PW_OUT", os.path.join(ROOT, "out"))
OM = {"ECMWF IFS 0.25": "ecmwf_ifs025", "ECMWF AIFS": "ecmwf_aifs025_single", "NOAA GFS": "gfs_seamless",
      "DWD ICON": "icon_seamless"}
OMV = {"AT": "temperature_2m", "RH": "relative_humidity_2m", "WS": "wind_speed_10m"}
FIELDS = ["issued_utc", "station", "target_utc", "lead_h", "var", "source", "p10", "p50", "p90"]


def open_meteo(lat, lon):
    import requests
    p = {"latitude": ",".join(f"{x:.4f}" for x in lat), "longitude": ",".join(f"{x:.4f}" for x in lon),
         "hourly": ",".join(OMV.values()), "models": ",".join(OM.values()), "wind_speed_unit": "ms",
         "timezone": "GMT", "past_days": 1, "forecast_days": 3}
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=p, timeout=120,
                     headers={"User-Agent": "paradox-world-model-live"})
    r.raise_for_status()
    j = r.json()
    return j if isinstance(j, list) else [j]


def main():
    os.makedirs(OUT, exist_ok=True)
    D = Wx("LIVE")
    pack = torch.load(os.path.join(OUT, "live_models.pt"), map_location="cpu", weights_only=False)
    assert pack["keep"] == D.keep.tolist(), "live data and models disagree on stations; retrain"
    models = []
    for st in pack["states"]:
        m = WxModel(**pack["cfg"]).to(WT.DEV)
        m.load_state_dict(st)
        models.append(m)
    seen = np.where(np.isfinite(D.Y[:, :, 0]).any(1))[0]
    o = int(seen[-1]) + 1                                            # first hour not yet observed anywhere
    assert o + H <= D.T, "no room for 24 forecast hours"
    q = np.mean([WT.predict(m, D, np.array([o]))[0][0] for m in models], 0)          # [n, K, H, 3]
    issued = str(D.dates[o])
    hours = [str(D.dates[o + i]) for i in range(H)]
    fc = {"issued_utc": issued, "model": "PWM-W v0.9 (pure: observations only)",
          "trained_until_utc": pack["trained_until_utc"], "stations": {}}
    rows = []
    for j, sname in enumerate(D.stations):
        last = {v: (float(D.Y[o - 1, j, k]) if np.isfinite(D.Y[o - 1, j, k]) else None) for k, v in enumerate(TARGETS)}
        st = {"lat": float(D.lat[j]), "lon": float(D.lon[j]), "last_observed": last, "hours_utc": hours, "pwm": {},
              "global": {}}
        for k, v in enumerate(TARGETS):
            st["pwm"][v] = {"p10": q[j, k, :, 0].round(2).tolist(), "p50": q[j, k, :, 1].round(2).tolist(),
                            "p90": q[j, k, :, 2].round(2).tolist()}
            for i in range(H):
                rows.append([issued, sname, hours[i], i + 1, v, "PWM-W"] + [round(float(x), 3) for x in q[j, k, i]])
        fc["stations"][sname] = st
    try:
        om = open_meteo(D.lat, D.lon)
        for j, sname in enumerate(D.stations):
            hh = om[j]["hourly"]
            tix = {t[:13]: i for i, t in enumerate(hh["time"])}
            for gname, mid in OM.items():
                for v, var in OMV.items():
                    col = hh.get(f"{var}_{mid}")
                    if col is None:
                        continue
                    vals = [col[tix[h[:13]]] if h[:13] in tix else None for h in hours]
                    fc["stations"][sname]["global"].setdefault(gname, {})[v] = vals
                    for i, x in enumerate(vals):
                        if x is not None:
                            rows.append([issued, sname, hours[i], i + 1, v, gname, "", round(float(x), 3), ""])
    except Exception as e:
        fc["global_error"] = str(e)[:300]
        print(f"Open-Meteo: {e}", flush=True)
    json.dump(fc, open(os.path.join(OUT, "live_forecast.json"), "w"), indent=1)

    # carry the log forward and score every matured forecast
    log_p = os.path.join(OUT, "live_log.csv")                       # an earlier log is copied here by the runner
    prev = []
    if os.path.exists(log_p):
        prev = list(csv.reader(open(log_p)))[1:]
    keyset = {tuple(r[:6]) for r in prev}
    allrows = prev + [[str(x) for x in r] for r in rows if tuple(str(x) for x in r[:6]) not in keyset]
    with open(log_p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(FIELDS); w.writerows(allrows)
    t_ix = {str(d)[:13]: i for i, d in enumerate(D.dates[:D.T])}
    sidx = {s: j for j, s in enumerate(D.stations)}
    err = {}
    for r in allrows:
        issued_r, sname, tgt, lead, v, src, p10, p50, p90 = r
        if sname not in sidx or tgt[:13] not in t_ix or not p50:
            continue
        i = t_ix[tgt[:13]]
        if i >= o:                                                   # not yet observed
            continue
        y = D.Y[i, sidx[sname], TARGETS.index(v)]
        if np.isfinite(y):
            err.setdefault(v, {}).setdefault(src, []).append(abs(float(p50) - float(y)))
    scores = {v: {src: {"MAE": round(float(np.mean(e)), 3), "n": len(e)} for src, e in d.items()} for v, d in err.items()}
    json.dump({"as_of_utc": issued, "note": "MAE over every logged forecast hour that has since been observed",
               "scores": scores}, open(os.path.join(OUT, "live_scores.json"), "w"), indent=1)
    print(f"LIVE forecast issued {issued} UTC for {len(D.stations)} stations; log {len(allrows)} rows", flush=True)
    for j, sname in enumerate(D.stations):
        p = fc["stations"][sname]["pwm"]
        print(f"  {sname}: next 24 h temperature {min(p['AT']['p50']):.1f}..{max(p['AT']['p50']):.1f} C, humidity "
              f"{min(p['RH']['p50']):.0f}..{max(p['RH']['p50']):.0f} %, wind {min(p['WS']['p50']):.1f}.."
              f"{max(p['WS']['p50']):.1f} m/s", flush=True)
    for v, d in scores.items():
        print(f"LIVE-SCORE {v}: " + "; ".join(f"{s} {x['MAE']} (n={x['n']})" for s, x in d.items()), flush=True)


if __name__ == "__main__":
    main()
