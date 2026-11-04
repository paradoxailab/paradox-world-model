"""Train PWM-Dyn (v0.4-v0.7) from scratch (random initialisation) on real observations.

v0.4 changes vs v0.3: --lc adds the seasonal-lag window (long-context variant, Track B of ParadoxBench-1);
default recipe batch 64 / 40 epochs / peak lr 3e-3 / validation every epoch on every 4th window.

  python train.py --data PEMS08 --version v0.3-s0 --seed 0
  python train.py --data IMD_central_india --version v0.3-s0 --seed 0

Every run is saved to models/<data>/<version>/ (weights + report). A run is PROMOTED for its
dataset only if its VALIDATION MAE beats the currently promoted run. Test numbers are
recorded but never used to choose models.
"""
import argparse, json, os, sys, time
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pwm.data import load, ROOT
from pwm.evaluation import score
from pwm.model import PWMDyn, pinball

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def build(ds, cfg):
    return PWMDyn(ds.N, in_len=ds.in_len, out_len=ds.out_len, d=cfg["d"], layers=cfg["layers"],
                  transductive=cfg["variant"] == "transductive", steps_per_day=ds.period,
                  mask_aware=True, lag_len=ds.extra_len, use_clim=cfg.get("clim", False),
                  fallback=cfg.get("fallback", False))


@torch.no_grad()
def predict(model, ds, idx, bs=64, drop_nodes=None, gaps=None):
    """Returns q10, q50, q90, y as numpy [S, H, N] in real units.
    drop_nodes: locations with no observations at all (Track R); gaps: bool [S, in_len, N], True = this recent
    input reading is removed (v0.7, Track G real-outage replay)."""
    model.eval()
    A = ds.A.to(next(model.parameters()).device)
    dev = A.device
    Q, Y = [], []
    for s in range(0, len(idx), bs):
        x, obs, y, p, d, c = ds.batch(idx[s:s + bs], dev)
        if drop_nodes is not None:                       # simulate offline sensors
            obs = obs.clone(); obs[..., drop_nodes] = False
            x = x * obs
        if gaps is not None:                             # replayed outages in the recent input window
            g = torch.from_numpy(gaps[s:s + bs]).to(dev)
            obs = obs.clone(); obs[:, -g.shape[1]:] &= ~g
            x = x * obs
        q = ds.inv(model(x, p, d, A, obs, c))
        Q.append(q.cpu().numpy()); Y.append(y.cpu().numpy())
    q, y = np.concatenate(Q), np.concatenate(Y)
    return q[..., 0], q[..., 1], q[..., 2], y


def evaluate(model, ds, split, stride=1):
    q10, q50, q90, y = predict(model, ds, ds.indices(split, stride))
    return score(q10, q50, q90, y, ds.valid(y))


def outage_masks(B, L, N, p, mean, device, gen=None):
    """v0.7 training augmentation: with probability p a (sample, location) gets one outage that starts at a uniform
    step of the recent window and lasts 1 + Exp(mean - 1) steps (clipped by the window end, so long outages remove
    the latest readings, as real outages mostly do). Returns bool [B, L, N], True = removed."""
    sel = torch.rand(B, 1, N, device=device, generator=gen) < p
    start = torch.randint(0, L, (B, 1, N), device=device, generator=gen)
    u = torch.rand(B, 1, N, device=device, generator=gen).clamp(min=1e-6)
    length = 1 + torch.floor(-torch.log(u) * max(mean - 1, 1e-3))
    t = torch.arange(L, device=device)[None, :, None]
    return sel & (t >= start) & (t < start + length)


class EMA:
    """v0.7: exponential moving average of the weights; validation and the saved checkpoint use the average."""

    def __init__(self, model, decay):
        self.decay, self.n = decay, 0
        self.shadow = {k: v.detach().clone() for k, v in model.state_dict().items()}

    @torch.no_grad()
    def update(self, model):
        self.n += 1
        d = min(self.decay, (1 + self.n) / (10 + self.n))
        for k, v in model.state_dict().items():
            if v.dtype.is_floating_point:
                self.shadow[k].mul_(d).add_(v.detach(), alpha=1 - d)
            else:
                self.shadow[k].copy_(v)

    def swap(self, model):
        cur = {k: v.detach().clone() for k, v in model.state_dict().items()}
        model.load_state_dict(self.shadow)
        self.shadow = cur


def run(args):
    ds = load(args.data, lc=args.lc, profile=args.profile)
    print(ds.describe(), "| device:", DEV, flush=True)
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    cfg = {k: getattr(args, k) for k in ("d", "layers", "variant", "clim", "lc", "profile", "fallback")}
    model = build(ds, cfg).to(DEV)
    A = ds.A.to(DEV)
    nparam = sum(p.numel() for p in model.parameters())
    print(f"PWM-Dyn [{args.variant}{', long-context' if args.lc else ''}{', profile' if args.profile else ''}] context {ds.context} steps, parameters: {nparam:,} (random init, no pretrained weights)", flush=True)
    tr = ds.indices("train")
    if args.step_budget:            # v0.6: a fixed optimisation-step budget (the one validated on PEMS08)
        args.epochs = int(min(args.epochs, -(-args.step_budget // (len(tr) // args.bs + 1))))
        print(f"step budget {args.step_budget} -> {args.epochs} epochs", flush=True)
    steps = args.epochs * (len(tr) // args.bs + 1)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, args.lr, total_steps=steps)
    best, best_state, log, t0 = 1e18, None, [], time.time()
    ema = EMA(model, args.ema) if args.ema > 0 else None
    # v0.8 relative-error weights: 1 / max(y, floor) scaled so that the mean weight on the training split is ~1;
    # floor = 10% of the training mean of valid readings (rain: 1 mm/day), so near-zero truths cannot dominate
    _, b = ds.bounds["train"]
    trv = ds.raw[:b][ds.observed[:b] & (ds.raw[:b] > (1e-4 if ds.mask_zero else -1))]
    rel_floor = 1.0 if ds.transform == "log1p" else 0.1 * float(trv.mean())
    rel_scale = 1.0 / float(np.mean(1.0 / np.maximum(trv, rel_floor)))
    for ep in range(args.epochs):
        model.train()
        perm, tot = np.random.permutation(tr), 0.0
        for s in range(0, len(perm), args.bs):
            x, obs, y, p, d, c = ds.batch(perm[s:s + args.bs], DEV)
            if args.mask_p > 0:          # hide random locations: forces use of physical neighbours
                rate = torch.rand(len(x), 1, 1, device=DEV) * args.mask_p
                obs = obs & (torch.rand(len(x), 1, ds.N, device=DEV) >= rate)
                x = x * obs
            if args.gap_p > 0:           # v0.7: burst outages inside the recent window
                g = outage_masks(len(x), ds.in_len, ds.N, args.gap_p, args.gap_mean, DEV)
                obs = obs.clone(); obs[:, -ds.in_len:] &= ~g
                x = x * obs
            valid = ~torch.isnan(y)
            if ds.mask_zero:
                valid &= y > 1e-4
            y0 = torch.nan_to_num(y, nan=0.0)
            yt = torch.log1p(y0.clamp(min=0)) if ds.transform == "log1p" else y0
            yn = (yt - ds.mean) / ds.std
            q = model(x, p, d, A, obs, c)
            loss = pinball(q, yn, valid) + (torch.abs(q[..., 1] - yn) * valid).sum() / valid.sum().clamp(min=1)
            if args.rel_w > 0:           # v0.8: relative-error term, low readings count more (MAPE-aware)
                w = rel_scale / y0.clamp(min=rel_floor)
                loss = loss + args.rel_w * (torch.abs(q[..., 1] - yn) * w * valid).sum() / valid.sum().clamp(min=1)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step(); sched.step()
            if ema is not None:
                ema.update(model)
            tot += loss.item() * len(x)
        if ema is not None:
            ema.swap(model)              # evaluate (and keep) the averaged weights
        val = evaluate(model, ds, "val", stride=args.val_stride)
        log.append({"epoch": ep + 1, "loss": tot / len(perm), "val_MAE": val["MAE"]})
        print(f"ep {ep+1:3d} loss {tot/len(perm):.4f} val MAE {val['MAE']:.3f} ({(time.time()-t0)/60:.1f} min)", flush=True)
        if val["MAE"] < best:
            best, best_state = val["MAE"], {k: v.detach().clone() for k, v in model.state_dict().items()}
        if ema is not None:
            ema.swap(model)              # back to the raw weights for the next epoch
        if args.max_minutes and (time.time() - t0) / 60 > args.max_minutes:
            print("time budget reached", flush=True)
            break
    model.load_state_dict(best_state)

    out = os.path.join(ROOT, "models", ds.name, args.version)
    os.makedirs(out, exist_ok=True)
    torch.save({k: v.cpu() for k, v in model.state_dict().items()}, f"{out}/weights.pt")
    rep = {"model": "PWM-Dyn", "provenance": "Paradox-trained from random initialisation",
           "dataset": ds.name, "version": args.version, "parameters": nparam,
           "config": vars(args), "train_log": log,
           "val": evaluate(model, ds, "val", stride=2)}
    json.dump(rep, open(f"{out}/report.json", "w"), indent=1)
    v = rep["val"]          # test numbers are NOT printed here: ParadoxBench scoring happens once, in paradoxbench/run_pwm.py
    print(f"{ds.name} {args.version}: best val MAE {v['MAE']:.3f} cov80 {v['interval_80_coverage']*100:.1f}% "
          f"({(time.time()-t0)/60:.1f} min)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="PEMS08")
    ap.add_argument("--version", required=True)
    ap.add_argument("--variant", default="transductive", choices=["transductive", "inductive"])
    ap.add_argument("--lc", action="store_true", help="v0.4 long-context variant (seasonal-lag window)")
    ap.add_argument("--profile", action="store_true", help="v0.5 multi-scale profile of the last day / year")
    ap.add_argument("--no_clim", dest="clim", action="store_false",
                    help="disable the train-split climatology input (used for zero-shot transfer models)")
    ap.add_argument("--fallback", action="store_true",
                    help="v0.7: base = last observed reading, else climatology; adds age / no-reading cues")
    ap.add_argument("--gap_p", type=float, default=0.0, help="v0.7: share of (sample, location) pairs given an outage")
    ap.add_argument("--gap_mean", type=float, default=6.0, help="v0.7: mean outage length in steps")
    ap.add_argument("--ema", type=float, default=0.0, help="v0.7: EMA decay of the weights (0 = off)")
    ap.add_argument("--rel_w", type=float, default=0.0, help="v0.8: weight of the relative-error loss term (0 = off)")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--bs", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--d", type=int, default=96)
    ap.add_argument("--layers", type=int, default=3)
    ap.add_argument("--mask_p", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--val_stride", type=int, default=4)
    ap.add_argument("--max_minutes", type=float, default=0, help="stop early after this many minutes (0 = off)")
    ap.add_argument("--step_budget", type=int, default=0, help="cap epochs so that total steps <= this (0 = off)")
    run(ap.parse_args())
