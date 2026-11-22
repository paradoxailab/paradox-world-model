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
# Atlas-Delhi (atlas/PREREG_DELHI.md): every other global system Open-Meteo archives; a system without data is skipped
SYSTEMS_ALL = dict(SYSTEMS, **{"AIGFS": ["ncep_aigfs025"], "ICON": ["icon_global", "icon_seamless"],
                               "UKMO": ["ukmo_global_deterministic_10km", "ukmo_seamless"],
                               "ARPEGE": ["meteofrance_arpege_world", "meteofrance_seamless"],
                               "JMA": ["jma_gsm", "jma_seamless"], "CMA": ["cma_grapes_global"], "GEM": ["gem_global", "gem_seamless"]})
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


def resolve(cands, la, lo, dates=("2024-06-01", "2024-12-01", "2025-07-01")):
    """First model id with data on ANY of `dates` (PREREG deviation 7: GraphCast's archive has gaps, e.g. June 2024,
    so a single test date wrongly reported it missing)."""
    for m in cands:
        for d in dates:
            j = get(dict(latitude=la, longitude=lo, hourly="temperature_2m_previous_day1", models=m,
                         start_date=d, end_date=d, timezone="GMT"))
            j = j[0] if isinstance(j, list) else j
            if not j.get("error") and any(v is not None for v in j.get("hourly", {}).get("temperature_2m_previous_day1", [])):
                return m
    return None


def fetch(a):
    M = np.load(os.path.join(a.raw, "W5K_META.npz"))
    T = int((np.datetime64(str(M["live_end"])) - START) / np.timedelta64(1, "h")) + 1
    lat, lon = M["lat"].astype(float), M["lon"].astype(float)
    HS = np.array(json.load(open(a.stations_file))["index"], dtype=np.int64) if a.stations_file else stations(len(lat))
    cache = os.path.join(a.out, "cache"); os.makedirs(cache, exist_ok=True)
    end = (START + np.timedelta64(T - 1, "h")).astype("datetime64[D]").astype(str)
    hv = [f"{v}_{o}" for o in OFFS for v in OM_VARS]
    SYS = SYSTEMS_ALL if a.systems == "all" else SYSTEMS
    F = np.full((len(SYS), T, len(HS), 5, 2), np.nan, np.float32)
    ids = {}
    keep = json.loads(str(np.load(a.reuse_ids)["ids"])) if a.reuse_ids else {}   # deviation 7: same ids as the first archive
    for si, (sysname, cands) in enumerate(SYS.items()):
        mid = keep.get(sysname) or resolve(cands, lat[HS[0]], lon[HS[0]])
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
    np.savez_compressed(os.path.join(a.out, a.nwp_name), F=F, systems=np.array(list(SYS)), ids=np.array(json.dumps(ids)),
                        stations=HS, vars=np.array(OM_VARS), offsets=np.array(OFFS), start=np.array(str(START)))
    cov = {s: float(np.isfinite(F[i]).mean()) for i, s in enumerate(SYS)}
    print("NWP " + json.dumps(dict(ids=ids, coverage=cov, hours=T, stations=len(HS))), flush=True)


# ================================================================================================= model
def widen_forcing(view, extra, systems=None):
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
    big.hybrid_meta = dict(extra_forcing=extra, systems=list(systems or SYSTEMS), offset="previous_day2")   # kept out of cfg: load_any reads cfg
    return big


def fresh_mask(fresh_lat, L, H=24, device="cpu"):
    """Atlas-100M-H2 (PREREG addendum H2): for input position p of the L+H window, True where the system's day1 run
    (issued 24 h before that valid hour) was published by the forecast start under a publication delay of fresh_lat
    hours: lead = p - L + 1 <= 24 - fresh_lat. Past hours (lead <= 0) always qualify."""
    lead = torch.arange(L + H, device=device) - L + 1
    return lead <= 24 - fresh_lat


class HybridData:
    def __init__(self, raw, nwp, k=32, fresh_lat=0, input_systems=None, model_systems=None):
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
        names = [str(x) for x in z["systems"]]
        sel = [names.index(n) for n in model_systems] if model_systems else list(range(len(names)))   # Atlas-Delhi:
        self.names = [names[i] for i in sel]                                  # the systems (and order) the model reads
        Fm = z["F"][sel]
        self.sysF = enc(Fm[..., 1])                                           # day2: [systems, T, S, 5] -> 6 channels
        self.Ms = len(sel)
        self.extra = self.Ms * 6
        if fresh_lat:
            self.sysF1 = enc(Fm[..., 0])                                      # day1
            self.use1 = fresh_mask(fresh_lat, R5.L, 24, DEV)                  # [L+24]
            self.extra = self.Ms * 7                                          # + a "day1 run used" flag per system
        self.T = min(self.Z.shape[1], z["F"].shape[1])
        if input_systems:                                                     # deviation 7: the hybrid reads only the
            for i, n in enumerate(self.names):                                # systems it was trained with; the others
                                                                              # are opponents only (inputs zero, flag 0)
                if n not in input_systems:
                    self.sysF[i] = 0
                    if fresh_lat:
                        self.sysF1[i] = 0

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


def subset(D, fn):
    """Positions in D.HS of the WEATHER-5K stations listed in a JSON file's 'index' (Atlas-Delhi: training / scoring subsets)."""
    if not fn:
        return None
    want = set(int(i) for i in json.load(open(fn))["index"])
    pos = [k for k, h in enumerate(D.HS.tolist()) if int(h) in want]
    assert pos, f"none of the stations in {fn} is in the archive"
    return np.array(pos, dtype=np.int64)


def model_systems(a, nwp):
    if not a.model_systems:
        return None
    if a.model_systems == "all":                                              # every system with data in the archive
        z = np.load(nwp)
        return [str(n) for i, n in enumerate(z["systems"]) if np.isfinite(z["F"][i]).any()]
    return a.model_systems.split(",")


def train(a):
    D = HybridData(a.raw, a.nwp, fresh_lat=a.fresh_latency, model_systems=model_systems(a, a.nwp))
    trs, vas = subset(D, a.train_stations), subset(D, a.val_stations)
    torch.manual_seed(a.seed)
    tag = a.name
    if a.init:                                                                # Atlas-Delhi stage 2: continue from a hybrid
        ck = torch.load(a.init, map_location=DEV)
        m = load_any(a.init, DEV).to(DEV); m.hybrid_meta = dict(ck.get("meta", {}), init=os.path.basename(a.init))
        assert m.hybrid_meta.get("systems", D.names) == D.names, "the checkpoint reads other systems than the archive gives"
        pure = None
    else:
        pure = load_any(a.view, DEV).to(DEV)
        m = widen_forcing(pure, D.extra, D.names).to(DEV)
    if a.fresh_latency:
        m.hybrid_meta.update(offset=f"freshest published, delay {a.fresh_latency} h", fresh_latency=a.fresh_latency)
    with torch.no_grad():                                                     # exactness: the widened model = the pure one
        t0 = torch.as_tensor(D.starts("val", 24)[:64], device=DEV); si = torch.arange(len(t0), device=DEV) % len(D.HS)
        b = D.batch(si, t0)
        q1 = m(b["yc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])[0]
        q0 = q1 if pure is None else pure(b["yc"], b["mc"], b["uc"][..., :4], b["uf"][..., :4], b["geo"], None, b["static"])[0]
        gap = float((q1 - q0).abs().max())
    if pure is not None:
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
                for si0 in (vas if vas is not None else range(len(D.HS))):
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
        si = torch.randint(0, len(D.HS), (a.bs,), device=DEV) if trs is None else \
            torch.as_tensor(trs, device=DEV)[torch.randint(0, len(trs), (a.bs,), device=DEV)]
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
    json.dump(dict(history=hist, best=best, fresh_latency=a.fresh_latency, seed=a.seed, systems=D.names,
                   train_stations=a.train_stations, val_stations=a.val_stations, init=a.init), open(os.path.join(a.out, f"{tag}_train.json"), "w"), indent=1)


# ================================================================================================= score
def compare_days(a, b, names, B=10000, seed=0, block=7):
    """Atlas-Delhi (PREREG_DELHI.md A6): with two stations a station bootstrap means nothing, so the interval comes from a
    moving-block bootstrap over DAYS (7-day blocks) and the Diebold-Mariano test runs on the daily mean difference."""
    import paired_w5k as PW
    rng = np.random.default_rng(seed)
    rows = []
    nd = a["sae"].shape[1]
    nb = int(math.ceil(nd / block))
    idx = (rng.integers(0, max(nd - block + 1, 1), size=(B, nb))[..., None] + np.arange(block)).reshape(B, -1)[:, :nd]
    for v, n in enumerate(names):
        m = (a["cnt"][..., v] > 0) & (b["cnt"][..., v] > 0)
        c = np.where(m, a["cnt"][..., v], 0).astype(np.float64)
        sa = np.where(m, a["sae"][..., v], 0).astype(np.float64); sb = np.where(m, b["sae"][..., v], 0).astype(np.float64)
        if c.sum() == 0:
            continue
        mae_a, mae_b = sa.sum() / c.sum(), sb.sum() / c.sum()
        Dd, Cd = (sa - sb).sum(0), c.sum(0)                                     # per day, summed over stations
        boot = Dd[idx].sum(1) / np.maximum(Cd[idx].sum(1), 1)
        p_boot = min(1.0, 2 * min((boot >= 0).mean(), (boot <= 0).mean()) + 1 / B)
        day = Dd / np.maximum(Cd, 1)
        rows.append(dict(variable=n, ours=round(mae_a, 4), theirs=round(mae_b, 4), diff_pct=round(100 * (mae_a / mae_b - 1), 2),
                         ci95_pct=[round(100 * np.quantile(boot, 0.025) / mae_b, 2), round(100 * np.quantile(boot, 0.975) / mae_b, 2)],
                         p_bootstrap=float(p_boot), p_dm=float(PW.dm(day[Cd > 0])), points=int(c.sum()), cluster=f"days ({block}-day blocks)"))
    return rows


def tsfm_forecasts(key, D, sel, st, H=24, ctx=512):
    """Zero-shot foundation model on each station's own past (gap-filled inputs, own units): [starts, S, 24, 5]."""
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "delhi", "pw"))
    import opponents as Op
    fc = Op.make(key, ctx, H)
    sd, mu = R5.STD, R5.MEAN
    HSs = D.HS[sel]
    out = np.full((len(st), len(sel), H, 5), np.nan, np.float32)
    for j0 in range(0, len(st), 256):
        jj = st[j0:j0 + 256] + R5.L                                             # forecast start hours
        tt = np.clip(jj[:, None] + np.arange(-ctx, 0)[None], 0, None)           # [n, ctx]
        w = D.Z[torch.as_tensor(HSs, device=DEV)[:, None, None], torch.as_tensor(tt, device=DEV)[None]].float().cpu().numpy()
        w = w * sd + mu                                                         # [S, n, ctx, 5] own units
        c = np.nan_to_num(w.transpose(0, 1, 3, 2).reshape(-1, ctx))             # [S*n*5, ctx]
        q = np.asarray(fc(c))[..., 1].reshape(len(sel), len(jj), 5, H)          # median
        out[j0:j0 + len(jj)] = q.transpose(1, 0, 3, 2)
    return out, fc.name


def score(a):
    import paired_w5k as PW
    ins = a.input_systems.split(",") if a.input_systems else None
    ms = model_systems(a, a.nwp)                                              # the systems the hybrids were trained on
    D = HybridData(a.raw, a.nwp, input_systems=ins, model_systems=ms)
    D2 = HybridData(a.raw, a.nwp, fresh_lat=a.fresh_latency, input_systems=ins, model_systems=ms) if a.hybrid2 else None
    D3 = None
    if a.delhi:                                                                # Atlas-Delhi reads every system it was trained on
        dsys = torch.load(a.delhi, map_location="cpu").get("meta", {}).get("systems")
        D3 = HybridData(a.raw, a.nwp, fresh_lat=a.delhi_latency, model_systems=dsys)
    z = np.load(a.nwp); Fall = z["F"]                                         # [Ms, T, S, 5, 2] own units
    sel = subset(D, a.score_stations)
    sel = np.arange(len(D.HS)) if sel is None else sel
    Fall = Fall[:, :, sel]
    O = np.load(os.path.join(a.raw, "W5K_OBS.npy"), mmap_mode="r")
    M = np.load(os.path.join(a.raw, "W5K_META.npz")); off = M["offset"].astype(np.float32)
    obs = (O[D.HS[sel], :D.T].astype(np.float32) + off).transpose(1, 0, 2)    # [T, S, 5] own units
    st = D.starts("test", 6)                                                   # first input hours
    starts = st + R5.L                                                         # forecast start hours
    days = (starts - starts[0]) // 24
    nd = int(days.max()) + 1
    S = len(sel)
    out = {}
    P = {}                                                                     # name -> forecasts [starts, S, 24, 5]
    Y = np.stack([obs[s0:s0 + 24].transpose(1, 0, 2) for s0 in starts]).astype(np.float32)   # truth [starts, S, 24, 5]

    def acc(pred_fn, name, pre=None):
        sae = np.zeros((S, nd, 5)); cnt = np.zeros((S, nd, 5))
        Pn = np.full((len(starts), S, 24, 5), np.nan, np.float32) if pre is None else pre
        for j, s0 in enumerate(starts):
            p = Pn[j] if pre is not None else pred_fn(j, s0)                   # [S, 24, 5] own units
            Pn[j] = p
            y = obs[s0:s0 + 24]                                                # [24, S, 5]
            ok = np.isfinite(y).transpose(1, 0, 2) & np.isfinite(p)
            e = np.where(ok, np.abs(p - np.nan_to_num(y).transpose(1, 0, 2)), 0)
            sae[:, days[j]] += e.sum(1); cnt[:, days[j]] += ok.sum(1)
        out[name] = dict(sae=sae, cnt=cnt)
        P[name] = Pn
        mae = sae.sum((0, 1)) / np.maximum(cnt.sum((0, 1)), 1)
        print(f"{name:<28} " + "  ".join(f"{x:.3f}" for x in mae), flush=True)

    def model_fn(path, hybrid, D=D):
        """The model works in (value - benchmark mean) / benchmark std; R5.load's offset cancels, so value = p*std + mean."""
        m = load_any(path, DEV).to(DEV).eval()
        sd, mu = torch.tensor(R5.STD, device=DEV), torch.tensor(R5.MEAN, device=DEV)

        def f(j, s0):
            t0 = torch.full((S,), int(st[j]), device=DEV); si = torch.as_tensor(sel, device=DEV)
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
    if D3 is not None:
        acc(model_fn(a.delhi, True, D3), "Atlas-Delhi")
    lead = np.arange(1, 25)
    published, newest = [], []
    for mi, sysname in enumerate([str(x) for x in z["systems"]]):
        if not np.isfinite(Fall[mi]).any():
            print(f"{sysname}: no data", flush=True); continue
        use1 = lead <= 24 - LATENCY                                           # day1 run already published at the start

        def raw_fn(j, s0, mi=mi, fresh=False, use1=use1):
            v = s0 + np.arange(24)
            f1, f2 = Fall[mi, v, :, :, 0], Fall[mi, v, :, :, 1]               # [24, S, 5]
            f = np.where((np.ones_like(use1) if fresh else use1)[:, None, None], f1, f2)
            return f.transpose(1, 0, 2)

        def bias_fn(j, s0, mi=mi, fresh=False, use1=use1):
            f = raw_fn(j, s0, mi, fresh)                                       # [S, 24, 5]
            past = np.arange(s0 - 30 * 24, s0)                                 # valid hours wholly before the start
            past = past[past >= 0]
            b1 = np.nanmean(Fall[mi, past, :, :, 0] - obs[past], 0)            # [S, 5]
            b2 = np.nanmean(Fall[mi, past, :, :, 1] - obs[past], 0)
            bb = np.where((np.ones_like(use1) if fresh else use1)[None, :, None], b1[:, None], b2[:, None])
            bb[..., 2] = 0                                                     # wind direction is circular: not corrected
            return f - np.nan_to_num(bb)

        acc(raw_fn, f"{sysname} raw")
        acc(bias_fn, f"{sysname} bias-corrected")
        acc(lambda j, s0, mi=mi: raw_fn(j, s0, mi, True), f"{sysname} day1 (freshest, not yet published)")
        published += [f"{sysname} raw", f"{sysname} bias-corrected"]
        newest.append(f"{sysname} day1 (freshest, not yet published)")
        if a.delhi:                                                            # PREREG_DELHI A5: the upper-bound family
            acc(lambda j, s0, mi=mi: bias_fn(j, s0, mi, True), f"{sysname} day1 bias-corrected (not yet published)")
            newest.append(f"{sysname} day1 bias-corrected (not yet published)")
    if a.delhi:
        bc = [k for k in published if k.endswith("bias-corrected")]
        ens = np.nanmean(np.stack([P[k] for k in bc]), 0)                      # mean of the bias-corrected systems
        ens[..., 2] = np.nan                                                   # (no mean of a circular variable)
        acc(None, "Ensemble of all systems (bias-corrected)", pre=ens)
        published.append("Ensemble of all systems (bias-corrected)")
        for key in [k for k in a.tsfm.split(",") if k]:
            try:
                Pt, nm = tsfm_forecasts(key, D, sel, st)
                acc(None, nm, pre=Pt); published.append(nm)
            except Exception as e:
                print(f"{key}: not run ({str(e)[:160]})", flush=True)

    def joint(na, nb, PP=P, YY=Y):
        """PREREG deviation 8: both forecasts scored on exactly the same hours (truth observed and BOTH forecasts present),
        then summed per station-day. Before, our errors were summed over all our hours while only the hours shared with
        the opponent were counted, which inflated our error wherever an opponent's archive had gaps."""
        K = YY.shape[-1]
        sa = np.zeros((S, nd, K)); sb = np.zeros((S, nd, K)); c = np.zeros((S, nd, K))
        ok = np.isfinite(YY) & np.isfinite(PP[na]) & np.isfinite(PP[nb])       # [starts, S, h, K]
        ea = np.where(ok, np.abs(PP[na] - np.nan_to_num(YY)), 0).sum(2)        # [starts, S, K]
        eb = np.where(ok, np.abs(PP[nb] - np.nan_to_num(YY)), 0).sum(2)
        n = ok.sum(2)
        for j in range(len(starts)):
            sa[:, days[j]] += ea[j]; sb[:, days[j]] += eb[j]; c[:, days[j]] += n[j]
        return dict(sae=sa, cnt=c), dict(sae=sb, cnt=c)

    def family(oursname, skip, fname, only=None, PP=P, YY=Y, names=None):
        """One Holm family: `oursname` against every other forecast in `out` except those in `skip` (or only those in `only`)."""
        rows = []
        opp = only if only is not None else [k for k in out if k != oursname and k not in skip]
        for k in opp:
            if k == oursname or k not in PP:
                continue
            ja, jb = joint(oursname, k, PP, YY)
            res = compare_days(ja, jb, names or PW.NAMES) if (a.cluster == "days" or names) else PW.compare(ja, jb)
            for r in res:
                r.update(opponent=k); rows.append(r)
        p = np.array([max(1.0 if np.isnan(r["p_dm"]) else r["p_dm"], r["p_bootstrap"]) for r in rows])
        for r, ph in zip(rows, PW.holm(p)):
            r["p_holm"] = float(ph)
            ci_ok = r["ci95_pct"][1] < 0 if r["diff_pct"] < 0 else r["ci95_pct"][0] > 0
            r["verdict"] = ("WIN" if r["diff_pct"] < 0 else "LOSS") if (ph < 0.01 and ci_ok) else "TIE"
            print(f"TEST {oursname} vs {r['opponent']:<34} {r['variable']:<19} {r['ours']:.3f} vs {r['theirs']:.3f} "
                  f"{r['diff_pct']:+.2f}% p_holm {r['p_holm']:.2g} {r['verdict']}", flush=True)
        os.makedirs(a.out, exist_ok=True)
        json.dump(dict(model=oursname, tests=rows, stations=S, station_ids=D.HS[sel].tolist(), starts=len(starts),
                       first=str(START + np.timedelta64(int(starts[0]), "h")),
                       last=str(START + np.timedelta64(int(starts[-1]), "h")), latency_h=LATENCY, cluster=a.cluster,
                       hybrid_input_latency_h=(a.fresh_latency if oursname == "Atlas-100M-H2" else
                                               a.delhi_latency if oursname == "Atlas-Delhi" else None),
                       mae={k: (v["sae"].sum((0, 1)) / np.maximum(v["cnt"].sum((0, 1)), 1)).tolist() for k, v in out.items()}),
                  open(os.path.join(a.out, fname.replace(".json", f"{a.suffix}.json")), "w"), indent=1, default=float)

    family("Atlas-100M hybrid", {"Atlas-100M-H2", "Atlas-Delhi"}, "atlas100m_hybrid_results.json")    # registered family (H)
    if D2 is not None:
        family("Atlas-100M-H2", {"Atlas-Delhi"}, "atlas100m_h2_results.json")                        # addendum H2
    if D3 is not None:                                                                               # PREREG_DELHI
        f1 = published + ["Atlas-100M-H2", "Atlas-100M hybrid", "Atlas-100M pure"]
        family("Atlas-Delhi", set(), "atlas_delhi_F1_published.json", only=f1)
        family("Atlas-Delhi", set(), "atlas_delhi_F2_newest_run.json", only=newest)
        # F3: 24-h maximum and minimum temperature of each forecast window (hours where the truth was observed)
        okY = np.isfinite(Y[..., 0])                                                                 # [starts, S, 24]
        full = okY.sum(2) >= 20
        def mm(X):
            x = np.where(okY, X[..., 0], np.nan)
            r = np.stack([np.nanmax(x, 2), np.nanmin(x, 2)], -1)[:, :, None]                        # [starts, S, 1, 2]
            r[~full] = np.nan
            return r
        with np.errstate(all="ignore"):
            P3 = {k: mm(v) for k, v in P.items()}; Y3 = mm(Y)
        family("Atlas-Delhi", set(), "atlas_delhi_F3_maxmin.json", only=f1, PP=P3, YY=Y3,
               names=["24-h max temperature", "24-h min temperature"])
        # seasons (descriptive): MAE per forecaster and variable by the month the forecast starts
        mon = ((START + starts.astype("timedelta64[h]")).astype("datetime64[M]").astype(int) % 12) + 1
        seasons = dict(winter_DJF=(12, 1, 2), premonsoon_MAM=(3, 4, 5), monsoon_JJAS=(6, 7, 8, 9), postmonsoon_ON=(10, 11))
        tab = {}
        for sn, months in seasons.items():
            jm = np.isin(mon, months)
            tab[sn] = {}
            for k, Pk in P.items():
                okk = np.isfinite(Y[jm]) & np.isfinite(Pk[jm])
                tab[sn][k] = (np.where(okk, np.abs(Pk[jm] - np.nan_to_num(Y[jm])), 0).sum((0, 1, 2)) / np.maximum(okk.sum((0, 1, 2)), 1)).tolist()
        json.dump(dict(seasons=tab, variables=PW.NAMES), open(os.path.join(a.out, f"atlas_delhi_seasons{a.suffix}.json"), "w"), indent=1)
    if a.save_forecasts:
        np.savez_compressed(os.path.join(a.out, f"forecasts{a.suffix}.npz"), names=np.array(list(P)), starts=starts,
                            stations=D.HS[sel], Y=Y, **{f"P{i}": v for i, v in enumerate(P.values())})


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
    ap.add_argument("--stations-file", dest="stations_file", default="", help="fetch: JSON with an 'index' list (e.g. india_stations.json)")
    ap.add_argument("--nwp-name", dest="nwp_name", default="NWP_W5K.npz", help="fetch: archive file name")
    ap.add_argument("--reuse-ids", dest="reuse_ids", default="", help="fetch: keep the model ids found for an earlier archive")
    ap.add_argument("--suffix", default="", help="score: added to the result file names (e.g. _india)")
    ap.add_argument("--input-systems", dest="input_systems", default="",
                    help="score: systems the hybrids read (others scored as opponents only), e.g. IFS,AIFS,GFS")
    # Atlas-Delhi (atlas/PREREG_DELHI.md); every default below leaves the registered H / H2 / I runs unchanged
    ap.add_argument("--systems", default="core", choices=["core", "all"], help="fetch: core = IFS, AIFS, GFS, GraphCast; all = + 7 more")
    ap.add_argument("--model-systems", dest="model_systems", default="",
                    help="train/score: systems the model reads, in order ('all' = every system with data); default = all in the archive")
    ap.add_argument("--init", default="", help="train: continue from this hybrid checkpoint instead of widening the pure view")
    ap.add_argument("--train-stations", dest="train_stations", default="", help="train: JSON 'index' list of stations to train on")
    ap.add_argument("--val-stations", dest="val_stations", default="", help="train: JSON 'index' list of stations to validate on")
    ap.add_argument("--test-end", dest="test_end", default="2026-01-01T00", help="exclusive end of the test period")
    ap.add_argument("--score-stations", dest="score_stations", default="", help="score: JSON 'index' list (a subset of the archive)")
    ap.add_argument("--cluster", default="stations", choices=["stations", "days"], help="score: bootstrap unit")
    ap.add_argument("--delhi", default="", help="score: the Atlas-Delhi checkpoint (families F1-F3 of PREREG_DELHI)")
    ap.add_argument("--delhi-latency", dest="delhi_latency", type=int, default=12)
    ap.add_argument("--tsfm", default="", help="score (with --delhi): zero-shot foundation models, e.g. chronos2,tfm25")
    ap.add_argument("--save-forecasts", dest="save_forecasts", action="store_true")
    a = ap.parse_args()
    SPLIT["test"] = (SPLIT["test"][0], a.test_end)
    os.environ["PW_RAW"] = a.raw
    R5.RAW = a.raw
    {"fetch": fetch, "train": train, "score": score}[a.cmd](a)
