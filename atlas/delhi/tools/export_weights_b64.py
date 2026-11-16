"""Release helper: write attached weight files (*.pt under /kaggle/input) as base64 text parts plus a manifest with
SHA-256 and size, so they can be read back through Kaggle's text preview and committed to the repository's models/.

  python export_weights_b64.py --names w5k_atlas_1m_h24_s600.pt atlas_w1_s400.pt ...
"""
import argparse, base64, glob, hashlib, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--names", nargs="+", required=True)
ap.add_argument("--out", default="/kaggle/working/out")
ap.add_argument("--chunk", type=int, default=100_000)              # Kaggle text previews stop at 102,400 bytes
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
man = {}
for n in a.names:
    hits = sorted(glob.glob(f"/kaggle/input/**/{n}", recursive=True))
    if not hits:
        man[n] = {"error": "not found"}; print("MISSING", n); continue
    b = open(hits[0], "rb").read()
    s = base64.b64encode(b).decode()
    parts = [s[i:i + a.chunk] for i in range(0, len(s), a.chunk)]
    for k, p in enumerate(parts):
        open(os.path.join(a.out, f"{n}.b64.{k:03d}.txt"), "w").write(p)
    man[n] = {"source": hits[0], "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "parts": len(parts), "chunk": a.chunk}
    print("EXPORT", n, man[n])
json.dump(man, open(os.path.join(a.out, "weights_manifest.json"), "w"), indent=1)
print("MANIFEST " + json.dumps(man))
