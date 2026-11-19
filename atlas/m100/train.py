"""Train Atlas-100M on three domains at once (rules: atlas/m100/PREREG.md, fixed before this ran).

  python -u atlas/m100/train.py --init models/series/59_atlas-5k-25m_weather5k_adopted.pt --out $ATLAS_OUT
Re-running the same command resumes from {out}/{tag}_last.pt (model, optimiser, schedule, step, best, random state).

Every step draws one domain (weather 0.5, AQ 0.25, traffic 0.25) and takes one batch of that domain's own harness,
with that harness's own loss. Every --every steps each domain's validation metric is computed on fixed windows; the
checkpoint kept is the one with the lowest S = sum over domains of log(validation metric) -- equivalently the lowest
product, so no domain's units or reference matter. No test window is read by this script.
"""
import argparse, json, math, os, sys, time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from m100 import domains as Dm
from m100.multi import MultiAtlas, build_from_24m
from atlas.grow import load_any

DEV = Dm.DEV


def log(*a):
    print(*a, flush=True)


def lr_lambda(total, warm):
    return lambda s: min(1.0, (s + 1) / max(1, warm)) * (0.1 + 0.45 * (1 + math.cos(math.pi * min(1.0, s / max(1, total)))))


def main(a):
    T0 = time.time()
    torch.manual_seed(a.seed); rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)
    f_last, f_best = os.path.join(a.out, f"{a.tag}_last.pt"), os.path.join(a.out, f"{a.tag}_best.pt")
    f_log = os.path.join(a.out, f"{a.tag}_log.jsonl")
    names = [d for d in a.domains.split(",") if d]
    probs = dict(zip(names, [float(x) for x in a.probs.split(",")]))
    assert abs(sum(probs.values()) - 1) < 1e-6
    t = time.time()
    doms = {}
    if "weather" in names:
        doms["weather"] = Dm.Weather(k=a.k, bs=a.bs_weather, quick=a.quick)
    if "aq" in names:
        doms["aq"] = Dm.AQ(quick=a.quick)
    if "traffic" in names:
        doms["traffic"] = Dm.Traffic(tasks=a.traffic.split(",") if a.traffic else None, quick=a.quick)
    log(f"data ready in {(time.time() - t) / 60:.1f} min: " + ", ".join(doms))

    resumed = os.path.exists(f_last)
    if resumed:
        model, ck = MultiAtlas.load(f_last)
    else:
        model = build_from_24m(a.init, doms["aq"].view_kw if "aq" in doms else None,
                               doms["traffic"].view_kw if "traffic" in doms else None, f=2, noise=a.grow_noise, seed=a.seed)
    model = model.to(DEV)
    bd = model.breakdown()
    log("Atlas-100M parameters: " + json.dumps({k: f"{v:,}" for k, v in bd.items()}))
    assert a.quick or 90_000_000 <= bd["total"] <= 110_000_000, bd

    pre = model.core_params() + model.adapter_params("weather")          # the grown 24.1M model's own weights
    pre_ids = {id(p) for p in pre}
    new = [p for p in model.parameters() if id(p) not in pre_ids]
    opt = torch.optim.AdamW([dict(params=pre, lr=a.lr), dict(params=new, lr=a.lr_new)], weight_decay=a.wd)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_lambda(a.steps, int(a.warmup * a.steps)))
    bf16 = DEV == "cuda" and torch.cuda.is_bf16_supported()
    scaler = torch.amp.GradScaler(enabled=(DEV == "cuda" and not bf16))
    amp = dict(device_type=DEV, dtype=torch.bfloat16 if bf16 else torch.float16, enabled=(DEV == "cuda"))

    best, best_step, bad, first, done, hist = float("inf"), 0, 0, 1, False, []
    if resumed:
        opt.load_state_dict(ck["opt"]); sched.load_state_dict(ck["sched"]); scaler.load_state_dict(ck["scaler"])
        best, best_step, bad, first, done = ck["best"], ck["best_step"], ck["bad"], ck["step"] + 1, ck["done"]
        rng = np.random.default_rng(); rng.bit_generator.state = ck["rng"]
        torch.manual_seed(a.seed + ck["step"])
        log(f"RESUME step {ck['step']}: best S {best:.5f} at step {best_step}" + (" (finished)" if done else ""))

    def validate(step):
        v = {d: float(doms[d].val(model.view(d))) for d in doms}
        S = float(sum(math.log(x) for x in v.values()))
        return v, S

    def save_last(step, done=False):
        model.save(f_last + ".tmp", dict(opt=opt.state_dict(), sched=sched.state_dict(), scaler=scaler.state_dict(),
                                         step=step, best=best, best_step=best_step, bad=bad, done=done,
                                         rng=rng.bit_generator.state, args=vars(a)))
        os.replace(f_last + ".tmp", f_last)

    if not resumed:
        v0, S0 = validate(0)
        rec = dict(step=0, val=v0, S=S0, note="as initialised")
        if "weather" in doms and a.check_24m:                # G0: the grown model must forecast exactly as the 24.1M
            small = load_any(a.init).to(DEV)
            e24 = doms["weather"].val(small); del small
            rec["weather_24m"] = e24
            log(f"G0 growth check: weather val E grown {v0['weather']:.5f} vs 24.1M {e24:.5f} (|diff| {abs(v0['weather'] - e24):.2e})")
            assert abs(v0["weather"] - e24) < 2e-4, "the grown model does not reproduce the 24.1M model: stop"
        open(f_log, "a").write(json.dumps(rec) + "\n")
        log("step 0 val " + json.dumps({k: round(x, 5) for k, x in v0.items()}) + f" S {S0:.5f}")
        best, best_step = S0, 0
        model.save(f_best, dict(step=0, val=v0, S=S0))

    cnt = {d: 0 for d in doms}; lsum = {d: 0.0 for d in doms}
    t0, t_eval = time.time(), 0.0
    keys, pp = list(probs), np.array([probs[k] for k in probs])
    step = first - 1
    for step in (range(first, a.steps + 1) if not done else []):
        d = keys[int(rng.choice(len(keys), p=pp))]
        model.train()
        with torch.autocast(**amp):
            loss = doms[d].loss(model.view(d), rng)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward(); scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt); scaler.update(); sched.step()
        cnt[d] += 1; lsum[d] += loss.item()
        if step % a.every == 0 or step == a.steps:
            te = time.time()
            v, S = validate(step)
            if S < best - 1e-5:
                best, best_step, bad = S, step, 0
                model.save(f_best, dict(step=step, val=v, S=S))
            else:
                bad += 1
            t_eval += time.time() - te
            sps = (time.time() - t0 - t_eval) / max(1, step - first + 1)
            rec = dict(step=step, val=v, S=S, best=best, best_step=best_step, train_loss={k: lsum[k] / max(1, cnt[k]) for k in cnt},
                       batches=dict(cnt), s_per_step=sps, minutes=(time.time() - T0) / 60)
            open(f_log, "a").write(json.dumps(rec) + "\n")
            log(f"step {step} val " + " ".join(f"{k} {x:.4f}" for k, x in v.items()) + f" S {S:.5f} (best {best:.5f} @ {best_step}) "
                f"loss " + " ".join(f"{k} {lsum[k] / max(1, cnt[k]):.4f}" for k in cnt) + f" | {sps:.3f} s/step, "
                f"{(time.time() - T0) / 60:.0f} min, ~{sps * (a.steps - step) / 3600:.1f} h of training left")
            cnt = {k: 0 for k in doms}; lsum = {k: 0.0 for k in doms}
            stop = bad >= a.patience or step == a.steps
            save_last(step, done=stop)
            if stop:
                log(f"STOP at step {step}: " + ("patience" if bad >= a.patience else "end of schedule")); break
            if (time.time() - T0) / 60 > a.cap:
                log(f"PAUSED at step {step} (time cap {a.cap} min). Run the same command again to resume."); return
    if done or step >= first:
        bm, bck = MultiAtlas.load(f_best)
        for d in doms:
            bm.export_view(d, os.path.join(a.out, f"{a.tag}_{d}_view.pt"), meta=dict(step=bck["step"], val=bck["val"], S=bck["S"]))
        summ = dict(params=bd, best_step=bck["step"], best_val=bck["val"], best_S=bck["S"], steps_run=step,
                    minutes_total=round((time.time() - T0) / 60, 1), gpu=torch.cuda.get_device_name(0) if DEV == "cuda" else "cpu",
                    probs=probs, args=vars(a))
        json.dump(summ, open(os.path.join(a.out, f"{a.tag}_summary.json"), "w"), indent=1, default=float)
        log("TRAINING FINISHED " + json.dumps(summ, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", required=True, help="the adopted Atlas-5K 24.1M checkpoint (models/series/59)")
    ap.add_argument("--out", default=os.environ.get("ATLAS_OUT", "out"))
    ap.add_argument("--tag", default="atlas100m")
    ap.add_argument("--domains", default="weather,aq,traffic")
    ap.add_argument("--probs", default="0.5,0.25,0.25")
    ap.add_argument("--traffic", default="", help="subset of traffic networks (default: all six)")
    ap.add_argument("--steps", type=int, default=100_000)
    ap.add_argument("--every", type=int, default=2500)
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1.5e-4, help="the grown 24.1M model's weights (core + weather adapter)")
    ap.add_argument("--lr-new", type=float, default=1e-3, help="the new AQ and traffic adapters")
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--warmup", type=float, default=0.03)
    ap.add_argument("--bs-weather", type=int, default=256)
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--grow-noise", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=700)
    ap.add_argument("--cap", type=float, default=690, help="minutes, then pause (resume by re-running)")
    ap.add_argument("--check-24m", type=int, default=1)
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args())
