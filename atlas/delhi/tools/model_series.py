"""Model series release (ParadoxAI Lab): every PWM model version, with its dataset named inside the file.

Step 1, inventory (no push):  python model_series.py inventory
  Walks /kaggle/input/** for weight files (.pt/.pth/.ckpt), loads each on CPU and records its path, size, SHA-256,
  top-level keys, parameter count and the files next to it (configs, logs, results). Writes out/INVENTORY.json and
  prints one line per file, so the release list can be chosen from what actually exists.

Step 2, release:  python model_series.py release --plan series_plan.json [--push]
  For each entry of the plan: loads the chosen checkpoint, keeps the reported weights, adds a "meta" block (series
  number, name, version, model family, task, dataset(s), parameters, headline result, source run and original file
  SHA-256), saves it as models/series/<NN>_<name>.pt, writes SHA256SUMS and SERIES.json, and with --push commits them
  to GitHub using the Kaggle secret GITHUB_TOKEN (never printed or stored).
"""
import argparse, glob, hashlib, json, os, sys, time

import torch

OUT = os.environ.get("ATLAS_OUT", "/kaggle/working/out")


def log(*a):
    print(*a, flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def count_params(obj, depth=0):
    """Parameters in the first state-dict-like mapping found (tensors only)."""
    if isinstance(obj, dict):
        ts = [v for v in obj.values() if torch.is_tensor(v)]
        if ts and len(ts) >= 0.5 * len(obj):
            return int(sum(t.numel() for t in ts)), "flat"
        if depth < 2:
            for k in ("sd", "E", "state", "model", "state_dict", "C", "F"):
                if k in obj:
                    n, _ = count_params(obj[k], depth + 1)
                    if n:
                        return n, k
            for k, v in obj.items():
                n, _ = count_params(v, depth + 1)
                if n:
                    return n, str(k)
    if isinstance(obj, (list, tuple)) and obj and depth < 2:
        n, w = count_params(obj[0], depth + 1)
        if n:
            return n, f"[0 of {len(obj)}]"
    return 0, None


def describe(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in list(obj.items())[:40]:
            if torch.is_tensor(v):
                out[str(k)] = f"tensor{tuple(v.shape)}"
            elif isinstance(v, dict):
                out[str(k)] = f"dict({len(v)})"
            elif isinstance(v, (list, tuple)):
                out[str(k)] = f"{type(v).__name__}({len(v)})"
            elif isinstance(v, (int, float, str, bool)) or v is None:
                out[str(k)] = v if not isinstance(v, str) else v[:120]
            else:
                out[str(k)] = type(v).__name__
        return out
    return type(obj).__name__


def inventory():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(set(glob.glob("/kaggle/input/**/*.pt", recursive=True) + glob.glob("/kaggle/input/**/*.pth", recursive=True)
                       + glob.glob("/kaggle/input/**/*.ckpt", recursive=True)))
    log(f"INVENTORY {len(files)} weight files under /kaggle/input")
    rows = []
    for f in files:
        rel = f.replace("/kaggle/input/", "")
        row = dict(path=rel, bytes=os.path.getsize(f))
        try:
            obj = torch.load(f, map_location="cpu", weights_only=False)
            row["params"], row["weights_key"] = count_params(obj)
            row["keys"] = describe(obj)
            if isinstance(obj, dict):
                for k in ("cfg", "config", "info", "meta"):
                    if k in obj and isinstance(obj[k], dict):
                        row[k] = {kk: (vv if isinstance(vv, (int, float, str, bool)) or vv is None else str(type(vv).__name__))
                                  for kk, vv in list(obj[k].items())[:30]}
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {str(e)[:160]}"
        d = os.path.dirname(f)
        row["siblings"] = sorted(os.listdir(d))[:25]
        row["sha256"] = sha256(f)
        rows.append(row)
        log(f"PT {rel} | {row['bytes']:,} B | params {row.get('params')} via {row.get('weights_key')} | "
            f"keys {list(row['keys'])[:8] if isinstance(row.get('keys'), dict) else row.get('keys')} | "
            f"siblings {[s for s in row['siblings'] if not s.endswith('.pt')][:6]}" + (f" | ERROR {row['error']}" if "error" in row else ""))
    json.dump(rows, open(os.path.join(OUT, "INVENTORY.json"), "w"), indent=1, default=str)
    by = {}
    for r in rows:
        top = r["path"].split("/")[2] if r["path"].startswith("notebooks/") else r["path"].split("/")[0]
        by.setdefault(top, [0, 0])
        by[top][0] += 1; by[top][1] += r["bytes"]
    for k, (n, b) in sorted(by.items()):
        log(f"SOURCE {k}: {n} files, {b / 1e6:.1f} MB")
    log(f"TOTAL {len(rows)} files, {sum(r['bytes'] for r in rows) / 1e6:.1f} MB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["inventory", "release"])
    ap.add_argument("--plan")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    if a.mode == "inventory":
        inventory()
    else:
        sys.exit("release mode is added after the inventory has been read")


if __name__ == "__main__":
    main()
