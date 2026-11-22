"""Add the Atlas-100M follow-up weights to Hugging Face (PARADOXAIlabs/atlas-100m) and update the card.
Adds traffic/ (Atlas-100M-T, T1d, TXL2) and hybrid/ (registered hybrid, H2); the v1.0 files are not touched.
Every new file's SHA-256 is computed locally and compared with what Hugging Face reports after upload.
The token comes from a prior `hf auth login`; it is never printed or written.

  python atlas/m100/publish_hf_m100_v11.py --store /content/drive/MyDrive/PWM-100M
"""
import argparse, hashlib, os

from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download

HERE = os.path.dirname(os.path.abspath(__file__))
RID = "PARADOXAIlabs/atlas-100m"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def main(a):
    api = HfApi()
    me = api.whoami()["name"]
    assert me == "paradoxailab", f"logged in as '{me}', expected 'paradoxailab'"
    files = {f"traffic/{t}_best.pt": os.path.join(a.store, "traffic_plus", f"{t}_best.pt")
             for t in ("atlas100mT", "atlas100mT1d", "atlas100mTXL2")}
    files.update({f"hybrid/{t}_best.pt": os.path.join(a.store, "out", f"{t}_best.pt") for t in ("hybrid", "hybrid2")})
    sums = {}
    for dst, src in files.items():
        sums[dst] = sha(src)
        print(f"{dst}: {os.path.getsize(src):,} B  sha256 {sums[dst]}", flush=True)
    old = open(hf_hub_download(RID, "SHA256SUMS")).read()                 # keep the v1.0 lines unchanged
    sp = "/tmp/SHA256SUMS"
    open(sp, "w").write(old.rstrip("\n") + "\n" + "".join(f"{s}  {f}\n" for f, s in sums.items()))
    ops = [CommitOperationAdd("README.md", os.path.join(HERE, "hf_card", "README.md")), CommitOperationAdd("SHA256SUMS", sp)]
    ops += [CommitOperationAdd(dst, src) for dst, src in files.items()]
    api.create_commit(RID, ops, commit_message="Atlas-100M v1.1 (interim): traffic follow-ups T / T1d / TXL2, hybrid and H2 weights, standings card")
    info = api.model_info(RID, files_metadata=True)
    got = {s.rfilename: (s.lfs.sha256 if s.lfs is not None and hasattr(s.lfs, "sha256") else (s.lfs or {}).get("sha256"))
           for s in info.siblings}
    bad = [f for f in sums if got.get(f) != sums[f]]
    print("VERIFIED: all new files match their SHA-256 on Hugging Face" if not bad else f"MISMATCH: {bad}", flush=True)
    assert not bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="/content/drive/MyDrive/PWM-100M")
    main(ap.parse_args())
