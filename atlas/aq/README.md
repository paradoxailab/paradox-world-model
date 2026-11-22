# Atlas-AQ data pipeline (atlas/PREREG_AQ.md)

Run in Colab (the fetchers need the open internet). Each writes resumable monthly files under Drive `PWM-AQ/`.

| Step | Source | Script | Status |
|---|---|---|---|
| USA truth | AirNow hourly files (all US sites, PM2.5 / NO₂ / O₃) | `fetch_airnow.py` | written, parser tested on sample lines |
| India truth | OpenAQ archive `s3://openaq-data-archive` (CPCB / DPCC) | `fetch_openaq.py` | next |
| China truth | CN-AEBench (Hugging Face / ScienceDB) | `fetch_cnaebench.py` | next |
| CAMS forecasts | ADS `cams-global-atmospheric-composition-forecasts` (needs the lab owner's ADS licence + key) | `fetch_cams.py` | next |
| GEOS-CF forecasts | NASA OPeNDAP `geos-cf/v2/fcst`, from 5 Aug 2025 | `fetch_geoscf.py` | next |
| NOAA AQM forecasts | AWS `noaa-nws-naqfc-pds` (raw + bias-corrected O₃, PM2.5) | `fetch_naqfc.py` | next |
| Fires | NASA FIRMS (`FIRMS_MAP_KEY`) | `fetch_firms.py` | next |
| Aurora | `microsoft/aurora` air-pollution checkpoint, run on CAMS analyses | `run_aurora.py` | after CAMS |
