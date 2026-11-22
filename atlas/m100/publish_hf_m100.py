"""Upload Atlas-100M to Hugging Face (PARADOXAIlabs/atlas-100m): weights, model card, licence, SHA256SUMS.
Every weights file's SHA-256 is computed locally first and compared with what Hugging Face reports after upload.
The token comes from HF_TOKEN or a prior `hf auth login`; it is never printed or written.

  python atlas/m100/publish_hf_m100.py --out /content/drive/MyDrive/PWM-100M/out
"""
import argparse, hashlib, os, sys

from huggingface_hub import HfApi, CommitOperationAdd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
FILES = ["atlas100m_best.pt", "atlas100m_weather_view.pt", "atlas100m_aq_view.pt", "atlas100m_traffic_view.pt"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def main(a):
    api = HfApi(token=os.environ.get("HF_TOKEN"))
    me = api.whoami()["name"]
    assert me == "paradoxailab", f"logged in as '{me}', expected 'paradoxailab'"
    rid = "PARADOXAIlabs/atlas-100m"
    sums = {f: sha(os.path.join(a.out, f)) for f in FILES}
    for f, s in sums.items():
        print(f"{f}: {os.path.getsize(os.path.join(a.out, f)):,} B  sha256 {s}", flush=True)
    sp = "/tmp/SHA256SUMS"
    open(sp, "w").write("".join(f"{s}  {f}\n" for f, s in sums.items()))
    api.create_repo(rid, repo_type="model", exist_ok=True, private=False)
    ops = [CommitOperationAdd("README.md", os.path.join(HERE, "hf_card", "README.md")),
           CommitOperationAdd("LICENSE", os.path.join(REPO, "LICENSE")), CommitOperationAdd("SHA256SUMS", sp)]
    ops += [CommitOperationAdd(f, os.path.join(a.out, f)) for f in FILES]
    api.create_commit(rid, ops, commit_message="Atlas-100M (interim release): weights, model card, licence, checksums")
    info = api.model_info(rid, files_metadata=True)
    got = {s.rfilename: (s.lfs.sha256 if s.lfs is not None and hasattr(s.lfs, "sha256") else (s.lfs or {}).get("sha256"))
           for s in info.siblings if s.rfilename in FILES}
    bad = [f for f in FILES if got.get(f) != sums[f]]
    if bad:
        sys.exit(f"SHA-256 mismatch on Hugging Face for {bad}: stopped")
    print(f"HF-PUBLISHED https://huggingface.co/{rid} (all {len(FILES)} weights files verified)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/content/drive/MyDrive/PWM-100M/out")
    main(ap.parse_args())
