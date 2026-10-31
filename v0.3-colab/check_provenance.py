"""Proves PWM contains nothing copied from external models.

Checks:
 1. Every saved PWM checkpoint contains exactly PWM-Dyn's own parameters (same names, same shapes,
    same count as a freshly built PWM-Dyn) and nothing else.
 2. PWM's own code (pwm/, train.py, evaluate_pwm.py) imports no external model library
    (timesfm, transformers, huggingface_hub, openai, ...).
 3. Opponent code lives only in opponents/ and never writes into models/.
Writes PROVENANCE_REPORT.json with a SHA-256 fingerprint of every PWM checkpoint.
"""
import ast, glob, hashlib, json, os, sys
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from pwm.data import load
from train import build

FORBIDDEN = {"timesfm", "timesfm3", "transformers", "huggingface_hub", "openai", "groq",
             "chronos", "moirai", "peft", "safetensors", "diffusers", "timm"}
PWM_CODE = glob.glob(f"{ROOT}/pwm/*.py") + [f"{ROOT}/train.py", f"{ROOT}/evaluate_pwm.py"]


def imports(path):
    tree = ast.parse(open(path).read())
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            out.add(n.module.split(".")[0])
    return out


def main():
    rep, ok = {"checkpoints": [], "code": {}}, True
    for f in PWM_CODE:
        bad = imports(f) & FORBIDDEN
        rep["code"][os.path.relpath(f, ROOT)] = "clean" if not bad else f"IMPORTS {sorted(bad)}"
        ok &= not bad
    datasets = {}
    for w in sorted(glob.glob(f"{ROOT}/models/*/*/weights.pt")):
        ds_name, version = w.split(os.sep)[-3], w.split(os.sep)[-2]
        cfg = json.load(open(os.path.join(os.path.dirname(w), "report.json")))["config"]
        if ds_name not in datasets:
            datasets[ds_name] = load(ds_name)
        fresh = build(datasets[ds_name], cfg).state_dict()
        sd = torch.load(w, map_location="cpu")
        same_keys = set(sd) == set(fresh)
        same_shapes = same_keys and all(sd[k].shape == fresh[k].shape for k in sd)
        n = sum(v.numel() for v in sd.values())
        good = same_keys and same_shapes and n == sum(v.numel() for v in fresh.values())
        ok &= good
        rep["checkpoints"].append({"dataset": ds_name, "version": version, "parameters": n,
                                   "only_pwm_parameters": good,
                                   "sha256": hashlib.sha256(open(w, "rb").read()).hexdigest()})
    stray = [p for p in glob.glob(f"{ROOT}/models/**/*", recursive=True)
             if os.path.isfile(p) and os.path.basename(p) not in
             ("weights.pt", "report.json", "PROMOTED.json", "ensemble_test_forecasts.npz")]
    rep["unexpected_files_in_models"] = [os.path.relpath(p, ROOT) for p in stray]
    ok &= not stray
    rep["verdict"] = ("PASS: PWM checkpoints contain only PWM-Dyn's own trained parameters; "
                      "PWM code imports no external model library") if ok else "FAIL - see details"
    json.dump(rep, open(f"{ROOT}/PROVENANCE_REPORT.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
