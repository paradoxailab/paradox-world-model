"""Atlas League v2.0: Atlas v1.3 against every scorable model on the list (rules: atlas/README.md, written first).

Delhi PM2.5, next 24 h, the Delhi league's windows and tracks. Each opponent writes one forecast file
(OUT/league2/<key>.npz: qv = validation windows [Wv, N, 24, 3], qt = test windows [Wt, N, 24, 3], meta); --score
reads them all, calibrates every entry on validation exactly as fuse.py does, and tests Atlas v1.3 against each.

  python league_v2.py --cams                                   # group B: CAMS global (Open-Meteo archive)
  python league_v2.py --spec stid --ext EXT --minutes 100      # group C: one graph architecture, authors' code in EXT
  python league_v2.py --tsfm moirai2                           # group A: one foundation model, zero-shot
  python league_v2.py --score                                  # all files against Atlas v1.3 -> LEAGUE2_REPORT.md

Inputs (Kaggle: attach the output of atlas-delhi-fusion-v13 and atlas-delhi-long): DELHI.npz, DELHI_LONG.npz,
fusion_members_atlas.npz (Atlas v1.3's saved forecasts) and opponents/*.npz (TimesFM 2.5, Chronos-2, Chronos-Bolt).
"""
import argparse, datetime as dt, glob, importlib.util, json, math, os, re, sys, time, types

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import Delhi, SPD, FLOOR, TARGETS, RAW, DM
from pw import evaluate as E
import run_atlas_delhi as R

OUT = R.OUT
L2 = os.path.join(OUT, "league2")
H, LIN = R.H, R.L                                          # 24 h ahead, 72 h of input (as Atlas)
FIRST = "2018-01-01"                                       # Atlas v1.3's Delhi stage starts here
FM = {"tfm25": "TimesFM 2.5 (Google, zero-shot)", "chronos2": "Chronos-2 (Amazon, zero-shot)",
      "chronos-bolt": "Chronos-Bolt (Amazon, zero-shot)"}
T0 = time.time()


def log(*a):
    print(*a, flush=True)


def find(name):
    hits = sorted(glob.glob(os.path.join(OUT, "**", name), recursive=True)) + \
           sorted(glob.glob(os.path.join("/kaggle/input", "**", name), recursive=True)) + \
           sorted(glob.glob(os.path.join(RAW, name)))
    return hits[0] if hits else None


def league():
    """The Delhi league on the long-history file: same stations, tracks and windows as atlas-delhi-fusion-v13."""
    D = Delhi(path=os.path.join(RAW, "DELHI_LONG.npz"), targets=TARGETS, backbone=False, wxfc=False, first=FIRST)
    te, va = D.origins("test", R.TEST_STRIDE), D.origins("val", R.VAL_STRIDE)
    return D, te, va, va[::4]


def save_entry(key, name, qv, qt, meta):
    os.makedirs(L2, exist_ok=True)
    np.savez_compressed(os.path.join(L2, key + ".npz"), qv=qv.astype(np.float32), qt=qt.astype(np.float32),
                        name=np.array(name), meta=np.array(json.dumps(meta, default=float)))
    log(f"saved {key}: {name}")


# ================================================================================================ B: CAMS
def http(url, params, tries=10):
    import requests
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=300, headers={"User-Agent": "paradox-world-model-league"})
            if r.status_code == 429:
                time.sleep(65); continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log(f"    retry {k + 1}: {str(e)[:150]}")
            time.sleep(min(60, 5 * (k + 1)))
    return None


BOX = (28.35, 28.95, 76.80, 77.45)                         # Delhi NCR: a geocode outside it is rejected


def geocode(name):
    base = re.split(r"\s+-\s+", str(name))[0]
    base = re.sub(r",?\s*(New\s+)?Delhi\b.*$", "", base, flags=re.I).strip(" ,")
    for q in dict.fromkeys([f"{base}, Delhi, India", f"{base.split(',')[0].split('(')[0].strip()}, Delhi, India",
                            f"{' '.join(base.split()[:2])}, Delhi, India"]):
        j = http("https://nominatim.openstreetmap.org/search", dict(q=q, format="json", limit=5, countrycodes="in"))
        time.sleep(1.1)
        for h in j or []:
            la, lo = float(h["lat"]), float(h["lon"])
            if BOX[0] <= la <= BOX[1] and BOX[2] <= lo <= BOX[3]:
                return la, lo
    return None


def cams(a):
    D, te, va, va4 = league()
    log(D.describe())
    first = min(va4[0], te[0]) - 40 * SPD                  # 30 trailing days for the bias correction, and margin
    d0 = dt.datetime.fromisoformat(str(D.dates[first])[:19])
    d1 = dt.datetime.fromisoformat(str(D.dates[te[-1] + H])[:19]) + dt.timedelta(days=1)
    C = np.full((D.T + 2 * H, D.N), np.nan, np.float32)
    coords = {}
    for i, s in enumerate(D.stations):
        g = geocode(s)
        coords[s] = g
        if not g:
            log(f"  {s}: not placed, left out"); continue
        j = http("https://air-quality-api.open-meteo.com/v1/air-quality",
                 dict(latitude=round(g[0], 3), longitude=round(g[1], 3), hourly="pm2_5", domains="cams_global",
                      start_date=d0.date().isoformat(), end_date=d1.date().isoformat(), timezone="Asia/Kolkata"))
        h = (j or {}).get("hourly", {})
        for ts, v in zip(h.get("time", []), h.get("pm2_5", [])):
            k = first + int((dt.datetime.fromisoformat(ts) - d0).total_seconds() // 3600)
            if 0 <= k < len(C) and v is not None:
                C[k, i] = v
        log(f"  {s}: {g[0]:.4f}, {g[1]:.4f}; CAMS hours in test {100 * np.isfinite(C[te[0]:te[-1] + H, i]).mean():.0f}%")
    Yp = D.Y[:, :, 0]

    def at(org, bc):
        tt = org[:, None] + np.arange(H)[None]                                  # [W, H]
        v = C[tt].transpose(0, 2, 1)                                           # [W, N, H]
        if bc:                                     # trailing 30-day bias at the same hour, only days before the origin
            lag = tt[:, :, None] - SPD * np.arange(1, 31)[None, None]          # [W, H, 30]
            lag = np.where(lag < org[:, None, None], lag, lag - SPD)            # never a value at or after the origin
            lag = np.clip(lag, 0, D.T - 1)
            e = C[lag] - Yp[lag]                                               # [W, H, 30, N]
            with np.errstate(all="ignore"):
                b = np.where(np.isfinite(e).sum(2) >= 10, np.nanmean(e, 2), 0.0)   # [W, H, N]
            v = v - b.transpose(0, 2, 1)
        return np.repeat(np.maximum(v, 0)[..., None], 3, -1)

    meta = dict(source="Open-Meteo air-quality archive, domain cams_global (0.4 deg); most recent run for each hour",
                coords=coords, placed=int(sum(1 for g in coords.values() if g)))
    save_entry("cams", "CAMS global (ECMWF Copernicus), archived forecast", at(va4, False), at(te, False), meta)
    save_entry("cams_bc", "CAMS global + 30-day local bias correction", at(va4, True), at(te, True), meta)


# ================================================================================================ C: graph architectures
NAMES = {"stid": "STID (CIKM 2022, authors' code)", "gwnet": "Graph WaveNet (IJCAI 2019, authors' code)",
         "staeformer": "STAEformer (CIKM 2023, authors' code)", "agcrn": "AGCRN (NeurIPS 2020, authors' code)",
         "mtgnn": "MTGNN (KDD 2020, authors' code)"}


class Windows:
    """Each repository's input format, built from the Delhi league: PM2.5 z-scored over the training period,
    missing = the repositories' null value (0 before scaling), plus time of day and day of week."""

    def __init__(self, D):
        self.D = D
        y = D.Y[:, :, 0].copy()
        b = D.bounds["train"][1]
        tr = y[:b][:, D.seen]
        tr = tr[np.isfinite(tr)]
        self.mean, self.std = float(tr.mean()), float(tr.std())
        self.raw = np.nan_to_num(y).astype(np.float32)                 # 0 = missing, as in the repositories
        self.tod = (D.tod.astype(np.float32) / 24.0)
        self.dow = D.dow.astype(np.float32)
        self.hideU = np.zeros(D.N, bool); self.hideU[D.unseen] = True
        self.seen_mask = np.zeros(D.N, bool); self.seen_mask[D.seen] = True

    def batch(self, idx, hide_unseen, dev):
        import torch
        hi = idx[:, None] + np.arange(-LIN, 0)[None]
        fo = idx[:, None] + np.arange(H)[None]
        v = self.raw[hi].copy()                                          # [B, L, N]
        if hide_unseen:
            v[..., self.hideU] = 0.0
        x = (v - self.mean) / self.std
        B, Lx, N = x.shape
        tod = np.broadcast_to(self.tod[hi][..., None], (B, Lx, N))
        dow = np.broadcast_to(self.dow[hi][..., None], (B, Lx, N))
        X = torch.from_numpy(np.stack([x, tod, dow], -1).astype(np.float32)).to(dev)
        Y = torch.from_numpy(self.raw[np.minimum(fo, len(self.raw) - 1)]).to(dev)   # [B, H, N], 0 = missing
        return X, Y


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


class Runner:
    """The authors' model class, unchanged, with their published hyper-parameters (the METR-LA configuration where
    the repository has one: METR-LA has missing readings, like Delhi; otherwise PEMS04)."""

    def __init__(self, kind, D, ext, dev):
        import torch, torch.nn as nn
        self.kind, N = kind, D.N
        if kind == "stid":
            sys.path.insert(0, os.path.join(ext, "STID", "stid"))
            from arch.stid_arch import STID
            self.net = STID(num_nodes=N, input_len=LIN, input_dim=3, embed_dim=32, output_len=H, num_layer=3,
                            if_node=True, node_dim=32, if_T_i_D=True, if_D_i_W=True, temp_dim_tid=32,
                            temp_dim_diw=32, time_of_day_size=24, day_of_week_size=7)
            self.cfg = dict(lr=2e-3, wd=1e-4, bs=64, epochs=100, milestones=[1, 50, 80], gamma=0.5, clip=5.0, patience=None,
                            source="STID/stid/METR-LA.py")
        elif kind == "gwnet":
            # The official file builds 2-D kernels with nn.Conv1d, which PyTorch accepted before 1.11 and now rejects;
            # the one compatibility change is to construct those layers as nn.Conv2d (what the old behaviour computed).
            src = open(os.path.join(ext, "Graph-WaveNet", "model.py")).read().replace("nn.Conv1d(", "nn.Conv2d(")
            m = types.ModuleType("gwnet_model")
            exec(compile(src, "Graph-WaveNet/model.py (Conv1d->Conv2d)", "exec"), m.__dict__)
            A = D.A.astype(np.float64)

            def asym(a):                                                 # util.asym_adj
                d = a.sum(1)
                d = np.where(d > 0, 1.0 / d, 0.0)
                return (d[:, None] * a).astype(np.float32)
            sup = [torch.tensor(asym(A)).to(dev), torch.tensor(asym(A.T)).to(dev)]     # "doubletransition"
            self.net = m.gwnet(dev, N, 0.3, supports=sup, gcn_bool=True, addaptadj=True, aptinit=None, in_dim=2,
                               out_dim=H, residual_channels=32, dilation_channels=32, skip_channels=256, end_channels=512)
            self.cfg = dict(lr=1e-3, wd=1e-4, bs=64, epochs=100, milestones=None, gamma=None, clip=5.0, patience=None,
                            source="Graph-WaveNet/train.py defaults (METR-LA)")
        elif kind == "staeformer":
            import yaml
            m = _module(os.path.join(ext, "STAEformer", "model", "STAEformer.py"), "staeformer_model")
            y = yaml.safe_load(open(os.path.join(ext, "STAEformer", "model", "STAEformer.yaml")))["METRLA"]
            args = dict(y["model_args"], num_nodes=N, in_steps=LIN, out_steps=H, steps_per_day=24)
            self.net = m.STAEformer(**args)
            self.cfg = dict(lr=y["lr"], wd=y.get("weight_decay", 0), bs=y["batch_size"], epochs=y["max_epochs"],
                            milestones=y["milestones"], gamma=y.get("lr_decay_rate", 0.1), clip=y.get("clip_grad", 0) or 0,
                            patience=y.get("early_stop"), source="STAEformer/model/STAEformer.yaml [METRLA]")
        elif kind == "agcrn":
            sys.path.insert(0, os.path.join(ext, "AGCRN"))
            from model.AGCRN import AGCRN
            args = types.SimpleNamespace(num_nodes=N, input_dim=1, rnn_units=64, output_dim=1, horizon=H, num_layers=2,
                                         embed_dim=10, cheb_k=2, default_graph=True)
            self.net = AGCRN(args)
            for p in self.net.parameters():                              # as model/Run.py
                nn.init.xavier_uniform_(p) if p.dim() > 1 else nn.init.uniform_(p)
            self.cfg = dict(lr=3e-3, wd=0.0, bs=64, epochs=100, milestones=None, gamma=None, clip=0, patience=15,
                            source="AGCRN/model/PEMSD4_AGCRN.conf (no METR-LA configuration in the repository)")
        elif kind == "mtgnn":
            sys.path.insert(0, os.path.join(ext, "MTGNN"))
            from net import gtnet
            self.net = gtnet(True, True, 2, N, dev, predefined_A=None, dropout=0.3, subgraph_size=20, node_dim=40,
                             dilation_exponential=1, conv_channels=32, residual_channels=32, skip_channels=64,
                             end_channels=128, seq_length=LIN, in_dim=2, out_dim=H, layers=3, propalpha=0.05,
                             tanhalpha=3, layer_norm_affline=True)
            self.cfg = dict(lr=1e-3, wd=1e-4, bs=64, epochs=100, milestones=None, gamma=None, clip=5.0, patience=None,
                            source="MTGNN/train_multi_step.py defaults (METR-LA), without the curriculum schedule")
        self.net = self.net.to(dev)

    def forward(self, X):
        import torch.nn as nn
        if self.kind == "stid":
            Xs = X.clone()
            Xs[..., 2] = Xs[..., 2] / 7.0                                # STID reads day of week as a fraction
            return self.net(Xs, None, 0, 0, True)[..., 0]                # [B, H, N]
        if self.kind == "gwnet":
            x = nn.functional.pad(X[..., :2].permute(0, 3, 2, 1), (1, 0, 0, 0))   # [B, 2, N, L+1], as engine.py
            return self.net(x)[..., -1]                                  # [B, H, N, T'] -> latest position
        if self.kind == "agcrn":
            return self.net(X[..., :1], None)[..., 0]
        if self.kind == "mtgnn":
            return self.net(X[..., :2].permute(0, 3, 2, 1))[..., 0]      # [B, 2, N, L] -> [B, H, N, 1]
        return self.net(X)[..., 0]                                       # STAEformer


def spec(a):
    import torch
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    D, te, va, va4 = league()
    log(D.describe())
    import run_atlas_long as RL
    tr = D.origins("train", R.TRAIN_STRIDE)
    tr = RL.valid_origins(D, tr[tr >= max(DM * SPD, 7 * SPD) + LIN], 8)   # exactly run_atlas_long.py's windows
    win, run = Windows(D), Runner(a.spec, D, a.ext, dev)
    cfg = run.cfg
    nparam = sum(p.numel() for p in run.net.parameters())
    opt = torch.optim.Adam(run.net.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=cfg["milestones"], gamma=cfg["gamma"]) if cfg["milestones"] else None
    if a.quick:
        tr, va, te, va4, cfg["epochs"] = tr[:128], va[:32], te[:16], va4[:8], 1
    S = torch.as_tensor(win.seen_mask, device=dev)
    vy = np.nan_to_num(D.Y[va[:, None] + np.arange(H)[None], :, 0])[:, :, D.seen]          # [W, H, nS]
    vm = vy > 1e-4

    def predict(idx, hide_unseen, bs=64):
        run.net.eval()
        out = []
        with torch.no_grad():
            for s in range(0, len(idx), bs):
                X, _ = win.batch(idx[s:s + bs], hide_unseen, dev)
                out.append((run.forward(X).float() * win.std + win.mean).cpu().numpy())
        return np.concatenate(out)                                       # [W, H, N]

    log(f"{NAMES[a.spec]}: {nparam:,} parameters, {len(tr)} training windows, device {dev}, budget {a.minutes} min, "
        f"recipe {json.dumps(cfg)}")
    best, best_state, bad, ep, t0, stop = 1e18, None, 0, 0, time.time(), "authors' epoch limit"
    for ep in range(1, cfg["epochs"] + 1):
        run.net.train()
        perm = np.random.permutation(tr)
        for s in range(0, len(perm), cfg["bs"]):
            X, Y = win.batch(perm[s:s + cfg["bs"]], True, dev)
            pred = run.forward(X).float() * win.std + win.mean
            m = ((Y > 1e-4) & S[None, None]).float()                    # observed targets at trained stations only
            m = m / m.mean().clamp(min=1e-8)
            loss = (torch.abs(pred - Y) * m).nan_to_num().mean()       # masked MAE, as the repositories
            opt.zero_grad(); loss.backward()
            if cfg["clip"]:
                torch.nn.utils.clip_grad_norm_(run.net.parameters(), cfg["clip"])
            opt.step()
            if a.minutes and (time.time() - t0) / 60 > a.minutes:
                break
        if sched:
            sched.step()
        p = predict(va, True)[:, :, D.seen]
        vmae = float(np.abs(p - vy)[vm].mean())
        if vmae < best:
            best, bad = vmae, 0
            best_state = {k: v.detach().clone() for k, v in run.net.state_dict().items()}
        else:
            bad += 1
        mins = (time.time() - t0) / 60
        log(f"  epoch {ep:3d} validation MAE {vmae:.3f} (best {best:.3f}) {mins:.1f} min")
        if cfg["patience"] and bad >= cfg["patience"]:
            stop = "authors' early stopping"; break
        if a.minutes and mins > a.minutes:
            stop = "wall-clock budget"; break
    run.net.load_state_dict(best_state)
    log(f"{NAMES[a.spec]}: stopped after {ep} epochs ({stop}); best validation MAE {best:.3f}")

    def quantiles(org):
        f = predict(org, True)                                           # trained stations: unseen inputs hidden
        g = predict(org, False)                                          # unseen stations: whole network as input
        f[:, :, D.unseen] = g[:, :, D.unseen]
        q = np.maximum(f.transpose(0, 2, 1), 0)                          # [W, N, H]
        return np.repeat(q[..., None], 3, -1)

    meta = dict(type="graph architecture, authors' code, trained on Atlas v1.3's Delhi windows", params=nparam,
                recipe=cfg, epochs_run=ep, stopped_by=stop, budget_minutes=a.minutes, best_val_MAE=best, seed=a.seed,
                train_windows=int(len(tr)), device=dev, quick=bool(a.quick))
    if a.quick:
        log("quick run: pipeline OK, nothing saved"); return
    save_entry("spec_" + a.spec, NAMES[a.spec], quantiles(va4), quantiles(te), meta)


# ================================================================================================ A: foundation models
def tsfm(a):
    """Zero-shot, 512 h of each station's own PM2.5 (gaps forward-filled), every station, validation and test windows."""
    from pw import opponents as OP
    D, te, va, va4 = league()
    log(D.describe())
    y, ALL = D.Y[:, :, 0], np.arange(D.N)
    org = np.concatenate([va4, te])
    if a.quick:
        org = np.concatenate([va4[:4], te[:4]])
    t0 = time.time()
    key = a.tsfm
    try:
        if key in ("tfm3", "tfm3mv"):
            q, meta = OP.run(key, y, org, ALL, H, ctx=512, chunk=a.chunk, log=log)
            name = meta["name"] + ", zero-shot"
        else:
            from pw import opponents2 as OP2
            fc = OP2.KEYS[key](512, H)
            c = OP.contexts(y, org, ALL, 512)
            out = []
            for i in range(0, len(c), a.chunk):
                out.append(np.asarray(fc(c[i:i + a.chunk]), np.float32))
                if i == 0:
                    log(f"    {fc.name}: first {min(a.chunk, len(c))} of {len(c)} series in {time.time() - t0:.0f}s")
            q = np.sort(np.maximum(np.concatenate(out).reshape(len(org), D.N, H, 3), 0), -1)
            name, meta = fc.name + ", zero-shot", dict(name=fc.name, licence=fc.licence, params=fc.params, context_steps=512)
    except Exception as e:
        import traceback
        traceback.print_exc()
        log(f"NOT RUN {key}: {type(e).__name__}: {str(e)[:500]}")
        os.makedirs(L2, exist_ok=True)
        json.dump({"key": key, "error": f"{type(e).__name__}: {e}"}, open(os.path.join(L2, f"notrun_{key}.json"), "w"))
        return
    meta.update(minutes=round((time.time() - t0) / 60, 1), device=OP.DEV)
    log(f"{name}: {meta['minutes']} min on {OP.DEV}")
    if a.quick:
        log("quick run: pipeline OK, nothing saved"); return
    nv = len(va4 if not a.quick else va4[:4])
    save_entry("tsfm_" + key, name, q[:nv], q[nv:], meta)


# ================================================================================================ scoring
def score(a):
    D, te, va, va4 = league()
    log(D.describe())
    S, U, ALL = D.seen, D.unseen, np.arange(D.N)
    yv, yt = R.truth(D, va4, ALL), R.truth(D, te, ALL)
    z = np.load(find("fusion_members_atlas.npz"))
    assert z["qt"].shape[:2] == (len(te), D.N) and z["qv"].shape[:2] == (len(va4), D.N), "Atlas v1.3 windows differ"
    assert np.array_equal(z["test_origins"] - z["test_origins"][0], te - te[0]), "test windows differ"
    zl = Delhi(targets=TARGETS, backbone=False, wxfc=False)            # the league file: same stations, same order
    assert list(zl.stations) == list(D.stations), "station lists differ"
    A = "Atlas v1.3 (ours, 967,632 parameters)"
    entries = {A: (z["qv"], z["qt"])}
    for k, nm in FM.items():
        f = find(os.path.join("opponents", k + ".npz"))
        if f:
            o = np.load(f)
            entries[nm] = (o["qv"], o["qt"])
    metas = {}
    for f in sorted(glob.glob(os.path.join(L2, "*.npz")) + glob.glob("/kaggle/input/**/league2/*.npz", recursive=True)):
        o = np.load(f)
        nm = str(o["name"])
        if nm in entries:
            continue
        if o["qt"].shape[:2] != (len(te), D.N):
            log(f"  {f}: shape {o['qt'].shape} does not match the windows, left out"); continue
        entries[nm], metas[nm] = (o["qv"], o["qt"]), json.loads(str(o["meta"]))
    sc = lambda qq, yy: E.score(qq, yy, horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)
    res = {"tracks": {}, "significance": {}, "claims": {}, "meta": metas}
    P = {}
    for nm, (qv, qt) in entries.items():
        qv, qt = np.sort(qv.astype(np.float32), -1), np.sort(qt.astype(np.float32), -1)
        okv = np.isfinite(qv[..., 1])
        d = E.fit_cqr(np.nan_to_num(qv[:, S]), np.where(okv[:, S], yv[:, S], np.nan))
        q = E.apply_cqr(qt, d)
        P[nm] = q
        cov = {t: float(np.isfinite(q[:, c][..., 1]).mean()) for t, c in (("S", S), ("U", U))}
        res["tracks"][nm] = {t: sc(np.nan_to_num(q[:, c]), np.where(np.isfinite(q[:, c][..., 1]), yt[:, c], np.nan))
                             for t, c in (("S", S), ("U", U))}
        res["tracks"][nm]["coverage_of_cells"] = cov
        log(f"TEST {nm}: Track S MAE {res['tracks'][nm]['S']['MAE']:.2f}, Track U MAE {res['tracks'][nm]['U']['MAE']:.2f}"
            f" (cells covered: S {100 * cov['S']:.0f}%, U {100 * cov['U']:.0f}%)")
    chk = (res["tracks"][A]["S"]["MAE"], res["tracks"][A]["U"]["MAE"])
    res["check_atlas_v13"] = dict(recorded=[28.91, 25.56], reproduced=chk)
    if not os.environ.get("LEAGUE2_TEST_ONLY_NO_CHECK"):                  # set only by the local pipeline test on fake data
        assert abs(chk[0] - 28.91) < 0.006 and abs(chk[1] - 25.56) < 0.006, f"Atlas v1.3 not reproduced: {chk}"
    log(f"CHECK Atlas v1.3 reproduced: {chk[0]:.2f} / {chk[1]:.2f} (recorded 28.91 / 25.56)")
    for nm in entries:
        if nm == A:
            continue
        r = {}
        for t, c in (("S", S), ("U", U)):
            ok = np.isfinite(P[nm][:, c][..., 1])
            y = np.where(ok, yt[:, c], np.nan)
            r[t] = {m: E.compare(P[A][:, c], np.nan_to_num(P[nm][:, c]), y, R.PER_DAY, m, reps=a.reps, floor=FLOOR["PM2.5"])
                    for m in ("MAE", "QL")}
        res["significance"][nm] = r
        vS, vU = r["S"]["MAE"]["verdict"], r["U"]["MAE"]["verdict"]
        res["claims"][nm] = "Atlas BEATS it" if (vS, vU) == ("WIN", "WIN") else ("Atlas LOSES to it" if "LOSS" in (vS, vU) else "level")
        log(f"SIG Atlas v1.3 vs {nm}: S {vS} {r['S']['MAE']['rel_diff_pct']:+.2f}% p={r['S']['MAE']['p']:.2g}; "
            f"U {vU} {r['U']['MAE']['rel_diff_pct']:+.2f}% p={r['U']['MAE']['p']:.2g} -> {res['claims'][nm]}")
    res["minutes"] = round((time.time() - T0) / 60, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "league2_results.json"), "w"), indent=1, default=float)
    o = ["# Atlas League v2.0: Atlas v1.3 against every scorable model (Delhi PM2.5, next 24 h)", "",
         f"Check: Atlas v1.3 reproduced {chk[0]:.2f} / {chk[1]:.2f} (recorded 28.91 / 25.56).", "",
         "| Entry | Trained: MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | Never trained: MAE | cells covered S / U | Atlas v1.3 against it (trained / never trained) | Verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for nm in sorted(entries, key=lambda n: res["tracks"][n]["S"]["MAE"]):
        s, u, cv = res["tracks"][nm]["S"], res["tracks"][nm]["U"], res["tracks"][nm]["coverage_of_cells"]
        g = res["significance"].get(nm)
        cmp = "–" if not g else " / ".join(f"{g[t]['MAE']['verdict']} {g[t]['MAE']['rel_diff_pct']:+.1f}% (p={g[t]['MAE']['p']:.2g})" for t in ("S", "U"))
        o.append(f"| {nm} | {s['MAE']:.2f} | {s['RMSE']:.2f} | {s['QL']:.2f} | {s['COV80']:.0f} | {s['MAE@1h']:.2f} | {s['MAE@6h']:.2f} | "
                 f"{s['MAE@12h']:.2f} | {s['MAE@24h']:.2f} | {u['MAE']:.2f} | {100 * cv['S']:.0f}% / {100 * cv['U']:.0f}% | {cmp} | {res['claims'].get(nm, '–')} |")
    o += ["", "## How each trained opponent ran", ""] + [f"- {n}: " + json.dumps({k: v for k, v in m.items() if k != 'coords'}, default=float) for n, m in metas.items()]
    open(os.path.join(OUT, "LEAGUE2_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))
    log(f"done in {res['minutes']} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cams", action="store_true")
    ap.add_argument("--spec", choices=list(NAMES))
    ap.add_argument("--ext", default="/kaggle/working/ext")
    ap.add_argument("--minutes", type=float, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tsfm", help="one of tfm3, tfm3mv, moirai2, toto, tirex, ttm, sundial")
    ap.add_argument("--chunk", type=int, default=256)
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if a.cams:
        cams(a)
    if a.spec:
        spec(a)
    if a.tsfm:
        tsfm(a)
    if a.score:
        score(a)
