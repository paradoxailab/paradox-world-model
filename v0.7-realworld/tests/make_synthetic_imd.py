"""TEST ONLY. Writes a SYNTHETIC file shaped exactly like the cached IMD rainfall file so the
rainfall pipeline can be exercised where the IMD server is unreachable. Its name starts with
SYNTHETIC_ and results from it are never reported (compare.py refuses them)."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pwm.data import RAW

rng = np.random.default_rng(0)
dates = np.arange(np.datetime64("2015-01-01"), np.datetime64("2024-12-31"))
T = len(dates)
lat, lon = np.arange(21.0, 23.0, 0.25), np.arange(76.0, 78.0, 0.25)
doy = np.array([(d - d.astype("datetime64[Y]")).astype(int) for d in dates])
season = np.clip(np.sin((doy - 150) / 365 * 2 * np.pi) * 12, 0, None)       # fake monsoon
rain = np.maximum(0, season[:, None, None] * rng.gamma(0.6, 1.5, (T, len(lat), len(lon))) - 1)
rain = rain.astype(np.float32)
rain[:, 0, 0] = np.nan                                                      # an ocean cell
path = os.path.join(RAW, "SYNTHETIC_IMD_rain_test.npz")
np.savez_compressed(path, rain=rain, lat=lat, lon=lon, dates=np.array([str(d) for d in dates]))
print("wrote", path, rain.shape)
