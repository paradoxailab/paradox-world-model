"""Training and prediction for PWM-W Delhi. Validation chooses the checkpoint; test is never touched here."""
import copy, math, time

import numpy as np
import torch

from pw.ddata import L
from pw.dmodel import DelhiModel

DEV = "cuda" if torch.cuda.is_available() else "cpu"
QS = torch.tensor([0.1, 0.5, 0.9])
MKEYS = ("d", "layers", "heads", "ff", "experts", "hier", "use_aux", "use_graph")


def build(cfg, data):
    return DelhiModel(data.K, data.Ca, **{k: cfg[k] for k in MKEYS if k in cfg}).to(DEV)


def augment(b, drop_p=0.1, gap_p=0.2, gap_mean=6.0):
    """Practise real outages: whole stations dark for the window, and bursts of missing hours up to the origin."""
    B, n = b["s"].shape[:2]
    dev = b["s"].device
    keep = (torch.rand(B, n, 1, device=dev) >= drop_p).float().expand(B, n, L).clone()
    g = torch.rand(B, n, device=dev) < gap_p
    ln = (1 + torch.empty(B, n, device=dev).exponential_(1 / max(gap_mean - 1, 1e-3))).clamp(max=L).long()
    t = torch.arange(L, device=dev)[None, None]
    keep *= (~(g[..., None] & (t >= (L - ln)[..., None]))).float()
    b = dict(b)
    b["ho"] = b["ho"] * keep[:, :, None]
    b["ao"] = b["ao"] * keep[:, :, None]
    do = b["do"].clone()
    do[..., -1] = do[..., -1] * keep.amin(-1)[:, :, None]                 # the last day's mean hides with it
    b["do"] = do
    return b


def pinball(q, b):
    """Quantile loss in real units per target, normalised by that target's mean scale, averaged over targets."""
    s, y, v = b["s"], b["y"], b["yo"].float()
    qr = q * s[..., None, None]
    e = y[..., None] - qr
    l = torch.maximum(QS.to(q.device) * e, (QS.to(q.device) - 1) * e).mean(-1)          # [B, n, K, H]
    per = (l * v).sum((0, 1, 3)) / v.sum((0, 1, 3)).clamp(min=1) / s.mean((0, 1)).clamp(min=1e-3)
    return per.mean()


def predict(model, data, org, nodes=None, dark=None, amp=True, chunk=64, seed=0):
    """Real-unit quantiles [W, n, K, H, 3] and truth [W, n, K, H] (NaN = not observed)."""
    model.eval()
    gen = torch.Generator(device="cpu").manual_seed(seed)
    out, ys = [], []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=amp and DEV == "cuda"):
        for i in range(0, len(org), chunk):
            b = data.batch(org[i:i + chunk], nodes, DEV)
            if dark:
                B, n = b["s"].shape[:2]
                k = (torch.rand(B, n, 1, 1, generator=gen) >= dark).float().to(DEV)
                b["ho"], b["ao"] = b["ho"] * k, b["ao"] * k
                b["do"] = b["do"].clone(); b["do"][..., -1] *= k[..., 0]
            q, _ = model(b)
            out.append((q * b["s"][..., None, None]).clamp(min=0).float().cpu().numpy())
            ys.append(torch.where(b["yo"], b["y"], torch.full_like(b["y"], float("nan"))).cpu().numpy())
    return np.concatenate(out), np.concatenate(ys)


def val_mae(model, data, org, nodes, k=0):
    q, y = predict(model, data, org, nodes)
    v = ~np.isnan(y[:, :, k])
    return float(np.abs(q[:, :, k, :, 1] - np.nan_to_num(y[:, :, k]))[v].mean())


def train(cfg, data, org, nodes, val=None, steps=6000, seed=0, log=print):
    """org: training origins; nodes: training stations; val: (origins, nodes) - checkpoint chosen on PM2.5 MAE."""
    torch.manual_seed(seed)
    gen = np.random.default_rng(seed)
    model = build(cfg, data)
    amp = bool(cfg.get("amp", True)) and DEV == "cuda"
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.get("lr", 1.5e-3), weight_decay=1e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    warm = min(300, steps // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda t: min(1, (t + 1) / max(warm, 1)) *
                                              (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(t / steps, 1)))))
    every = cfg.get("eval_every", max(steps // 10, 25))
    best, best_state, t0, t_eval = float("inf"), None, time.time(), 0.0
    for step in range(steps):
        model.train()
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
            te = time.time()
            m = val_mae(model, data, val[0], val[1])
            t_eval += time.time() - te
            if m < best:
                best, best_state = m, copy.deepcopy(model.state_dict())
            log(f"    step {step + 1}/{steps} loss {loss.item():.4f} val PM2.5 MAE {m:.3f} ({time.time() - t0:.0f}s)")
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, {"val_MAE_PM25": best, "seconds": round(time.time() - t0, 1), "steps": steps,
                   "params": model.n_params(), "sec_per_step": round((time.time() - t0 - t_eval) / steps, 4)}
