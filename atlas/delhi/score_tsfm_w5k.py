"""Score Atlas and the time-series foundation models on exactly the same WEATHER-5K windows, with per-window errors kept
so every comparison can be paired (README, "Head-to-head on WEATHER-5K").

Windows: forecast starts at 00:00 UTC every `--origin-every` hours inside the chosen year, on every `--stations-every`-th
station; 24 h ahead (H), five variables. A window-variable counts when its truth hour is observed and the station has at
least one observation of that variable in the 48 h before the start (the history Atlas reads).
Opponents get `--ctx` hours of their own history (default 512 h, longer than Atlas's 48), gaps forward-filled.
Opponents are only run to be scored: nothing here trains on their outputs or mixes them into Atlas.

  python score_tsfm_w5k.py --year val --models tfm25,tfm3,chronos2,chronos-bolt \
      --atlas atlas10m=../../models/series/58_atlas-5k-10m_weather5k_adopted.pt,v2c=../../models/series/57_atlas-5k_v2c_weather5k_adopted.pt
Writes {ATLAS_OUT}/h2h/{name}_{year}.npz  (sae [S, O, H?->5], cnt) and h2h_{year}.json (MAE table per model).
"""
import argparse, glob, json, os, sys, time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "pw"))
import run_atlas_5k as R                                   # data loading, neighbourhoods and Atlas batching (one source)

DEV = R.DEV


def windows(bounds, H, origin_every, N, stations_every, min_hist, stations_file=""):
    a, e = bounds
    starts = np.arange(a + min_hist, e - H + 1)                     # forecast start hours wholly inside the period
    starts = starts[(starts % 24) == 0][::max(1, origin_every // 24)]
    S = np.arange(0, N, stations_every)
    if stations_file:                                               # an explicit station list (e.g. atlas/m100/india_stations.json)
        S = np.array(json.load(open(stations_file))["index"], dtype=np.int64)
    return S, starts


def own_units(z):
    return z * torch.tensor(R.STD, device=z.device) + torch.tensor(R.MEAN, device=z.device)


def ffill(c):
    """c [M, T] float tensor with NaN; forward-fill, then back-fill the start; all-NaN rows -> 0 (masked later)."""
    T = c.shape[1]
    ok = torch.isfinite(c)
    idx = torch.where(ok, torch.arange(T, device=c.device)[None].expand_as(c), torch.zeros_like(c, dtype=torch.long))
    idx = torch.cummax(idx, 1).values
    c = torch.gather(c, 1, idx)
    first = torch.argmax(ok.float(), 1)
    fv = torch.gather(c, 1, first[:, None])
    c = torch.where(torch.isfinite(c), c, fv)
    return torch.nan_to_num(c)


def truth(Zt, s, t0, L, H):
    """Observed values for the H hours after the start and 'any observation in the L hours before', from Zt."""
    tt = t0[:, None] + torch.arange(L + H, device=t0.device)[None]
    w = Zt[s, tt].float()                                                     # [B, L+H, 5]
    return w[:, L:], torch.isfinite(w[:, :L]).any(1)


def score_atlas(path, Z, lat, lon, elev, S, starts, H, k=32, bs=2048, Zt=None):
    Zt = Z if Zt is None else Zt
    from atlas.grow import load_any
    model = load_any(path, DEV).to(DEV).eval()
    nb = R.neighbours(lat, lon, k); geo = R.geometry(lat, lon, nb); st = R.static_feats(lat, lon, elev)
    bt = R.Batcher(Z, nb, geo, st, H)
    sae = np.zeros((len(S), len(starts), 5), np.float32); cnt = np.zeros_like(sae, dtype=np.uint8)
    t0s = torch.as_tensor(starts - R.L, device=DEV)
    sd = torch.tensor(R.STD, device=DEV)
    with torch.no_grad():
        for i, s in enumerate(S.tolist()):
            for j in range(0, len(t0s), bs):
                t0 = t0s[j:j + bs]; b = bt(torch.full_like(t0, s), t0)
                with torch.autocast(DEV, dtype=torch.float16, enabled=(DEV == "cuda")):
                    p = R.predict_center(model, "atlas", b).float()
                y, hist = truth(Zt, s, t0, R.L, H)                                    # truth [B, H, 5], [B, 5]
                my = torch.isfinite(y)
                err = torch.where(my, ((p - torch.nan_to_num(y)) * sd).abs(), torch.zeros_like(p))
                sae[i, j:j + bs] = (err.sum(1) * hist).cpu().numpy(); cnt[i, j:j + bs] = (my.sum(1) * hist).cpu().numpy()
    return sae, cnt, dict(name=os.path.basename(path), params=model.n_params(), neighbours=k)


def score_opponent(key, Z, S, starts, H, ctx, chunk_st=8, log=print, Zt=None):
    import opponents as O
    Zt = Z if Zt is None else Zt
    fc = None
    sae = np.zeros((len(S), len(starts), 5), np.float32); cnt = np.zeros_like(sae, dtype=np.uint8)
    st = torch.as_tensor(starts, device=DEV)
    t0 = time.time()
    mv = key in ("chronos2mv", "tfm3mv")
    if key == "persist":                                  # last observed value held (a reference, no model)
        meta = dict(name="Persistence (last value)", licence="-", params=0)
    elif key == "chronos2mv":
        from chronos import BaseChronosPipeline
        pipe = BaseChronosPipeline.from_pretrained("amazon/chronos-2", device_map=DEV)
        meta = dict(name="Chronos-2 multivariate (Amazon, 120M)", licence="Apache-2.0", params=120e6)
    else:
        fc = O.make(key, ctx, H)
        meta = dict(name=fc.name, licence=fc.licence, params=fc.params)
    for i in range(0, len(S), chunk_st):
        ss = torch.as_tensor(S[i:i + chunk_st], device=DEV)
        tt = st[None, :, None] + torch.arange(-ctx, H, device=DEV)[None, None]          # [1, O, ctx+H]
        tt = tt.clamp(min=0)
        w = own_units(Z[ss[:, None, None], tt].float())                                   # inputs [s, O, ctx+H, 5]
        wt = Zt[ss[:, None, None], tt].float()                                            # observed (standardised)
        hist = torch.isfinite(wt[:, :, ctx - R.L:ctx]).any(2)                             # [s, O, 5]
        y = own_units(wt[:, :, ctx:])                                                     # truth [s, O, H, 5]
        c = w[:, :, :ctx].permute(0, 1, 3, 2).reshape(-1, ctx)                            # [s*O*5, ctx]
        c = ffill(c)
        if key == "persist":
            p = c[:, -1:].expand(-1, H).reshape(-1, 5, H).permute(0, 2, 1)
        elif mv:
            cm = c.reshape(-1, 5, ctx)                                                    # one 5-variate series per window
            if key == "chronos2mv":
                q, _ = pipe.predict_quantiles(cm.cpu(), prediction_length=H, quantile_levels=[0.5])
                q = torch.stack([torch.as_tensor(x) for x in q]) if isinstance(q, (list, tuple)) else torch.as_tensor(q)
                p = q.float().reshape(len(cm), 5, H).to(DEV)
            else:
                p = torch.as_tensor(np.asarray(fc(cm.cpu().numpy()))[..., 1], device=DEV).reshape(len(cm), 5, H)
            p = p.permute(0, 2, 1)                                                        # [W, H, 5]
        else:
            out = []
            cn = c.cpu().numpy()
            for j in range(0, len(cn), 4096):
                out.append(np.asarray(fc(cn[j:j + 4096]))[..., 1])                         # median [n, H]
            p = torch.as_tensor(np.concatenate(out), device=DEV).reshape(-1, 5, H).permute(0, 2, 1)
        p = p.reshape(len(ss), len(starts), H, 5)
        m = torch.isfinite(y)
        err = torch.where(m, (p - torch.nan_to_num(y)).abs(), torch.zeros_like(p))
        sae[i:i + len(ss)] = (err.sum(2) * hist).cpu().numpy(); cnt[i:i + len(ss)] = (m.sum(2) * hist).cpu().numpy()
        if i == 0:
            log(f"  {meta['name']}: first {len(ss)} stations x {len(starts)} starts in {time.time() - t0:.0f}s "
                f"(about {(time.time() - t0) * len(S) / len(ss) / 60:.0f} min for all)")
    meta.update(context_hours=ctx, minutes=round((time.time() - t0) / 60, 1))
    return sae, cnt, meta


def table(sae, cnt):
    s, c = sae.sum((0, 1)).astype(np.float64), cnt.sum((0, 1)).astype(np.float64)
    mae = s / np.maximum(c, 1)
    return dict(MAE=dict(zip(R.NAMES, mae.round(4).tolist())), E=float(np.mean(mae / R.STD)), points=int(c[0]))


def main(a):
    out = os.path.join(R.OUT, a.h2h_dir); os.makedirs(out, exist_ok=True)
    Z, lat, lon, elev, M = R.load(a.quick)
    Zt, start0 = Z, R.START
    if a.year == "live":                                  # fresh NOAA observations after the benchmark (fetch_isd_live.py)
        O = np.load(os.path.join(R.RAW, "W5K_OBS.npy"), mmap_mode="r")
        off = M["offset"].astype(np.float32); mu = R.MEAN - off
        Zt = torch.empty_like(Z)
        for i in range(0, Z.shape[0], 256):
            Zt[i:i + 256] = torch.from_numpy(((O[i:i + 256, :Z.shape[1]].astype(np.float32) - mu) / R.STD).astype(np.float16)).to(DEV)
        start0 = np.datetime64(str(M["start"]))
        bounds, min_hist = (0, Z.shape[1]), max(R.L, a.ctx)
        print(f"live data: {start0} to {M['live_end']}", flush=True)
    else:
        bounds, min_hist = R.YEARS[a.year], R.L
    S, starts = windows(bounds, a.H, a.origin_every, Z.shape[0], a.stations_every, min_hist, a.stations_file)
    print(f"{a.year}: {len(S)} stations x {len(starts)} forecast starts x 5 variables, H={a.H}, opponent context {a.ctx} h", flush=True)
    fj = os.path.join(out, f"h2h_{a.year}.json")
    res = json.load(open(fj)) if os.path.exists(fj) else {}
    res["_windows"] = dict(year=a.year, stations=len(S), stations_every=a.stations_every, starts=len(starts),
                           origin_every_h=a.origin_every, H=a.H, first_start=str(start0 + np.timedelta64(int(starts[0]), "h")),
                           last_start=str(start0 + np.timedelta64(int(starts[-1]), "h")))
    jobs = [("atlas", x.split("=", 1)[0], x.split("=", 1)[1]) for x in a.atlas.split(",") if x] + \
           [("opp", k, None) for k in a.models.split(",") if k]
    for kind, name, path in jobs:
        f = os.path.join(out, f"{name}_{a.year}.npz")
        if os.path.exists(f) and not a.redo:
            d = np.load(f); res[name] = res.get(name) or dict(table(d["sae"], d["cnt"]))
            print(f"{name}: already scored -> {json.dumps(res[name]['MAE'])}", flush=True); continue
        t0 = time.time()
        if kind == "atlas":
            p = path if os.path.exists(path) else next(iter(glob.glob(f"/content/**/{os.path.basename(path)}", recursive=True)), path)
            sae, cnt, meta = score_atlas(p, Z, lat, lon, elev, S, starts, a.H, a.k, Zt=Zt)
        else:
            sae, cnt, meta = score_opponent(name, Z, S, starts, a.H, a.ctx, Zt=Zt)
        np.savez_compressed(f, sae=sae, cnt=cnt, stations=S, starts=starts)
        res[name] = dict(table(sae, cnt), **meta, minutes_total=round((time.time() - t0) / 60, 1))
        print(f"{name}: {json.dumps(res[name]['MAE'])} E {res[name]['E']:.5f} ({res[name]['minutes_total']} min)", flush=True)
        json.dump(res, open(fj, "w"), indent=1)
    json.dump(res, open(fj, "w"), indent=1)
    print("H2H " + json.dumps({k: v for k, v in res.items()}, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="val", choices=["val", "test", "live"])
    ap.add_argument("--H", type=int, default=24)
    ap.add_argument("--models", default="tfm25,tfm3,chronos2,chronos-bolt")
    ap.add_argument("--atlas", default="")
    ap.add_argument("--stations-every", type=int, default=4)
    ap.add_argument("--origin-every", type=int, default=24, help="hours between forecast starts (multiple of 24)")
    ap.add_argument("--ctx", type=int, default=512)
    ap.add_argument("--k", type=int, default=32, help="Atlas stations per neighbourhood (v2c and 10M: 32)")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--stations-file", dest="stations_file", default="", help="JSON with an 'index' list of stations (overrides --stations-every)")
    ap.add_argument("--h2h-dir", dest="h2h_dir", default="h2h", help="output folder under ATLAS_OUT (a separate study keeps its own)")
    main(ap.parse_args())
