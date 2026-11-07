"""Foundation-model backbone forecasts for the PWM-W Delhi hybrid (v0.2).

Chronos-2 (Amazon, Apache-2.0) and TimesFM 2.5 (Google, Apache-2.0) forecast PM2.5 zero-shot from each station's
own past 512 hours. PWM-W then learns how to correct those forecasts with what they cannot see: the station network,
the other pollutants and meteorology, and the weather forecast. Only open-licence models are used as a backbone;
TimesFM 3.0 (non-commercial licence) stays an opponent only.

Origins: every 3 h in train and validation, the test origins (every 6 h), and the first hour after the data
(for the live forecast). Contexts use only readings before each origin.

  python tools/backbone.py           # -> data/raw/DELHI_backbone.npz
"""
import json, os, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pw.ddata import Delhi, RAW, H
from pw import opponents as OPP

BACKBONES = ("chronos2", "tfm25")


def main():
    D = Delhi(targets=["PM2.5"], backbone=False, wxfc=False)
    org = np.unique(np.concatenate([D.origins("train", 3), D.origins("val", 3), D.origins("test", 6), [D.T]]))
    y = np.concatenate([D.Y[:, :, 0], np.full((H, D.N), np.nan, np.float32)])   # room for the live origin
    out = {"origins": org, "stations": np.array(D.stations)}
    meta = {}
    for key in BACKBONES:
        t0 = time.time()
        q, m = OPP.run(key, y, org, np.arange(D.N), H, ctx=512, chunk=4096)
        out[key] = q.astype(np.float16)
        meta[key] = m
        print(f"backbone {m['name']}: {len(org)} origins x {D.N} stations in {(time.time() - t0) / 60:.1f} min",
              flush=True)
    out["meta"] = np.array(json.dumps(meta))
    np.savez_compressed(os.path.join(RAW, "DELHI_backbone.npz"), **out)
    print("wrote", os.path.join(RAW, "DELHI_backbone.npz"), flush=True)


if __name__ == "__main__":
    main()
