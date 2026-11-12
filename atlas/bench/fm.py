"""ATF v1.2, part 1: foundation models zero-shot on exactly the windows of curves.py (validation and test, every
network and target). Each model reads the last 512 h of the target variable at one station (no other variables).
GPU recommended (TimesFM on CPU took about 7 h for Delhi alone).

  python fm.py --models chronos2,chronos-bolt,tfm25,tfm3          # -> $ATF_OUT/fm/<network>__<model>.npz, FM lines
"""
import argparse, json, os, sys, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "delhi"))
import curves as CV
from pw import opponents as OPP

OUT = CV.OUT


def main(a):
    os.makedirs(os.path.join(OUT, "fm"), exist_ok=True)
    nets = [n for n in CV.NETWORKS() if not a.only or n["name"] in a.only.split(",")]
    T0 = time.time()
    for spec in nets:
        if not os.path.exists(os.path.join(CV.RAW, spec["file"])):
            CV.log(f"SKIP {spec['name']}: data file missing"); continue
        net = CV.Net(spec)
        yt, yv = net.truth(net.test_org), net.truth(net.val_org)
        for key in a.models.split(","):
            f = os.path.join(OUT, "fm", f"{spec['name']}__{key}.npz")
            if os.path.exists(f):
                continue
            if time.time() - T0 > a.hours * 3600:
                CV.log(f"BUDGET {spec['name']} {key}: skipped"); continue
            try:
                qt, qv, meta = [], [], None
                for k in net.ti:
                    y = net.X[..., k].astype(np.float32)
                    q1, meta = OPP.run(key, y, net.test_org, np.arange(net.N), CV.H, ctx=512, chunk=a.chunk, log=CV.log)
                    q2, _ = OPP.run(key, y, net.val_org, np.arange(net.N), CV.H, ctx=512, chunk=a.chunk, log=CV.log)
                    qt.append(q1); qv.append(q2)
                qt, qv = np.stack(qt, 3), np.stack(qv, 3)                 # [W, N, H, K, 3]
                np.savez_compressed(f, qt=qt.astype(np.float16), qv=qv.astype(np.float16), meta=np.array(json.dumps(meta)))
                CV.log("FM " + json.dumps(dict(network=spec["name"], model=key, name=meta["name"], params=meta["params"],
                                              test=CV.metrics(net, qt[..., 1], yt), val=CV.metrics(net, qv[..., 1], yv))))
            except Exception as e:
                CV.log(f"FM-FAILED {spec['name']} {key}: {type(e).__name__}: {e}")
    CV.log(f"done in {(time.time() - T0) / 60:.1f} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="chronos2,chronos-bolt,tfm25,tfm3")
    ap.add_argument("--only", default="")
    ap.add_argument("--chunk", type=int, default=512)
    ap.add_argument("--hours", type=float, default=11.0)
    main(ap.parse_args())
