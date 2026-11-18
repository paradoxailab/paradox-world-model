"""Hugging Face model cards for every released model in models/series, written from the metadata stored inside each
file (meta, results["records"]) and SERIES.json. Nothing is typed by hand; the script checks each file's SHA-256,
recounts its parameters from the weights, and fails on any mismatch.

  python models/hf/make_hf_cards.py --ns paradoxailab
    -> models/hf/cards/<repo>/README.md  (one per model, 56)
       models/hf/cards/paradox-world-model-series/README.md  (index of all 56, oldest first)
       models/hf/plan.json  (repo ids, files, SHA-256, collection notes; read by publish_hf.py)
"""
import argparse, hashlib, json, os, re

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SER = os.path.join(REPO, "models", "series")
GH = "https://github.com/paradoxailab/paradox-world-model"
# where a file's source_run names only the evaluation session's GPU (atlas/README.md, "Atlas-5K 25M results, part 1")
TRAINED = {59: "Google Colab: steps 0-8,000 on an A100, steps 8,000-80,000 on an L4; final evaluation on an A100-40GB"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tensors(W):
    """{name: tensor} or {checkpoint: {name: tensor}} -> list of (checkpoint or None, count)."""
    if all(hasattr(v, "numel") for v in W.values()):
        return [(None, sum(v.numel() for v in W.values() if v.is_floating_point()))]
    return [(k, sum(t.numel() for t in v.values() if t.is_floating_point())) for k, v in W.items()]


def record_link(r):
    m = re.match(r"branch (\S+) / (\S+)", r)
    if m:
        return f"[{r}]({GH}/blob/{m.group(1)}/{m.group(2)})"
    return f"[{r}]({GH}/blob/main/{r})"


def tags(m):
    t = (m["task"] + " " + " ".join(m["datasets"])).lower()
    out = ["paradoxailab", "paradox-world-model", m["family"].lower(), "forecasting", "spatiotemporal"]
    if "traffic" in t: out.append("traffic-forecasting")
    if "rain" in t: out.append("rainfall")
    if "pm2.5" in t or "air" in t: out.append("air-quality")
    if any(w in t for w in ("temperature", "humidity", "wind", "weather", "dew")): out.append("weather-forecasting")
    if "india" in t or "delhi" in t or "imd" in t or "cpcb" in t: out.append("india")
    return out


def main(a):
    S = json.load(open(os.path.join(SER, "SERIES.json")))
    models = sorted(S["models"], key=lambda m: m["series_no"])
    same = {}
    for x in S.get("identical_to_earlier", []):
        same.setdefault(x["same_as"], []).append(x)
    names = [m["name"] for m in models]
    assert len(set(names)) == len(names), "duplicate repo names"
    assert all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,94}", n) and "--" not in n and ".." not in n for n in names)
    C = os.path.join(HERE, "cards"); os.makedirs(C, exist_ok=True)
    plan = dict(ns=a.ns, index_repo=f"{a.ns}/paradox-world-model-series", models=[])
    rows = []
    for i, m in enumerate(models):
        f = os.path.join(SER, m["file"])
        assert sha(f) == m["sha256"], f"#{m['series_no']}: SHA-256 differs from SERIES.json"
        ck = torch.load(f, map_location="cpu", weights_only=False)
        assert ck["meta"]["series_no"] == m["series_no"]
        parts = tensors(ck["weights"])
        assert all(n == m["parameters"] for _, n in parts), f"#{m['series_no']}: parameter count differs"
        recs = list(ck["results"].get("records", {}))
        rid = f"{a.ns}/{m['name']}"
        prev = models[i - 1] if i else None
        nxt = models[i + 1] if i + 1 < len(models) else None
        hybrid = "hybrid" in (m["task"] + " " + m["improvement"]).lower()
        L = ["---", "license: apache-2.0", "library_name: pytorch", "pipeline_tag: time-series-forecasting", "tags:"]
        L += [f"- {t}" for t in tags(m)]
        L += ["---", "", f"# {m['version']}", "",
              f"**ParadoxAI Lab · Paradox World Model series #{m['series_no']:02d}** "
              f"(model {i + 1} of {len(models)} released; series numbers 01–{models[-1]['series_no']:02d}).", "",
              "| | |", "|---|---|",
              f"| Family | {m['family']} |",
              f"| Task | {m['task']} |",
              f"| Data | {'; '.join(m['datasets'])} |",
              f"| Parameters | {m['parameters']:,}" + (f" per checkpoint; this file holds {len(parts)} checkpoints ("
                                                         f"{', '.join(str(k) for k, _ in parts)}), the training stages "
                                                         f"recorded for this version" if len(parts) > 1 else "") + " |",
              f"| Status | {m['status']} |",
              f"| Trained | {m['date']} ({TRAINED.get(m['series_no'], m['source_run'])}) |",
              f"| Released | {m['released']} |", ""]
        L += ["## Result (as recorded)", "", m["result"], "", "## What changed in this version", "", m["improvement"], ""]
        if len(parts) > 1:
            eq = all(torch.equal(v, list(ck["weights"].values())[0][k]) for k, v in list(ck["weights"].values())[-1].items())
            L += [f"Checkpoints {', '.join(str(k) for k, _ in parts)} are " + ("identical in this file." if eq else
                  "different training stages; the record says which stage each result uses."), ""]
        if m["series_no"] in same:
            L += ["## Also stands for", ""] + [f"* #{x['series_no']:02d} {x['version']}: same weights as this file, so it "
                                              f"is not stored twice." for x in same[m["series_no"]]] + [""]
        if hybrid:
            L += ["## Note on hybrid use", "",
                  "This version was used in a hybrid setup that combines its output with forecasts from outside models "
                  "(see the record). Those outside models are **not** included here: this file holds only ParadoxAI "
                  "Lab's own trained weights.", ""]
        L += ["## Files", "", "| File | Bytes | SHA-256 |", "|---|---|---|",
              f"| `{m['file']}` | {m['bytes']:,} | `{m['sha256']}` |", "",
              "## Load", "", "```python", "import torch",
              "from huggingface_hub import hf_hub_download",
              f'path = hf_hub_download("{rid}", "{m["file"]}")',
              'ck = torch.load(path, map_location="cpu", weights_only=False)',
              'print(ck["meta"])            # name, task, data, parameters, result, source run',
              'weights = ck["weights"]       # PyTorch state dict' + (" per checkpoint" if len(parts) > 1 else ""),
              'results = ck["results"]       # every recorded result, the record text and the run logs', "```", ""]
        if m["family"] == "Atlas" and m["name"].startswith("atlas-5k"):
            L += ["Build the model with the repository's Atlas class (clone the GitHub repository first):", "",
                  "```python", "import sys; sys.path.insert(0, 'paradox-world-model/atlas')",
                  "from atlas.model import Atlas",
                  'model = Atlas(**{k: v for k, v in ck["cfg"].items() if k != "grown_from"})',
                  'model.load_state_dict(ck["weights"]); model.eval()',
                  "# q, recon, extras = model(yc, mc, uc, uf, geo, None, static)",
                  "# q: [batch, 32 stations, 24 hours, 5 variables, 3 quantiles]; the median q[..., 1] is the forecast",
                  "```", "", f"Inputs are built as in `atlas/delhi/run_atlas_5k.py`. Paper: [Grow, Don't Restart]"
                  f"({GH}/blob/main/atlas/paper4/Atlas5K_growth_preprint.pdf).", ""]
        else:
            L += [f"The architecture code for this version is in the [GitHub repository]({GH}) (see the record below); "
                  "the configuration it was trained with is stored in the file (`ck['cfg']`).", ""]
        L += ["## Record", "", "Rules, predictions and full results for this version:", ""]
        L += [f"* {record_link(r)}" for r in recs] + [f"* [Series index (all models)]({GH}/blob/main/models/series/README.md)", ""]
        L += ["Training data are not included; their sources and terms are in "
              f"[DATA_SOURCES.md]({GH}/blob/main/DATA_SOURCES.md).", "",
              "## Series", ""]
        L += [f"Previous: [#{prev['series_no']:02d} {prev['version']}](https://huggingface.co/{a.ns}/{prev['name']}) · "
              if prev else ""]
        L[-1] += (f"Next: [#{nxt['series_no']:02d} {nxt['version']}](https://huggingface.co/{a.ns}/{nxt['name']}) · " if nxt else "")
        L[-1] += f"[All models](https://huggingface.co/{plan['index_repo']})"
        L += ["", "## Licence and citation", "",
              f"Apache-2.0. ParadoxAI Lab (Aditya Kumar, Anupam Singh), [paradoxailab.com](https://paradoxailab.com). "
              f"Cite with [CITATION.cff]({GH}/blob/main/CITATION.cff).", ""]
        d = os.path.join(C, m["name"]); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "README.md"), "w").write("\n".join(L))
        note = f"#{m['series_no']:02d} · {m['version']} · {m['parameters']:,} params · {m['result']}"
        plan["models"].append(dict(series_no=m["series_no"], repo=rid, file=m["file"], sha256=m["sha256"],
                                   bytes=m["bytes"], card=os.path.relpath(os.path.join(d, "README.md"), REPO),
                                   note=note[:497] + ("..." if len(note) > 500 else "")))
        rows.append(f"| {m['series_no']:02d} | [{m['version']}](https://huggingface.co/{rid}) | {m['family']} | "
                    f"{m['task']} | {m['parameters']:,} | {m['status']} |")
    tot = sum(m["bytes"] for m in models)
    idx = ["---", "license: apache-2.0", "tags:", "- paradoxailab", "- paradox-world-model", "---", "",
           "# Paradox World Model: every released model", "",
           f"ParadoxAI Lab's full model series, oldest first: **{len(models)} models** (series #01–#"
           f"{models[-1]['series_no']:02d}; {tot / 1e6:.1f} MB). Each has its own repository with the weights, the "
           "data it was trained on, its recorded results and a SHA-256 checksum. Source and records: "
           f"[github.com/paradoxailab/paradox-world-model]({GH}).", "",
           "| # | Model | Family | Task | Parameters | Status |", "|---|---|---|---|---|---|"] + rows + [
           "", "Versions whose weights are identical to an earlier file (not stored twice): " +
           "; ".join(f"#{x['series_no']:02d} {x['version']} = #{x['same_as']:02d}" for x in S.get("identical_to_earlier", [])) + ".",
           "", "Licence: Apache-2.0. ParadoxAI Lab, [paradoxailab.com](https://paradoxailab.com).", ""]
    d = os.path.join(C, "paradox-world-model-series"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "README.md"), "w").write("\n".join(idx))
    plan["index_card"] = os.path.relpath(os.path.join(d, "README.md"), REPO)
    json.dump(plan, open(os.path.join(HERE, "plan.json"), "w"), indent=1)
    print(f"{len(models)} model cards + index written; all SHA-256 and parameter counts verified")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--ns", default="paradoxailab")
    main(ap.parse_args())
