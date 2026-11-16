"""Put each model's full results inside its file in models/series/ (weights unchanged).

For every series entry the file gets ck["results"] = {
  "summary":          the headline result (as in meta),
  "benchmark_rows":   PWM-Dyn: every row of the ParadoxBench table for that task (this model and every opponent, all tracks),
  "significance":     PWM-Dyn: the significance-test lines for that task,
  "records":          the record text written for that version (RESULTS.md section, version README, atlas/README.md sections,
                      or the PWM-W branch README),
  "run_outputs":      the run's own output files (result JSON, reports, test tables, logs) from atlas/results/kaggle/,
  "identical_versions": results of later versions whose weights are byte-identical to this file,
}
Run from the repository root:  python atlas/delhi/tools/embed_results.py
"""
import glob, hashlib, json, os, re, subprocess

import torch

ROOT = os.getcwd()
D = os.path.join(ROOT, "models", "series")
K = os.path.join(ROOT, "atlas", "results", "kaggle")
SERIES = json.load(open(os.path.join(D, "SERIES.json")))
PLAN = {e["id"]: e for e in json.load(open(os.path.join(ROOT, "atlas", "delhi", "tools", "series_plan.json")))["models"]}


def git_show(path, ref="origin/india-v2.0"):
    try:
        return subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return ""


def md_sections(text, heads):
    """Sections of a Markdown text whose heading line contains any of `heads`, each up to the next heading of the same
    or higher level."""
    lines = text.split("\n"); out = []
    for i, l in enumerate(lines):
        m = re.match(r"^(#{2,4}) (.*)", l)
        if m and any(h in m.group(2) for h in heads):
            lvl = len(m.group(1)); j = i + 1
            while j < len(lines):
                n = re.match(r"^(#{2,4}) ", lines[j])
                if n and len(n.group(1)) <= lvl:
                    break
                j += 1
            out.append("\n".join(lines[i:j]).strip())
    return "\n\n".join(out)


def run_outputs(folders, key=None):
    out = {}
    for fo in folders:
        for f in sorted(glob.glob(os.path.join(K, fo, "*"))):
            name = os.path.basename(f)
            if key and not any(k in name.lower() for k in (key, "log", "report")) and re.search(r"cpcb|wmo|metar", name.lower()):
                continue                                          # keep only this league's files in multi-league runs
            txt = open(f, encoding="utf-8", errors="replace").read()
            v = {"text": txt}
            if name.endswith(".json"):
                try:
                    v = {"json": json.loads(txt)}
                except Exception:
                    v = {"text": txt, "note": "partial copy: Kaggle's preview returns at most about 100 KB; the full file stays in the run"}
            if "[TRUNCATED IN TRANSFER" in txt:
                v["note"] = "middle omitted when copied (file larger than the transfer limit); full file stays in the Kaggle run"
            out[f"{fo}/{name}"] = v
    return out


RESULTS_MD = open(os.path.join(ROOT, "RESULTS.md")).read()
ATLAS_MD = open(os.path.join(ROOT, "atlas", "README.md")).read()
PB = {"v0.4": "results/paradoxbench1_results.json", "v0.4.1": "results/paradoxbench1_results.json",
      "v0.6": "results/paradoxbench1.1_results.json", "v0.7": "results/paradoxbench1.2_v07_results.json"}
TASK = {"IMD_central_india": "IMD-CI", "IMD_west_coast": "IMD-WC"}
SIG = {"v0.6": "v0.6-conference/results/v06_rows_and_tests.txt", "v0.7": "v0.7-realworld/results/v07_rows_sig_valcond.txt"}
VREADME = {"v0.6": "v0.6-conference/README.md", "v0.7": "v0.7-realworld/README.md", "v0.4": "v0.4-paradoxbench/README.md",
           "v0.4.1": "v0.4-paradoxbench/README.md"}
RSEC = {"v0.4": ["2. ParadoxBench-1"], "v0.4.1": ["2. ParadoxBench-1"], "v0.6": ["3. ParadoxBench-1.1"], "v0.7": ["4. ParadoxBench-1.2"]}

PWMW = {  # series number -> (branch README folders, run folders, league key)
    19: (["delhi-v0.1"], ["notebookce65e86211"], None), 20: (["delhi-v0.2"], ["pwm-delhi-v02-pm25"], None),
    21: (["delhi-v0.3"], ["pwm-weather-league-gpu"], "cpcb"), 22: (["delhi-v0.3"], ["pwm-weather-league-gpu"], "wmo"),
    23: (["delhi-v0.4"], ["pwm-weather-v04-gpu"], "cpcb"), 24: (["delhi-v0.4"], ["pwm-weather-v04-gpu"], "wmo"),
    25: (["delhi-v0.5"], ["pwm-weather-v05-metar"], "metar"), 26: (["delhi-v0.6"], ["pwm-weather-v06-cpcb"], "cpcb"),
    27: (["delhi-v0.7"], ["pwm-weather-v07-cpcb"], "cpcb"), 28: (["delhi-v0.8"], ["pwm-weather-v08-cpcb"], "cpcb"),
    29: (["delhi-v0.8"], ["pwm-x-cpcb"], "cpcb"), 30: (["delhi-v0.8"], ["pwm-v09-live"], None),
    31: (["delhi-v1.0"], ["pwm-v10"], "cpcb"), 32: (["delhi-v1.0"], ["pwm-v10"], "metar"), 33: (["delhi-v1.0"], ["pwm-v10"], "wmo"),
    34: (["india-v2.0"], ["pwm-v20"], "cpcb"), 35: (["india-v2.0"], ["pwm-v20"], None), 36: (["india-v2.0", "delhi-v1.1"], ["pwm-v21"], None),
}
ATLAS = {  # series number -> (atlas/README.md heading fragments, run folders)
    37: (["Stage 7 results", "Atlas-Delhi league: against"], ["atlas-delhi"]),
    38: (["Atlas-Delhi v1.1: all of Delhi", "Atlas-Delhi v1.1 results"], ["atlas-long-s300"]),
    39: (["Atlas-Delhi v1.2: the whole", "Atlas-Delhi v1.2 results"], ["atlas-long2-a"]),
    40: (["India first: the all-India league", "Atlas-India v1.0 results", "Atlas-India v1.0 against TimesFM", "L1 results", "T1 results"],
         ["atlas-india-s400", "atlas-india-score", "atlas-lono-score", "atlas-thr-score-t1"]),
    41: (["Atlas-Delhi v1.3: pre-trained", "Atlas-Delhi v1.3 results"], ["atlas-v13-s320"]),
    42: (["Atlas-Delhi v1.3: pre-trained", "Atlas-Delhi v1.3 results", "Atlas League v2.0"], ["atlas-v13-s320", "atlas-league2-score"]),
    43: (["Atlas-W: the output-first", "Atlas-W air core v0 results"], ["atlasw-v0"]),
    44: (["Atlas-W days 2 and 3", "Atlas-W day 2 results", "Atlas-W day 3a", "Atlas-W day 3b"], ["atlasw-v13-s320"]),
    45: (["Atlas-W days 2 and 3", "Atlas-W day 2 results", "Atlas-W day 3a", "Atlas-W day 3b"], ["atlasw-v13-s320"]),
    46: (["I1 results"], ["atlas-i1-s320", "atlas-i1-score"]),
    47: (["Atlas v1.4 programme", "V1 results"], ["atlas-v14n-s400"]),
    48: (["Atlas v1.4 programme", "V1 results"], ["atlas-indiap-s400"]),
    49: (["Atlas v2 programme: the parameter ladder", "S results"], ["atlas-scale3m-s400"]),
    50: (["Atlas v2 programme: the parameter ladder", "S results"], ["atlas-scale10m-s400"]),
    51: (["Atlas v2-W: the 10M model with weather", "W results", "T-A results"], ["atlas-w1-s400", "atlas-w1-s401", "atlas-w1-s402", "atlas-wa-score"]),
    52: (["Atlas v2-W: the 10M model with weather", "W results"], ["atlas-w10-s400"]),
    53: (["Atlas v2-W: the 10M model with weather", "W results"], ["atlas-w10r-s400"]),
    54: (["T-B results"], ["atlas-tb-s320", "atlas-tb-score"]),
    55: (["World benchmarks: plan", "WB1 results"], ["atlas-w5k-fetch", "atlas-w5k-check", "atlas-w5k-atlas1m-h24"]),
    56: (["Atlas-5K v2: improving"], ["atlas-w5k-v2a"]),
    57: (["Atlas-5K v2: improving"], ["atlas-w5k-v2c"]),
}


def results_for(no):
    e = PLAN[no]; r = {"summary": e["result"], "status": e.get("status", ""), "records": {}, "run_outputs": {}}
    v = e["version"]
    if e["family"] == "PWM-Dyn":
        ver = v.split()[-1]
        ds = e["source_glob"].split("/models/")[1].split("/")[0]
        task = TASK.get(ds, ds)
        rows = [x for x in json.load(open(os.path.join(ROOT, PB[ver])))["rows"] if x.get("task") == task]
        r["benchmark_rows"] = rows
        r["benchmark"] = os.path.basename(PB[ver])
        if ver in SIG:
            lines = open(os.path.join(ROOT, SIG[ver])).read().split("\n")
            r["significance"] = "\n".join(l for l in lines if task in l)
        r["records"]["RESULTS.md"] = md_sections(RESULTS_MD, RSEC[ver])
        p = os.path.join(ROOT, VREADME[ver])
        if os.path.exists(p):
            r["records"][VREADME[ver]] = md_sections(open(p).read(), ["Result", "result"]) or open(p).read()
    elif no in PWMW:
        heads, runs, key = PWMW[no]
        for h in heads:
            ref = "origin/delhi-v1.1" if h == "delhi-v1.1" else "origin/india-v2.0"
            r["records"][f"branch {h} / README.md"] = git_show(f"{h}/README.md", ref)
        r["run_outputs"] = run_outputs(runs, key)
    elif no in ATLAS:
        heads, runs = ATLAS[no]
        r["records"]["atlas/README.md"] = md_sections(ATLAS_MD, heads)
        r["run_outputs"] = run_outputs(runs)
    return r


def main():
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
    same = {}
    for s in SERIES["identical_to_earlier"]:
        same.setdefault(s["same_as"], []).append(s["series_no"])
    report = []
    for m in SERIES["models"]:
        no = m["series_no"]; p = os.path.join(D, m["file"])
        ck = torch.load(p, map_location="cpu", weights_only=False)
        before = {k: t.clone() for k, t in _flat(ck["weights"])}
        res = results_for(no)
        if no in same:
            res["identical_versions"] = {PLAN[n]["version"]: results_for(n) for n in same[no]}
        ck["results"] = res
        torch.save(ck, p)
        ck2 = torch.load(p, map_location="cpu", weights_only=False)
        after = dict(_flat(ck2["weights"]))
        assert before.keys() == after.keys() and all(torch.equal(before[k], after[k]) for k in before), f"weights changed in {p}"
        assert ck2["meta"] == ck["meta"] and ck2.get("cfg") == ck.get("cfg")
        size = len(json.dumps(res, default=str))
        m["bytes"], m["sha256"] = os.path.getsize(p), sha(p)
        m["results_chars"] = size
        report.append((no, m["file"], size, len(res.get("run_outputs", {})), len(res.get("benchmark_rows", [])), list(res["records"])))
    json.dump(SERIES, open(os.path.join(D, "SERIES.json"), "w"), indent=1)
    with open(os.path.join(D, "SHA256SUMS"), "w") as f:
        for m in SERIES["models"]:
            f.write(f"{m['sha256']}  {m['file']}\n")
    for row in report:
        print(*row, sep=" | ")


def _flat(w, pre=""):
    if torch.is_tensor(w):
        yield pre or "w", w
    elif isinstance(w, dict):
        for k, v in w.items():
            yield from _flat(v, f"{pre}.{k}" if pre else str(k))
    elif isinstance(w, (list, tuple)):
        for i, v in enumerate(w):
            yield from _flat(v, f"{pre}[{i}]")


if __name__ == "__main__":
    main()
