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


def pick(obj, key):
    """The reported weights inside a checkpoint: key path like 'sd', 'E', 'state', 'states[0]', or '' for the whole object."""
    if not key:
        return obj
    if "," in key:
        return {k: pick(obj, k) for k in key.split(",")}
    for part in key.split("."):
        if part.endswith("]"):
            name, idx = part[:-1].split("[")
            obj = obj[name] if name else obj
            obj = obj[int(idx)]
        else:
            obj = obj[part]
    return obj


def write_readme(rows, same, path):
    L = ["# PWM model series (ParadoxAI Lab)", "",
         "Every saved model version, oldest first. Each file holds `meta` (name, version, family, task, datasets, parameters,",
         "result, source run, source file SHA-256), `weights` (the reported weights only) and `cfg`. Results are copied from",
         "the repository's records; results of seed ensembles are marked as such (the file holds one seed).", "",
         "```python", "import torch", "ck = torch.load(\"models/series/<file>.pt\", map_location=\"cpu\", weights_only=False)",
         "print(ck[\"meta\"][\"name\"], ck[\"meta\"][\"datasets\"])   # the dataset is named inside the file", "```", "",
         "Atlas files load into `atlas/atlas/model.py` (`Atlas(**ck[\"cfg\"])`); PWM-Dyn files into the matching version folder's",
         "`pwm` package; PWM-W files into the code on the `delhi-v*` / `india-v2.0` branches.", "",
         "| # | Version | Family | Dataset | Task | Parameters | Result (from the records) | What changed | Status | File |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['series_no']} | {r['version']} | {r['family']} | {'; '.join(r['datasets'])} | {r['task']} | {r['parameters']:,} | "
                 f"{r['result']} | {r['improvement']} | {r['status']} | `{r['file']}` |")
    if same:
        L += ["", "Versions whose weights are identical to an earlier file (not stored twice):", ""]
        L += [f"* #{s['series_no']} {s['version']}: same weights as #{s['same_as']} (`{s['same_as_file']}`)" for s in same]
    L += ["", "Not included: PWM-Dyn v0.3 (trained on Colab; weights were not kept), v0.5 (stopped, no model reported), extra seeds",
          "and ablation runs (on Kaggle). Atlas-5K v2c is added when its training finishes.", "",
          f"{len(rows)} files, {sum(r['bytes'] for r in rows) / 1e6:.1f} MB. Checksums: `SHA256SUMS`. Machine-readable: `SERIES.json`."]
    open(path, "w").write("\n".join(L) + "\n")


def release(plan_path, push):
    import subprocess, base64, shutil
    plan = json.load(open(plan_path))
    stage = "/kaggle/working/release"
    shutil.rmtree(stage, ignore_errors=True)
    dst = os.path.join(stage, "models", "series")
    os.makedirs(dst, exist_ok=True)
    rows, same = [], []
    for e in plan["models"]:
        hits = glob.glob(os.path.join("/kaggle/input", "**", e["source_glob"]), recursive=True)
        hits = sorted(h for h in hits if all(x not in h for x in e.get("exclude", [])))
        if len(hits) != 1:
            log(f"SKIP {e['id']} {e['name']}: {len(hits)} matches for {e['source_glob']}: {hits[:4]}")
            continue
        src = hits[0]
        src_sha = sha256(src)
        dup = next((r for r in rows if r["source_sha256"] == src_sha and r["weights_key"] == e.get("weights_key", "")), None)
        if dup:
            log(f"SAME {e['id']} {e['name']}: identical weights to #{dup['series_no']} {dup['name']}; not stored twice")
            same.append(dict(series_no=e["id"], name=e["name"], version=e["version"], same_as=dup["series_no"], same_as_file=dup["file"]))
            continue
        obj = torch.load(src, map_location="cpu", weights_only=False)
        w = pick(obj, e.get("weights_key", ""))
        if isinstance(w, dict) and w and all(isinstance(v, dict) for v in w.values()) and "," in e.get("weights_key", ""):
            n = max(count_params(v)[0] for v in w.values())
        else:
            n, _ = count_params(w if isinstance(w, dict) else {"w": w})
        cfg = None
        if isinstance(obj, dict):
            for k in ("cfg", "config", "info"):
                if k in obj:
                    cfg = obj[k]; break
        meta = dict(series_no=e["id"], name=e["name"], version=e["version"], family=e["family"], task=e["task"],
                    datasets=e["datasets"], parameters=n, result=e["result"], improvement=e.get("improvement", ""),
                    trained_on=e.get("trained_on", ""), source_run=e["source_run"], source_file=src.replace("/kaggle/input/", ""),
                    source_sha256=src_sha, weights_key=e.get("weights_key", ""), date=e.get("date", ""), status=e.get("status", ""),
                    note=e.get("note", ""),
                    code=e.get("code", ""), license="see LICENSE in github.com/paradoxailab/paradox-world-model",
                    organisation="ParadoxAI Lab", released="2026-11-17")
        out = {"meta": meta, "weights": w, "cfg": cfg}
        for k in e.get("extra_keys", []):
            if isinstance(obj, dict) and k in obj:
                out[k] = obj[k]
        fn = f"{e['id']:02d}_{e['file']}.pt"
        torch.save(out, os.path.join(dst, fn))
        meta["file"] = fn
        meta["bytes"] = os.path.getsize(os.path.join(dst, fn))
        meta["sha256"] = sha256(os.path.join(dst, fn))
        rows.append(meta)
        log(f"RELEASE {fn} | {meta['bytes']:,} B | params {n:,} | dataset {', '.join(e['datasets'])} | from {meta['source_file']}")
    with open(os.path.join(dst, "SHA256SUMS"), "w") as f:
        for r in rows:
            f.write(f"{r['sha256']}  {r['file']}\n")
    json.dump({"models": rows, "identical_to_earlier": same}, open(os.path.join(dst, "SERIES.json"), "w"), indent=1)
    write_readme(rows, same, os.path.join(dst, "README.md"))
    shutil.copy(os.path.join(dst, "SERIES.json"), os.path.join(OUT, "SERIES.json"))
    log(f"SERIES {len(rows)} models, {sum(r['bytes'] for r in rows) / 1e6:.1f} MB")
    if not push:
        return
    from kaggle_secrets import UserSecretsClient
    tok = UserSecretsClient().get_secret("GITHUB_TOKEN")
    hdr = "Authorization: Basic " + base64.b64encode(f"x-access-token:{tok}".encode()).decode()

    def git(*args, cwd=None):
        r = subprocess.run(["git", "-c", f"http.extraHeader={hdr}", *args], cwd=cwd, capture_output=True, text=True)
        txt = (r.stdout + r.stderr).replace(tok, "***").replace(hdr, "***")
        log("git " + " ".join(a for a in args if "Authorization" not in a)[:80] + " -> " + str(r.returncode) + " " + txt.strip()[-300:])
        if r.returncode:
            raise SystemExit("git failed")
        return txt

    repo = "/kaggle/working/push"
    shutil.rmtree(repo, ignore_errors=True)
    git("clone", "-q", "--depth", "1", "-b", "atlas-v0.1", "https://github.com/paradoxailab/paradox-world-model.git", repo)
    target = os.path.join(repo, "models", "series")
    os.makedirs(target, exist_ok=True)
    for fn in os.listdir(dst):
        shutil.copy(os.path.join(dst, fn), os.path.join(target, fn))
    git("add", "-f", "models/series", cwd=repo)
    git("-c", "user.name=Aditya Kumar", "-c", "user.email=contact.paradoxailab@gmail.com", "commit", "-q", "-m",
        plan["commit_message"], cwd=repo)
    git("push", "origin", "HEAD:atlas-v0.1", cwd=repo)
    git("push", "origin", "HEAD:main", cwd=repo)
    log("PUSHED " + git("rev-parse", "HEAD", cwd=repo).strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["inventory", "release"])
    ap.add_argument("--plan")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    if a.mode == "inventory":
        inventory()
    else:
        release(a.plan, a.push)


if __name__ == "__main__":
    main()
