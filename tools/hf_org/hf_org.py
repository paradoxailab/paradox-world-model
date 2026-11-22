"""Move ParadoxAI Lab's Hugging Face repos into the organization and set it up (models, datasets, collections, card).

  python tools/hf_org/hf_org.py move            # every model of user 'paradoxailab' -> org (HF keeps redirects)
  python tools/hf_org/hf_org.py datasets --repo <checkout> --nwp <NWP_W5K.npz>
  python tools/hf_org/hf_org.py collections
  python tools/hf_org/hf_org.py card --repo <checkout>
The token comes from a prior `hf auth login`; it is never printed or written.
"""
import argparse, glob, os, shutil, tempfile

from huggingface_hub import HfApi

USER, ORG = "paradoxailab", "PARADOXAIlabs"
HERE = os.path.dirname(os.path.abspath(__file__))
api = HfApi()


def move(a):
    have = {m.id.split("/")[1] for m in api.list_models(author=ORG, limit=1000)}
    for m in api.list_models(author=USER, limit=1000):
        name = m.id.split("/")[1]
        if name in have:
            print("already in org:", name, flush=True); continue
        try:
            api.move_repo(m.id, f"{ORG}/{name}", repo_type="model")
            print(f"moved {m.id} -> {ORG}/{name}", flush=True)
        except Exception as e:
            print(f"FAILED {m.id}: {str(e)[:200]}", flush=True)
    print("models in org:", len(list(api.list_models(author=ORG, limit=1000))), flush=True)


def datasets(a):
    r = a.repo
    # 1) every Atlas result: scores, logs, plans and the station lists (no third-party forecasts are included)
    rid = f"{ORG}/atlas-benchmark-results"
    api.create_repo(rid, repo_type="dataset", exist_ok=True)
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(r, "atlas/m100/results"), os.path.join(d, "results"))
    for f in ("RESULTS.md", "STANDINGS.md", "PREREG.md", "PREREG_TRAFFIC.md", "india_stations.json"):
        shutil.copy(os.path.join(r, "atlas/m100", f), d)
    shutil.copy(os.path.join(HERE, "card_results.md"), os.path.join(d, "README.md"))
    api.upload_folder(repo_id=rid, repo_type="dataset", folder_path=d, commit_message="Atlas benchmark results (v1.1)")
    print("uploaded", rid, sum(len(fs) for _, _, fs in os.walk(d)), "files", flush=True)
    # 2) the archived global forecasts at the 178 hybrid stations (ECMWF IFS / AIFS open data, NOAA GFS; via Open-Meteo)
    if a.nwp and os.path.exists(a.nwp):
        rid = f"{ORG}/atlas-station-forecast-archive"
        api.create_repo(rid, repo_type="dataset", exist_ok=True)
        api.upload_file(path_or_fileobj=a.nwp, path_in_repo="NWP_W5K.npz", repo_id=rid, repo_type="dataset",
                        commit_message="IFS / AIFS / GFS forecasts at 178 WEATHER-5K stations, 2024-01 - 2025-08")
        api.upload_file(path_or_fileobj=os.path.join(HERE, "card_nwp.md"), path_in_repo="README.md", repo_id=rid,
                        repo_type="dataset", commit_message="card")
        print("uploaded", rid, flush=True)


COLLECTIONS = [
    ("Atlas-100M: one world model for weather, air quality and traffic",
     "98.6M-parameter shared core; traffic follow-ups up to 119M; hybrid with ECMWF/GFS forecasts. Pre-registered, every loss reported.",
     ["model:atlas-100m", "model:atlas-5k-25m", "dataset:atlas-benchmark-results", "dataset:atlas-station-forecast-archive"]),
    ("Atlas growth series: 0.97M to 100M by function-preserving growth",
     "Station weather world models grown step by step without losing what they learned.",
     ["model:paradox-world-model-series", "model:atlas-5k-v1", "model:atlas-5k-v2a", "model:atlas-5k-v2c", "model:atlas-5k-10m",
      "model:atlas-5k-25m", "model:atlas-scale-3m", "model:atlas-scale-10m", "model:atlas-w1", "model:atlas-w10", "model:atlas-w10r",
      "model:atlas-100m"]),
    ("Atlas India: PM2.5 and weather over India",
     "Air-quality and weather models for Delhi and all-India CPCB stations.",
     ["model:atlas-india-v1.0", "model:atlas-india-v1.3-pretrain", "model:atlas-delhi-v1.0", "model:atlas-delhi-v1.1",
      "model:atlas-delhi-v1.2", "model:atlas-delhi-v1.3", "model:atlas-delhi-i1", "model:atlas-w-v0", "model:atlas-w-v1-pretrain",
      "model:atlas-w-v1-delhi", "model:atlas-w-delhi-tb", "model:atlas-v1.4n", "model:atlas-p"]),
    ("PWM-Dyn: compact dynamics for traffic and rainfall",
     "Single-domain world model for road networks (PeMS, METR-LA, PEMS-BAY) and IMD rainfall.",
     ["model:pwm-dyn-v0.7-pems08", "model:pwm-dyn-v0.7-pems04", "model:pwm-dyn-v0.7-pems03", "model:pwm-dyn-v0.7-pems07",
      "model:pwm-dyn-v0.7-metr-la", "model:pwm-dyn-v0.7-pems-bay", "model:pwm-dyn-v0.6-pems08", "model:pwm-dyn-v0.4-imd_central_india",
      "model:pwm-dyn-v0.4-imd_west_coast"]),
    ("Paradox World Model (PWM-W / PWM-F) early series",
     "The first PWM weather and air-quality models and encoders.",
     ["model:pwm-w-v1.0-metar", "model:pwm-w-v1.0-wmo", "model:pwm-w-live-v0.9", "model:pwm-w-weather-v0.8-cpcb",
      "model:pwm-x-cpcb", "model:pwm-f-encoder-v2.1", "model:pwm-w-delhi-v0.2"]),
]


def collections(a):
    have = {c.title: c for c in api.list_collections(owner=ORG, limit=100)}
    for title, desc, items in COLLECTIONS:
        c = have.get(title) or api.create_collection(title=title, namespace=ORG, description=desc, private=False)
        inside = {i.item_id for i in api.get_collection(c.slug).items}
        for it in items:
            kind, name = it.split(":")
            iid = f"{ORG}/{name}"
            if iid in inside:
                continue
            try:
                api.add_collection_item(c.slug, item_id=iid, item_type=kind)
            except Exception as e:
                print(f"  skip {iid}: {str(e)[:120]}", flush=True)
        print("collection:", c.slug, flush=True)


def cards(a):
    """Re-upload every model card (links now point at the organization)."""
    names = {m.id.split("/")[1] for m in api.list_models(author=ORG, limit=1000)}
    src = {os.path.basename(os.path.dirname(f)): f for f in glob.glob(os.path.join(a.repo, "models/hf/cards/*/README.md"))}
    src["atlas-100m"] = os.path.join(a.repo, "atlas/m100/hf_card/README.md")
    n = 0
    for name, f in sorted(src.items()):
        if name in names:
            api.upload_file(path_or_fileobj=f, path_in_repo="README.md", repo_id=f"{ORG}/{name}",
                            commit_message="Card: links to the ParadoxAI Lab organization")
            n += 1
    print("cards updated:", n, flush=True)


def card(a):
    rid = f"{ORG}/README"
    api.create_repo(rid, repo_type="space", space_sdk="static", exist_ok=True)
    api.upload_file(path_or_fileobj=os.path.join(HERE, "org_card.md"), path_in_repo="README.md", repo_id=rid,
                    repo_type="space", commit_message="ParadoxAI Lab organization card")
    api.upload_file(path_or_fileobj=os.path.join(HERE, "index.html"), path_in_repo="index.html", repo_id=rid,
                    repo_type="space", commit_message="static page")
    print("org card:", rid, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["move", "datasets", "collections", "card", "cards", "all"])
    ap.add_argument("--repo", default="/content/pwm2")
    ap.add_argument("--nwp", default="/content/drive/MyDrive/PWM-100M/nwp/NWP_W5K.npz")
    a = ap.parse_args()
    if a.cmd == "all":
        for f in (move, datasets, collections, card, cards):
            f(a)
    else:
        {"move": move, "datasets": datasets, "collections": collections, "card": card, "cards": cards}[a.cmd](a)
