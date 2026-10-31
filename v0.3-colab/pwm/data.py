"""PWM data layer: real physical-world observations on a spatial graph.

Every dataset becomes the same structure:
  raw     [T, N]  observations in real units (NaN = missing / not observed)
  A       [N, N]  row-normalised physical adjacency (road distances or geographic grid)
  period  index of the observation inside its natural cycle (5-min slot of day / day of year)
  dow     day of week (0 for daily climate data, where it carries no meaning)

Datasets
  PEMS08, PEMS04   Caltrans road-sensor traffic flow, 5-min steps (standard benchmark protocol:
                   12 -> 12 steps, chronological 60/20/20 split, zero-masked metrics)
  IMD_<region>     India Meteorological Department 0.25 deg gridded daily rainfall (mm/day),
                   30 days -> next 7 days, split by year, zeros are REAL (no zero-masking)
"""
import datetime as dt
import os

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")

# lat_min, lat_max, lon_min, lon_max  (0.25 deg IMD grid)
IMD_REGIONS = {
    "central_india": (21.0, 26.75, 74.0, 82.75),   # Madhya Pradesh and surroundings
    "north_india":   (26.0, 31.75, 74.0, 80.75),   # Delhi NCR, Haryana, west UP, Punjab
    "west_coast":    (14.0, 20.75, 72.5, 76.25),   # Mumbai, Konkan, Western Ghats
}


def _row_norm(A):
    np.fill_diagonal(A, 1.0)
    return torch.tensor(A / A.sum(1, keepdims=True), dtype=torch.float32)


class SeriesData:
    def __init__(self, name, raw, A, period_idx, dow, period, in_len, out_len, bounds,
                 transform="none", mask_zero=False, units="", meta=None):
        self.name, self.raw, self.A = name, raw.astype(np.float32), A
        self.period_idx, self.dow, self.period = period_idx.astype(np.int64), dow.astype(np.int64), period
        self.in_len, self.out_len, self.bounds = in_len, out_len, bounds
        self.transform, self.mask_zero, self.units, self.meta = transform, mask_zero, units, meta or {}
        self.T, self.N = raw.shape
        self.observed = ~np.isnan(self.raw)
        f = self.fwd(np.nan_to_num(self.raw, nan=0.0))
        a, b = bounds["train"]
        tr = f[:b][self.observed[:b]]
        self.mean, self.std = float(tr.mean()), float(tr.std())   # TRAIN split only
        self.norm = np.where(self.observed, (f - self.mean) / self.std, 0.0).astype(np.float32)

    def fwd(self, x):
        return np.log1p(np.maximum(x, 0)) if self.transform == "log1p" else x

    def inv(self, z):   # z: normalised model output (torch) -> real units
        v = z * self.std + self.mean
        return torch.clamp(torch.expm1(v), min=0) if self.transform == "log1p" else v

    def indices(self, split, stride=1):
        a, b = self.bounds[split]
        return np.arange(a + self.in_len, b - self.out_len + 1)[::stride]

    def valid(self, y):
        """Which ground-truth values count in metrics."""
        m = ~np.isnan(y)
        if self.mask_zero:
            m &= y > 1e-4
        return m

    def batch(self, idx, device="cpu"):
        hi = idx[:, None] + np.arange(-self.in_len, 0)[None]
        fo = idx[:, None] + np.arange(self.out_len)[None]
        x = torch.from_numpy(self.norm[hi]).to(device)
        obs = torch.from_numpy(self.observed[hi]).to(device)
        y = torch.from_numpy(self.raw[fo]).to(device)                 # real units, NaN = unknown
        p = torch.from_numpy(self.period_idx[idx - 1]).to(device)      # cycle position of last obs
        d = torch.from_numpy(self.dow[idx - 1]).to(device)
        return x, obs, y, p, d

    def describe(self):
        n = [len(self.indices(s)) for s in ("train", "val", "test")]
        return (f"{self.name}: {self.T} steps x {self.N} locations, "
                f"{int((self.A > 0).sum()) - self.N} links; train/val/test windows = {n}")


# --------------------------------------------------------------------------- PeMS traffic
PEMS_START = {"PEMS08": dt.date(2016, 7, 1), "PEMS04": dt.date(2018, 1, 1)}


def load_pems(name):
    raw = np.load(f"{RAW}/{name}.npz")["data"][..., 0].astype(np.float32)
    T, N = raw.shape
    edges = np.atleast_2d(np.genfromtxt(f"{RAW}/{name}.csv", delimiter=",", skip_header=1))
    dist = np.full((N, N), np.inf)
    for s, t, c in edges:
        dist[int(s), int(t)] = dist[int(t), int(s)] = c
    sigma = dist[np.isfinite(dist)].std()
    A = np.exp(-(dist / sigma) ** 2)
    A[A < 0.1] = 0.0
    t = np.arange(T)
    dow = (t // 288 + PEMS_START[name].weekday()) % 7
    n_tr, n_va = int(T * 0.6), int(T * 0.2)
    bounds = {"train": (0, n_tr), "val": (n_tr, n_tr + n_va), "test": (n_tr + n_va, T)}
    return SeriesData(name, raw, _row_norm(A), t % 288, dow, 288, 12, 12, bounds,
                      transform="none", mask_zero=True, units="vehicles / 5 min")


# --------------------------------------------------------------------------- IMD rainfall
def imd_cache_path(region, y0, y1):
    return f"{RAW}/IMD_rain_{region}_{y0}_{y1}.npz"


def download_imd(region="central_india", y0=2000, y1=2024):
    """Download IMD 0.25 deg daily gridded rainfall with imdlib and cache the region as .npz."""
    import imdlib as imd
    la0, la1, lo0, lo1 = IMD_REGIONS[region]
    obj = imd.load("rain", y0, y1, cache_dir=os.path.join(RAW, "imd_cache"))
    ds = obj.get_xarray()
    var = list(ds.data_vars)[0]
    da = ds[var]
    dims = {d.lower(): d for d in da.dims}
    tdim = next(dims[k] for k in dims if "time" in k or "date" in k)
    ladim = next(dims[k] for k in dims if "lat" in k)
    lodim = next(dims[k] for k in dims if "lon" in k)
    da = da.sortby(ladim).sortby(lodim)
    da = da.sel({ladim: slice(la0, la1), lodim: slice(lo0, lo1)}).transpose(tdim, ladim, lodim)
    if da.sizes[ladim] == 0 or da.sizes[lodim] == 0:
        raise RuntimeError(f"region {region} selected no IMD grid cells")
    arr = da.values.astype(np.float32)
    arr[arr < 0] = np.nan                                    # IMD fill value (-999) -> missing
    lat, lon = da[ladim].values, da[lodim].values
    dates = np.array([str(x)[:10] for x in da[tdim].values])
    np.savez_compressed(imd_cache_path(region, y0, y1), rain=arr, lat=lat, lon=lon, dates=dates)
    return imd_cache_path(region, y0, y1)


def load_imd(region="central_india", y0=2000, y1=2024, in_len=30, out_len=7, path=None, name=None):
    path = path or imd_cache_path(region, y0, y1)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} missing - run download_imd('{region}', {y0}, {y1}) first")
    z = np.load(path)
    arr, lat, lon, dates = z["rain"], z["lat"], z["lon"], z["dates"]
    Tn, H, W = arr.shape
    flat = arr.reshape(Tn, H * W)
    keep = np.where(np.mean(~np.isnan(flat), 0) > 0.9)[0]  # land cells with >90% coverage
    raw = flat[:, keep]
    ii, jj = np.unravel_index(keep, (H, W))
    clat, clon = lat[ii], lon[jj]
    # geographic graph: 8-neighbour cells on the 0.25 deg grid, weight decays with distance
    dlat = (clat[:, None] - clat[None]) * 111.0
    dlon = (clon[:, None] - clon[None]) * 111.0 * np.cos(np.deg2rad(clat[:, None]))
    km = np.sqrt(dlat ** 2 + dlon ** 2)
    A = np.where(km < 0.25 * 111 * 1.5, np.exp(-(km / 30.0) ** 2), 0.0)
    d = [dt.date.fromisoformat(s) for s in dates]
    doy = np.array([x.timetuple().tm_yday - 1 for x in d])
    years = np.array([x.year for x in d])
    yl = years.max()
    te0 = int(np.argmax(years >= yl - 2))
    va0 = int(np.argmax(years >= yl - 5))
    bounds = {"train": (0, va0), "val": (va0, te0), "test": (te0, Tn)}
    return SeriesData(name or f"IMD_{region}", raw, _row_norm(A), doy, np.zeros(Tn), 366, in_len, out_len,
                      bounds, transform="log1p", mask_zero=False, units="mm / day",
                      meta={"lat": clat.tolist(), "lon": clon.tolist(),
                            "years": [int(years.min()), int(yl)],
                            "test_years": [int(yl - 2), int(yl)], "val_years": [int(yl - 5), int(yl - 3)]})


def load(name, **kw):
    if name.startswith("PEMS"):
        return load_pems(name)
    if name == "SYNTHETIC_IMD":   # test-only data, never reported
        return load_imd(path=os.path.join(RAW, "SYNTHETIC_IMD_rain_test.npz"), name="SYNTHETIC_IMD")
    if name.startswith("IMD_"):
        return load_imd(name[4:], **kw)
    raise ValueError(name)
