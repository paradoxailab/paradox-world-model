"""Publish every model in models/hf/plan.json to Hugging Face, one repository per model, plus an index repository and a
collection that lists them oldest first. Re-runnable: a repository whose weights already match is only re-checked.
After each upload the SHA-256 that Hugging Face reports for the weights file is compared with SERIES.json; any
mismatch stops the run.

The token is read from the environment (HF_TOKEN), e.g. from Colab's secret store; it is never printed or written.

  python models/hf/publish_hf.py            # everything
  python models/hf/publish_hf.py --dry-run  # show what would be done
"""
import argparse, hashlib, json, os, sys

from huggingface_hub import HfApi, CommitOperationAdd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TITLE = "Paradox World Model series #01-#59"
DESC = "Every released ParadoxAI Lab model, oldest first: PWM-Dyn (traffic, rainfall), PWM-W (weather, air), Atlas."


def remote_sha(api, repo, fname):
    """SHA-256 of the file as stored on Hugging Face (from its large-file record, else by downloading it)."""
    info = api.model_info(repo, files_metadata=True)
    for s in info.siblings:
        if s.rfilename == fname:
            if s.lfs:
                return s.lfs.sha256 if hasattr(s.lfs, "sha256") else s.lfs.get("sha256")
            h = hashlib.sha256()
            with open(api.hf_hub_download(repo, fname, force_download=True), "rb") as f:
                for blk in iter(lambda: f.read(1 << 20), b""):
                    h.update(blk)
            return h.hexdigest()
    return None


def main(a):
    P = json.load(open(os.path.join(HERE, "plan.json")))
    api = HfApi(token=os.environ.get("HF_TOKEN"))
    me = api.whoami()["name"] if not a.dry_run else P["ns"]
    assert me == P["ns"], f"token belongs to '{me}', plan is for '{P['ns']}': regenerate cards with --ns {me}"
    lic = os.path.join(REPO, "LICENSE")
    done = []
    for m in P["models"]:
        rid = m["repo"]; wf = os.path.join(REPO, "models", "series", m["file"])
        if a.dry_run:
            print(f"would publish #{m['series_no']:02d} {rid} <- {m['file']} ({m['bytes']:,} B)"); continue
        api.create_repo(rid, repo_type="model", exist_ok=True, private=False)
        have = None
        try:
            have = remote_sha(api, rid, m["file"])
        except Exception:
            pass
        ops = [CommitOperationAdd("README.md", os.path.join(REPO, m["card"])), CommitOperationAdd("LICENSE", lic)]
        if have != m["sha256"]:
            ops.append(CommitOperationAdd(m["file"], wf))
        api.create_commit(rid, ops, commit_message=f"ParadoxAI Lab series #{m['series_no']:02d}: weights, model card, licence")
        got = remote_sha(api, rid, m["file"])
        if got != m["sha256"]:
            sys.exit(f"#{m['series_no']:02d} {rid}: Hugging Face reports SHA-256 {got}, expected {m['sha256']}: stopped")
        done.append(m); print(f"#{m['series_no']:02d} {rid}: published, SHA-256 verified")
    if a.dry_run:
        print(f"would publish index {P['index_repo']} and collection '{TITLE}' with {len(P['models'])} items"); return
    api.create_repo(P["index_repo"], repo_type="model", exist_ok=True, private=False)
    api.create_commit(P["index_repo"], [CommitOperationAdd("README.md", os.path.join(REPO, P["index_card"])),
                                        CommitOperationAdd("SERIES.json", os.path.join(REPO, "models/series/SERIES.json")),
                                        CommitOperationAdd("SHA256SUMS", os.path.join(REPO, "models/series/SHA256SUMS")),
                                        CommitOperationAdd("LICENSE", lic)],
                      commit_message="Index of every ParadoxAI Lab model, oldest first")
    old = [c for c in api.list_collections(owner=P["ns"]) if c.title == TITLE]
    col = old[0] if old else api.create_collection(TITLE, namespace=P["ns"], description=DESC, private=False)
    have = {i.item_id for i in api.get_collection(col.slug).items}
    for m in P["models"]:
        if m["repo"] not in have:
            api.add_collection_item(col.slug, item_id=m["repo"], item_type="model", note=m["note"], exists_ok=True)
    if P["index_repo"] not in have:
        api.add_collection_item(col.slug, item_id=P["index_repo"], item_type="model",
                                note="Index: all models in one table, with SERIES.json and SHA256SUMS.", exists_ok=True)
    items = [i.item_id for i in api.get_collection(col.slug).items]
    want = [m["repo"] for m in P["models"]]
    assert [i for i in items if i in want] == want, "collection order differs from the series order"
    print(f"PUBLISHED {len(done)} models (all SHA-256 verified); index {P['index_repo']}; "
          f"collection https://huggingface.co/collections/{col.slug} ({len(items)} items, series order checked)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    main(ap.parse_args())
