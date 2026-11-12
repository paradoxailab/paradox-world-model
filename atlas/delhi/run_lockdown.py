"""Atlas what-if test 1: the 2020 lockdown in Delhi (rules in atlas/README.md, written before any result).

Question: what would Delhi's PM2.5 have been from 25 March 2020 if emissions had gone on as usual? A forecaster that
reads yesterday's pollution cannot answer: its inputs already contain the lockdown. So this Atlas ("Atlas-BAU",
business as usual) never sees any pollutant reading. It is given only what the lockdown did not change:
  * each station's weather (temperature, humidity, wind speed and direction, solar radiation, pressure) for the last
    72 h and for the 24 h being simulated, plus the city-mean weather for the same hours;
  * the hour, the weekday and the season (two yearly harmonics);
  * each station's own usual PM2.5 level (its mean over the training period).
It is trained on 2018-01-15 .. 2020-02-29 only, to reproduce the PM2.5 that was measured, and never on:
  * the PLACEBO window, 25 March .. 31 May 2019 (the same dates one year before, no lockdown), nor
  * anything from 1 March 2020 on.
Then it simulates the placebo window, 1-21 March 2020 (just before) and the four lockdown phases with the weather
that actually occurred. Measured / simulated - 1 is the part of the change that weather does not explain. The same
ratio on the placebo window is the method's own bias; the reported effect is the lockdown ratio divided by the
placebo ratio (day-block bootstrap for the interval).

  python tools/build_delhi_long.py && python run_lockdown.py
"""
import argparse, json, math, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import Delhi, SPD, TARGETS, DM, RAW
from atlas.model import sized
import run_atlas_delhi as R

L, H, DEV, OUT = R.L, R.H, R.DEV, R.OUT
FIRST, LAST = "2018-01-01", "2020-06-01"                 # the file is cut here: nothing later is loaded at all
TRAIN = ("2018-01-15", "2020-03-01")
PLACEBO = ("2019-03-25", "2019-06-01")
GROUPS = {"placebo: 25 Mar - 31 May 2019": ("2019-03-25", "2019-06-01"),
          "placebo, phase-1 dates: 25 Mar - 14 Apr 2019": ("2019-03-25", "2019-04-15"),
          "just before: 1 - 21 Mar 2020": ("2020-03-01", "2020-03-22"),
          "lockdown 1: 25 Mar - 14 Apr 2020": ("2020-03-25", "2020-04-15"),
          "lockdown 2: 15 Apr - 3 May 2020": ("2020-04-15", "2020-05-04"),
          "lockdown 3: 4 - 17 May 2020": ("2020-05-04", "2020-05-18"),
          "lockdown 4: 18 - 31 May 2020": ("2020-05-18", "2020-06-01"),
          "all lockdown: 25 Mar - 31 May 2020": ("2020-03-25", "2020-06-01")}
PLACEBO_OF = {"lockdown 1: 25 Mar - 14 Apr 2020": "placebo, phase-1 dates: 25 Mar - 14 Apr 2019"}   # others: the whole placebo window
MET = slice(8, 15)                                        # weather channels among the 15; 0..7 are pollutants
T0 = time.time()
RES = {"groups": {}, "runs": {}}


def log(*a):
    print(*a, flush=True)


def load():
    z = np.load(os.path.join(RAW, "DELHI_LONG.npz"), allow_pickle=False)
    start = np.datetime64(str(z["start"])).astype("datetime64[h]")
    a = int((np.datetime64(FIRST).astype("datetime64[h]") - start).astype(int))
    b = int((np.datetime64(LAST).astype("datetime64[h]") - start).astype(int))
    f = os.path.join(RAW, "DELHI_LOCKDOWN_CUT.npz")
    np.savez(f, X=z["X"][a:b], vars=z["vars"], stations=z["stations"], start=np.array(str(start + np.timedelta64(a, "h"))))
    D = Delhi(path=f, targets=TARGETS, backbone=False, wxfc=False)
    os.remove(f)
    return D


def idx(D, date):
    return int((np.datetime64(date).astype("datetime64[h]") - D.start.astype("datetime64[h]")).astype(int))


def prepare(D):
    """Constant station scales (training-period means), city-mean weather and season features; nothing from the
    placebo window or from March 2020 on enters any of them."""
    a, b = idx(D, TRAIN[0]), idx(D, TRAIN[1])
    p0, p1 = idx(D, PLACEBO[0]), idx(D, PLACEBO[1])
    keep = np.zeros(D.T, bool); keep[a:b] = True; keep[p0:p1] = False
    with np.errstate(all="ignore"):
        m = np.nanmean(D.Y[keep], 0)                                           # [N, K]
        m = np.where(np.isfinite(m), m, np.nanmedian(m, 0)[None])
        city = np.nanmean(D.A_aux[:, D.seen][:, :, 4:11], 1)                   # [T, 7] standardised weather, city mean
    D.scale = np.broadcast_to(np.maximum(m, 1e-3)[None], D.scale.shape).astype(np.float32).copy()
    D.sflag = np.zeros_like(D.sflag)
    pad = np.zeros((2 * H, 7), np.float32)
    D.city = np.concatenate([np.nan_to_num(city).astype(np.float32), pad])
    D.city_ok = np.concatenate([np.isfinite(city).all(1, keepdims=True).astype(np.float32), pad[:, :1]])
    doy = (D.dates - D.dates.astype("datetime64[Y]")).astype("timedelta64[D]").astype(int) / 365.25 * 2 * math.pi
    D.season = np.stack([np.sin(doy), np.cos(doy), np.sin(2 * doy), np.cos(2 * doy)], -1).astype(np.float32)
    return keep


def batch(D, org, nodes, drop=0.0):
    """Atlas inputs with every pollutant reading removed; weather and calendar as forcing for past and simulated hours."""
    b = R.make_batch(D, org, nodes)
    dev = b["yc"].device
    if not hasattr(D, "t_city"):
        D.t_city, D.t_cok, D.t_season = (torch.as_tensor(x, device=dev) for x in (D.city, D.city_ok, D.season))
    o = torch.as_tensor(org, device=dev)
    hl = o[:, None] + torch.arange(-L, 0, device=dev)[None]
    fo = (o[:, None] + torch.arange(H, device=dev)[None]).clamp(max=D.T + 2 * H - 1)
    n = len(nodes)
    mc = b["mc"].clone(); mc[..., :8] = 0                                       # no pollutant history
    if drop:                                                                    # some stations' weather sensors hidden
        mc[..., MET] = mc[..., MET] * (torch.rand(mc.shape[0], n, 1, 1, device=dev) >= drop).float()
    yc = b["yc"] * mc
    of = b["of"][..., MET]
    if drop:
        of = of * (torch.rand(of.shape[0], n, 1, 1, device=dev) >= drop).float()
    ex = lambda t, ix: t[ix][:, None].expand(-1, n, -1, -1)
    uc = torch.cat([b["uc"], ex(D.t_season, hl), yc[..., MET], mc[..., MET], ex(D.t_city, hl), ex(D.t_cok, hl)], -1)
    uf = torch.cat([b["uf"], ex(D.t_season, fo), b["yf"][..., MET] * of, of, ex(D.t_city, fo), ex(D.t_cok, fo)], -1)
    st = torch.zeros_like(b["static"]); st[..., 2 * DM + 2 * H] = b["static"][..., 2 * DM + 2 * H]   # the station's usual level only
    return dict(yc=yc, mc=mc, uc=uc, uf=uf, yf=b["yf"], of=b["of"], static=st, geo=b["geo"], s=b["s"])


U = 4 + 4 + 7 + 7 + 7 + 1


def build(D, size):
    return sized(int(size), L=L, H=H, C=D.K + D.Ca, U=U, lat_steps=6, spatial=True, geo_dim=3, static=2 * DM + 2 * H + 2,
                 lo=[0.0] * D.K + [float("-inf")] * D.Ca, sysid=False, fill="interp").to(DEV)


@torch.no_grad()
def simulate(m, D, org, nodes, bs=48):
    m.eval(); out = []
    for i in range(0, len(org), bs):
        b = batch(D, org[i:i + bs], nodes)
        q = m(b["yc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])[0][:, :, :, 0] * b["s"][:, :, None, None]
        out.append(q.float().cpu().numpy())
    m.train()
    return np.concatenate(out)                                                  # [W, n, H, 3] ug/m3


def train(D, org, hold, seed, steps, size, every=400):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    m = build(D, size)
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1, (s + 1) / 100) * (0.1 + 0.45 * (1 + math.cos(math.pi * min(1, s / steps)))))
    chw = torch.tensor([1.0] + [0.1] * (D.K - 1) + [0.0] * D.Ca, device=DEV)
    qs = torch.tensor([0.1, 0.5, 0.9], device=DEV)
    yh = R.truth(D, hold, D.seen)
    best, state, t0 = float("inf"), None, time.time()
    for step in range(1, steps + 1):
        b = batch(D, rng.choice(org, 16, replace=False), D.seen, drop=0.2)
        q = m(b["yc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])[0]
        e = b["yf"][..., None] - q
        w = b["of"] * chw
        loss = (torch.maximum(qs * e, (qs - 1) * e).mean(-1) * w).sum() / w.sum().clamp(min=1)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step(); sched.step()
        if step % every == 0 or step == steps:
            v = float(np.nanmean(np.abs(simulate(m, D, hold, D.seen)[..., 1] - yh)))
            if v < best:
                best, state = v, {k: x.detach().clone() for k, x in m.state_dict().items()}
            log(f"  seed {seed} step {step} held-out days MAE {v:.2f} (best {best:.2f}) {time.time() - t0:.0f}s")
    m.load_state_dict(state)
    RES["runs"][str(seed)] = dict(params=m.n_params(), steps=steps, holdout_MAE=best, minutes=round((time.time() - t0) / 60, 1))
    return m


def day_sums(sim, y):
    """Per day: sum of measured and of simulated PM2.5 over the cells that were measured, and their count."""
    ok = np.isfinite(y)
    return np.where(ok, y, 0).sum((1, 2)), np.where(ok, sim, 0).sum((1, 2)), ok.sum((1, 2))


def boot(n, reps, rng, block=3):
    nb = int(math.ceil(n / block))
    st = rng.integers(0, max(n - block, 0) + 1, (reps, nb))
    return (st[:, :, None] + np.arange(block)[None, None]).reshape(reps, -1)[:, :n]


def main(a):
    q = a.quick
    D = load()
    keep = prepare(D)
    log(D.describe())
    S = D.seen
    day0 = np.arange(max(DM * SPD + L, 336 + L), D.T - H + 1)
    in_train = lambda o: keep[o] & keep[np.minimum(o + H - 1, D.T - 1)]
    cand = day0[::3]
    cand = cand[in_train(cand)]
    obs = np.isfinite(D.Y[:, S, 0]); cs = np.concatenate([np.zeros((1, len(S))), np.cumsum(obs, 0)])
    cand = cand[((cs[cand + H] - cs[cand]) >= 12).sum(1) >= 8]
    dnum = cand // SPD
    hold = cand[(dnum % 10 == 7) & (cand % SPD == 0)]                           # every tenth day, one simulation a day
    tr = cand[~np.isin(dnum % 10, (6, 7))]
    log(f"stations: {D.N} ({len(S)} trained on, {len(D.unseen)} unseen); training windows {len(tr)} ({D.dates[tr[0]]} .. {D.dates[tr[-1] + H - 1]}), "
        f"held-out days {len(hold)}; nothing from {PLACEBO[0]} .. {PLACEBO[1]} or from {TRAIN[1]} on is trained on")
    seeds = [500, 501] if q else [500, 501, 502]
    models = [train(D, tr, hold[:6] if q else hold, s, 60 if q else a.steps, 60000 if q else a.size, 20 if q else 400) for s in seeds]
    ALLN = np.arange(D.N)
    rng = np.random.default_rng(0)
    out = {}
    for name, (d0, d1) in GROUPS.items():
        org = np.arange(idx(D, d0), idx(D, d1), SPD)
        y = R.truth(D, org, ALLN)
        sim = np.zeros((len(org), D.N, H), np.float32)
        sim[:, S] = np.mean([simulate(m, D, org, S)[..., 1] for m in models], 0)
        if len(D.unseen):
            sim[:, D.unseen] = np.mean([simulate(m, D, org, ALLN)[..., 1] for m in models], 0)[:, D.unseen]
        so, sp, c = day_sums(sim[:, S], y[:, S])
        dm_o, dm_p = so / np.maximum(c, 1), sp / np.maximum(c, 1)
        ok = c > 0
        r2 = float(1 - ((dm_o[ok] - dm_p[ok]) ** 2).sum() / max(((dm_o[ok] - dm_o[ok].mean()) ** 2).sum(), 1e-9))
        g = dict(days=int(len(org)), measured=float(so.sum() / c.sum()), simulated=float(sp.sum() / c.sum()),
                 ratio=float(so.sum() / sp.sum()), daily_r2=r2, daily_corr=float(np.corrcoef(dm_o[ok], dm_p[ok])[0, 1]),
                 daily_MAE=float(np.abs(dm_o[ok] - dm_p[ok]).mean()))
        if len(D.unseen):
            uo, up, uc = day_sums(sim[:, D.unseen], y[:, D.unseen])
            g["ratio_unseen_stations"] = float(uo.sum() / max(up.sum(), 1e-9))
        ix = boot(len(org), a.reps, rng)
        g["_boot"] = so[ix].sum(1) / sp[ix].sum(1)
        g["ratio_ci95"] = [float(x) for x in np.percentile(g["_boot"], [2.5, 97.5])]
        out[name] = g
        np.savez_compressed(os.path.join(OUT, "lockdown_days_" + name.split(":")[0].replace(" ", "_").replace(",", "") + ".npz"),
                            dates=D.dates[org].astype(str), measured=dm_o, simulated=dm_p, cells=c)
    for name, g in out.items():
        pl = out[PLACEBO_OF.get(name, "placebo: 25 Mar - 31 May 2019")]
        if not name.startswith("placebo"):
            eff = g["_boot"] / pl["_boot"][rng.permutation(len(pl["_boot"]))] - 1
            g["effect_pct"] = float(100 * (g["ratio"] / pl["ratio"] - 1))
            g["effect_ci95_pct"] = [float(100 * x) for x in np.percentile(eff, [2.5, 97.5])]
        g["unexplained_pct"] = float(100 * (g["ratio"] - 1))
    # the comparisons the published studies make, from the same data (no weather adjustment)
    mean_of = lambda d0, d1: float(np.nanmean(D.Y[idx(D, d0):idx(D, d1), :, 0]))
    naive = {"phase 1 against the same dates in 2019": 100 * (mean_of("2020-03-25", "2020-04-15") / mean_of("2019-03-25", "2019-04-15") - 1),
             "phase 1 against 2-21 March 2020": 100 * (mean_of("2020-03-25", "2020-04-15") / mean_of("2020-03-02", "2020-03-22") - 1),
             "all lockdown against the same dates in 2019": 100 * (mean_of("2020-03-25", "2020-06-01") / mean_of("2019-03-25", "2019-06-01") - 1)}
    pl, pre, l1 = out["placebo: 25 Mar - 31 May 2019"], out["just before: 1 - 21 Mar 2020"], out["lockdown 1: 25 Mar - 14 Apr 2020"]
    gate = bool(abs(pl["ratio"] - 1) <= 0.15 and (pre["effect_ci95_pct"][0] <= 0 <= pre["effect_ci95_pct"][1] or abs(pre["effect_pct"]) < 15))
    detect = bool((l1["effect_ci95_pct"][1] < 0 or l1["effect_ci95_pct"][0] > 0) and abs(l1["effect_pct"]) > abs(pre["effect_pct"]))
    for g in out.values():
        g.pop("_boot")
    RES.update(groups=out, naive_pct=naive, gate_passed=gate, lockdown_detected=detect, describe=D.describe(),
               stations=dict(total=D.N, trained=int(len(S)), unseen=int(len(D.unseen))), train_windows=int(len(tr)), holdout_days=int(len(hold)),
               minutes_total=round((time.time() - T0) / 60, 1))
    json.dump(RES, open(os.path.join(OUT, "lockdown_results.json"), "w"), indent=1, default=float)
    o = ["# Atlas what-if test 1: the 2020 lockdown in Delhi (generated from lockdown_results.json)", "",
         "| Window | days | measured PM2.5 | simulated, business as usual | measured / simulated - 1 | 95% interval | effect after removing the placebo bias | 95% interval | day-to-day correlation |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, g in out.items():
        eff = f"{g['effect_pct']:+.1f}% | {g['effect_ci95_pct'][0]:+.1f}% .. {g['effect_ci95_pct'][1]:+.1f}%" if "effect_pct" in g else "- | -"
        o.append(f"| {name} | {g['days']} | {g['measured']:.1f} | {g['simulated']:.1f} | {g['unexplained_pct']:+.1f}% | "
                 f"{100 * (g['ratio_ci95'][0] - 1):+.1f}% .. {100 * (g['ratio_ci95'][1] - 1):+.1f}% | {eff} | {g['daily_corr']:.2f} |")
    o += ["", "Without any weather adjustment, from the same data: " + "; ".join(f"{k} {v:+.1f}%" for k, v in naive.items()) + ".", "",
          f"Runs: " + "; ".join(f"seed {k}: held-out days MAE {v['holdout_MAE']:.2f}, {v['minutes']} min" for k, v in RES["runs"].items()) + ".", "",
          f"Validity gate (placebo bias within 15% and no effect just before the lockdown): {'PASSED' if gate else 'FAILED'}.",
          f"Lockdown detected in phase 1 (interval excludes zero and the effect is larger than just before): {'YES' if detect else 'NO'}.", ""]
    open(os.path.join(OUT, "LOCKDOWN_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))
    log(f"done in {RES['minutes_total']} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--size", type=int, default=250_000)
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--quick", action="store_true")
    os.makedirs(OUT, exist_ok=True)
    main(ap.parse_args())
