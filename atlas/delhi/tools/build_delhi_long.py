"""Delhi long history: join CPCB's earlier hourly station files to the 2024-25 league file.

The league file (DELHI.npz, tools/fetch_delhi.py) starts on 2024-01-01 because OpenCity's earlier Delhi files hold
only the composite AQI. The measurements themselves for 2010-2023 exist in a public copy of CPCB's station exports:
the Kaggle dataset "Time Series Air Quality Data of India (2010-2023)" (one hourly CSV per station plus
stations_info.csv). Attach it to the notebook as an input; nothing is downloaded and no key is needed.

What this does, with every step printed so it can be checked:
  1. finds stations_info.csv under /kaggle/input and lists its Delhi rows;
  2. matches them to the league's stations by name (same words after dropping "Delhi" and file boilerplate; the agency
     - DPCC / CPCB / IMD / IITM - must agree when both names carry one). Unmatched stations get no earlier history;
  3. reads each matched file with the league's own reader (tools/fetch_delhi.read_station: hourly clock, the solar
     radiation peak decides whether the clock is UTC or Indian time) and applies the league's cleaning rules
     (non-numbers, negatives except temperature, values above the physical ceilings, pollutant readings stuck for 24 h);
  4. writes DELHI_LONG.npz: the earlier hours, then the league file unchanged, on one hourly clock. The last
     len(league) hours are bit-identical to DELHI.npz, so the validation and test windows do not move;
  5. prints coverage and medians by year, and old-against-new medians per variable to expose unit changes.

  python tools/build_delhi_long.py            # needs $PW_RAW/DELHI.npz and the Kaggle dataset attached
"""
import glob, json, os, re, sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fetch_delhi as FD

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
SEARCH = os.environ.get("LONG_SEARCH", "/kaggle/input")
STOP = {"delhi", "new", "minute", "aqi", "data", "for", "hourly", "csv", "15", "2024", "25", "2017", "2023", "the"}
AGENCY = {"dpcc", "cpcb", "imd", "iitm", "hspcb", "uppcb"}


def toks(s):
    t = set(re.sub(r"[^a-z0-9]+", " ", str(s).lower()).split()) - STOP
    return frozenset(t - AGENCY), frozenset(t & AGENCY)


def match(league, cands):
    """league: names; cands: {file: name}. Returns {league index: file}, with the reasoning printed."""
    out, used = {}, set()
    ct = {f: toks(n) for f, n in cands.items()}
    for i, nm in enumerate(league):
        w, ag = toks(nm)
        best = []
        for f, (cw, cag) in ct.items():
            if f in used or (ag and cag and ag != cag):
                continue
            j = len(w & cw) / max(len(w | cw), 1)
            best.append((j, f))
        best.sort(reverse=True)
        if best and best[0][0] >= 0.6 and (len(best) == 1 or best[0][0] > best[1][0]):
            out[i] = best[0][1]; used.add(best[0][1])
            print(f"  MATCH {best[0][0]:.2f}  {nm!r}  <-  {cands[best[0][1]]!r} ({os.path.basename(best[0][1])})", flush=True)
        else:
            top = "; ".join(f"{cands[f]!r} {j:.2f}" for j, f in best[:3])
            print(f"  NO MATCH  {nm!r}   (closest: {top})", flush=True)
    return out


def main():
    import pandas as pd
    hits = sorted(glob.glob(os.path.join(SEARCH, "**", "stations_info.csv"), recursive=True))
    if not hits:
        print("stations_info.csv not found. What is attached:", flush=True)
        for p in sorted(glob.glob(os.path.join(SEARCH, "*", "*")))[:60]:
            print("   ", p, flush=True)
        sys.exit(1)
    base = os.path.dirname(hits[0])
    info = pd.read_csv(hits[0])
    print(f"{hits[0]}: {len(info)} stations, columns {list(info.columns)}", flush=True)
    low = {c.lower(): c for c in info.columns}
    fcol = low.get("file_name", info.columns[0])
    ncol = low.get("station_location") or next((c for c in info.columns if "station" in c.lower() or "location" in c.lower()), info.columns[-1])
    isd = np.zeros(len(info), bool)
    for c in info.columns:
        isd |= info[c].astype(str).str.contains("delhi", case=False, na=False).to_numpy()
    dl = info[isd]
    print(f"Delhi rows: {len(dl)}", flush=True)
    print(dl.to_string(), flush=True)
    files = {}
    for _, r in dl.iterrows():
        stem = str(r[fcol])
        f = glob.glob(os.path.join(base, "**", stem + ("" if stem.lower().endswith(".csv") else ".csv")), recursive=True)
        if f:
            files[f[0]] = str(r[ncol])
        else:
            print(f"  file for {stem} not found", flush=True)

    z = np.load(os.path.join(RAW, "DELHI.npz"), allow_pickle=False)
    X1, names, vars_ = z["X"].astype(np.float32), [str(s) for s in z["stations"]], [str(v) for v in z["vars"]]
    assert vars_ == FD.VARS, vars_
    start1 = pd.Timestamp(str(z["start"]))
    print(f"league file: {X1.shape[0]} hours from {start1}, {len(names)} stations", flush=True)
    m = match(names, files)
    print(f"matched {len(m)} of {len(names)} league stations to earlier files ({len(files)} Delhi files on offer)", flush=True)

    parts, meta = {}, []
    for i, f in m.items():
        try:
            sid, nm, mean, inf = FD.read_station(f)
        except Exception as e:
            print(f"  {os.path.basename(f)}: FAILED {type(e).__name__}: {e}", flush=True); continue
        inf.update(league_station=names[i])
        meta.append(inf)
        if len(meta) == 1:
            print("  first file header:", list(pd.read_csv(f, nrows=2).columns), flush=True)
        parts[i] = mean[mean.index < start1]
    for inf in meta[:4]:
        print("  ", json.dumps(inf), flush=True)
    pk = [inf["solar_peak_hour"] for inf in meta if inf["solar_peak_hour"] is not None]
    print(f"solar-radiation peak hour over files: {sorted(set(pk))} (11-14 = Indian time as written; 4-8 = UTC, moved); "
          f"files moved: {sum(inf['shift_h'] > 0 for inf in meta)}; step minutes: {sorted({inf['step_min'] for inf in meta})}; "
          f"doubtful timestamps: {sum(inf['parsed'] < 0.95 or inf['increasing'] < 0.9 for inf in meta)}", flush=True)
    if not parts:
        print("nothing to join", flush=True); sys.exit(1)
    first_year = int(os.environ.get("LONG_FROM", 2010))
    t0 = max(min(p.index.min() for p in parts.values() if len(p)), pd.Timestamp(f"{first_year}-01-01")).floor("D")
    idx0 = pd.date_range(t0, start1 - pd.Timedelta(hours=1), freq="h")
    X0 = np.full((len(idx0), len(names), len(vars_)), np.nan, np.float32)
    for i, p in parts.items():
        X0[:, i] = p.reindex(idx0)[vars_].to_numpy(np.float32)
    for c, v in enumerate(vars_):                               # the league's cleaning rules
        x = X0[..., c]
        x[(x > FD.CEIL[v]) | ((x < 0) & (v != "AT"))] = np.nan
        if v in FD.POLLUTANTS:
            for j in range(x.shape[1]):
                x[FD.stuck(x[:, j]), j] = np.nan
        X0[..., c] = x
    X = np.concatenate([X0, X1])
    idx = pd.date_range(t0, periods=len(X), freq="h")
    assert idx[len(X0)] == start1
    np.savez_compressed(os.path.join(RAW, "DELHI_LONG.npz"), X=X, vars=np.array(vars_), stations=np.array(names),
                        start=np.array(str(idx[0])), league_start=np.array(str(start1)), league_offset=np.array(len(X0)),
                        has_history=np.array([i in parts for i in range(len(names))]))
    print(f"DELHI_LONG: {len(X)} hours ({idx[0]} .. {idx[-1]}) x {len(names)} stations x {len(vars_)} variables; "
          f"{len(X0)} earlier hours + {len(X1)} league hours", flush=True)

    yrs = idx.year.to_numpy()
    print("by year:  stations with PM2.5 on >= 50% of hours | PM2.5 observed % | median PM2.5 | AT observed % | WS observed %", flush=True)
    for y in sorted(set(yrs)):
        s = yrs == y
        pm = X[s][..., 0]
        cov = np.isfinite(pm).mean(0)
        print(f"  {y}: {int((cov >= 0.5).sum()):2d} | {100 * np.isfinite(pm).mean():5.1f} | {np.nanmedian(pm) if np.isfinite(pm).any() else float('nan'):6.1f} | "
              f"{100 * np.isfinite(X[s][..., vars_.index('AT')]).mean():5.1f} | {100 * np.isfinite(X[s][..., vars_.index('WS')]).mean():5.1f}", flush=True)
    old, new = (yrs >= 2019) & (yrs <= 2022), yrs >= 2024
    print("unit check: median 2019-2022 against 2024-25 (a ratio far from 1 means a unit or sensor change)", flush=True)
    warn = []
    for c, v in enumerate(vars_):
        a, b = np.nanmedian(X[old][..., c]) if np.isfinite(X[old][..., c]).any() else np.nan, np.nanmedian(X[new][..., c])
        r = a / b if b else np.nan
        flag = "" if (np.isfinite(r) and 0.6 <= r <= 1.6) else "   <-- CHECK"
        if flag:
            warn.append(v)
        print(f"  {v:6s} {a:9.2f} {b:9.2f}  ratio {r:5.2f}{flag}", flush=True)
    print("LONG " + json.dumps(dict(hours=len(X), earlier_hours=len(X0), start=str(idx[0]), matched=len(parts), league_stations=len(names),
                                    check=warn)), flush=True)


if __name__ == "__main__":
    main()
