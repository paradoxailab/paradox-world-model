"""Generate self-contained Kaggle notebook cells that recreate the PPB-1 / PWM v0.4 kit and run it."""
import hashlib, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("OUT", os.path.join(ROOT, "kaggle_cells"))
GROUPS = [
    ["pwm/__init__.py", "pwm/data.py"],
    ["pwm/model.py", "pwm/calibration.py", "pwm/evaluation.py", "train.py"],
    ["paradoxbench/__init__.py", "paradoxbench/spec.py", "paradoxbench/metrics.py", "paradoxbench/score.py", "paradoxbench/baselines.py",
     "paradoxbench/run_pwm.py", "paradoxbench/leaderboard.py", "check_provenance.py"],
    ["opponents/run_timesfm.py", "run_paradoxbench.py", "run_v05.py"],
]
if os.environ.get("RUN") == "run_v05.py":      # v0.5 study needs no opponent code
    GROUPS[3] = ["run_v05.py"]
K = "/kaggle/working/pwm_kit"
os.makedirs(OUT, exist_ok=True)
for i, g in enumerate(GROUPS, 1):
    L = ["import hashlib, os"] + (['import torch; print("GPUs:", torch.cuda.device_count()); '
                          'assert torch.cuda.is_available(), "set Accelerator to GPU T4 x2"'] if i == 1 else [])
    for d in sorted({os.path.dirname(f) for f in g} | {"data/raw"}):
        L.append(f'os.makedirs("{K}/{d}", exist_ok=True)')
    for f in g:
        src = open(os.path.join(ROOT, f)).read()
        assert "'''" not in src
        L.append(f'open("{K}/{f}","w").write(r' + "'''" + src + "''')")
        h = hashlib.sha256(src.encode()).hexdigest()[:16]
        L.append(f'assert hashlib.sha256(open("{K}/{f}").read().encode()).hexdigest()[:16] == "{h}", "typo in {f}"')
    L.append(f'print("cell {i} files written")')
    open(os.path.join(OUT, f"cell{i}.py"), "w").write("\n".join(L) + "\n")
run = f"""%cd {K}
!pip install -q imdlib timesfm 2>&1 | tail -1
!python -c "import timesfm, timesfm3, torch; print('timesfm OK, GPUs:', torch.cuda.device_count())"
!for d in PEMS08 PEMS04; do for e in npz csv; do curl -sL -o data/raw/$d.$e https://raw.githubusercontent.com/guoshnBJTU/ASTGNN/main/data/$d/$d.$e; done; done; ls -la data/raw
from pwm.data import download_imd
for r in ("central_india", "west_coast"): print("IMD:", download_imd(r, 2000, 2024))
import os
!python {os.environ.get("RUN", "run_paradoxbench.py")} 2>&1
print("KAGGLE-RUN-DONE")
"""
open(os.path.join(OUT, f"cell{len(GROUPS) + 1}.py"), "w").write(run)
for f in sorted(os.listdir(OUT)):
    print(f, len(open(os.path.join(OUT, f)).read()))
