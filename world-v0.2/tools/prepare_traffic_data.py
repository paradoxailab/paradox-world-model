"""Build the four extra ParadoxBench-1.1 traffic tasks from their public sources (no data is re-hosted).

  PEMS03, PEMS07   Caltrans PeMS flow (ASTGCN release). Values and time features from the STAEformer
                   repository's data.npz; road graph from the ASTGNN repository's distance CSV.
  METR-LA, PEMS-BAY  Loop-detector speed (Li et al., DCRNN). Values and time features from the STAEformer
                   repository's data.npz; road graph = DCRNN's published Gaussian-kernel adjacency.

Writes data/raw/<NAME>.pb.npz with
  data [T, N] float32 (real units), tod [T] int (5-min slot of day), dow [T] int (0 = Monday),
  adj [N, N] float32 (un-normalised road-distance kernel weights, 0 = no link).

  python tools/prepare_traffic_data.py --staeformer ext/STAEformer --astgnn ext/astgnn --dcrnn ext/dcrnn
"""
import argparse, datetime as dt, importlib, os, pickle, sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
# first day of each series: PEMS03 2018-09-01, PEMS07 2017-05-01 (ASTGCN / STSGCN papers)
START = {"PEMS03": dt.date(2018, 9, 1), "PEMS07": dt.date(2017, 5, 1)}
STAE = {"PEMS03": "PEMS03", "PEMS07": "PEMS07", "METR-LA": "METRLA", "PEMS-BAY": "PEMSBAY"}


class _NumpyOnly(pickle.Unpickler):
    """DCRNN ships its adjacency as a pickle; allow nothing but plain numpy arrays to be rebuilt."""
    OK = {("numpy", "dtype"), ("numpy", "ndarray"), ("numpy.core.multiarray", "_reconstruct"),
          ("numpy._core.multiarray", "_reconstruct")}

    def find_class(self, module, name):
        if (module, name) not in self.OK:
            raise pickle.UnpicklingError(f"refused global {module}.{name}")
        if name == "_reconstruct":
            try:
                return importlib.import_module("numpy._core.multiarray")._reconstruct
            except ImportError:
                return importlib.import_module("numpy.core.multiarray")._reconstruct
        return getattr(np, name)


def kernel(dist):
    """Gaussian kernel of road distance, sigma = std of the listed distances, weights < 0.1 dropped
    (the same rule as the DCRNN adjacency and as PWM's PEMS04/08 graphs)."""
    fin = np.isfinite(dist)
    sigma = dist[fin].std()
    A = np.exp(-(dist / sigma) ** 2)
    A[~fin] = 0.0
    A[A < 0.1] = 0.0
    return A.astype(np.float32)


def pems_adj(name, n, astgnn):
    edges = np.genfromtxt(os.path.join(astgnn, f"{name}.csv"), delimiter=",", skip_header=1)
    dist = np.full((n, n), np.inf)
    if name == "PEMS03":                                   # CSV lists sensor ids; order given by PEMS03.txt
        ids = [int(x) for x in open(os.path.join(astgnn, "PEMS03.txt")).read().split()]
        pos = {s: i for i, s in enumerate(ids)}
        edges = [(pos[int(s)], pos[int(t)], c) for s, t, c in edges if int(s) in pos and int(t) in pos]
    for s, t, c in edges:
        dist[int(s), int(t)] = dist[int(t), int(s)] = c
    return kernel(dist)


def main(a):
    os.makedirs(RAW, exist_ok=True)
    for name, sub in STAE.items():
        z = np.load(os.path.join(a.staeformer, "data", sub, "data.npz"))["data"]
        data = z[..., 0].astype(np.float32)
        T, N = data.shape
        tod = np.rint(z[:, 0, 1] * 288).astype(np.int64) % 288
        if name in START:
            dow = (np.arange(T) // 288 + START[name].weekday()) % 7
        else:                                              # METR-LA / PEMS-BAY: real weekday in the file
            dow = z[:, 0, 2].astype(np.int64)
        if name.startswith("PEMS0"):
            adj = pems_adj(name, N, a.astgnn)
            src = "STAEformer data.npz (values, time) + ASTGNN distance CSV (graph)"
        else:
            pk = {"METR-LA": "adj_mx.pkl", "PEMS-BAY": "adj_mx_bay.pkl"}[name]
            with open(os.path.join(a.dcrnn, pk), "rb") as f:
                ids, _, adj = _NumpyOnly(f, encoding="latin1").load()
            adj = np.asarray(adj, np.float32)
            np.fill_diagonal(adj, 0.0)
            src = "STAEformer data.npz (values, time) + DCRNN adj_mx (graph)"
        assert adj.shape == (N, N), (name, adj.shape, N)
        out = os.path.join(RAW, f"{name}.pb.npz")
        np.savez_compressed(out, data=data, tod=tod, dow=dow, adj=adj, source=np.array(src))
        print(f"{name}: {T} steps x {N} sensors, {int((adj > 0).sum())} directed links, "
              f"zeros {100 * (data == 0).mean():.2f}% -> {out}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--staeformer", required=True)
    ap.add_argument("--astgnn", required=True)
    ap.add_argument("--dcrnn", required=True)
    main(ap.parse_args())
