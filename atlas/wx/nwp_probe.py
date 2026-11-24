"""Probe the forecast archives used by fetch_nwp_runs.py: request time, HTTP status and the fields each index lists.
  python nwp_probe.py 20250301
"""
import json, sys, time, urllib.request

d = sys.argv[1] if len(sys.argv) > 1 else "20250301"
U = {
    "ifs": f"https://ecmwf-forecasts.s3.amazonaws.com/{d}/00z/ifs/0p25/oper/{d}000000-24h-oper-fc.index",
    "aifs": f"https://ecmwf-forecasts.s3.amazonaws.com/{d}/00z/aifs-single/0p25/oper/{d}000000-24h-oper-fc.index",
    "aifs_2024": f"https://ecmwf-forecasts.s3.amazonaws.com/{d}/00z/aifs/0p25/oper/{d}000000-24h-oper-fc.index",
    "gfs": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{d}/00/atmos/gfs.t00z.pgrb2.0p25.f024.idx",
}
for k, u in U.items():
    t = time.time()
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "ParadoxAI-Lab research"}), timeout=60).read()
        if k == "gfs":
            f = sorted({":".join(l.split(":")[3:5]) for l in b.decode().splitlines()} & {"TMP:2 m above ground", "DPT:2 m above ground",
                     "UGRD:10 m above ground", "VGRD:10 m above ground", "PRMSL:mean sea level", "APCP:surface"})
        else:
            f = sorted({json.loads(l)["param"] for l in b.decode().splitlines() if json.loads(l).get("levtype") == "sfc"}
                       & {"2t", "2d", "10u", "10v", "msl", "tp"})
        print(f"{k:10s} {time.time() - t:5.2f}s ok   fields {f}")
    except Exception as e:
        print(f"{k:10s} {time.time() - t:5.2f}s FAIL {e}")
