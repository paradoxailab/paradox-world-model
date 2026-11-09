"""Train the real-time PWM-W (v0.9) on every Indian airport report up to now (WX_LIVE.npz).

The setting is v0.8's, fixed in advance: 14-day encoder + weight averaging, d=128, 3 layers. The last 45 days before
the final 3 are validation (checkpoint choice only). Three seeds are saved for an ensemble.

  python tools/train_live.py --steps 6000      # -> $PW_OUT/live_models.pt
"""
import argparse, os, sys, time

import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pw.wdata import Wx
from pw import wtrain as WT

OUT = os.environ.get("PW_OUT", os.path.join(ROOT, "out"))
CFG = dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, longctx=True, ema=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=6000)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    D = Wx("LIVE")
    print(D.describe(), flush=True)
    tr, va = D.origins("train", 1), D.origins("val", 6)
    states, infos = [], []
    for s in (100, 101, 102):
        t0 = time.time()
        m, info = WT.train(dict(CFG), D, tr, None, va, a.steps, seed=s, log=lambda *x: None)
        states.append({k: v.detach().cpu() for k, v in m.state_dict().items()})
        infos.append(info)
        print(f"seed {s}: validation MAE/spread {info['val_score']:.4f} ({time.time() - t0:.0f}s)", flush=True)
    torch.save({"cfg": m.cfg, "states": states, "infos": infos, "keep": D.keep.tolist(), "stations": D.stations,
                "trained_until_utc": str(D.dates[D.bounds["val"][1] - 1])}, os.path.join(OUT, "live_models.pt"))
    print(f"saved {len(states)} models, trained on {len(tr)} windows up to {D.dates[D.bounds['train'][1] - 1]} UTC, "
          f"validated to {D.dates[D.bounds['val'][1] - 1]} UTC", flush=True)


if __name__ == "__main__":
    main()
