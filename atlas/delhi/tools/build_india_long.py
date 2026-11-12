"""All-India station history (India-first league, data step).

Every CPCB / state-board continuous station in the public copy of CPCB's exports (Kaggle dataset "Time Series Air
Quality Data of India (2010-2023)": one hourly CSV per station, 453 stations, plus stations_info.csv with state,
city and agency). Attach the dataset to the notebook as an input; nothing is downloaded and no key is needed.

Same reader and cleaning rules as the Delhi league (tools/fetch_delhi.py): hourly clock, the solar-radiation peak
decides whether a file's clock is UTC or Indian time, non-numbers / negatives (except temperature) / values above the
physical ceilings become missing, a pollutant reading stuck for 24 h becomes missing.

Writes INDIA_LONG.npz: X [hours, stations, 14 variables] float32 (NaN = missing), vars, stations ("<location> -
<agency>"), city, state, files, start. Then prints what a league on it would look like, so its rules can be fixed
before any model is scored: stations by state and city, coverage by year, and how many stations per city report
PM2.5 in the last 182 days (test), the 61 days before (validation) and earlier (training).

  python tools/build_india_long.py            # needs the Kaggle dataset attached
"""
import glob, json, os, sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fetch_delhi as FD

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
SEARCH = os.environ.get("LONG_SEARCH", "/kaggle/input")
FIRST = os.environ.get("INDIA_FROM", "2017-01-01 00:00")
LAST = os.environ.get("INDIA_TO", "2023-03-31 23:00")
TEST_DAYS, VAL_DAYS = 182, 61


def main():
    import pandas as pd
    hits = sorted(glob.glob(os.path.join(SEARCH, "**", "stations_info.csv"), recursive=True))
    if not hits:
        print("stations_info.csv not found under", SEARCH, flush=True); sys.exit(1)
    base = os.path.dirname(hits[0])
    info = pd.read_csv(hits[0])
    low = {c.lower(): c for c in info.columns}
    print(f"{hits[0]}: {len(info)} stations, columns {list(info.columns)}", flush=True)
    idx = pd.date_range(FIRST, LAST, freq="h")
    X = np.full((len(idx), len(info), len(FD.VARS)), np.nan, np.float32)
    names, city, state, files, meta, keep = [], [], [], [], [], []
    for j, r in enumerate(info.itertuples(index=False)):
        r = dict(zip(info.columns, r))
        stem = str(r[low.get("file_name", info.columns[0])])
        f = glob.glob(os.path.join(base, "**", stem + ("" if stem.lower().endswith(".csv") else ".csv")), recursive=True)
        if not f:
            print(f"  {stem}: file not found", flush=True); continue
        try:
            sid, nm, mean, inf = FD.read_station(f[0])
        except Exception as e:
            print(f"  {stem}: FAILED {type(e).__name__}: {e}", flush=True); continue
        X[:, j] = mean.reindex(idx)[FD.VARS].to_numpy(np.float32)
        loc, ag = str(r.get(low.get("station_location", ""), stem)).strip(), str(r.get(low.get("agency", ""), "")).strip()
        names.append(f"{loc} - {ag}" if ag and ag.lower() != "nan" else loc)
        city.append(str(r.get(low.get("city", ""), "")).strip()); state.append(str(r.get(low.get("state", ""), "")).strip())
        files.append(stem); keep.append(j)
        inf.update(station=names[-1]); meta.append(inf)
        if len(keep) % 50 == 0:
            print(f"  read {len(keep)} files", flush=True)
    X = X[:, keep]
    for c, v in enumerate(FD.VARS):                              # the league's cleaning rules
        x = X[..., c]
        x[(x > FD.CEIL[v]) | ((x < 0) & (v != "AT"))] = np.nan
        if v in FD.POLLUTANTS:
            for j in range(x.shape[1]):
                x[FD.stuck(x[:, j]), j] = np.nan
    pk = [m["solar_peak_hour"] for m in meta if m["solar_peak_hour"] is not None]
    print(f"read {len(keep)} of {len(info)} stations; clocks moved from UTC: {sum(m['shift_h'] > 0 for m in meta)}; "
          f"solar peak hours seen: {sorted(set(pk))}; step minutes: {sorted({m['step_min'] for m in meta})}; "
          f"doubtful timestamps: {sum(m['parsed'] < 0.95 or m['increasing'] < 0.9 for m in meta)}; "
          f"latest reading in any file: {max(m['last'] for m in meta)}", flush=True)
    os.makedirs(RAW, exist_ok=True)
    np.savez_compressed(os.path.join(RAW, "INDIA_LONG.npz"), X=X, vars=np.array(FD.VARS), stations=np.array(names),
                        city=np.array(city), state=np.array(state), files=np.array(files), start=np.array(str(idx[0])))
    print(f"INDIA_LONG: {len(idx)} hours ({idx[0]} .. {idx[-1]}) x {X.shape[1]} stations x {len(FD.VARS)} variables", flush=True)

    pm = np.isfinite(X[..., 0])
    yrs = idx.year.to_numpy()
    print("by year: stations with PM2.5 on >= 50% of hours | PM2.5 observed % | AT observed % | WS observed %", flush=True)
    for y in sorted(set(yrs)):
        s = yrs == y
        print(f"  {y}: {int((pm[s].mean(0) >= 0.5).sum()):3d} | {100 * pm[s].mean():5.1f} | "
              f"{100 * np.isfinite(X[s][..., FD.VARS.index('AT')]).mean():5.1f} | {100 * np.isfinite(X[s][..., FD.VARS.index('WS')]).mean():5.1f}", flush=True)
    print("medians and 1st / 99th percentiles (unit check)", flush=True)
    for c, v in enumerate(FD.VARS):
        x = X[::7, :, c]; x = x[np.isfinite(x)]
        print(f"  {v:6s} median {np.median(x):9.2f}   1% {np.percentile(x, 1):9.2f}   99% {np.percentile(x, 99):9.2f}   observed {100 * np.isfinite(X[..., c]).mean():5.1f}%", flush=True)
    # what a league would look like: last 182 days = test, 61 days before = validation, earlier = training
    n_te, n_va = TEST_DAYS * 24, VAL_DAYS * 24
    b = len(idx) - n_te - n_va
    ok = (pm[-n_te:].mean(0) >= 0.5) & (pm[:b].mean(0) >= 0.125) & (pm[b:b + n_va].mean(0) >= 0.25)
    months = pm[:b].sum(0) / (24 * 30.4)
    print(f"league sketch: train to {idx[b - 1]}, validation to {idx[b + n_va - 1]}, test {idx[-n_te]} .. {idx[-1]}", flush=True)
    print(f"stations usable (PM2.5 on >= 50% of test hours, >= 25% of validation hours, >= 12.5% of training hours): {int(ok.sum())} "
          f"of {len(ok)}; their months of PM2.5 before the validation period: median {np.median(months[ok]):.0f}, "
          f"10-90% {np.percentile(months[ok], 10):.0f}-{np.percentile(months[ok], 90):.0f}", flush=True)
    cs = pd.DataFrame({"state": state, "city": city, "ok": ok})
    by_state = cs.groupby("state")["ok"].agg(["size", "sum"]).sort_values("sum", ascending=False)
    print("by state (stations, usable): " + "; ".join(f"{k} {int(v['size'])}/{int(v['sum'])}" for k, v in by_state.iterrows()), flush=True)
    by_city = cs.groupby("city")["ok"].agg(["size", "sum"]).sort_values("sum", ascending=False)
    big = by_city[by_city["sum"] >= 4]
    print(f"cities with 4 or more usable stations ({len(big)}): " + "; ".join(f"{k} {int(v['sum'])}" for k, v in big.iterrows()), flush=True)
    print(f"usable stations in cities with fewer than 4: {int(by_city[by_city['sum'] < 4]['sum'].sum())} across {int((by_city['sum'] < 4).sum())} cities", flush=True)
    print("INDIA " + json.dumps(dict(hours=len(idx), stations=int(X.shape[1]), usable=int(ok.sum()), cities_4plus=int(len(big)),
                                     start=str(idx[0]), end=str(idx[-1]))), flush=True)


if __name__ == "__main__":
    main()
