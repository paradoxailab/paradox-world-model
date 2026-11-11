"""Simple references on the same data: persistence, ridge regression (one linear map from the observed window and
the forcing to the future, fitted on the same N training trajectories), and the equation-aware oracle.
Also the rate-distortion "complexity" of each system in bits.   python baselines.py -> results/baselines.json"""
import json

import numpy as np

from atlas import systems as S
from atlas.train import test_sets

NS = [30, 100, 300, 1000, 3000, 10000]


def feats(d):
    n = len(d["yc"])
    return np.concatenate([d["yc"].reshape(n, -1), d["uc"].reshape(n, -1), d["uf"].reshape(n, -1), np.ones((n, 1), np.float32)], 1).astype(np.float64)


def ridge(name, N, seed, noise=0.05):
    T = test_sets(name, noise)
    d = S.make(name, N, 10_000 + 1000 * seed + 7, noise)                 # the same trajectories Atlas gets
    n_tr = max(1, int(round(0.8 * N)))
    X, Y = feats(d), d["yfn"].reshape(N, -1).astype(np.float64)
    Xt = feats(T["te"])
    best = None
    for lam in (1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100):
        W = np.linalg.solve(X[:n_tr].T @ X[:n_tr] + lam * np.eye(X.shape[1]), X[:n_tr].T @ Y[:n_tr])
        v = ((X[n_tr:] @ W - Y[n_tr:]) ** 2).mean() if n_tr < N else 0
        if best is None or v < best[0]: best = (v, W)
    p = (Xt @ best[1]).reshape(T["te"]["yf"].shape).astype(np.float32)
    return S.nmse(p, T["te"])


if __name__ == "__main__":
    out = {}
    for name in S.SYSTEMS:
        T = test_sets(name, 0.05)
        out[name] = dict(persistence=T["persistence"], oracle=T["oracle"], oracle_ood=T["oracle_ood"],
                         ridge={N: [ridge(name, N, s) for s in (0, 1)] for N in NS},
                         complexity_bits={str(t): S.complexity_bits(name, t) for t in (0.1, 0.03, 0.01)})
        print(name, json.dumps(out[name]), flush=True)
    for noise in (0.0, 0.2, 0.5):
        T = test_sets("damped", noise)
        out[f"damped_noise{noise}"] = dict(oracle=T["oracle"], persistence=T["persistence"])
        print(noise, out[f"damped_noise{noise}"], flush=True)
    json.dump(out, open("results/baselines.json", "w"), indent=1)
