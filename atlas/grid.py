"""Run a list of experiments; every finished run is appended to a JSONL file, so the grid can stop and resume.

  python grid.py results/runs.jsonl ladder      # damped oscillator, all ten sizes x data amounts
  python grid.py results/runs.jsonl systems     # the other systems (sizes up to 1M here) + sweeps
"""
import json, os, sys, time

from atlas.train import run

SIZES = [10_000, 50_000, 100_000, 250_000, 500_000, 1_000_000, 2_000_000, 5_000_000, 7_500_000, 10_000_000]
NS = [30, 100, 300, 1000, 3000, 10000]
DENSE = [10, 18, 30, 55, 100, 180, 300, 550, 1000, 1800, 3000, 5500, 10000]


def plans(which):
    P = []
    if which == "ladder":       # model size x data amount on the damped oscillator
        for seed in (0, 1):
            for size in SIZES[:6]:
                for N in NS:
                    P.append(dict(name="damped", size=size, N=N, seed=seed))
        for size in SIZES[6:]:   # 2M..10M: one seed, three data amounts (CPU budget)
            for N in (100, 1000, 10000):
                P.append(dict(name="damped", size=size, N=N, seed=0))
    if which == "systems":
        for seed in (0, 1, 2):                                   # dense data axis: is the change sudden?
            for N in DENSE:
                P.append(dict(name="damped", size=250_000, N=N, seed=seed))
        for seed in (0, 1):
            for size in SIZES[:6]:
                for N in NS:
                    P.append(dict(name="harmonic", size=size, N=N, seed=seed))
        for seed in (0, 1):
            for N in NS:
                for noise in (0.0, 0.2, 0.5):                    # data quality
                    P.append(dict(name="damped", size=250_000, N=N, seed=seed, noise=noise))
                P.append(dict(name="damped", size=250_000, N=N, seed=seed, width=0.25))   # data diversity
            for N in (1000, 10000):
                for ms in (300, 1000, 10000):                    # training compute
                    P.append(dict(name="damped", size=250_000, N=N, seed=seed, max_steps=ms))
        for seed in (0, 1):
            for name in ("diffusion", "advdiff"):
                for N in NS:
                    for size in (10_000, 50_000, 250_000):
                        P.append(dict(name=name, size=size, N=N, seed=seed, max_steps=2000))
                    P.append(dict(name=name, size=250_000, N=N, seed=seed, max_steps=2000, physics=True))
        for N in (100, 1000, 10000):
            P.append(dict(name="advdiff", size=1_000_000, N=N, seed=0, max_steps=2000))
    if which == "fix":           # v0.2: in-context identification against the plain Atlas, same protocol (patience 10)
        for seed in (0, 1):
            for name in ("harmonic", "damped"):
                for N in NS:
                    for sysid in (False, True):
                        P.append(dict(name=name, size=250_000, N=N, seed=seed, sysid=sysid, patience=10))
        for size in (50_000, 1_000_000):
            for N in (100, 1000, 10000):
                P.append(dict(name="damped", size=size, N=N, seed=0, sysid=True, patience=10))
        P.append(dict(name="damped", size=10_000_000, N=10000, seed=0, sysid=True, patience=10))
        for seed in (0, 1):
            for name in ("diffusion", "advdiff"):
                for N in NS:
                    P.append(dict(name=name, size=250_000, N=N, seed=seed, max_steps=2000, patience=10))
        for seed in (1, 0):
            for name in ("diffusion", "advdiff"):
                for N in NS[::-1]:
                    P.append(dict(name=name, size=250_000, N=N, seed=seed, max_steps=2000, sysid=True, patience=10))
    return P


def key(p):
    return (p["name"], p["size"], p["N"], p["seed"], p.get("noise", 0.05), p.get("width", 1.0),
            int(p.get("physics", 0)), p.get("max_steps", 3000), int(p.get("sysid", 0)), p.get("patience", 6))


def done_keys(path):
    done = set()
    if os.path.exists(path):
        for l in open(path):
            r = json.loads(l)
            done.add((r["system"], r["size"], r["N"], r["seed"], r["noise"], r["width"], r["physics"], r["max_steps"], r.get("sysid", 0), r.get("patience", 6)))
    return done


if __name__ == "__main__":
    path, which = sys.argv[1], sys.argv[2]
    rev = len(sys.argv) > 3 and sys.argv[3] == "rev"          # a second worker can take the plan from the other end
    todo = [p for p in plans(which) if key({'max_steps': 3000, **p}) not in done_keys(path)]
    if rev: todo = todo[::-1]
    print(f"{which}: {len(todo)} runs to do", flush=True)
    t0 = time.time()
    for i, p in enumerate(todo):
        p = {'max_steps': 3000, **p}
        if key(p) in done_keys(path):                         # finished meanwhile by the other worker
            continue
        r = run(**p)
        with open(path, "a") as f:
            f.write(json.dumps(r) + "\n")
        print(f"[{i + 1}/{len(todo)} {time.time() - t0:6.0f}s] {r['system']} P={r['params']} N={r['N']} seed={r['seed']} "
              f"sysid={r.get('sysid', 0)} phys={r['physics']} steps={r['steps']} nmse={r['nmse']:.4f} "
              f"train={r['nmse_train']:.4f} ood={r['nmse_ood']:.3f} interv={r['interv_nmse']:.3f} (oracle {r['oracle']:.4f})",
              flush=True)
