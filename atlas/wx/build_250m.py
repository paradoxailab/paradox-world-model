"""Build the pre-registered 250M candidate (PREREG_WX addendum of 24 Nov 2026) and check it before any GPU time is spent.

  WX_DATA=<packed data, real or synthetic> python build_250m.py [--init <trained 10M checkpoint>]

1. Builds the 10M model exactly as Stage 1 does (or loads the trained one with --init).
2. Grows it with --grow 3,7,7 (width x3, 7 + 7 blocks) and checks the parameter count, 251,879,368.
3. Check G0: on real input windows the grown model gives the same forecasts as the 10M (function-preserving growth).
4. One training step (AdamW, as in Stage 1) at batch 1 and 2, timing it and measuring memory per window, so the
   batch that fits on an A100 (40 or 80 GB) can be worked out before renting one.
Writes build_250m.json next to the data (or into $ATLAS_OUT).
"""
import argparse, json, os, resource, sys, time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("ATLAS_DEVICE", "cpu")
import run_atlas_wx as W                                   # noqa: E402  (same data pipeline as Stage 1)
from atlas.model import sized                              # noqa: E402
from atlas.grow import grow, load_any                      # noqa: E402

TARGET = 251_879_368


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6      # Linux: kB -> GB (peak so far)


def call(model, b):
    return model(b["yc"] * b["mc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])


def main(a):
    torch.manual_seed(600); torch.set_num_threads(os.cpu_count() or 2)
    Z, lat, lon, elev, M = W.load(quick=True)
    N = Z.shape[0]
    nb = W.neighbours(lat, lon, W.K); geo = W.geometry(lat, lon, nb); st = W.static_feats(lat, lon, elev)
    bt = W.Batcher(Z, nb, geo, st, 24)
    out = dict(data=W.RAW, stations=N)

    if a.init:
        small = load_any(a.init); out["init"] = os.path.basename(a.init)
    else:                                                   # the Stage 1 10M as built (untrained: checks the build only)
        small = sized(10_000_000, L=W.L, H=24, C=5, U=4, lat_steps=6, spatial=True, geo_dim=3, static=4, fill="interp")
        out["init"] = "untrained 10M (build check only)"
    out["params_10m"] = small.n_params()
    t = time.time()
    big = grow(small, f=3, enc_depth=7, dyn_depth=7, noise=0.05, seed=600)
    out["grow_seconds"] = round(time.time() - t, 1)
    P = sum(p.numel() for p in big.parameters())
    out.update(params_250m=P, width=big.cfg["d"], heads=big.cfg["heads"], enc_depth=big.cfg["enc_depth"],
               dyn_depth=big.cfg["dyn_depth"], params_match_prereg=(P == TARGET))
    print(f"10M: {out['params_10m']:,}  ->  grown: {P:,} parameters (pre-registered {TARGET:,}: "
          f"{'MATCH' if P == TARGET else 'DIFFERENT'}), width {big.cfg['d']}, heads {big.cfg['heads']}, "
          f"depth {big.cfg['enc_depth']} + {big.cfg['dyn_depth']}", flush=True)

    # G0: same forecasts at the start, on real windows (validation year, 8 random stations and hours)
    g = torch.Generator().manual_seed(1)
    va, ve = W.YEARS["val"]
    s = torch.randint(0, N, (8,), generator=g); t0 = torch.randint(va, ve - (W.L + 24), (8,), generator=g)
    b = bt(s, t0)
    small.eval(); big.eval()
    with torch.no_grad():
        q0, q1 = call(small, b)[0], call(big, b)[0]
    diff = float((q0 - q1).abs().max()); scale = float(q0.abs().max())
    out.update(g0_max_abs_diff=diff, g0_output_scale=scale, g0_pass=diff <= 1e-4 * max(1.0, scale))
    print(f"G0 (same forecasts after growth): max |difference| {diff:.2e} on outputs of size {scale:.2f} -> "
          f"{'PASS' if out['g0_pass'] else 'FAIL'}", flush=True)
    del small

    # one Stage 1 training step at batch 1 and 2: time and memory per window
    big.train()
    opt = torch.optim.AdamW(big.parameters(), lr=2e-4, weight_decay=1e-4)
    ta, te = W.YEARS["train"]
    for bs in (1, 2):
        s = torch.randint(0, N, (bs,), generator=g); t0 = torch.randint(ta, te - (W.L + 24), (bs,), generator=g)
        b = bt(s, t0)
        before = rss_gb(); t = time.time()
        q, rec, _ = call(big, b)
        loss = W.pinball(q.float(), b["y"], b["my"]) + 0.2 * ((rec.float() - b["yc"]).abs() * b["mc"]).mean()
        opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(big.parameters(), 1.0); opt.step()
        out[f"step_bs{bs}_seconds_cpu"] = round(time.time() - t, 1); out[f"peak_rss_gb_after_bs{bs}"] = round(rss_gb(), 2)
        print(f"training step, batch {bs}: {out[f'step_bs{bs}_seconds_cpu']} s on CPU, loss {float(loss):.4f}, "
              f"peak memory {out[f'peak_rss_gb_after_bs{bs}']:.2f} GB (was {before:.2f})", flush=True)
    state_gb = P * 4 * 4 / 1e9                                  # fp32 weights + grads + two AdamW moments
    per_win = max(0.0, out["peak_rss_gb_after_bs2"] - out["peak_rss_gb_after_bs1"])
    out.update(state_gb_fp32=round(state_gb, 2), activation_gb_per_window_fp32=round(per_win, 3))
    if per_win > 0:
        for gpu in (40, 80):                                    # fp16 autocast roughly halves activation memory
            fit = int((gpu * 0.9 - state_gb) / (per_win / 2))
            out[f"a100_{gpu}gb_windows_per_pass_est"] = fit
            print(f"A100 {gpu} GB: about {fit} windows per pass (batch 256 = {max(1, -(-256 // max(fit, 1)))} part(s) with --micro)")
    f = os.path.join(os.environ.get("ATLAS_OUT", W.RAW), "build_250m.json")
    json.dump(out, open(f, "w"), indent=1, default=float); print("written", f)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--init", default="")
    main(ap.parse_args())
