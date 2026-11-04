"""Training for Paradox World Model v0.1: supervised forecasting, self-supervised masked reconstruction, sparse
experts, mixed precision, flow-conservation (physics) loss, and training on an arbitrary subset of windows
(used for active learning). Validation chooses the checkpoint; test is never touched here."""
import copy, math, time

import numpy as np
import torch
import torch.nn.functional as F

from pw.data import L, H
from pw.model import WorldModel

DEV = "cuda" if torch.cuda.is_available() else "cpu"
QS = torch.tensor([0.1, 0.5, 0.9])


def build(cfg):
    keys = ("d", "layers", "heads", "ff", "experts", "hier", "weather")
    return WorldModel(**{k: cfg[k] for k in keys if k in cfg}).to(DEV)


def crop_nodes(net, k, gen):
    """Connected sub-network of up to k sensors grown breadth-first from a random sensor (pretraining crops)."""
    if net.N <= k:
        return np.arange(net.N)
    nb = [np.where(net.A[i] > 0)[0] for i in range(net.N)]
    start = int(gen.integers(net.N))
    seen, frontier = [start], [start]
    mark = np.zeros(net.N, bool); mark[start] = True
    while frontier and len(seen) < k:
        nxt = []
        for i in frontier:
            for j in gen.permutation(nb[i]):
                if not mark[j]:
                    mark[j] = True; seen.append(j); nxt.append(j)
        frontier = nxt
    if len(seen) < k:                                  # disconnected graph: top up with random sensors
        rest = np.where(~mark)[0]
        seen += list(gen.choice(rest, k - len(seen), replace=False))
    return np.sort(np.array(seen[:k]))


def augment(b, gen, drop_p=0.1, gap_p=0.2, gap_mean=6.0):
    """Practise real failures: whole-window sensor dropout and bursts of missing readings up to the origin."""
    B, n, _ = b["ho"].shape
    dev = b["ho"].device
    keep = torch.ones(B, n, L, device=dev)
    if drop_p:
        keep *= (torch.rand(B, n, 1, device=dev) >= drop_p).float()
    if gap_p:
        g = torch.rand(B, n, device=dev) < gap_p
        ln = (1 + torch.empty(B, n, device=dev).exponential_(1 / max(gap_mean - 1, 1e-3))).clamp(max=L).long()
        end = torch.where(torch.rand(B, n, device=dev) < 0.7, torch.full_like(ln, L),
                          (torch.rand(B, n, device=dev) * L).long() + 1)
        t = torch.arange(L, device=dev)[None, None]
        gap = g[..., None] & (t >= (end - ln)[..., None]) & (t < end[..., None])
        keep *= (~gap).float()
    b = dict(b)
    b["ho"], b["ao"] = b["ho"] * keep, b["ao"] * keep
    return b


def ssl_mask(b, cell_p=0.3, sensor_p=0.15):
    """Masked modelling: hide 30% of history cells and 15% of whole sensor windows; the target is every hidden
    cell that was actually observed."""
    B, n, _ = b["ho"].shape
    dev = b["ho"].device
    m = (torch.rand(B, n, L, device=dev) < cell_p) | (torch.rand(B, n, 1, device=dev) < sensor_p)
    tgt = m.float() * b["ho"]
    b = dict(b)
    b["ho"], b["ao"] = b["ho"] * (~m).float(), b["ao"] * (~m).float()
    return b, tgt


def pinball(q, y, valid, s):
    """Quantile loss in real units (q in weekly-mean units times the sensor scale), normalised by the batch's mean
    scale so that flow and speed networks train at comparable magnitudes."""
    qr = q * s[..., None, None]
    e = y[..., None] - qr
    l = torch.maximum(QS.to(q.device) * e, (QS.to(q.device) - 1) * e).mean(-1)
    v = valid.float()
    return (l * v).sum() / v.sum().clamp(min=1) / s.mean().clamp(min=1e-3)


def physics_loss(q, s, net, nodes):
    """Flow conservation on detector pairs with a stable train-split ratio r: q50_j ~ r * q50_i."""
    if not len(net.pairs):
        return q.new_zeros(())
    pos = -np.ones(net.N, np.int64); pos[nodes] = np.arange(len(nodes))
    pi, pj = pos[net.pairs[:, 0]], pos[net.pairs[:, 1]]
    ok = (pi >= 0) & (pj >= 0)
    if not ok.any():
        return q.new_zeros(())
    pi, pj = torch.as_tensor(pi[ok], device=q.device), torch.as_tensor(pj[ok], device=q.device)
    r = torch.as_tensor(net.ratio[ok], device=q.device)
    m = q[..., 1] * s[..., None]                                       # [B, n, H] real units
    d = (m[:, pj] - r[None, :, None] * m[:, pi]) / s[:, pj, None].clamp(min=1e-3)
    return (d ** 2).mean()


def predict(model, net, org, nodes=None, dark=None, amp=True, chunk=32, seed=0):
    """Real-unit quantiles [W, n, H, 3], truth [W, n, H] (NaN = not observed). dark: share of sensors whose whole
    12-step input is blanked per window (fixed seed)."""
    model.eval()
    gen = torch.Generator(device="cpu").manual_seed(seed)
    out, ys = [], []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=amp and DEV == "cuda"):
        for i in range(0, len(org), chunk):
            b = net.batch(org[i:i + chunk], nodes, DEV)
            if dark:
                B, n, _ = b["ho"].shape
                k = (torch.rand(B, n, 1, generator=gen) >= dark).float().to(DEV)
                b["ho"], b["ao"] = b["ho"] * k, b["ao"] * k
            q, _ = model(b)
            q = (q * b["s"][..., None, None]).clamp(min=0)
            out.append(q.float().cpu().numpy())
            ys.append(torch.where(b["yo"], b["y"], torch.full_like(b["y"], float("nan"))).cpu().numpy())
    return np.concatenate(out), np.concatenate(ys)


def val_mae(model, net, org, nodes, amp):
    q, y = predict(model, net, org, nodes, amp=amp)
    v = ~np.isnan(y)
    return float(np.abs(q[..., 1] - np.nan_to_num(y))[v].mean())


def train(cfg, sources, val=None, steps=3000, seed=0, init=None, log=print, budget_s=None):
    """sources: list of (net, origins, nodes or None, weight). val: (net, origins, nodes) for checkpoint choice.
    cfg keys: model (d, layers, heads, ff, experts, hier, weather) and training (bs, lr, amp, ssl_steps, ssl_w,
    phys_w, moe_w, crop, drop_p, gap_p, eval_every)."""
    torch.manual_seed(seed)
    gen = np.random.default_rng(seed)
    model = build(cfg)
    if init is not None:
        model.load_state_dict(init)
    amp = bool(cfg.get("amp", True)) and DEV == "cuda"
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.get("lr", 2e-3), weight_decay=cfg.get("wd", 1e-4))
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    warm = min(200, steps // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda t: min(1, (t + 1) / max(warm, 1)) *
                                              (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(t / steps, 1)))))
    w = np.array([s[3] for s in sources], float); w /= w.sum()
    bs, crop = cfg.get("bs", 16), cfg.get("crop", 256)
    ssl_steps, ssl_w = int(cfg.get("ssl_steps", 0)), cfg.get("ssl_w", 0.0)
    phys_w, moe_w = cfg.get("phys_w", 0.0), cfg.get("moe_w", 0.01)
    every = cfg.get("eval_every", max(steps // 10, 50))
    best, best_state, curve = float("inf"), None, []
    t0, t_eval = time.time(), 0.0
    if DEV == "cuda":
        torch.cuda.reset_peak_memory_stats()
    for step in range(steps):
        model.train()
        k = gen.choice(len(sources), p=w)
        net, org, nodes, _ = sources[k]
        if nodes is None:
            nodes = crop_nodes(net, crop, gen)
        b = net.batch(gen.choice(org, bs), nodes, DEV)
        b = augment(b, gen, cfg.get("drop_p", 0.1), cfg.get("gap_p", 0.2))
        pre = step < ssl_steps                                         # self-supervised phase
        use_ssl = pre or ssl_w > 0
        if use_ssl:
            b, tgt = ssl_mask(b)
        with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
            q, z = model(b)
            loss = q.new_zeros(())
            if use_ssl:
                r = model.reconstruct(z)
                rec = (torch.abs(r - b["hx"]) * tgt).sum() / tgt.sum().clamp(min=1)
                loss = loss + (1.0 if pre else ssl_w) * rec
            if not pre:
                loss = loss + pinball(q, b["y"], b["yo"], b["s"])
                if phys_w:
                    loss = loss + phys_w * physics_loss(q, b["s"], net, nodes)
            if cfg.get("experts"):
                loss = loss + moe_w * model.moe_aux()
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt); scaler.update(); sched.step()
        last = step == steps - 1 or (budget_s and time.time() - t0 > budget_s)
        if val is not None and not pre and ((step + 1) % every == 0 or last):
            te = time.time()
            m = val_mae(model, val[0], val[1], val[2], amp)
            t_eval += time.time() - te
            curve.append((step + 1, round(time.time() - t0, 1), m))
            if m < best:
                best, best_state = m, copy.deepcopy(model.state_dict())
            log(f"    step {step + 1}/{steps} loss {loss.item():.4f} val MAE {m:.3f} ({time.time() - t0:.0f}s)")
        if last:
            break
    if best_state is None:
        best_state = copy.deepcopy(model.state_dict())
    model.load_state_dict(best_state)
    info = {"val_MAE": best, "curve": curve, "seconds": round(time.time() - t0, 1), "steps": step + 1,
            "params": model.n_params(), "active_params": model.n_params(active=True),
            "peak_mem_MB": round(torch.cuda.max_memory_allocated() / 2 ** 20) if DEV == "cuda" else None,
            "sec_per_step": round((time.time() - t0 - t_eval) / (step + 1), 4)}
    return model, info
