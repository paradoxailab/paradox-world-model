"""Training and prediction for PWM-W Weather. Validation chooses the checkpoint; test is never touched here."""
import copy, math, time

import numpy as np
import torch

from pw.wdata import L
from pw.wmodel import WxModel

DEV = "cuda" if torch.cuda.is_available() else "cpu"
QS = torch.tensor([0.1, 0.5, 0.9])
MKEYS = ("d", "layers", "heads", "ff", "experts", "hier", "use_graph", "use_nwp")


def build(cfg, data):
    return WxModel(data.K, data.Ca, data.Cn, **{k: cfg[k] for k in MKEYS if k in cfg}).to(DEV)


def augment(b, drop_p=0.1, gap_p=0.2, gap_mean=6.0):
    """Practise real outages: stations dark for the window, bursts of missing hours up to the origin."""
    B, n = b["base"].shape[:2]
    dev = b["base"].device
    Lh = b["ho"].shape[-1]
    keep = (torch.rand(B, n, 1, device=dev) >= drop_p).float().expand(B, n, Lh).clone()
    g = torch.rand(B, n, device=dev) < gap_p
    ln = (1 + torch.empty(B, n, device=dev).exponential_(1 / max(gap_mean - 1, 1e-3))).clamp(max=L).long()
    t = torch.arange(Lh, device=dev)[None, None]
    keep *= (~(g[..., None] & (t >= (Lh - ln)[..., None]))).float()
    b = dict(b)
    b["ho"] = b["ho"] * keep[:, :, None]
    b["hx"] = b["hx"] * keep[:, :, None]
    b["ao"] = b["ao"] * keep[:, :, None, -L:]
    return b


def pinball(q, b):
    """Quantile loss per target in units of its spread, averaged over targets."""
    y, v = b["y"], b["yo"].float()
    e = (y[..., None] - q) / b["sd"][None, None, :, None, None]
    l = torch.maximum(QS.to(q.device) * e, (QS.to(q.device) - 1) * e).mean(-1)          # [B, n, K, H]
    per = (l * v).sum((0, 1, 3)) / v.sum((0, 1, 3)).clamp(min=1)
    return per.mean()


LIM = np.array([[-40, 60], [0, 100], [0, 60]], np.float32)


def predict(model, data, org, nodes=None, amp=True, chunk=64):
    """Real-unit quantiles [W, n, K, H, 3] and truth [W, n, K, H] (NaN = not observed)."""
    model.eval()
    out, ys = [], []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=amp and DEV == "cuda"):
        for i in range(0, len(org), chunk):
            b = data.batch(org[i:i + chunk], nodes, DEV)
            q, _ = model(b)
            out.append(q.float().cpu().numpy())
            ys.append(torch.where(b["yo"], b["y"], torch.full_like(b["y"], float("nan"))).cpu().numpy())
    q = np.concatenate(out)
    q = np.clip(q, LIM[None, None, :, None, None, 0], LIM[None, None, :, None, None, 1])
    return q, np.concatenate(ys)


def val_score(model, data, org, nodes=None):
    q, y = predict(model, data, org, nodes)
    v = ~np.isnan(y)
    return float(np.mean([np.abs(q[:, :, k, :, 1] - np.nan_to_num(y[:, :, k]))[v[:, :, k]].mean() / data.sd[k]
                          for k in range(data.K)]))


def train(cfg, data, org, nodes=None, val=None, steps=6000, seed=0, log=print, extra=None):
    """extra: optional [(other_network, its_origins)] sampled for half of the batches (joint training across
    station networks; the model is inductive over stations). Validation uses `data` only."""
    torch.manual_seed(seed)
    gen = np.random.default_rng(seed)
    model = build(cfg, data)
    amp = bool(cfg.get("amp", True)) and DEV == "cuda"
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.get("lr", 1.5e-3), weight_decay=1e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    warm = min(300, steps // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda t: min(1, (t + 1) / max(warm, 1)) *
                                              (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(t / steps, 1)))))
    every = cfg.get("eval_every", max(steps // 12, 25))
    best, best_state, t0 = float("inf"), None, time.time()
    for step in range(steps):
        model.train()
        if extra and gen.random() < 0.5:
            dx, ox = extra[gen.integers(len(extra))]
            b = augment(dx.batch(gen.choice(ox, cfg.get("bs", 32)), None, DEV))
        else:
            b = augment(data.batch(gen.choice(org, cfg.get("bs", 32)), nodes, DEV))
        with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
            q, _ = model(b)
            loss = pinball(q, b)
            if cfg.get("experts"):
                loss = loss + 0.01 * model.moe_aux()
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt); scaler.update(); sched.step()
        if val is not None and ((step + 1) % every == 0 or step == steps - 1):
            m = val_score(model, data, val, nodes)
            if m < best:
                best, best_state = m, copy.deepcopy(model.state_dict())
            log(f"    step {step + 1}/{steps} loss {loss.item():.4f} val MAE/spread {m:.4f} ({time.time() - t0:.0f}s)")
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, {"val_score": best, "seconds": round(time.time() - t0, 1), "steps": steps,
                   "params": model.n_params()}
