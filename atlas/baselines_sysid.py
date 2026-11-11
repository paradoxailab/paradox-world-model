"""Identification with NO training at all (atlas/sysid.py on the noisy window, ridge 0.01, same lags as the model).
Reported for all test trajectories and for those with no forcing anywhere.  -> results/baselines_sysid.json"""
import json

import numpy as np
import torch

from atlas import systems as S
from atlas.sysid import identify, ring_basis, smooth_forecast

out = {}
for name in S.SYSTEMS:
    ring = S.is_ring(name); basis = ring_basis(S.M) if ring else torch.eye(1)[None]; p = 2 if ring else 3
    for ood in (False, True):
        d = S.make(name, 2000 if not ood else 1000, 998 if ood else 999, 0.05, ood=ood)
        y = torch.from_numpy(d["yc"]); ua = torch.from_numpy(np.concatenate([d["uc"], d["uf"]], 2))
        th = identify(y, ua[:, :, :S.L], basis, p, torch.full((p * basis.shape[0] * 2,), 0.01))
        fc = smooth_forecast(th, y, torch.ones_like(y), ua, basis, p, S.H)[1].numpy()
        unf = np.abs(d["u"]).sum((1, 2)) == 0
        e = lambda sel: float(((fc[sel] - d["yf"][sel]) ** 2).mean() / d["yf"].var())
        out[f"{name}_{'ood' if ood else 'in'}"] = dict(all=e(slice(None)), unforced=e(unf), unforced_share=float(unf.mean()))
        print(name, "unseen" if ood else "seen  ", out[f"{name}_{'ood' if ood else 'in'}"], flush=True)
json.dump(out, open("results/baselines_sysid.json", "w"), indent=1)
