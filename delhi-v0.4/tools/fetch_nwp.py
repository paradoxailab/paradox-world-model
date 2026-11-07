"""The global forecast systems' real archived forecasts at every station of a weather league (Open-Meteo
Previous Runs API; free for non-commercial use, no key). Nothing here is used to train the pure PWM-W model.

  score   every model in pw/leagues.NWP_MODELS, the latest run (day0) and the runs 24 h / 48 h before each valid
          time (day1, day2), temperature / humidity / wind speed, from 45 days before TEST to its end
          (45 days so the trailing bias correction has history on the first test day).
  hybrid  pw/leagues.HYBRID_INPUTS, day1 and day2 runs, from 2024-01-01 to the end of the data: inputs of the
          separately reported hybrid entries (each forecast hour uses only a run published before the origin).

  python tools/fetch_nwp.py --league METAR          # -> data/raw/NWP_METAR.npz
Requests are cached under data/raw/nwp_cache, so an interrupted run resumes where it stopped.
"""
import argparse, datetime as dt, hashlib, json, os, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pw.leagues import LEAGUES, NWP_MODELS, SUFFIXES, HYBRID_INPUTS, HYB_SUFFIXES, TARGETS, NWP_VARS, bounds

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
API = "https://previous-runs-api.open-meteo.com/v1/forecast"
UA = {"User-Agent": "paradox-world-model-data-builder"}


class DailyLimit(Exception):
    pass


def get(params, tries=12):
    import requests
    for k in range(tries):
        try:
            r = requests.get(API, params=params, timeout=300, headers=UA)
            if r.status_code == 429:
                why = r.text[:200]
                if "aily" in why:
                    raise DailyLimit(why)
                wait = 900 if "ourly" in why else 65
                print(f"    rate limit ({why[:80]}), waiting {wait}s", flush=True)
                time.sleep(wait)
                continue
            if r.status_code == 400:
                return {"error": True, "reason": r.text[:300]}
            r.raise_for_status()
            return r.json()
        except DailyLimit:
            raise
        except Exception as e:
            print(f"    retry {k + 1}/{tries}: {str(e)[:160]}", flush=True)
            if k == tries - 1:
                raise
            time.sleep(min(120, 10 * (k + 1)))


def resolve(cands, la, lo, day, tz):
    """First identifier that returns real temperatures around `day`."""
    for m in cands:
        j = get(dict(latitude=la, longitude=lo, hourly="temperature_2m,temperature_2m_previous_day1", models=m,
                     start_date=day, end_date=(dt.date.fromisoformat(day) + dt.timedelta(days=2)).isoformat(),
                     timezone=tz, wind_speed_unit="ms"))
        if isinstance(j, list):
            j = j[0]
        if j.get("error"):
            print(f"    {m}: {j.get('reason', '')[:120]}", flush=True)
            continue
        h = j.get("hourly", {})
        vals = [x for k, v in h.items() if k.startswith("temperature_2m") for x in v if x is not None]
        print(f"    {m}: {len(vals)} values", flush=True)
        if vals:
            return m
    return None


def chunks(a, b, days=91):
    out, s = [], a
    while s <= b:
        e = min(b, s + dt.timedelta(days=days - 1))
        out.append((s, e)); s = e + dt.timedelta(days=1)
    return out


def fetch(model_id, pts, varnames, a, b, start, T0, Tw, tz, cache):
    """[Tw, len(pts), len(varnames)] for valid hours start+T0 .. start+T0+Tw-1."""
    F = np.full((Tw, len(pts), len(varnames)), np.nan, np.float32)
    s0 = dt.datetime.fromisoformat(start)
    for (c0, c1) in chunks(a, b):
        for p0 in range(0, len(pts), 25):
            P = pts[p0:p0 + 25]
            key = f"{model_id}_{c0}_{c1}_{p0}_{len(P)}_{hashlib.md5(repr((varnames, P)).encode()).hexdigest()[:10]}.json"
            f = os.path.join(cache, key)
            if os.path.exists(f):
                j = json.load(open(f))
            else:
                j = get(dict(latitude=",".join(f"{la:.4f}" for la, _ in P), longitude=",".join(f"{lo:.4f}" for _, lo in P),
                             hourly=",".join(varnames), models=model_id, start_date=c0.isoformat(),
                             end_date=c1.isoformat(), timezone=tz, wind_speed_unit="ms"))
                if isinstance(j, dict) and j.get("error"):
                    print(f"    {model_id} {c0}..{c1}: {j['reason'][:160]}", flush=True)
                    continue
                json.dump(j, open(f, "w"))
            js = j if isinstance(j, list) else [j]
            for pi, jj in enumerate(js):
                h = jj.get("hourly", {})
                ts = h.get("time", [])
                kk = np.array([int((dt.datetime.fromisoformat(t) - s0).total_seconds() // 3600) - T0 for t in ts])
                ok = (kk >= 0) & (kk < Tw)
                for vi, v in enumerate(varnames):
                    arr = h.get(v, h.get(f"{v}_{model_id}"))
                    if arr is None:
                        continue
                    x = np.array([np.nan if y is None else y for y in arr], np.float32)
                    F[kk[ok], p0 + pi, vi] = x[ok]
        print(f"    {model_id} {c0} .. {c1}: done", flush=True)
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="WMO")
    ap.add_argument("--parts", default="score,hybrid")
    a = ap.parse_args()
    z = np.load(os.path.join(RAW, f"WX_{a.league}.npz"))
    start = str(z["start"]).replace("T", " ")[:13] + ":00"
    T, tz = z["X"].shape[0], str(z["tz"])
    lat, lon = z["lat"].astype(float), z["lon"].astype(float)
    pts_all = [(round(la * 20) / 20, round(lo * 20) / 20) for la, lo in zip(lat, lon)]   # 0.05 deg (~5 km) points
    pts = sorted(set(pts_all))
    col = np.array([pts.index(p) for p in pts_all])
    print(f"{a.league}: {len(lat)} stations -> {len(pts)} forecast points (0.05 deg), timezone {tz}", flush=True)
    cache = os.path.join(RAW, "nwp_cache"); os.makedirs(cache, exist_ok=True)
    B = bounds(a.league, T)
    s0 = dt.datetime.fromisoformat(start)
    day = lambda k: (s0 + dt.timedelta(hours=int(k))).date()
    out, meta = {"col": col}, {"league": a.league, "points": pts, "models": {}}
    prev = os.path.join(RAW, f"NWP_{a.league}.npz")
    if os.path.exists(prev):                     # keep parts not refetched in this call
        z0 = np.load(prev)
        for k in z0.files:
            if k == "meta":
                meta["models"].update(json.loads(str(z0["meta"])).get("models", {}))
            elif not ((k.startswith("hybrid") and "hybrid" in a.parts) or
                      ((k.startswith("score") or k == "suffixes") and "score" in a.parts)):
                out[k] = z0[k]
    try:
        if "score" in a.parts:
            T0 = max(0, B["test"][0] - 45 * 24)
            Tw = B["test"][1] - T0
            names = list(NWP_MODELS)
            Fs = np.full((Tw, len(pts), len(names), len(SUFFIXES), len(TARGETS)), np.nan, np.float32)
            out.update(score=Fs, score_t0=np.array(T0), score_models=np.array(names),
                       suffixes=np.array(list(SUFFIXES)))
            probe_day = day(B["test"][0] + 24 * 30).isoformat()
            for mi, nm in enumerate(names):
                print(f"  {nm}: resolving identifier", flush=True)
                mid = resolve(NWP_MODELS[nm], pts[0][0], pts[0][1], probe_day, tz)
                meta["models"][nm] = mid
                if not mid:
                    print(f"  {nm}: NOT AVAILABLE in the archive for this period", flush=True)
                    continue
                vn = [NWP_VARS[t] + sfx for sfx in SUFFIXES.values() for t in TARGETS]
                F = fetch(mid, pts, vn, day(T0), day(T0 + Tw - 1), start, T0, Tw, tz, cache)
                Fs[:, :, mi] = F.reshape(Tw, len(pts), len(SUFFIXES), len(TARGETS))
                cov = 100 * np.isfinite(Fs[B["test"][0] - T0:, :, mi]).mean((0, 1))
                print(f"  {nm} [{mid}]: test coverage % (day0/1/2 x AT/RH/WS) {np.round(cov, 1).tolist()}", flush=True)
        if "hybrid" in a.parts:
            T0 = max(0, int((dt.datetime(2024, 1, 1) - s0).total_seconds() // 3600))
            Tw = T + 48 - T0
            Fh = np.full((Tw, len(pts), len(HYBRID_INPUTS), len(HYB_SUFFIXES), len(TARGETS)), np.nan, np.float32)
            out.update(hybrid=Fh, hybrid_t0=np.array(T0), hybrid_models=np.array(HYBRID_INPUTS),
                       hybrid_suffixes=np.array(HYB_SUFFIXES))
            for mi, nm in enumerate(HYBRID_INPUTS):
                mid = meta["models"].get(nm) or resolve(NWP_MODELS[nm], pts[0][0], pts[0][1],
                                                        day(B["test"][0] + 24 * 30).isoformat(), tz)
                if not mid:
                    continue
                vn = [NWP_VARS[t] + SUFFIXES[s_] for s_ in HYB_SUFFIXES for t in TARGETS]
                F = fetch(mid, pts, vn, day(T0), day(T0 + Tw - 1), start, T0, Tw, tz, cache)
                Fh[:, :, mi] = F.reshape(Tw, len(pts), len(HYB_SUFFIXES), len(TARGETS))
                cov = 100 * np.isfinite(Fh[:, :, mi]).mean((0, 1))
                print(f"  hybrid input {nm} [{mid}] day1/day2: coverage % {np.round(cov, 1).tolist()}", flush=True)
    except DailyLimit as e:
        print(f"  Open-Meteo daily limit reached ({e}); saving what was fetched - rerun later to complete", flush=True)
        meta["incomplete"] = True
    out["meta"] = np.array(json.dumps(meta))
    np.savez_compressed(os.path.join(RAW, f"NWP_{a.league}.npz"), **out)
    print("wrote", os.path.join(RAW, f"NWP_{a.league}.npz"), json.dumps(meta["models"]), flush=True)


if __name__ == "__main__":
    main()
