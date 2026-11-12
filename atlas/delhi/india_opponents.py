"""Foundation models on the all-India league's windows (GPU): zero-shot, the same windows and stations Atlas-India is
scored on, 512 h of each station's own PM2.5 history (gaps forward-filled), as in the Delhi league.

Writes india_opp_<key>.npz per model (the name, and for every network the validation and test quantiles), which
score_india.py reads. TimesFM 3.0 is evaluation only (non-commercial licence).

  pip install timesfm chronos-forecasting && python india_opponents.py --keys chronos-bolt,chronos2,tfm25,tfm3
"""
import argparse, json, os, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw import opponents as OPP
import run_atlas_delhi as R
import run_atlas_india as RI

H, OUT = R.H, R.OUT


def main(a):
    nets = RI.networks(a.quick)
    O = [RI.origins(D, a.quick) for D in nets]
    os.makedirs(OUT, exist_ok=True)
    for key in a.keys.split(","):
        f = os.path.join(OUT, f"india_opp_{key}.npz")
        if os.path.exists(f):
            print(f"{key}: already done", flush=True); continue
        t0 = time.time()
        try:
            fc = OPP.make(key, a.ctx, H)
            save = {}
            for D, (tr, va4, te) in zip(nets, O):
                ALL = np.arange(D.N)
                for nm, org in (("qv", va4), ("qt", te)):
                    c = OPP.contexts(D.Y[:, :, 0], org, ALL, a.ctx)
                    chunk = a.chunk
                    if key == "tfm3mv":
                        c, chunk = c.reshape(len(org), D.N, a.ctx), 8
                    q = np.concatenate([np.asarray(fc(c[i:i + chunk]), np.float32) for i in range(0, len(c), chunk)])
                    save[f"{D.name}|{nm}"] = np.sort(np.maximum(q.reshape(len(org), D.N, H, 3), 0), -1)
                e = np.abs(save[f"{D.name}|qt"][..., 1] - R.truth(D, te, ALL))
                print(f"  {fc.name} {D.name}: test MAE {np.nanmean(e):.2f} ({time.time() - t0:.0f}s)", flush=True)
            meta = dict(name=fc.name + " zero-shot", licence=fc.licence, context_steps=a.ctx, minutes=round((time.time() - t0) / 60, 1))
            np.savez_compressed(f, name=np.array(meta["name"]), meta=np.array(json.dumps(meta)), **save)
            print("OPP " + json.dumps(meta), flush=True)
            del fc
        except Exception as e:
            print(f"OPP-FAILED {key}: {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", default="chronos-bolt,chronos2,tfm25,tfm3")
    ap.add_argument("--ctx", type=int, default=512)
    ap.add_argument("--chunk", type=int, default=1024)
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args())
