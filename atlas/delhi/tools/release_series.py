"""Release the grown Atlas-5K models into models/series (dataset name, metadata and results inside each file):
  #58 Atlas-5K 10M (adopted, WB1 entry until #59), #59 Atlas-5K 25M (adopted), and the v2c 2023 test into #57.
Also copies the run JSONs, logs and head-to-head results into atlas/results/colab/. No git: commit and push yourself
(or use release_colab.py on Colab with a GITHUB_TOKEN secret).

  python release_series.py --in <folder with the .pt/.json files from Drive PWM-10M/out> --h2h <folder with h2h jsons> --repo <repo>
"""
import argparse, glob, hashlib, json, os, re, shutil, sys

import torch

DS = ["WEATHER-5K (ICML 2026): 5,672 weather stations worldwide, hourly 2014–2023"]
TASK = "next 24 h of temperature, dew point, wind direction, wind speed, sea-level pressure at stations"
NAMES = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
PF = [1.55, 1.59, 57.37, 1.21, 1.43]                       # PhysicsFormer 24 h, published
HRES = [1.76, 1.85, 63.8, 1.48, 0.86]                      # ECMWF-HRES 24 h, published


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verdict(t):
    m = [t["MAE"][n] for n in NAMES]
    pf = [n for n, a, b in zip(NAMES, m, PF) if a < b]
    hr = [n for n, a, b in zip(NAMES, m, HRES) if a < b]
    return dict(lower_than_PhysicsFormer=pf, beats_PhysicsFormer=len(pf) >= 4, lower_than_ECMWF_HRES=hr,
                beats_ECMWF_HRES=all(n in hr for n in ("Temperature", "Dewpoint", "Wind speed", "Sea-level pressure")))


def tline(t):
    return (f"T {t['Temperature']:.3f} / Td {t['Dewpoint']:.3f} / WD {t['Wind direction']:.2f} / WS {t['Wind speed']:.3f} / "
            f"SLP {t['Sea-level pressure']:.3f}")


def h2h_summary(H, ours):
    """Paired head-to-head verdicts (Phase 6, Holm over 50 pairs) for one of our models."""
    out = {}
    for per in ("test", "live"):
        f = os.path.join(H, f"paired_{ours}_{per}_r25.json")
        if os.path.exists(f):
            P = json.load(open(f))
            out[per] = {k: f"{sum(r['verdict'] == 'WIN' for r in rows)}/5 significant wins" for k, rows in P.items()}
    return out


def main(a):
    R, O, H = a.repo, a.inp, a.h2h
    D = os.path.join(R, "models", "series"); S = json.load(open(os.path.join(D, "SERIES.json")))
    S["models"] = [m for m in S["models"] if m["series_no"] not in (58, 59)]
    v2c = json.load(open(os.path.join(O, "w5k_atlas_1m_h24_v2c_final_s600.json")))

    # run outputs into the results folder
    C = os.path.join(R, "atlas", "results", "colab", "atlas5k_grown"); os.makedirs(C, exist_ok=True)
    outs = {}
    for f in sorted(glob.glob(os.path.join(O, "*.json")) + glob.glob(os.path.join(O, "log_*.txt")) + glob.glob(os.path.join(H, "*.json"))):
        shutil.copy(f, C)
        txt = open(f, encoding="utf-8", errors="replace").read()
        outs[f"colab/atlas5k_grown/{os.path.basename(f)}"] = {"json": json.loads(txt)} if f.endswith(".json") else {"text": txt}

    specs = [
        dict(no=58, tag="w5k_atlas_10m_h24_g1", name="atlas-5k-10m", version="Atlas-5K 10M (adopted)", ours="atlas10m",
             base=0.28140, base_name="v2c", rule="10M-A", date="2026-11-17",
             improvement="v2c grown to 9.64M parameters (width 196->392, 4->8 heads, 2->7 encoder and 2->7 dynamics blocks; "
                         "same forecasts at start) and trained 80,000 more steps at peak learning rate 3e-4",
             status="adopted; superseded as the WB1 entry by #59 (Atlas-5K 25M)",
             file="58_atlas-5k-10m_weather5k_adopted.pt", readme="section 'Atlas-5K 10M' and Phase 5/6"),
        dict(no=59, tag="w5k_atlas_25m_h24_g2", name="atlas-5k-25m", version="Atlas-5K 25M (adopted)", ours="atlas25m",
             base=0.27592, base_name="10M (#58)", rule="25M-A", date="2026-11-18",
             improvement="#58 grown to 24.1M parameters (hidden layer of every block 784->1,960 units with zero-output new units, "
                         "one encoder block added; same forecasts at start) and trained 80,000 more steps at peak learning rate 2e-4",
             status="adopted; WB1 entry at 24 h", file="59_atlas-5k-25m_weather5k_adopted.pt",
             readme="sections 'Atlas-5K 25M' (rules, predictions) and 'Atlas-5K 25M results, part 1/2'"),
    ]
    built = []
    for sp in specs:
        run = json.load(open(os.path.join(O, f"{sp['tag']}_s600.json")))
        assert run.get("adopted") and "test" in run, f"{sp['tag']}: not adopted or no test result"
        src = os.path.join(O, f"{sp['tag']}_s600.pt")
        ck = torch.load(src, map_location="cpu", weights_only=False)
        vt = verdict(run["test"]); hh = h2h_summary(H, sp["ours"])
        n_won = sum(v.startswith("5/5") for per in hh.values() for v in per.values())
        summary = (f"validation E {run['val_E']:.5f} (-{100 * (1 - run['val_E'] / sp['base']):.2f}% vs {sp['base_name']}; adopted by rule "
                   f"{sp['rule']}); 2023 test MAE {tline(run['test']['MAE'])}: lower than PhysicsFormer (19.3M) on "
                   f"{len(vt['lower_than_PhysicsFormer'])} of 5; {'beats' if vt['beats_ECMWF_HRES'] else 'does not beat'} ECMWF-HRES "
                   f"(pressure); head-to-head (709 stations, 2023 test and live 2024-25): significant wins on all five variables "
                   f"against {n_won} of {sum(len(v) for v in hh.values())} opponent-periods (TimesFM 2.5/3.0, Chronos-2, Chronos-Bolt, "
                   f"TiRex, Sundial, Time-MoE, TTM, persistence)")
        meta = dict(series_no=sp["no"], name=sp["name"], version=sp["version"], family="Atlas", task=TASK, datasets=DS,
                    parameters=run["params"], result=summary, improvement=sp["improvement"],
                    trained_on="all 2014–2021 training days (5,672 stations)", source_run=f"Google Colab ({run.get('gpu')}), {sp['date']}",
                    source_file=f"Google Drive PWM-10M/out/{sp['tag']}_s600.pt", source_sha256=sha(src), weights_key="sd",
                    date=sp["date"], status=sp["status"], note="", code="atlas/atlas/grow.py, atlas/delhi/run_atlas_5k.py",
                    license="see LICENSE in github.com/paradoxailab/paradox-world-model", organisation="ParadoxAI Lab",
                    released="2026-11-18")
        res = dict(summary=summary, status=sp["status"], test_2023=run["test"], validation_2022=run["val"], verdict_WB1=vt,
                   head_to_head=hh, published={"PhysicsFormer (19.3M)": dict(zip(NAMES, PF)), "ECMWF-HRES": dict(zip(NAMES, HRES))},
                   records={"atlas/README.md": sp["readme"]}, run_outputs=outs)
        fn = os.path.join(D, sp["file"])
        torch.save(dict(meta=meta, weights=ck["sd"], cfg=ck["cfg"], results=res), fn)
        ck2 = torch.load(fn, map_location="cpu", weights_only=False)
        assert all(torch.equal(ck2["weights"][k], ck["sd"][k]) for k in ck["sd"])
        assert os.path.getsize(fn) < 100 * 2 ** 20, f"{fn} is over GitHub's 100 MB file limit"
        S["models"].append(dict(meta, file=sp["file"], bytes=os.path.getsize(fn), sha256=sha(fn)))
        built.append((sp, summary, meta))

    # #57: v2c's 2023 test (weights unchanged)
    e57 = next(m for m in S["models"] if m["series_no"] == 57); p57 = os.path.join(D, e57["file"])
    c57 = torch.load(p57, map_location="cpu", weights_only=False)
    vv = verdict(v2c["test"])
    c57["results"]["test_2023"] = v2c["test"]; c57["results"]["verdict_WB1"] = vv
    c57["results"]["head_to_head"] = h2h_summary(H, "v2c")
    s57 = (f"validation E 0.28140 (-3.93% vs v1); 2023 test MAE {tline(v2c['test']['MAE'])}: lower than PhysicsFormer on "
           f"{len(vv['lower_than_PhysicsFormer'])} of 5; grown into #58 and #59")
    c57["results"]["summary"] = c57["meta"]["result"] = s57
    c57["meta"]["status"] = c57["results"]["status"] = "adopted, tested; grown into #58 (10M) and #59 (25M)"
    torch.save(c57, p57)
    e57.update(result=s57, status=c57["meta"]["status"], bytes=os.path.getsize(p57), sha256=sha(p57))

    S["models"].sort(key=lambda m: m["series_no"])
    json.dump(S, open(os.path.join(D, "SERIES.json"), "w"), indent=1)
    with open(os.path.join(D, "SHA256SUMS"), "w") as f:
        for m in S["models"]:
            f.write(f"{m['sha256']}  {m['file']}\n")
    md = os.path.join(D, "README.md"); lines = open(md).read().split("\n")
    lines = [l for l in lines if not (l.startswith("| 58 |") or l.startswith("| 59 |"))]
    i = max(k for k, l in enumerate(lines) if l.startswith("| 57 |"))
    c = lines[i].split("|")
    c[7] = f" {s57} "; c[9] = f" {e57['status']} "
    lines[i] = "|".join(c)
    for k, (sp, summary, meta) in enumerate(built):
        lines.insert(i + 1 + k, f"| {sp['no']} | {sp['version']} | Atlas | {DS[0]} | {TASK} | {meta['parameters']:,} | {summary} | "
                                f"{sp['improvement']} | {sp['status']} | `{sp['file']}` |")
    tot = sum(m["bytes"] for m in S["models"])
    txt = "\n".join(lines)
    txt = re.sub(r"\d+ files, [\d.]+ MB\.", f"{len(S['models'])} files, {tot / 1e6:.1f} MB.", txt)
    open(md, "w").write(txt)
    for sp, summary, _ in built:
        print(f"#{sp['no']}: {summary}")
    print(f"#57: {s57}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--h2h", required=True)
    ap.add_argument("--repo", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    main(ap.parse_args())
