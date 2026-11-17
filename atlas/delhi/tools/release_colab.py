"""Release a Colab run into the repository: the model file into models/series (dataset name, metadata and results
inside, as for every series file), the run's result JSONs and logs into atlas/results/colab/, and the v2c 2023 test into
series file #57. Then commit and push with a GitHub token from the environment (never printed or stored).

  GITHUB_TOKEN=... python release_colab.py --out /content/drive/MyDrive/PWM-10M/out --repo /content/pwm
"""
import argparse, base64, glob, hashlib, json, os, shutil, subprocess, sys

import torch

DS = ["WEATHER-5K (ICML 2026): 5,672 weather stations worldwide, hourly 2014–2023"]
TASK = "next 24 h of temperature, dew point, wind direction, wind speed, sea-level pressure at stations"
NAMES = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
PF = [1.55, 1.59, 57.37, 1.21, 1.43]                       # PhysicsFormer 24 h, published
HRES = [1.76, 1.85, 63.8, 1.48, 0.86]                      # ECMWF-HRES 24 h, published


def sh(*a, cwd=None, check=True):
    return subprocess.run(a, cwd=cwd, check=check, capture_output=True, text=True).stdout


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def verdict(t):
    m = [t["MAE"][n] for n in NAMES]
    pf = [n for n, a, b in zip(NAMES, m, PF) if a < b]
    hr = [n for n, a, b in zip(NAMES, m, HRES) if a < b]
    return dict(lower_than_PhysicsFormer=pf, beats_PhysicsFormer=len(pf) >= 4, lower_than_ECMWF_HRES=hr,
                beats_ECMWF_HRES=all(n in hr for n in ("Temperature", "Dewpoint", "Wind speed", "Sea-level pressure")))


def main(a):
    R, O = a.repo, a.out
    tok = os.environ.get("GITHUB_TOKEN", "")
    assert tok or a.dry, "set GITHUB_TOKEN (Colab: key icon -> Secrets -> GITHUB_TOKEN, notebook access on)"
    auth = "Authorization: Basic " + base64.b64encode(f"x-access-token:{tok}".encode()).decode()
    git = lambda *x: sh("git", "-c", f"http.extraHeader={auth}", *x, cwd=R)
    if not a.dry:
        git("fetch", "--depth", "1", "origin", a.branch); git("reset", "--hard", f"origin/{a.branch}")

    run = json.load(open(os.path.join(O, f"{a.tag}_s600.json")))
    v2c = json.load(open(os.path.join(O, "w5k_atlas_1m_h24_v2c_final_s600.json")))
    assert run.get("adopted") and "test" in run, "the 10M run is not adopted or has no test result"
    D = os.path.join(R, "models", "series"); S = json.load(open(os.path.join(D, "SERIES.json")))
    S["models"] = [m for m in S["models"] if m["series_no"] != 58]

    # results folder: JSONs and logs of both runs
    C = os.path.join(R, "atlas", "results", "colab", a.tag); os.makedirs(C, exist_ok=True)
    outs = {}
    for f in sorted(glob.glob(os.path.join(O, "*.json")) + glob.glob(os.path.join(O, "log_*.txt"))):
        shutil.copy(f, C)
        txt = open(f, encoding="utf-8", errors="replace").read()
        outs[f"colab/{a.tag}/{os.path.basename(f)}"] = {"json": json.loads(txt)} if f.endswith(".json") else {"text": txt}

    # series file #58: the 10M model
    ck = torch.load(os.path.join(O, f"{a.tag}_s600.pt"), map_location="cpu", weights_only=False)
    vt, vv = verdict(run["test"]), verdict(v2c["test"])
    t = run["test"]["MAE"]
    summary = (f"validation E {run['val_E']:.5f} (-{100 * (1 - run['val_E'] / 0.28140):.2f}% vs v2c; adopted by rule 10M-A); "
               f"2023 test MAE T {t['Temperature']:.3f} / Td {t['Dewpoint']:.3f} / WD {t['Wind direction']:.2f} / WS {t['Wind speed']:.3f} / "
               f"SLP {t['Sea-level pressure']:.3f}: lower than PhysicsFormer (19.3M) on {len(vt['lower_than_PhysicsFormer'])} of 5 "
               f"({'beats it' if vt['beats_PhysicsFormer'] else 'does not beat it'} by rule WB1); "
               f"{'beats' if vt['beats_ECMWF_HRES'] else 'does not beat'} ECMWF-HRES (pressure)")
    meta = dict(series_no=58, name="atlas-5k-10m", version="Atlas-5K 10M (adopted)", family="Atlas", task=TASK, datasets=DS,
                parameters=run["params"], result=summary,
                improvement="v2c grown to 9.64M parameters (width 196->392, 4->8 heads, 2->7 encoder and 2->7 dynamics blocks; "
                            "same forecasts at start) and trained 80,000 more steps at peak learning rate 3e-4",
                trained_on="all 2014–2021 training days (5,672 stations)", source_run=f"Google Colab ({run.get('gpu')}), 2026-11-17",
                source_file=f"Google Drive PWM-10M/out/{a.tag}_s600.pt", source_sha256=sha(os.path.join(O, f"{a.tag}_s600.pt")),
                weights_key="sd", date="2026-11-17", status="adopted; WB1 entry at 24 h", note="", code="atlas/atlas/grow.py, atlas/delhi/run_atlas_5k.py",
                license="see LICENSE in github.com/paradoxailab/paradox-world-model", organisation="ParadoxAI Lab", released="2026-11-17")
    res = dict(summary=summary, status=meta["status"], test_2023=run["test"], validation_2022=run["val"], verdict_WB1=vt,
               published={"PhysicsFormer (19.3M)": dict(zip(NAMES, PF)), "ECMWF-HRES": dict(zip(NAMES, HRES))},
               records={"atlas/README.md": "see section 'Atlas-5K 10M' (rules, predictions and results)"}, run_outputs=outs)
    fn = "58_atlas-5k-10m_weather5k_adopted.pt"
    torch.save(dict(meta=meta, weights=ck["sd"], cfg=ck["cfg"], results=res), os.path.join(D, fn))
    S["models"].append(dict(meta, file=fn, bytes=os.path.getsize(os.path.join(D, fn)), sha256=sha(os.path.join(D, fn))))

    # series file #57: v2c's 2023 test (weights unchanged)
    e57 = next(m for m in S["models"] if m["series_no"] == 57); p57 = os.path.join(D, e57["file"])
    c57 = torch.load(p57, map_location="cpu", weights_only=False)
    t2 = v2c["test"]["MAE"]
    c57["results"]["test_2023"] = v2c["test"]; c57["results"]["verdict_WB1"] = vv
    c57["results"]["run_outputs"][f"colab/{a.tag}/w5k_atlas_1m_h24_v2c_final_s600.json"] = {"json": v2c}
    s57 = (f"validation E 0.28140 (-3.93% vs v1); 2023 test MAE T {t2['Temperature']:.3f} / Td {t2['Dewpoint']:.3f} / "
           f"WD {t2['Wind direction']:.2f} / WS {t2['Wind speed']:.3f} / SLP {t2['Sea-level pressure']:.3f}: lower than PhysicsFormer on "
           f"{len(vv['lower_than_PhysicsFormer'])} of 5; superseded as the WB1 entry by #58 (Atlas-5K 10M)")
    c57["results"]["summary"] = c57["meta"]["result"] = s57; c57["meta"]["status"] = c57["results"]["status"] = "adopted, tested; superseded by #58"
    torch.save(c57, p57)
    e57.update(result=s57, status=c57["meta"]["status"], bytes=os.path.getsize(p57), sha256=sha(p57))

    json.dump(S, open(os.path.join(D, "SERIES.json"), "w"), indent=1)
    with open(os.path.join(D, "SHA256SUMS"), "w") as f:
        for m in S["models"]:
            f.write(f"{m['sha256']}  {m['file']}\n")
    md = os.path.join(D, "README.md"); txt = open(md).read()
    row = (f"| 58 | Atlas-5K 10M (adopted) | Atlas | {DS[0]} | {TASK} | {run['params']:,} | {summary} | {meta['improvement']} | "
           f"{meta['status']} | `{fn}` |")
    lines = [l for l in txt.split("\n") if not l.startswith("| 58 |")]
    i = max(k for k, l in enumerate(lines) if l.startswith("| 57 |"))
    lines[i] = "| 57 |" + "|".join(lines[i].split("|")[2:7]) + f"| {s57} |" + lines[i].split("|")[8] + f"| {e57['status']} |" + "|".join(lines[i].split("|")[10:])
    lines.insert(i + 1, row)
    open(md, "w").write("\n".join(lines))

    # check: both files load and #58 reproduces its saved weights
    from atlas.grow import load_any  # noqa: F401  (import check of the code that loads it)
    ck2 = torch.load(os.path.join(D, fn), map_location="cpu", weights_only=False)
    assert all(torch.equal(ck2["weights"][k], ck["sd"][k]) for k in ck["sd"])
    if a.dry:
        print("dry run: not committed"); print(sh("git", "status", "--short", cwd=R)); print(vt, vv); return
    git("add", "models/series", "atlas/results/colab")
    sh("git", "-c", "user.name=Aditya Kumar", "-c", "user.email=contact.paradoxailab@gmail.com", "commit", "-q", "-m",
       "Atlas-5K 10M released as series #58 (dataset, metadata and results inside); v2c 2023 test added to #57; Colab run outputs\n\n"
       "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
       "Claude-Session: https://claude.ai/code/session_01TCvEAwgYb9HyrCaEGd5YWa", cwd=R)
    print(git("push", "origin", f"HEAD:{a.branch}").replace(tok, "***") or "pushed")
    print(sh("git", "log", "--oneline", "-1", cwd=R))
    print("10M:", json.dumps(vt)); print("v2c:", json.dumps(vv))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--repo", default="/content/pwm")
    ap.add_argument("--tag", default="w5k_atlas_10m_h24_g1"); ap.add_argument("--branch", default="atlas-v0.1")
    ap.add_argument("--dry", action="store_true", help="build the files, no commit or push")
    sys.path.insert(0, os.path.join(ap.parse_known_args()[0].repo, "atlas"))
    main(ap.parse_args())
