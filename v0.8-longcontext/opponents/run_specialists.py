"""OPPONENTS: published traffic-forecasting specialists, trained on each ParadoxBench task's TRAIN split with
their authors' own model code and published hyper-parameters, then scored on exactly the official windows.

  STID          Shao et al., CIKM 2022   - official code: github.com/GestaltCogTeam/STID (Apache-2.0)
  Graph WaveNet Wu et al., IJCAI 2019    - official code: github.com/nnzhan/Graph-WaveNet (MIT)
  STAEformer    Liu et al., CIKM 2023    - official code: github.com/XDZhelheim/STAEformer

The model classes are imported unchanged from a clone of each repository (path given by --ext); no file of
theirs is copied into this kit, and nothing here is imported by PWM-Dyn. What is ours: the data windows (the
same ones PWM-Dyn trains and is scored on), the training loop (re-implemented from each repository's
train script: optimiser, learning-rate schedule, batch size, loss, gradient clipping, best-validation
checkpoint) and a wall-clock budget. Every run states how many epochs it completed and whether the budget,
not the authors' stopping rule, ended it.

  python opponents/run_specialists.py --task PEMS08 --model staeformer --ext /kaggle/working/ext --minutes 40
"""
import argparse, importlib.util, json, math, os, sys, time

import numpy as np
import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from pwm.data import load                                   # data only
from paradoxbench.spec import TASKS, official_windows, validation_windows, hidden_sensors
from paradoxbench.score import record

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STAE_KEY = {"PEMS03": "PEMS03", "PEMS04": "PEMS04", "PEMS07": "PEMS07", "PEMS08": "PEMS08",
            "METR-LA": "METRLA", "PEMS-BAY": "PEMSBAY"}
NAMES = {"stid": "STID (CIKM'22, official code)", "gwnet": "Graph WaveNet (IJCAI'19, official code)",
         "staeformer": "STAEformer (CIKM'23, official code)"}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def masked_mae(pred, y):
    m = (y > 1e-4).float()                                  # null value 0, as in all three repositories
    m = m / m.mean().clamp(min=1e-8)
    return (torch.abs(pred - y) * m).nan_to_num().mean()


class Windows:
    """Batches in each repository's input format, built from the same windows PWM-Dyn uses."""

    def __init__(self, ds):
        self.ds = ds
        a, b = ds.bounds["train"]
        v = np.nan_to_num(ds.raw[:b])                       # repositories z-score the raw series, zeros included
        self.mean, self.std = float(v.mean()), float(v.std())
        self.val = np.nan_to_num(ds.raw).astype(np.float32)
        self.tod = (ds.period_idx % ds.period).astype(np.float32) / ds.period
        self.dow = ds.dow.astype(np.float32)

    def batch(self, idx, hide=None):
        ds = self.ds
        hi = idx[:, None] + np.arange(-ds.in_len, 0)[None]   # [B, L]
        fo = idx[:, None] + np.arange(ds.out_len)[None]
        x = (self.val[hi] - self.mean) / self.std            # [B, L, N]
        if hide is not None:                                  # dead sensors: the repositories' own missing value (0)
            x[..., hide] = (0.0 - self.mean) / self.std
        B, L, N = x.shape
        tod = np.broadcast_to(self.tod[hi][..., None], (B, L, N))
        dow = np.broadcast_to(self.dow[hi][..., None], (B, L, N))
        X = torch.from_numpy(np.stack([x, tod, dow], -1).astype(np.float32)).to(DEV)   # [B, L, N, 3]
        Y = torch.from_numpy(self.val[fo]).to(DEV)            # [B, H, N] real units, 0 = missing
        return X, Y


class Runner:
    def __init__(self, kind, ds, ext, task):
        self.kind, self.ds = kind, ds
        N = ds.N
        if kind == "stid":
            sys.path.insert(0, os.path.join(ext, "STID", "stid"))
            from arch.stid_arch import STID                   # noqa: E402  (official class, unchanged)
            self.net = STID(num_nodes=N, input_len=12, input_dim=3, embed_dim=32, output_len=12, num_layer=3,
                            if_node=True, node_dim=32, if_T_i_D=True, if_D_i_W=True, temp_dim_tid=32,
                            temp_dim_diw=32, time_of_day_size=ds.period, day_of_week_size=7)
            self.cfg = dict(lr=2e-3, wd=1e-4, bs=64, epochs=100, milestones=[1, 50, 80], gamma=0.5, clip=5.0,
                            patience=None, loss="masked_mae")
        elif kind == "gwnet":
            # The official file builds 2-D kernels with nn.Conv1d, which PyTorch accepted before 1.11 and now
            # rejects; the one compatibility change made here is to construct those layers as nn.Conv2d,
            # which is what the old behaviour computed. Nothing else in the file is touched.
            src = open(os.path.join(ext, "Graph-WaveNet", "model.py")).read().replace("nn.Conv1d(", "nn.Conv2d(")
            m = type(sys)("gwnet_model")
            exec(compile(src, "Graph-WaveNet/model.py (Conv1d->Conv2d)", "exec"), m.__dict__)
            A = ds.A_raw.astype(np.float64)

            def asym(a):                                      # util.asym_adj: row-normalised transition matrix
                d = a.sum(1)
                d = np.where(d > 0, 1.0 / d, 0.0)
                return (d[:, None] * a).astype(np.float32)
            sup = [torch.tensor(asym(A)).to(DEV), torch.tensor(asym(A.T)).to(DEV)]   # "doubletransition"
            self.net = m.gwnet(DEV, N, 0.3, supports=sup, gcn_bool=True, addaptadj=True, aptinit=None,
                               in_dim=2, out_dim=12, residual_channels=32, dilation_channels=32,
                               skip_channels=256, end_channels=512)
            self.cfg = dict(lr=1e-3, wd=1e-4, bs=64, epochs=100, milestones=None, gamma=None, clip=5.0,
                            patience=None, loss="masked_mae")
        elif kind == "staeformer":
            import yaml
            m = _module(os.path.join(ext, "STAEformer", "model", "STAEformer.py"), "staeformer_model")
            y = yaml.safe_load(open(os.path.join(ext, "STAEformer", "model", "STAEformer.yaml")))[STAE_KEY[task]]
            self.net = m.STAEformer(**y["model_args"])
            self.cfg = dict(lr=y["lr"], wd=y.get("weight_decay", 0), bs=y["batch_size"], epochs=y["max_epochs"],
                            milestones=y["milestones"], gamma=y.get("lr_decay_rate", 0.1),
                            clip=y.get("clip_grad", 0) or 0, patience=y.get("early_stop"),
                            loss="masked_mae" if task in ("METR-LA", "PEMS-BAY") else "huber")
        self.net = self.net.to(DEV)

    def forward(self, X):
        if self.kind == "stid":
            Xs = X.clone()
            Xs[..., 2] = Xs[..., 2] / 7.0                      # STID reads day-of-week as a fraction of the week
            return self.net(Xs, None, 0, 0, True)[..., 0]     # [B, H, N, 1] -> [B, H, N]
        if self.kind == "gwnet":
            x = X[..., :2].permute(0, 3, 2, 1)                 # [B, L, N, 2] -> [B, 2, N, L], as train.py
            x = nn.functional.pad(x, (1, 0, 0, 0))             # as in engine.trainer
            return self.net(x)[..., 0]                         # [B, H(out channels), N, 1] -> [B, H, N]
        return self.net(X)[..., 0]                             # STAEformer: [B, H, N, 1] -> [B, H, N]


def predict(run, win, idx, hide=None, bs=64):
    run.net.eval()
    out = []
    with torch.no_grad(), torch.autocast("cuda", enabled=DEV == "cuda"):
        for s in range(0, len(idx), bs):
            X, _ = win.batch(idx[s:s + bs], hide)
            out.append((run.forward(X).float() * win.std + win.mean).cpu().numpy())
    return np.concatenate(out)


def main(a):
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    loader = TASKS[a.task][0]
    ds = load(loader)
    win = Windows(ds)
    run = Runner(a.model, ds, a.ext, a.task)
    cfg = run.cfg
    nparam = sum(p.numel() for p in run.net.parameters())
    opt = torch.optim.Adam(run.net.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    sched = (torch.optim.lr_scheduler.MultiStepLR(opt, milestones=cfg["milestones"], gamma=cfg["gamma"])
             if cfg["milestones"] else None)
    scaler = torch.cuda.amp.GradScaler(enabled=DEV == "cuda")
    huber = nn.HuberLoss()
    tr = ds.indices("train")
    va = validation_windows(ds)
    if a.quick:                                         # pipeline check only, never reported
        tr, va, cfg["epochs"] = tr[:256], va[:64], 2
    vy = np.nan_to_num(ds.raw[va[:, None] + np.arange(ds.out_len)[None]])
    vmask = vy > 1e-4
    print(f"{NAMES[a.model]} on {a.task}: {nparam:,} parameters, {len(tr)} train windows, budget {a.minutes} min, "
          f"recipe {json.dumps(cfg)}", flush=True)
    best, best_state, bad, ep, t0, stop = 1e18, None, 0, 0, time.time(), "authors' epoch limit"
    for ep in range(1, cfg["epochs"] + 1):
        run.net.train()
        perm = np.random.permutation(tr)
        for s in range(0, len(perm), cfg["bs"]):
            X, Y = win.batch(perm[s:s + cfg["bs"]])
            with torch.autocast("cuda", enabled=DEV == "cuda"):
                pred = run.forward(X).float() * win.std + win.mean
            loss = huber(pred, Y) if cfg["loss"] == "huber" else masked_mae(pred, Y)
            opt.zero_grad()
            scaler.scale(loss).backward()
            if cfg["clip"]:
                scaler.unscale_(opt)
                torch.nn.utils.clip_grad_norm_(run.net.parameters(), cfg["clip"])
            scaler.step(opt); scaler.update()
        if sched:
            sched.step()
        p = predict(run, win, va)
        vmae = float(np.abs(p - vy)[vmask].mean())
        if vmae < best:
            best, bad = vmae, 0
            best_state = {k: v.detach().clone() for k, v in run.net.state_dict().items()}
        else:
            bad += 1
        mins = (time.time() - t0) / 60
        print(f"  ep {ep:3d} val MAE {vmae:.3f} (best {best:.3f}) {mins:.1f} min", flush=True)
        if cfg["patience"] and bad >= cfg["patience"]:
            stop = "authors' early stopping"; break
        if a.minutes and mins > a.minutes:
            stop = "wall-clock budget"; break
    run.net.load_state_dict(best_state)
    print(f"{NAMES[a.model]} {a.task}: stopped after {ep} epochs ({stop}), best val MAE {best:.3f}", flush=True)
    meta = {"type": "specialist (published model, official code, trained on task)", "params": nparam,
            "context_steps": 12, "trained_on": f"{a.task} train split", "seed": a.seed,
            "recipe": cfg, "epochs_run": ep, "stopped_by": stop, "budget_minutes": a.minutes,
            "best_val_MAE": best, "mixed_precision": DEV == "cuda"}
    idx = official_windows(ds)
    if a.quick:
        print("quick run: pipeline OK, not recorded", flush=True); return
    q50 = predict(run, win, idx)
    for track in ("A", "B"):
        record(a.task, track, NAMES[a.model], None, q50, None, meta, ds)
    q50r = predict(run, win, idx, hide=hidden_sensors(ds.N))
    record(a.task, "R", NAMES[a.model], None, q50r, None, meta, ds)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=[t for t in TASKS if not t.startswith("IMD")])
    ap.add_argument("--model", required=True, choices=list(NAMES))
    ap.add_argument("--ext", required=True, help="folder holding the cloned repositories")
    ap.add_argument("--minutes", type=float, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--quick", action="store_true", help="pipeline check on a few windows (not recorded)")
    main(ap.parse_args())
