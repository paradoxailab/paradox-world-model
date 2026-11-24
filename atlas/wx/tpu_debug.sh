#!/bin/bash
# Find why Atlas-WX fails on native TorchTPU (Colab v5e-1): single training steps in synchronous debug mode
# (TORCH_TPU_LAUNCH_BLOCKING=1), full tracebacks, from tiny to the Stage 1 10M, batch 8 -> 256. About 10 minutes.
#   bash tpu_debug.sh 2>&1 | tee /content/tpu_debug.log
set -u
cd "$(dirname "$0")"
[ -f /content/wx_synth/wx_2025.npz ] || python make_synth_wx.py --out /content/wx_synth --stations 300 > /dev/null
export ATLAS_DEVICE=tpu WX_DATA=/content/wx_synth PYTHONWARNINGS=ignore
clean() { grep -v -E "^I0000|^W0000|PrivateUse1|Registered Python|Device type|Initializing TPU|absl|env_vars.h"; }
echo "== 1. plain ops on tpu"
python - <<'PY' 2>&1 | clean
import torch, time
x = torch.randn(256, 768, 680, device="tpu"); w = torch.randn(680, 680, device="tpu", requires_grad=True)
t = time.time(); y = (x @ w).relu().sum(); y.backward(); print("matmul+backward ok", float(y), round(time.time() - t, 2), "s")
i = torch.randint(0, 256, (64,)); print("index_select ok", x[i.to("tpu")].shape)
print("autocast bf16:", torch.amp.is_autocast_available("tpu"))
with torch.autocast("tpu", dtype=torch.bfloat16):
    print("autocast matmul dtype", (x[:2] @ w).dtype)
PY
step() {   # step(label, env..., -- args...)
  local label=$1; shift
  echo "== $label"
  env TORCH_TPU_LAUNCH_BLOCKING=1 "$@" python -u - <<'PY' 2>&1 | clean | tail -25
import os, sys, time, traceback, torch
sys.argv = ["x"]; sys.path.insert(0, "..")
import run_atlas_wx as W
from atlas.model import sized
size, bs = int(os.environ["SIZE"]), int(os.environ["BS"])
Z, lat, lon, elev, M = W.load(quick=True); N = Z.shape[0]
nb = W.neighbours(lat, lon, W.K); geo = W.geometry(lat, lon, nb); st = W.static_feats(lat, lon, elev)
bt = W.Batcher(Z, nb, geo, st, 24)
m = sized(size, L=W.L, H=24, C=5, U=4, lat_steps=6, spatial=True, geo_dim=3, static=4, fill="interp").to(W.DEV)
opt = torch.optim.AdamW(m.parameters(), lr=1e-3)
ta, te = W.YEARS["train"]
for k in range(3):
    try:
        t = time.time()
        b = bt(torch.randint(0, N, (bs,)), torch.randint(ta, te - 72, (bs,)))
        with torch.autocast("tpu", dtype=torch.bfloat16, enabled=os.environ.get("AMP") == "1"):
            q, rec, _ = m(b["yc"] * b["mc"], b["mc"], b["uc"], b["uf"], b["geo"], None, b["static"])
            loss = W.pinball(q.float(), b["y"], b["my"])
        opt.zero_grad(); loss.backward(); opt.step()
        print(f"step {k}: loss {float(loss):.4f}, {time.time() - t:.2f} s", flush=True)
    except Exception:
        traceback.print_exc(limit=12); break
PY
}
step "2. 1M, batch 8, float32"      SIZE=1000000  BS=8   AMP=0
step "3. 10M, batch 8, float32"     SIZE=10000000 BS=8   AMP=0
step "4. 10M, batch 8, bf16"        SIZE=10000000 BS=8   AMP=1
step "5. 10M, batch 64, bf16"       SIZE=10000000 BS=64  AMP=1
step "6. 10M, batch 64, bf16, DeferAndFuse, asynchronous" SIZE=10000000 BS=64 AMP=1 TORCH_TPU_DEFER_AND_FUSE=1 TORCH_TPU_LAUNCH_BLOCKING=0
