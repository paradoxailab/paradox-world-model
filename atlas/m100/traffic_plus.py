"""Atlas-100M-T: a larger traffic adapter on the frozen Atlas-100M (rules: atlas/m100/PREREG_TRAFFIC.md).

Weather and air quality are untouched by construction: this script starts from the exported traffic view
(atlas100m_traffic_view.pt), never loads or writes the multi-domain checkpoint or the other two views, and freezes every
weight of the shared core. What is added, all of it used only by traffic:

  LoRA      a low-rank update (rank r) on every linear layer of the frozen core (encoder and dynamics blocks, spatial
            query/key/value and output). B starts at zero, so the update starts at zero.
  sensor    a learned embedding per sensor of every network (E numbers), fed as extra static inputs; the new input
            weights start at zero, so the model starts exactly as Atlas-100M's traffic view (check T0).
  adapter   the traffic view's own adapter (input, forcing embedding, decoder, reconstruction, geometry MLP) keeps training.

Training uses the traffic harness of Atlas-100M unchanged (atlas/m100/domains.py: Traffic.loss, Traffic.val): traffic
batches only, 12 steps of context, validation = mean over networks of MAE / last-reading MAE. No test window is read.

  cd v0.6-conference && python -u ../atlas/m100/traffic_plus.py train --base $OUT/atlas100m_traffic_view.pt --out $STORE/traffic_plus
  cd v0.6-conference && python -u ../atlas/m100/score_traffic.py --plus $STORE/traffic_plus/atlas100mT_best.pt --name Atlas-100M-T
"""
import argparse, json, math, os, sys, time

import numpy as np
import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from atlas.model import Atlas
from atlas.grow import load_any

CORE = ("enc.", "dyn.", "sp.n.", "sp.qkv.", "sp.o.")        # the shared core (atlas/m100/multi.py); frozen here
ADAPTER = ("inp.", "rec.", "uemb.", "dec.", "sp.geo.")       # the traffic view's own adapter
SENSORS = {170: "PEMS08", 307: "PEMS04", 358: "PEMS03", 883: "PEMS07", 207: "METR-LA", 325: "PEMS-BAY"}


class LoRA(nn.Module):
    """y = W x + b + (alpha / r) B A x, with W, b frozen; B starts at zero."""

    def __init__(self, base, r, alpha):
        super().__init__()
        self.base = base
        for p in base.parameters():
            p.requires_grad_(False)
        self.A = nn.Parameter(torch.randn(r, base.in_features) / math.sqrt(base.in_features))
        self.B = nn.Parameter(torch.zeros(base.out_features, r))
        self.s = alpha / r

    def forward(self, x):
        return self.base(x) + (x @ self.A.t().to(x.dtype)) @ self.B.t().to(x.dtype) * self.s

    def merged_weight(self):
        return self.base.weight + self.s * self.B @ self.A


def widen_context(view, ctx):
    """The view with a longer context window (ctx > L steps) whose input weights for the older steps are ZERO, so the
    forecasts start unchanged (Atlas-100M-T1d, PREREG_TRAFFIC.md addendum A). The last L steps keep their weights."""
    cfg = {k: v for k, v in view.cfg.items() if k != "grown_from"}
    L, C, U, S0 = cfg["L"], cfg["C"], cfg["U"], cfg.get("static", 0)
    big = Atlas(**dict(cfg, L=ctx)).to(next(view.parameters()).device)
    sd = view.state_dict(); new = big.state_dict()
    for k in new:
        if k not in ("inp.weight", "rec.weight", "rec.bias"):
            new[k] = sd[k]
    w0 = sd["inp.weight"]; w = torch.zeros_like(new["inp.weight"]); off = ctx - L
    blocks_old = [(0, L * C, C), (L * C, 2 * L * C, C), (2 * L * C, 2 * L * C + L * U, U)]
    blocks_new = [(0, ctx * C, C), (ctx * C, 2 * ctx * C, C), (2 * ctx * C, 2 * ctx * C + ctx * U, U)]
    for (a0, b0, k), (a1, b1, _) in zip(blocks_old, blocks_new):      # step t of the old window = step off + t
        w[:, a1 + off * k:b1] = w0[:, a0:b0]
    w[:, 2 * ctx * C + ctx * U:] = w0[:, 2 * L * C + L * U:]           # static inputs
    new["inp.weight"] = w
    rw = torch.zeros_like(new["rec.weight"]); rb = torch.zeros_like(new["rec.bias"])
    rw[off * C:] = sd["rec.weight"]; rb[off * C:] = sd["rec.bias"]     # reconstruction: a training aid only
    new["rec.weight"], new["rec.bias"] = rw, rb
    big.load_state_dict(new)
    return big


def set_context(dom, ctx):
    """Traffic harness with a longer look-back: validation baseline (last reading within 12 steps) computed first, as
    for Atlas-100M; training windows without a full look-back are dropped; validation and test windows are unchanged."""
    if dom.persist is None:
        dom.persist = dom._persist()
    for n in dom.nets:
        n.L = ctx
        n.train_idx = n.train_idx[n.train_idx >= ctx]
        n.bs_train = max(1, n.bs_train)
    return dom


def widen_static(view, extra):
    """The view with `extra` more static inputs whose input weights are ZERO: forecasts are unchanged."""
    cfg = {k: v for k, v in view.cfg.items() if k != "grown_from"}
    S0 = cfg.get("static", 0)
    big = Atlas(**dict(cfg, static=S0 + extra)).to(next(view.parameters()).device)
    sd = view.state_dict(); new = big.state_dict()
    for k in new:
        if k != "inp.weight":
            new[k] = sd[k]
    w = torch.zeros_like(new["inp.weight"]); w[:, :sd["inp.weight"].shape[1]] = sd["inp.weight"]
    new["inp.weight"] = w
    big.load_state_dict(new)
    return big


class TrafficPlus(nn.Module):
    def __init__(self, view, r=32, alpha=32, E=32, seed=800, ctx=None):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        self.r, self.alpha, self.E = r, alpha, E
        if ctx and ctx != view.L:
            view = widen_context(view, ctx)
        self.ctx = view.L
        self.view = widen_static(view, E)
        for n, p in self.view.named_parameters():
            p.requires_grad_(n.startswith(ADAPTER))
        torch.manual_seed(seed)
        for blk in list(self.view.enc) + list(self.view.dyn):
            blk.a = LoRA(blk.a, r, alpha); blk.b = LoRA(blk.b, r, alpha)
        self.view.sp.qkv = LoRA(self.view.sp.qkv, r, alpha); self.view.sp.o = LoRA(self.view.sp.o, r, alpha)
        self.emb = nn.ParameterDict({str(N): nn.Parameter(torch.randn(N, E, generator=g) * 0.1) for N in SENSORS})

    def forward(self, yc, mc, uc, uf, geo=None, basis=None, static=None):
        B, N = yc.shape[:2]
        e = self.emb[str(N)].to(static.dtype)[None].expand(B, -1, -1)
        return self.view(yc, mc, uc, uf, geo, basis, torch.cat([static, e], -1))

    def counts(self):
        tr = [p for p in self.parameters() if p.requires_grad]
        lora = sum(p.numel() for n, p in self.named_parameters() if n.endswith((".A", ".B")))
        emb = sum(p.numel() for p in self.emb.parameters())
        return dict(trainable=sum(p.numel() for p in tr), lora=lora, sensor_embeddings=emb, adapter=sum(p.numel() for n, p in self.view.named_parameters()
                    if p.requires_grad and not n.endswith((".A", ".B"))), frozen_core=sum(p.numel() for p in self.parameters() if not p.requires_grad))

    def meta(self):
        return dict(base_cfg={k: v for k, v in self.view.cfg.items() if k != "grown_from"}, r=self.r, alpha=self.alpha, E=self.E,
                    ctx=self.ctx)


def load_plus(path, dev="cpu"):
    ck = torch.load(path, map_location=dev, weights_only=False)
    m = ck["meta"]
    base = Atlas(**dict(m["base_cfg"], static=m["base_cfg"]["static"] - m["E"]))
    model = TrafficPlus(base, r=m["r"], alpha=m["alpha"], E=m["E"])
    model.load_state_dict(ck["sd"])
    return model.to(dev).eval()


def lr_lambda(total, warm):
    return lambda s: min(1.0, (s + 1) / max(1, warm)) * (0.1 + 0.45 * (1 + math.cos(math.pi * min(1.0, s / max(1, total)))))


def train(a):
    from m100 import domains as Dm
    DEV = Dm.DEV
    T0 = time.time()
    torch.manual_seed(a.seed); rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)
    f_last, f_best, f_log = (os.path.join(a.out, f"{a.tag}_{s}") for s in ("last.pt", "best.pt", "log.jsonl"))
    dom = Dm.Traffic(quick=a.quick)
    base = load_any(a.base, DEV).to(DEV).eval()
    v0 = dom.val(base)
    print(f"Atlas-100M traffic view, validation ratio {v0:.5f}", flush=True)
    if a.ctx and a.ctx != base.L:
        set_context(dom, a.ctx)
        print(f"context: {a.ctx} steps (Track B only)", flush=True)
    model = TrafficPlus(base, r=a.r, alpha=a.alpha, E=a.E, seed=a.seed, ctx=a.ctx).to(DEV)
    t0 = dom.val(model.eval())
    print(f"CHECK T0: Atlas-100M-T at start {t0:.5f} vs Atlas-100M {v0:.5f} (diff {abs(t0 - v0):.2e})", flush=True)
    assert abs(t0 - v0) < 2e-3, "T0 failed: the expanded model does not start as Atlas-100M"
    print("parameters: " + json.dumps({k: f"{v:,}" for k, v in model.counts().items()}), flush=True)
    new = [p for n, p in model.named_parameters() if p.requires_grad and (n.endswith((".A", ".B")) or n.startswith("emb."))]
    old = [p for n, p in model.named_parameters() if p.requires_grad and not (n.endswith((".A", ".B")) or n.startswith("emb."))]
    opt = torch.optim.AdamW([{"params": new, "lr": a.lr_new}, {"params": old, "lr": a.lr}], weight_decay=a.wd)
    sch = torch.optim.lr_scheduler.LambdaLR(opt, lr_lambda(a.steps, int(a.warmup * a.steps)))
    step, best, bad = 0, (v0, 0), 0
    if os.path.exists(f_last):
        ck = torch.load(f_last, map_location=DEV, weights_only=False)
        model.load_state_dict(ck["sd"]); opt.load_state_dict(ck["opt"]); sch.load_state_dict(ck["sch"])
        step, best, bad = ck["step"], tuple(ck["best"]), ck["bad"]
        rng = np.random.default_rng(a.seed + step)
        print(f"resumed at step {step}, best {best}", flush=True)
    elif not os.path.exists(f_best):
        torch.save({"sd": model.state_dict(), "meta": model.meta(), "step": 0, "val": t0}, f_best)
    model.train(); ts = time.time()
    while step < a.steps:
        with torch.autocast(DEV, dtype=torch.bfloat16, enabled=(DEV == "cuda")):
            loss = dom.loss(model, rng)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
        opt.step(); sch.step(); step += 1
        if step % a.every == 0 or step == a.steps:
            v = dom.val(model.eval()); model.train()
            better = v < best[0] - 1e-5
            if better:
                best, bad = (v, step), 0
                torch.save({"sd": model.state_dict(), "meta": model.meta(), "step": step, "val": v}, f_best)
            else:
                bad += 1
            rec = dict(step=step, val=round(v, 5), best=round(best[0], 5), best_step=best[1], loss=round(float(loss.item()), 4),
                       min=round((time.time() - T0) / 60, 1))
            print(json.dumps(rec), flush=True)
            open(f_log, "a").write(json.dumps(rec) + "\n")
            torch.save({"sd": model.state_dict(), "opt": opt.state_dict(), "sch": sch.state_dict(), "step": step,
                        "best": list(best), "bad": bad}, f_last)
            if bad >= a.patience or (time.time() - T0) / 60 > a.cap:
                print(f"stop at step {step} ({'patience' if bad >= a.patience else 'time cap'})", flush=True)
                break
    summ = dict(model=a.name, base=os.path.basename(a.base), val_atlas100m=v0, val_start=t0, best_val=best[0],
                best_step=best[1], steps_run=step, minutes=round((time.time() - T0) / 60, 1), params=model.counts(),
                args=vars(a), gpu=torch.cuda.get_device_name(0) if DEV == "cuda" else "cpu")
    json.dump(summ, open(os.path.join(a.out, f"{a.tag}_summary.json"), "w"), indent=1)
    print("SUMMARY " + json.dumps(summ), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["train"])
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="atlas100mT")
    ap.add_argument("--r", type=int, default=32)
    ap.add_argument("--alpha", type=float, default=32)
    ap.add_argument("--E", type=int, default=32)
    ap.add_argument("--steps", type=int, default=40000)
    ap.add_argument("--every", type=int, default=2000)
    ap.add_argument("--patience", type=int, default=6)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--lr_new", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--warmup", type=float, default=0.03)
    ap.add_argument("--cap", type=float, default=240)
    ap.add_argument("--seed", type=int, default=800)
    ap.add_argument("--ctx", type=int, default=0, help="look-back in steps; 0 = the view's own 12 (Atlas-100M-T)")
    ap.add_argument("--name", default="Atlas-100M-T")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    train(a)
