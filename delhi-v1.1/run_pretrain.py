"""PWM-F pretraining: one ~10M-parameter model on every Indian NOAA ISD station network (WX_IN01 .. WX_INnn,
tools/fetch_india_isd.py), 2015-01-01 .. 2024-11-30.

The model is PWM-W's station-graph world model scaled up, with the v0.9 21-day patch encoder whose feed-forward
layers are a shared + routed mixture of experts (pw/moe.py), trained with the forecast (pinball) loss plus masked-patch
reconstruction. Every batch comes from one regional network chosen at random, so the model learns weather across
India's climates and station types; it never sees any league's validation or test period (all data end 2024-11-30).
Checkpoint choice uses the pretraining networks' own last 60 days (2024-09-25 .. 2024-11-23), averaged over networks.

  python run_pretrain.py [--steps 40000]     -> $PW_OUT/pwmf_pretrained.pt
"""
import argparse, glob, json, os, time

import numpy as np
import torch

from pw.wdata import Wx, RAW
from pw import wtrain as WT

OUT = os.environ.get("PW_OUT", "out")
PWMF = dict(d=256, layers=4, heads=8, ff=2, experts=0, use_graph=True, xarch=True, ssl=True, xlayers=4,
            xmoe=True, x_experts=12, x_topk=2, ema=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=40000)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--val_nets", type=int, default=4, help="networks whose validation windows pick the checkpoint")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = sorted(os.path.basename(p)[3:-4] for p in glob.glob(os.path.join(RAW, "WX_IN[0-9]*.npz")))
    if not names:
        raise SystemExit("no WX_IN*.npz networks: run tools/fetch_india_isd.py first")
    nets = []
    for nm in names:
        D = Wx(nm)
        tr = D.origins("train", 1)
        if D.N >= 3 and len(tr) > 1000:
            nets.append((D, tr))
            print(f"{nm}: {D.N} stations, {len(tr)} training origins, other channels {D.aux_names}", flush=True)
    aux = nets[0][0].aux_names
    assert all(D.aux_names == aux for D, _ in nets), "pretraining networks must share one channel layout"
    nets.sort(key=lambda x: -x[0].N)
    vnets = [(D, D.origins("val", 6)) for D, _ in nets[:a.val_nets]]
    sh = int(sum(np.isfinite(D.Y[..., 0]).sum() for D, _ in nets))
    print(f"PRETRAIN-DATA: {len(nets)} networks, {sum(D.N for D, _ in nets)} stations, {sh:,} station-hours with a "
          f"temperature; checkpoint chosen on {[D.league for D, _ in vnets]}", flush=True)

    # validation = mean over the chosen networks; WT.train scores `data` only, so wrap its val_score
    orig = WT.val_score

    def multi_val(model, data, org, nodes=None):
        return float(np.mean([orig(model, D, o) for D, o in vnets]))

    WT.val_score = multi_val
    cfg = dict(PWMF, lr=a.lr, bs=a.bs, extra_p=1.0, eval_every=max(500, a.steps // 20))
    t0 = time.time()
    D0, tr0 = nets[0]
    model, info = WT.train(cfg, D0, tr0, None, vnets[0][1], a.steps, seed=0, log=print, extra=nets)
    WT.val_score = orig
    meta = {"networks": [D.league for D, _ in nets], "stations": int(sum(D.N for D, _ in nets)),
            "station_hours": sh, "aux_names": aux, "cfg": PWMF, "steps": a.steps, "val_score": info["val_score"],
            "params": info["params"], "seconds": round(time.time() - t0, 1), "data_end": "2024-11-30"}
    torch.save({"state": model.state_dict(), "meta": meta}, os.path.join(OUT, "pwmf_pretrained.pt"))
    json.dump(meta, open(os.path.join(OUT, "pwmf_pretrained.json"), "w"), indent=1)
    print(f"PRETRAIN-DONE: {info['params']:,} parameters, {a.steps} steps, best multi-network validation "
          f"{info['val_score']:.4f}, {time.time() - t0:.0f}s -> {OUT}/pwmf_pretrained.pt", flush=True)


if __name__ == "__main__":
    main()
