"""PWM-India (v2.0) pretraining: the 10.1M-parameter PWM-X model trained on the India-wide station corpus.

Corpus: data/raw/WX_INDIA.npz (tools/fetch_india.py): every Indian NOAA ISD station with records overlapping 2024,
2015-01-01 .. 2024-11-30. It ends before the earliest validation period of any league, so the pretrained weights
have seen nothing from any league's validation or test period. The corpus's own last 30 days only pick the
checkpoint. Each batch is one spatially coherent group of 48 stations (a random station and its 47 nearest).

  python pretrain_india.py --steps 30000        # -> out/pwm_india_pretrained.pt
"""
import argparse, json, os, time

import numpy as np
import torch

from pw.wdata import Wx
from pw import wtrain as WT

OUT = os.environ.get("PW_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
CFG = dict(d=288, layers=6, heads=8, ff=2, experts=0, use_graph=True, xarch=True, ssl=True, ema=True, xlayers=4,
           lr=7e-4, bs=32, sub=48)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    D = Wx("INDIA")
    print(D.describe(), flush=True)
    tr, va = D.origins("train", 1), D.origins("val", 6)
    print(f"pretraining origins {len(tr)}, checkpoint-selection origins {len(va)}; {D.N} stations; "
          f"other channels {D.aux_names}", flush=True)
    # validation on a fixed set of neighbourhoods (the full network does not fit one batch for the 10M model)
    g = np.random.default_rng(123)
    groups = [D.subset(g, CFG["sub"]) for _ in range(4)]
    t0 = time.time()
    cfg = dict(CFG, steps=a.steps, eval_every=max(a.steps // 20, 100))
    model, info = train_grouped(cfg, D, tr, va, groups, a.seed)
    path = os.path.join(OUT, "pwm_india_pretrained.pt")
    torch.save({"state": model.state_dict(), "cfg": CFG, "aux_names": list(D.aux_names), "stations": D.stations,
                "n_params": model.n_params(), "info": info, "corpus_end": str(D.dates[-1])}, path)
    print(f"PRETRAINED {model.n_params():,} parameters on {D.N} stations, {len(tr)} origins, {a.steps} steps, "
          f"checkpoint score {info['val_score']:.4f} ({time.time() - t0:.0f}s) -> {path}", flush=True)
    json.dump({k: v for k, v in info.items()}, open(os.path.join(OUT, "pretrain_india.json"), "w"), indent=1)


def train_grouped(cfg, D, tr, va, groups, seed):
    """Like WT.train, but every training batch is a random 48-station neighbourhood and the checkpoint score is the
    mean over fixed neighbourhoods."""
    import copy, math
    torch.manual_seed(seed)
    gen = np.random.default_rng(seed)
    model = WT.build(cfg, D)
    amp = WT.DEV == "cuda"
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=1e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    steps = cfg["steps"]
    warm = min(1000, steps // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda t: min(1, (t + 1) / max(warm, 1)) *
                                              (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(t / steps, 1)))))
    ema = copy.deepcopy(model)
    best, best_state, t0 = float("inf"), None, time.time()
    for step in range(steps):
        model.train()
        b = WT.augment(D.batch(gen.choice(tr, cfg["bs"]), D.subset(gen, cfg["sub"]), WT.DEV))
        with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
            q, _ = model(b)
            loss = WT.pinball(q, b) + 0.1 * model.ssl_loss
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt); scaler.update(); sched.step()
        dcy = min(0.998, (step + 1) / (step + 10))
        with torch.no_grad():
            for pe, pm in zip(ema.parameters(), model.parameters()):
                pe.mul_(dcy).add_(pm.detach(), alpha=1 - dcy)
        if (step + 1) % cfg["eval_every"] == 0 or step == steps - 1:
            m = float(np.mean([WT.val_score(ema, D, va, grp) for grp in groups]))
            if m < best:
                best, best_state = m, copy.deepcopy(ema.state_dict())
            print(f"    step {step + 1}/{steps} loss {loss.item():.4f} checkpoint MAE/spread {m:.4f} "
                  f"({time.time() - t0:.0f}s)", flush=True)
    model.load_state_dict(best_state)
    return model, {"val_score": best, "seconds": round(time.time() - t0, 1), "steps": steps,
                   "params": model.n_params()}


if __name__ == "__main__":
    main()
