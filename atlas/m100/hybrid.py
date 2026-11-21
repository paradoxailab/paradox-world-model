"""Atlas-100M hybrid: the weather view that also reads the global forecast systems' archived forecasts, against those
systems themselves, at WEATHER-5K stations in 2025 (rules: atlas/m100/PREREG.md, section H).

Stations: every 4th of the 709 head-to-head stations (WEATHER-5K order, stations 0, 32, 64, ...): 178 stations.
Period: NOAA ISD-Lite observations from tools/fetch_isd_live.py (1 Jan 2024 .. 24 Aug 2025 22:00 UTC).
  train  2024-01-01 .. 2024-10-31   (hybrid input layers fitted, all weights at a low learning rate)
  val    2024-11-01 .. 2024-12-31   (early stopping)
  test   2025-01-01 .. 2025-08-24   (scored once; forecast starts every 6 h)
Global systems (Open-Meteo Previous Runs API, archived from January 2024): ECMWF IFS 0.25, ECMWF AIFS, NOAA GFS,
GraphCast (run on GFS initial conditions), at each station: temperature, dewpoint, wind speed and direction at 10 m,
mean sea-level pressure, as forecast 24 h (day1) and 48 h (day2) before each valid hour.

  python hybrid.py fetch  --raw /content/live --out $W/nwp        # resumable; stops at the free daily limit, re-run next day
  python hybrid.py train  --raw /content/live --nwp $W/nwp/NWP_W5K.npz --view atlas100m_weather_view.pt --out $W/out
  python hybrid.py score  --raw /content/live --nwp $W/nwp/NWP_W5K.npz --hybrid $W/out/hybrid_best.pt --pure atlas100m_weather_view.pt

Inputs of the hybrid (no look-ahead): for every valid hour of the 48-h window and the 24-h forecast, each system's
DAY2 forecast (issued 48 h before the valid hour, so always published before the forecast starts) and a flag.
Opponents are scored on the freshest run published before the forecast starts: day1 if the run (issued 24 h before
the valid hour) was out LATENCY hours later and still before the start, else day2. LATENCY = 6 h for every system
(at or below the real delay of each; a shorter delay can only favour the opponents). Bias-corrected opponents: minus
their mean error at that station, variable and offset over the 30 days before the start (valid hours before it only).
"""
import argparse, datetime as dt, hashlib, json, math, os, sys, time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from m100 import domains as Dm                            # puts atlas/delhi on the path
import run_atlas_5k as R5
from atlas.model import Atlas
from atlas.grow import load_any

DEV = Dm.DEV
API = "https://previous-runs-api.open-meteo.com/v1/forecast"
SYSTEMS = {"IFS": ["ecmwf_ifs025", "ecmwf_ifs"], "AIFS": ["ecmwf_aifs025_single", "ecmwf_aifs025"],
           "GFS": ["gfs_global", "gfs_seamless"], "GraphCast": ["gfs_graphcast025"]}
OM_VARS = ["temperature_2m", "dew_point_2m", "wind_direction_10m", "wind_speed_10m", "pressure_msl"]   # = W5K order
OFFS = ["previous_day1", "previous_day2"]
LATENCY = 6
START = np.datetime64("2024-01-01T00")
SPLIT = dict(train=("2024-01-01T00", "2024-11-01T00"), val=("2024-11-01T00", "2025-01-01T00"), test=("2025-01-01T00", "2026-01-01T00"))
hour = lambda s: int((np.datetime64(s) - START) / np.timedelta64(1, "h"))


def stations(N):
    return np.arange(0, N, 8)[::4]                        # every 4th of the 709 head-to-head stations


# ================================================================================================= fetch
class DailyLimit(Exception):
    pass


def get(params, tries=12):
    import requests
    for k in range(tries):
        try:
            r = requests.get(API, params=params, timeout=300, headers={"User-Agent": "paradox-world-model-research"})
            if r.status_code == 429:
                why = r.text[:200]
                if "aily" in why:
                    raise DailyLimit(why)
                time.sleep(900 if "ourly" in why else 65); continue
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


def resolve(cands, la, lo):
    for m in cands:
        j = get(dict(latitude=la, longitude=lo, hourly="temperature_2m_previous_day1", models=m,
                     start_date="2024-06-01", end_date="2024-06-03", timezone="GMT"))
        j = j[0] if isinstance(j, list) else j
        if not j.get("error") and any(v is not None for v in j.get("hourly", {}).get("temperature_2m_previous_day1", [])):
            return m
    return None


def fetch(a):
    M = np.load(os.path.join(a.raw, "W5K_META.npz"))
    T = int((np.datetime64(str(M["live_end"])) - START) / np.timedelta64(1, "h")) + 1
    lat, lon = M["lat"].astype(float), M["lon"].astype(float)
    HS = stations(len(lat))
    cache = os.path.join(a.out, "cache"); os.makedirs(cache, exist_ok=True)
    end = (START + np.timedelta64(T - 1, "h")).astype("datetime64[D]").astype(str)
    hv = [f"{v}_{o}" for o in OFFS for v in OM_VARS]
    F = np.full((len(SYSTEMS), T, len(HS), 5, 2), np.nan, np.float32)
    ids = {}
    for si, (sysname, cands) in enumerate(SYSTEMS.items()):
        mid = resolve(cands, lat[HS[0]], lon[HS[0]])
        ids[sysname] = mid
        print(f"{sysname}: {mid}", flush=True)
        if mid is None:
            continue
        chunks, s = [], dt.date(2024, 1, 1)
        while s <= dt.date.fromisoformat(end):
            e = min(dt.date.fromisoformat(end), s + dt.timedelta(days=90)); chunks.append((s, e)); s = e + dt.timedelta(days=1)
        for c0, c1 in chunks:
            for p0 in range(0, len(HS), 25):
                P = HS[p0:p0 + 25]
                key = f"{mid}_{c0}_{c1}_{p0}_{hashlib.md5(repr((hv, P.tolist())).encode()).hexdigest()[:10]}.json"
                fn = os.path.join(cache, key)
                if os.path.exists(fn):
                    j = json.load(open(fn))
                else:
                    try:
                        j = get(dict(latitude=",".join(f"{lat[i]:.4f}" for i in P), longitude=",".join(f"{lon[i]:.4f}" for i in P),
                                     hourly=",".join(hv), models=mid, start_date=str(c0), end_date=str(c1), timezone="GMT",
                                     wind_speed_unit="ms"))
                    except DailyLimit as e:
                        print(f"DAILY LIMIT reached ({e}); everything so far is cached. Run the same command again tomorrow.", flush=True)
                        return
                    if isinstance(j, dict) and j.get("error"):
                        print(f"  {sysname} {c0}: {j['reason'][:120]}", flush=True); continue
                    json.dump(j, open(fn, "w"))
                for q, jj in zip(P, j if isinstance(j, list) else [j]):
                    t = np.array(jj["hourly"]["time"], dtype="datetime64[h]")
                    ix = ((t - START) / np.timedelta64(1, "h")).astype(int)
                    ok = (ix >= 0) & (ix < T)
                    k = int(np.where(HS == q)[0][0])
                    for oi, o in enumerate(OFFS):
                        for vi, v in enumerate(OM_VARS):
                            x = np.array([np.nan if z is None else z for z in jj["hourly"][f"{v}_{o}"]], np.float32)
                            F[si, ix[ok], k, vi, oi] = x[ok]
            print(f"  {sysname}: {c1} done", flush=True)
    np.savez_compressed(os.path.join(a.out, "NWP_W5K.npz"), F=F, systems=np.array(list(SYSTEMS)), ids=np.array(json.dumps(ids)),
                        stations=HS, vars=np.array(OM_VARS), offsets=np.array(OFFS), start=np.array(str(START)))
    cov = {s: float(np.isfinite(F[i]).mean()) for i, s in enumerate(SYSTEMS)}
    print("NWP " + json.dumps(dict(ids=ids, coverage=cov, hours=T, stations=len(HS))), flush=True)


# ================================================================================================= model
def widen_forcing(view, extra):
    """The weather view with `extra` more forcing channels, whose input weights are ZERO: forecasts are unchanged."""
    cfg = {k: v for k, v in view.cfg.items() if k != "grown_from"}
    L, C, U, S0 = cfg["L"], cfg["C"], cfg["U"], cfg.get("static", 0)
    k = cfg["H"] // cfg["lat_steps"]
    cfg2 = dict(cfg, U=U + extra)
    big = Atlas(**cfg2).to(next(view.parameters()).device)
    sd = view.state_dict(); new = big.state_dict()
    for name in new:
        if name in ("inp.weight", "uemb.weight"):
            continue
        new[name] = sd[name]
    U2 = U + extra
    w = sd["inp.weight"]; w2 = torch.zeros_like(new["inp.weight"])
    w2[:, :2 * L * C] = w[:, :2 * L * C]
    for l in range(L):
        w2[:, 2 * L * C + l * U2: 2 * L * C + l * U2 + U] = w[:, 2 * L * C + l * U: 2 * L * C + (l + 1) * U]
    w2[:, 2 * L * C + L * U2:] = w[:, 2 * L * C + L * U:]
    new["inp.weight"] = w2
    w = sd["uemb.weight"]; w2 = torch.zeros_like(new["uemb.weight"])
    for j in range(k):
        w2[:, j * U2: j * U2 + U] = w[:, j * U: (j + 1) * U]
    new["uemb.weight"] = w2
    big.load_state_dict(new)
    big.hybrid_meta = dict(extra_forcing=extra, systems=list(SYSTEMS), offset="previous_day2")   # kept out of cfg: load_any reads cfg
    return big


def fresh_mask(fresh_lat, L, H=24, device="cpu"):
    """Atlas-100M-H2 (PREREG addendum H2): for input position p of the L+H window, True where the system's day1 run
    (issued 24 h before that valid hour) was published by the forecast start under a publication delay of fresh_lat
    hours: lead = p - L + 1 <= 24 - fresh_lat. Past hours (lead <= 0) always qualify."""
    lead = torch.arange(L + H, device=device) - L + 1
    return lead <= 24 - fresh_lat


class HybridData:
    def __init__(self, raw, nwp, k=32, fresh_lat=0):
        self.Z, lat, lon, elev, M = R5.load(False)                          # live inputs (gaps carried forward)
        O = np.load(os.path.join(raw, "W5K_OBS.npy"), mmap_mode="r")
        off = M["offset"].astype(np.float32); mu = R5.MEAN - off
        self.Zt = torch.empty_like(self.Z)
        for i in range(0, self.Z.shape[0], 256):
            self.Zt[i:i + 256] = torch.from_numpy(((O[i:i + 256, :self.Z.shape[1]].astype(np.float32) - mu) / R5.STD).astype(np.float16)).to(DEV)
        nb = R5.neighbours(lat, lon, k)
        self.bt = R5.Batcher(self.Z, nb, R5.geometry(lat, lon, nb), R5.static_feats(lat, lon, elev), 24)
        z = np.load(nwp)
        self.HS = z["stations"]
        self.fresh_lat = fresh_lat                                            # 0: registered hybrid (day2 only); >0: H2

        def enc(F):
            Fz = (F - R5.MEAN[None, None, None]) / R5.STD[None, None, None]   # the benchmark's scaler
            ok = np.isfinite(Fz).all(-1, keepdims=True)
            return torch.from_numpy(np.concatenate([np.nan_to_num(Fz), ok], -1).astype(np.float16)).to(DEV)  # [Ms, T, S, 6]
        self.sysF = enc(z["F"][..., 1])                                       # day2: [systems, T, S, 5] -> 6 channels
        self.Ms = z["F"].shape[0]
        self.extra = self.Ms * 6
        if fresh_lat:
            self.sysF1 = enc(z["F"][..., 0])                                  # day1
            self.use1 = fresh_mask(fresh_lat, R5.L, 24, DEV)                  # [L+24]
            self.extra = self.Ms * 7                                          # + a "day1 run used" flag per system
        self.T = min(self.Z.shape[1], z["F"].shape[1])

    def batch(self, si, t0):
        """si: index into HS [B]; t0 first input hour [B]. The centre station gets the systems' forecasts; neighbours a 0 flag."""
        s = torch.as_tensor(self.HS, device=DEV)[si]
        b = self.bt(s, t0)
        tt = t0[:, None] + torch.arange(R5.L + 24, device=DEV)[None]
        x = self.sysF[:, tt, si[:, None]]                                     # [Ms, B, L+H, 6]
        if self.fresh_lat:
            u = self.use1[None, None, :, None]
            x = torch.where(u, self.sysF1[:, tt, si[:, None]], x)
            x = torch.cat([x, u.expand(*x.shape[:3], 1).to(x.dtype)], -1)     # [Ms, B, L+H, 7]
        x = x.permute(1, 2, 0, 3).reshape(len(si), R5.L + 24, -1).float()     # [B, L+H, Ms*6 or Ms*7]
        ext = torch.zeros(len(si), b["yc"].shape[1], R5.L + 24, self.extra, device=DEV)
        ext[:, 0] = x
        b["uc"] = torch.cat([b["uc"], ext[:, :, :R5.L]], -1)
        b["uf"] = torch.cat([b["uf"], ext[:, :, R5.L:]], -1)
        tr = self.Zt[s[:, None], tt[:, R5.L:]].float()                        # observed truth [B, H, 5]
        b["y"], b["my"] = torch.nan_to_num(tr), torch.isfinite(tr).float()
        return b

    def starts(self, split, every=1):
        a, e = hour(SPLIT[split][0]), min(hour(SPLIT[split][1]), self.T)
        return np.arange(max(a, R5.L), e - 24 + 1, every) - R5.L             # first input hours


def train(a):
    D = HybridData(a.raw, a.nwp, fresh_lat=a.fresh_latency)
    pure = load_any(a.view, DEV).to(DEV)
    m = widen_forcing(pure, D.extra).to(DEV)
    if a.fresh_latency:
        m.hybrid_meta.update(offset=f"freshest published, delay {a.fresh_latency} h", fresh_latency=a.fresh_latency)
    torch.manual_seed(a.seed)
    tag = a.name
    with torch.no_grad():                                                     # exactness: the widened model = the pure one
        t0 = torch.as_tensor(D.starts("val", 24)[:64], device=DEV); si = torch.arange(len(t0), device=DEV) % len(D.HS)
        b = D.batch(si, t0)
        q1 = m(b["yc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])[0]
        q0 = pure(b["yc"], b["mc"], b["uc"][..., :4], b["uf"][..., :4], b["geo"], None, b["static"])[0]
        gap = float((q1 - q0).abs().max())
    print(f"H0 widening check: max |hybrid - pure| at start = {gap:.2e}", flush=True)
    assert gap < 1e-3, "the widened model does not start as the pure model (a logic error shows up at order 1)"
    del pure
    tr = torch.as_tensor(D.starts("train"), device=DEV); va = D.starts("val", 6)
    opt = torch.optim.AdamW(m.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1, (s + 1) / 500) * (0.1 + 0.45 * (1 + math.cos(math.pi * min(1, s / a.steps)))))
    bf16 = DEV == "cuda" and torch.cuda.is_bf16_supported()

    def val():
        m.eval(); sae = torch.zeros(5, device=DEV, dtype=torch.float64); cnt = torch.zeros_like(sae)
        with torch.no_grad():
            for j in range(0, len(va), 64):
                t0 = torch.as_tensor(va[j:j + 64], device=DEV)
                for si0 in range(len(D.HS)):
                    si = torch.full_like(t0, si0); b = D.batch(si, t0)
                    with torch.autocast(DEV, dtype=torch.bfloat16, enabled=bf16):
                        p = m(b["yc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])[0][:, 0, :, :, 1].float()
                    e = (p - b["y"]).abs() * torch.tensor(R5.STD, device=DEV) * b["my"]
                    sae += e.sum((0, 1)).double(); cnt += b["my"].sum((0, 1)).double()
        m.train()
        mae = (sae / cnt).cpu().numpy()
        return float(np.mean(mae / R5.STD)), mae.tolist()

    best, bad, hist = *val()[:1], 0, []
    print(f"step 0 (= pure model) val E {best:.5f}", flush=True)
    os.makedirs(a.out, exist_ok=True)
    torch.save(dict(sd=m.state_dict(), cfg=m.cfg, meta=m.hybrid_meta), os.path.join(a.out, f"{tag}_best.pt"))
    for step in range(1, a.steps + 1):
        t0 = tr[torch.randint(0, len(tr), (a.bs,), device=DEV)]
        si = torch.randint(0, len(D.HS), (a.bs,), device=DEV)
        b = D.batch(si, t0)
        with torch.autocast(DEV, dtype=torch.bfloat16, enabled=bf16):
            q, _, _ = m(b["yc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])
            loss = Dm.pinball(q[:, 0].float(), b["y"], b["my"])
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step(); sched.step()
        if step % a.every == 0 or step == a.steps:
            E, mae = val()
            hist.append(dict(step=step, E=E, mae=mae, loss=loss.item()))
            if E < best - 1e-5:
                best, bad = E, 0
                torch.save(dict(sd=m.state_dict(), cfg=m.cfg, meta=m.hybrid_meta, step=step, val_E=E), os.path.join(a.out, f"{tag}_best.pt"))
            else:
                bad += 1
            print(f"step {step} val E {E:.5f} (best {best:.5f}) loss {loss.item():.4f}", flush=True)
            if bad >= a.patience:
                break
    json.dump(dict(history=hist, best=best, fresh_latency=a.fresh_latency, seed=a.seed), open(os.path.join(a.out, f"{tag}_train.json"), "w"), indent=1)


# ================================================================================================= score
def score(a):
    import paired_w5k as PW
    D = HybridData(a.raw, a.nwp)
    D2 = HybridData(a.raw, a.nwp, fresh_lat=a.fresh_latency) if a.hybrid2 else None
    z = np.load(a.nwp); Fall = z["F"]                                         # [Ms, T, S, 5, 2] own units
    O = np.load(os.path.join(a.raw, "W5K_OBS.npy"), mmap_mode="r")
    M = np.load(os.path.join(a.raw, "W5K_META.npz")); off = M["offset"].astype(np.float32)
    obs = (O[D.HS, :D.T].astype(np.float32) + off).transpose(1, 0, 2)          # [T, S, 5] own units
    st = D.starts("test", 6)                                                   # first input hours
    starts = st + R5.L                                                         # forecast start hours
    days = (starts - starts[0]) // 24
    nd = int(days.max()) + 1
    S = len(D.HS)
    out = {}

    def acc(pred_fn, name):
        sae = np.zeros((S, nd, 5)); cnt = np.zeros((S, nd, 5))
        for j, s0 in enumerate(starts):
            p = pred_fn(j, s0)                                                 # [S, 24, 5] own units
            y = obs[s0:s0 + 24]                                                # [24, S, 5]
            ok = np.isfinite(y).transpose(1, 0, 2) & np.isfinite(p)
            e = np.where(ok, np.abs(p - np.nan_to_num(y).transpose(1, 0, 2)), 0)
            sae[:, days[j]] += e.sum(1); cnt[:, days[j]] += ok.sum(1)
        out[name] = dict(sae=sae, cnt=cnt)
        mae = sae.sum((0, 1)) / np.maximum(cnt.sum((0, 1)), 1)
        print(f"{name:<28} " + "  ".join(f"{x:.3f}" for x in mae), flush=True)

    def model_fn(path, hybrid, D=D):
        """The model works in (value - benchmark mean) / benchmark std; R5.load's offset cancels, so value = p*std + mean."""
        m = load_any(path, DEV).to(DEV).eval()
        sd, mu = torch.tensor(R5.STD, device=DEV), torch.tensor(R5.MEAN, device=DEV)

        def f(j, s0):
            t0 = torch.full((S,), int(st[j]), device=DEV); si = torch.arange(S, device=DEV)
            b = D.batch(si, t0)
            uc, uf = (b["uc"], b["uf"]) if hybrid else (b["uc"][..., :4], b["uf"][..., :4])
            with torch.no_grad(), torch.autocast(DEV, dtype=torch.float16, enabled=(DEV == "cuda")):
                p = m(b["yc"], b["mc"], uc, uf, b["geo"], None, b["static"])[0][:, 0, :, :, 1].float()
            return (p * sd + mu).cpu().numpy()                                 # [S, 24, 5] own units
        return f

    acc(model_fn(a.pure, False), "Atlas-100M pure")
    acc(model_fn(a.hybrid, True), "Atlas-100M hybrid")
    if D2 is not None:
        acc(model_fn(a.hybrid2, True, D2), "Atlas-100M-H2")
    lead = np.arange(1, 25)
    for mi, sysname in enumerate([str(x) for x in z["systems"]]):
        if not np.isfinite(Fall[mi]).any():
            print(f"{sysname}: no data", flush=True); continue
        use1 = lead <= 24 - LATENCY                                           # day1 run already published at the start

        def raw_fn(j, s0, mi=mi, fresh=False):
            v = s0 + np.arange(24)
            f1, f2 = Fall[mi, v, :, :, 0], Fall[mi, v, :, :, 1]               # [24, S, 5]
            f = np.where((np.ones_like(use1) if fresh else use1)[:, None, None], f1, f2)
            return f.transpose(1, 0, 2)

        def bias_fn(j, s0, mi=mi):
            f = raw_fn(j, s0)                                                  # [S, 24, 5]
            past = np.arange(s0 - 30 * 24, s0)                                 # valid hours wholly before the start
            past = past[past >= 0]
            b1 = np.nanmean(Fall[mi, past, :, :, 0] - obs[past], 0)            # [S, 5]
            b2 = np.nanmean(Fall[mi, past, :, :, 1] - obs[past], 0)
            bb = np.where(use1[None, :, None], b1[:, None], b2[:, None])
            bb[..., 2] = 0                                                     # wind direction is circular: not corrected
            return f - np.nan_to_num(bb)

        acc(raw_fn, f"{sysname} raw")
        acc(bias_fn, f"{sysname} bias-corrected")
        acc(lambda j, s0, mi=mi: raw_fn(j, s0, mi, True), f"{sysname} day1 (freshest, not yet published)")
    def family(oursname, skip, fname):
        """One Holm family: `oursname` against every other forecast in `out` except those in `skip`."""
        rows = []
        ours = out[oursname]
        for k, v in out.items():
            if k == oursname or k in skip:
                continue
            both = dict(sae=ours["sae"], cnt=np.minimum(ours["cnt"], v["cnt"]))
            for r in PW.compare(dict(sae=ours["sae"], cnt=both["cnt"]), dict(sae=v["sae"], cnt=both["cnt"])):
                r.update(opponent=k); rows.append(r)
        p = np.array([max(1.0 if np.isnan(r["p_dm"]) else r["p_dm"], r["p_bootstrap"]) for r in rows])
        for r, ph in zip(rows, PW.holm(p)):
            r["p_holm"] = float(ph)
            ci_ok = r["ci95_pct"][1] < 0 if r["diff_pct"] < 0 else r["ci95_pct"][0] > 0
            r["verdict"] = ("WIN" if r["diff_pct"] < 0 else "LOSS") if (ph < 0.01 and ci_ok) else "TIE"
            print(f"TEST {oursname} vs {r['opponent']:<34} {r['variable']:<19} {r['ours']:.3f} vs {r['theirs']:.3f} "
                  f"{r['diff_pct']:+.2f}% p_holm {r['p_holm']:.2g} {r['verdict']}", flush=True)
        os.makedirs(a.out, exist_ok=True)
        json.dump(dict(model=oursname, tests=rows, stations=len(D.HS), starts=len(starts),
                       first=str(START + np.timedelta64(int(starts[0]), "h")),
                       last=str(START + np.timedelta64(int(starts[-1]), "h")), latency_h=LATENCY,
                       hybrid_input_latency_h=(a.fresh_latency if oursname == "Atlas-100M-H2" else None),
                       mae={k: (v["sae"].sum((0, 1)) / np.maximum(v["cnt"].sum((0, 1)), 1)).tolist() for k, v in out.items()}),
                  open(os.path.join(a.out, fname), "w"), indent=1, default=float)

    family("Atlas-100M hybrid", {"Atlas-100M-H2"}, "atlas100m_hybrid_results.json")    # the registered family (section H)
    if D2 is not None:
        family("Atlas-100M-H2", set(), "atlas100m_h2_results.json")                   # addendum H2: its own family


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "train", "score"])
    ap.add_argument("--raw", required=True, help="the live data folder (fetch_isd_live.py): W5K_X.npy, W5K_OBS.npy, W5K_META.npz")
    ap.add_argument("--nwp", default="")
    ap.add_argument("--view", default="", help="Atlas-100M weather view (pure)")
    ap.add_argument("--hybrid", default="")
    ap.add_argument("--pure", default="")
    ap.add_argument("--out", default=os.environ.get("ATLAS_OUT", "out"))
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--every", type=int, default=1000)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", default="hybrid", help="checkpoint tag: hybrid (registered) or hybrid2 (addendum H2)")
    ap.add_argument("--fresh-latency", dest="fresh_latency", type=int, default=0,
                    help="0 = registered inputs (day2 only); >0 = H2: freshest run published this many hours before the start")
    ap.add_argument("--hybrid2", default="", help="score: the H2 checkpoint (scored in its own Holm family)")
    a = ap.parse_args()
    os.environ["PW_RAW"] = a.raw
    R5.RAW = a.raw
    {"fetch": fetch, "train": train, "score": score}[a.cmd](a)
