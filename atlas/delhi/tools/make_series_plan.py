"""Writes series_plan.json (input of model_series.py release) and models/series/README.md from one table.

Every result string is copied from the repository's own records (RESULTS.md, atlas/README.md, the delhi-v*/india-v2.0
branch READMEs); where a version's README records no result, the entry says so.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

NB = "notebooks/aditya16kumar/"
PEMS = {"PEMS08": "PEMS08 (Caltrans PeMS District 8, San Bernardino; 170 sensors, Jul–Aug 2016)",
        "PEMS04": "PEMS04 (Caltrans PeMS District 4, SF Bay Area; 307 sensors, Jan–Feb 2018)",
        "PEMS03": "PEMS03 (Caltrans PeMS District 3; 358 sensors)",
        "PEMS07": "PEMS07 (Caltrans PeMS District 7, Los Angeles; 883 sensors)",
        "METR-LA": "METR-LA (Los Angeles highway loop detectors; 207 sensors)",
        "PEMS-BAY": "PEMS-BAY (SF Bay Area; 325 sensors)",
        "IMD_central_india": "IMD 0.25° gridded daily rainfall, central India (2000–2024)",
        "IMD_west_coast": "IMD 0.25° gridded daily rainfall, Konkan / Western Ghats (2000–2024)"}
DELHI = "CPCB Delhi, 39 continuous ambient air-quality stations (OpenCity 'Delhi Hourly Air Quality Reports')"
INDIA = "CPCB all-India stations, 14 networks / 263 stations (Kaggle 'Time Series Air Quality Data of India (2010-2023)')"
ERA5 = "ERA5 weather at each station (Open-Meteo archive, Copernicus C3S)"
W5K = "WEATHER-5K (ICML 2026): 5,672 weather stations worldwide, hourly 2014–2023"
CPCBW = "CPCB/DPCC Delhi station meteorology (25 stations)"
WMO = "WMO synoptic stations in India (NOAA ISD)"
METAR = "METAR reports from six Indian airports incl. Delhi Palam"

M = []


def add(**e):
    e["id"] = len(M) + 1
    M.append(e)


# ---- PWM-Dyn: traffic and rainfall dynamics (Oct 30 - Nov 4) ------------------------------------------------
v04 = {"PEMS08": "14.53", "PEMS04": "19.21", "IMD_central_india": "2.84 mm/day", "IMD_west_coast": "3.41 mm/day"}
for ds, r in v04.items():
    add(name=f"pwm-dyn-v0.4-{ds.lower()}", file=f"pwm-dyn_v0.4_{ds}", version="PWM-Dyn v0.4", family="PWM-Dyn",
        task="next 12 steps of traffic flow" if ds.startswith("PEMS") else "next days of gridded rainfall",
        datasets=[PEMS[ds]], source_run="Kaggle notebook0387a11c3a (version 364310290), 2026-11-01",
        source_glob=f"notebook0387a11c3a/pwm_kit/models/{ds}/v04-s0/weights.pt", weights_key="", date="2026-11-01",
        result=f"ParadoxBench-1 Track A test MAE {r} (3-seed ensemble; this file is seed 0)",
        improvement="ParadoxBench-1 tracks and split-conformal calibration; rainfall 80% coverage 54.7% -> 84.7% vs v0.3",
        status="reported")
for ds, r in {"PEMS08": "14.50", "PEMS04": "19.02"}.items():
    add(name=f"pwm-dyn-v0.4.1-{ds.lower()}", file=f"pwm-dyn_v0.4.1_{ds}", version="PWM-Dyn v0.4.1", family="PWM-Dyn",
        task="next 12 steps of traffic flow", datasets=[PEMS[ds]],
        source_run="Kaggle notebookab27dd6f3e (version 364348754), 2026-11-01",
        source_glob=f"notebookab27dd6f3e/pwm_kit/models/{ds}/v041-s0/weights.pt", weights_key="", date="2026-11-01",
        result=f"ParadoxBench-1 Track A test MAE {r} (3-seed ensemble; this file is seed 0)",
        improvement="training recipe chosen on PEMS08 validation (100 epochs); Track B PEMS08 14.38 -> 14.15",
        status="reported")
v06 = {"PEMS08": "14.12", "PEMS04": "18.46", "PEMS03": "14.34", "PEMS07": "19.56", "METR-LA": "2.92", "PEMS-BAY": "1.52"}
for ds, r in v06.items():
    add(name=f"pwm-dyn-v0.6-{ds.lower()}", file=f"pwm-dyn_v0.6_{ds}", version="PWM-Dyn v0.6", family="PWM-Dyn",
        task="next 12 steps of traffic", datasets=[PEMS[ds]], source_run="Kaggle notebookd0ba070ac4 (version 365009705), 2026-11-02/03",
        source_glob=f"notebookd0ba070ac4/repo/v0.6-conference/models/{ds}/v06-s100/weights.pt", weights_key="", date="2026-11-03",
        result=f"ParadoxBench-1.1 Track A test MAE {r} (3-seed ensemble, fresh seeds 100-102; this file is seed 100)",
        improvement="climatology input removed (the v0.4 loss); beats v0.3 on PEMS08/04; best on PEMS04, PEMS07, METR-LA, PEMS-BAY vs re-run STID/Graph WaveNet/STAEformer",
        status="reported")
v07 = {"PEMS08": ("14.22", "18.09"), "PEMS04": ("18.53", "21.05"), "PEMS03": ("14.60", "18.39"), "PEMS07": ("19.78", "25.01"),
       "METR-LA": ("2.918", "3.147"), "PEMS-BAY": ("1.533", "1.959")}
for ds, (a, g) in v07.items():
    add(name=f"pwm-dyn-v0.7-{ds.lower()}", file=f"pwm-dyn_v0.7_{ds}", version="PWM-Dyn v0.7", family="PWM-Dyn",
        task="next 12 steps of traffic under sensor outages", datasets=[PEMS[ds]],
        source_run="Kaggle notebook8ffe55b5c8 (version 365414722), commit b0f6a08, 2026-11-04",
        source_glob=f"notebook8ffe55b5c8/repo/v0.7-realworld/models/{ds}/v07-s200/weights.pt", weights_key="", date="2026-11-04",
        result=f"ParadoxBench-1.2 test MAE clean {a}, real outages (Track G) {g} (3-seed ensemble; this file is seed 200)",
        improvement="fallback base + outage training: real-outage error -11 to -22% vs v0.6 on five networks; clean +0.4-1.8%",
        status="reported")

# ---- PWM-W: station world model for Delhi / India weather and air (Nov 5 - 9) --------------------------------
add(name="pwm-w-delhi-v0.1", file="pwm-w_delhi_v0.1_pm25", version="PWM-W Delhi v0.1", family="PWM-W",
    task="next 24 h of PM2.5, PM10, NO2, ozone at Delhi stations", datasets=[DELHI],
    source_run="Kaggle notebookce65e86211, 2026-11-05/06", source_glob="notebookce65e86211/out/pwm_w_delhi_v01.pt",
    weights_key="states[0]", extra_keys=["config", "targets", "stations", "cqr_delta"], date="2026-11-06",
    result="PM2.5 test MAE 32.63 (3 seeds); beats every simple baseline by 19-29%; loses to TimesFM 3.0 (29.95) and level with Chronos",
    improvement="first real-data world model (Delhi air)", status="reported")
add(name="pwm-w-delhi-v0.2", file="pwm-w_delhi_v0.2_pm25_hybrid", version="PWM-W Delhi v0.2", family="PWM-W",
    task="next 24 h of PM2.5 (hybrid: corrects Chronos-2 / TimesFM 2.5 with the station graph)", datasets=[DELHI, "Open-Meteo day-before weather forecasts"],
    source_run="Kaggle pwm-delhi-v02-pm25", source_glob="pwm-delhi-v02-pm25/out/pwm_w_delhi_v02.pt",
    weights_key="states[0]", extra_keys=["config", "targets", "stations", "cqr_delta"], date="2026-11-06",
    result="result in branch delhi-v0.2 README (not restated here)",
    improvement="long context (72 h + 14 daily means), day-ahead weather, hybrid on top of foundation models", status="see branch")
for ds, lab in (("cpcb", CPCBW), ("wmo", WMO)):
    add(name=f"pwm-w-weather-v0.3-{ds}", file=f"pwm-w_weather_v0.3_{ds}", version="PWM-W Weather v0.3 (league run)", family="PWM-W",
        task="next 24 h of temperature, humidity, wind at stations", datasets=[lab],
        source_run="Kaggle pwm-weather-league-gpu", source_glob=f"pwm-weather-league-gpu/out/pwm_w_weather_{ds}.pt",
        weights_key="states[0]", extra_keys=["stations"], date="2026-11-07",
        result="weather league against the global AI weather models; results in paper-weather (v0.3 section)",
        improvement="from air quality to weather; station-only world model vs global models", status="see paper")
for ds, lab in (("cpcb", CPCBW), ("wmo", WMO)):
    add(name=f"pwm-w-weather-v0.4-{ds}", file=f"pwm-w_weather_v0.4_{ds}", version="PWM-W Weather v0.4", family="PWM-W",
        task="next 24 h of temperature, humidity, wind", datasets=[lab], source_run="Kaggle pwm-weather-v04-gpu",
        source_glob=f"pwm-weather-v04-gpu/out/pwm_w_weather_{ds}.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-07",
        result="CPCB: pure model beats IFS 0.25, IFS 9 km and GFS on all three variables; loses to Chronos-2 by 6.0-8.3%"
        if ds == "cpcb" else "WMO league: see delhi-v0.4 README",
        improvement="learned-correction hybrid and the issued-before-start rule; METAR hybrid beats ECMWF AIFS (-4.4% temp)", status="reported")
add(name="pwm-w-weather-v0.5-metar", file="pwm-w_weather_v0.5_metar", version="PWM-W Weather v0.5", family="PWM-W",
    task="next 24 h of temperature, humidity, wind", datasets=[METAR], source_run="Kaggle pwm-weather-v05-metar",
    source_glob="pwm-weather-v05-metar/out/pwm_w_weather_metar.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-07",
    result="see branch delhi-v0.5 README", improvement="more global-model predictors for the correction (cloud, radiation, dew point, pressure, wind direction)",
    status="see branch")
add(name="pwm-w-weather-v0.6-cpcb", file="pwm-w_weather_v0.6_cpcb", version="PWM-W Weather v0.6", family="PWM-W",
    task="next 24 h of temperature, humidity, wind", datasets=[CPCBW, WMO + " (extra training)"], source_run="Kaggle pwm-weather-v06-cpcb",
    source_glob="pwm-weather-v06-cpcb/out/pwm_w_weather_cpcb.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-08",
    result="validation 0.4735 vs 0.4922 (about 5 sigma better); still trails Chronos-2 / TimesFM 3.0 by 4-7% on test",
    improvement="trains on the larger WMO network too", status="reported")
add(name="pwm-w-weather-v0.7-cpcb", file="pwm-w_weather_v0.7_cpcb", version="PWM-W Weather v0.7", family="PWM-W",
    task="next 24 h of temperature, humidity, wind", datasets=[CPCBW], source_run="Kaggle pwm-weather-v07-cpcb",
    source_glob="pwm-weather-v07-cpcb/out/pwm_w_weather_cpcb.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-08",
    result="rolling weekly updates NOT adopted (validation 0.4727 vs 0.4650); final model is v0.6's; hybrid ties all three foundation models",
    improvement="negative result, kept for the record", status="not adopted")
add(name="pwm-w-weather-v0.8-cpcb", file="pwm-w_weather_v0.8_cpcb", version="PWM-W Weather v0.8", family="PWM-W",
    task="next 24 h of temperature, humidity, wind", datasets=[CPCBW, WMO], source_run="Kaggle pwm-weather-v08-cpcb",
    source_glob="pwm-weather-v08-cpcb/out/pwm_w_weather_cpcb.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-08",
    result="validation 0.4678 (6.4 sigma better than P0); three losses to the foundation models became ties; wind still trails",
    improvement="14-day encoder + weight averaging", status="reported")
add(name="pwm-x-cpcb", file="pwm-x_v0.9_cpcb", version="PWM-X (v0.9)", family="PWM-W",
    task="next 24 h of temperature, humidity, wind", datasets=[CPCBW, WMO, METAR], source_run="Kaggle pwm-x-cpcb",
    source_glob="pwm-x-cpcb/out/pwm_w_weather_cpcb.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-09",
    result="data-threshold study: about 24 months of local history to stop losing to TimesFM/Chronos, about 48 to beat them",
    improvement="cross-network model; the data threshold measured", status="reported")
add(name="pwm-w-live-v0.9", file="pwm-w_live_v0.9", version="PWM-W v0.9 live", family="PWM-W",
    task="real-time 24 h forecasts for Indian stations", datasets=[CPCBW, WMO, METAR], source_run="Kaggle pwm-v09-live",
    source_glob="pwm-v09-live/out/live_models.pt", weights_key="states[0]", extra_keys=["stations", "trained_until_utc"], date="2026-11-09",
    result="live track (see paper-weather v0.9)", improvement="first real-time Indian forecasts", status="see paper")
for ds, lab in (("cpcb", CPCBW), ("metar", METAR), ("wmo", WMO)):
    add(name=f"pwm-w-v1.0-{ds}", file=f"pwm-w_v1.0_{ds}", version="PWM-W v1.0", family="PWM-W",
        task="next 24 h of temperature, humidity, wind", datasets=[lab], source_run="Kaggle pwm-v10",
        source_glob=f"pwm-v10/out/pwm_w_weather_{ds}.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-09",
        result="no result recorded in the delhi-v1.0 README", improvement="self-correction and a two-architecture ensemble (adopted only if >2 sigma better)",
        status="not recorded")
add(name="pwm-w-india-v2.0-cpcb", file="pwm-w_india_v2.0_cpcb", version="PWM-W India v2.0", family="PWM-W",
    task="next 24 h of temperature, humidity, wind", datasets=[CPCBW], source_run="Kaggle pwm-v20, 2026-11-09",
    source_glob="pwm-v20/out/pwm_w_weather_cpcb.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-09",
    result="validation 0.4597 (P10, chosen over the PWM-F variants 0.4620 / 0.4617)", improvement="kept PWM-X; PWM-F tested", status="reported")
add(name="pwm-f-encoder-v2.0", file="pwm-f_encoder_v2.0_10m", version="PWM-F encoder (India v2.0)", family="PWM-W",
    task="10M-parameter weather encoder pre-trained on all of India", datasets=["NOAA ISD, 187 Indian stations, 2015-01 to 2024-11"],
    source_run="Kaggle pwm-v20, 2026-11-09", source_glob="pwm-v20/out/fenc.pt", weights_key="state", extra_keys=["step", "val"], date="2026-11-09",
    result="held-out MAE 0.862 °C, 4.80 %RH, 0.578 m/s; not adopted for CPCB (validation 0.4620 vs 0.4597)", improvement="pre-training at 10M", status="not adopted")
add(name="pwm-f-encoder-v2.1", file="pwm-f_encoder_v2.1_10m", version="PWM-F encoder (v2.1 run)", family="PWM-W",
    task="10M-parameter weather encoder pre-trained on all of India", datasets=["NOAA ISD, Indian stations"],
    source_run="Kaggle pwm-v21", source_glob="pwm-v21/out/fenc.pt", weights_key="state", extra_keys=["step", "val"], date="2026-11-10",
    result="see branch india-v2.0", improvement="second pre-training run", status="see branch")

# ---- Atlas: station-graph world model (Nov 12 - 17) ----------------------------------------------------------
A = dict(family="Atlas", task="next 24 h of PM2.5 at stations")
add(name="atlas-delhi-v1.0", file="atlas_delhi_v1.0", version="Atlas-Delhi v1.0", datasets=[DELHI], source_run="Kaggle atlas-delhi v2, 2026-11-12",
    source_glob="atlas-delhi/out/atlas_delhi.pt", weights_key="states[0]", extra_keys=["stations", "cqr_delta"], date="2026-11-12",
    result="test MAE 33.42 / 29.07 (trained / unseen stations, 3 seeds); loses to TimesFM 2.5 (30.83, +8.4%)",
    improvement="Atlas architecture (learned station state, geometry attention, latent steps, quantile decoder)", status="reported", **A)
add(name="atlas-delhi-v1.1", file="atlas_delhi_v1.1", version="Atlas-Delhi v1.1", datasets=[DELHI + ", all history since 2018"],
    source_run="Kaggle atlas-long-s300, 2026-11-13", source_glob="atlas-long-s300/out/atlas_long_s300.pt", weights_key="B,C",
    extra_keys=["stations", "first"], date="2026-11-13", result="validation 20.807 vs 22.127 for the 16-month model: adopted",
    improvement="all of Delhi's history (19,082 windows)", status="adopted", **A)
add(name="atlas-delhi-v1.2", file="atlas_delhi_v1.2", version="Atlas-Delhi v1.2", datasets=[DELHI + ", all history since 2018"],
    source_run="Kaggle atlas-long2-a, 2026-11-13", source_glob="atlas-long2-a/out/atlas_long2_s310.pt", weights_key="E",
    extra_keys=["stations", "first"], date="2026-11-13", result="adopted on validation; not better than v1.1 on test (recorded honestly)",
    improvement="whole schedule, more seeds", status="adopted", **A)
add(name="atlas-india-v1.0", file="atlas_india_v1.0", version="Atlas-India v1.0", datasets=[INDIA],
    source_run="Kaggle atlas-india-s400, 2026-11-13", source_glob="atlas-india-s400/out/atlas_india_s400.pt", weights_key="E",
    extra_keys=["networks"], date="2026-11-13", result="all-India test MAE 20.99 / 20.86 vs TimesFM 2.5 22.35 / 21.93",
    improvement="one model for all of India (263 stations); beats TimesFM 2.5", status="reported", **A)
add(name="atlas-india-v1.3-pretrain", file="atlas_india_v1.3_pretrain", version="Atlas v1.3 (pre-training on 13 networks)", datasets=[INDIA + " (13 networks, Delhi left out)"],
    source_run="Kaggle atlas-v13-s320, 2026-11-13", source_glob="atlas-v13-s320/out/atlas_india13_s320.pt", weights_key="E",
    extra_keys=["networks", "meta"], date="2026-11-13", result="pooled validation 8.507 on the 13 networks", improvement="pre-training stage of v1.3", status="stage", **A)
add(name="atlas-delhi-v1.3", file="atlas_delhi_v1.3", version="Atlas-Delhi v1.3", datasets=[DELHI, INDIA + " (pre-training)"],
    source_run="Kaggle atlas-v13-s320, 2026-11-13", source_glob="atlas-v13-s320/out/atlas_long3_s320.pt", weights_key="B,C",
    extra_keys=["stations", "first"], date="2026-11-13", result="adopted; League v2.0 MAE 28.91 / 25.56, beats Moirai 2.0 (30.50) by 5.2%",
    improvement="pre-trained on the rest of India, then Delhi", status="adopted", **A)
add(name="atlas-w-v0", file="atlas-w_v0_14k", version="Atlas-W v0 (air core)", datasets=[DELHI], source_run="Kaggle atlasw-v0, 2026-11-13",
    source_glob="atlasw-v0/out/atlasw_v0.pt", weights_key="states[0]", extra_keys=["stations"], date="2026-11-13",
    result="14,043 parameters; 6-13% lower error than Atlas at every amount of data", improvement="information-efficient output-first design", status="reported", **A)
add(name="atlas-w-v1-pretrain", file="atlas-w_v1_pretrain", version="Atlas-W v1 (pre-training)", datasets=[INDIA + " (13 networks)"],
    source_run="Kaggle atlasw-v13-s320, 2026-11-13", source_glob="atlasw-v13-s320/out/atlas_windia13_s320.pt", weights_key="E",
    extra_keys=["networks", "meta"], date="2026-11-13", result="pooled validation 8.83-8.86", improvement="Atlas-W trained the v1.3 way", status="stage", **A)
add(name="atlas-w-v1-delhi", file="atlas-w_v1_delhi", version="Atlas-W v1 (Delhi)", datasets=[DELHI],
    source_run="Kaggle atlasw-v13-s320, 2026-11-13", source_glob="atlasw-v13-s320/out/atlas_wlong3_s320.pt", weights_key="B,C",
    extra_keys=["stations", "first"], date="2026-11-13", result="see League v2.0 (Atlas-W day 2 results)", improvement="small model at v1.3 recipe", status="reported", **A)
add(name="atlas-delhi-i1", file="atlas_delhi_i1", version="Atlas-Delhi I1 (operational comparison)", datasets=[DELHI + ", winter 2024-25"],
    source_run="Kaggle atlas-i1-s320, 2026-11-15", source_glob="atlas-i1-s320/out/atlas_i1_s320.pt", weights_key="B,C",
    extra_keys=["stations", "first"], date="2026-11-15", result="Delhi winter 2024-25 MAE 31.27 (stage C, 3 seeds); IITM WRF-Chem 58.75 / IMD SILAM 71.68 published (by number)",
    improvement="evaluated against India's operational forecasts", status="reported", **A)
add(name="atlas-v1.4n", file="atlas_v1.4n", version="Atlas v1.4n (neighbours only)", datasets=[INDIA], source_run="Kaggle atlas-v14n-s400, 2026-11-15",
    source_glob="atlas-v14n-s400/out/atlas_v14n_s400.pt", weights_key="E", extra_keys=["networks"], date="2026-11-15",
    result="validation 9.106 vs 9.104: not adopted", improvement="architecture test (negative)", status="not adopted", **A)
add(name="atlas-p", file="atlas-p_physics_decoder", version="Atlas-P (physics decoder)", datasets=[INDIA], source_run="Kaggle atlas-indiap-s400, 2026-11-15",
    source_glob="atlas-indiap-s400/out/atlas_indiap_s400.pt", weights_key="E", extra_keys=["networks"], date="2026-11-15",
    result="validation 9.227 vs 9.104: not adopted", improvement="physics decoder test (negative)", status="not adopted", **A)
add(name="atlas-scale-3m", file="atlas_scale_3m", version="Atlas S2 (3M parameters)", datasets=[INDIA], source_run="Kaggle atlas-scale3m-s400, 2026-11-15",
    source_glob="atlas-scale3m-s400/out/atlas_scale3m_s400.pt", weights_key="E", extra_keys=["networks"], date="2026-11-15",
    result="validation 9.139 (+0.38% vs 1M): not adopted", improvement="parameter ladder", status="not adopted", **A)
add(name="atlas-scale-10m", file="atlas_scale_10m", version="Atlas S3 (10M parameters)", datasets=[INDIA], source_run="Kaggle atlas-scale10m-s400, 2026-11-15",
    source_glob="atlas-scale10m-s400/out/atlas_scale10m_s400.pt", weights_key="E", extra_keys=["networks"], date="2026-11-15",
    result="validation 9.222 (+1.30% vs 1M): not adopted", improvement="parameter ladder: more parameters did not help", status="not adopted", **A)
add(name="atlas-w1", file="atlas_w1_weather", version="Atlas W1 (1M + weather)", datasets=[INDIA, ERA5], source_run="Kaggle atlas-w1-s400, 2026-11-16",
    source_glob="atlas-w1-s400/out/atlas_w1_s400.pt", weights_key="E", extra_keys=["networks"], date="2026-11-16",
    result="validation 8.684 (-4.61%): adopted; all-India test 19.86 / 19.92 with ERA5 weather (upper bound) vs TimesFM 2.5 22.35 / 21.93",
    improvement="weather forcing", status="adopted", **A)
add(name="atlas-w10", file="atlas_w10_weather_10m", version="Atlas W10 (10M + weather)", datasets=[INDIA, ERA5], source_run="Kaggle atlas-w10-s400, 2026-11-16",
    source_glob="atlas-w10-s400/out/atlas_w10_s400.pt", weights_key="E", extra_keys=["networks"], date="2026-11-16",
    result="validation 8.773 (+1.02% vs W1): not adopted", improvement="10M with weather (negative)", status="not adopted", **A)
add(name="atlas-w10r", file="atlas_w10r_weather_10m_reg", version="Atlas W10r (10M + weather, regularised)", datasets=[INDIA, ERA5],
    source_run="Kaggle atlas-w10r-s400, 2026-11-16", source_glob="atlas-w10r-s400/out/atlas_w10r_s400.pt", weights_key="E", extra_keys=["networks"],
    date="2026-11-16", result="validation 8.825 (+1.62% vs W1): not adopted", improvement="regularised 10M (negative)", status="not adopted", **A)
add(name="atlas-w-delhi-tb", file="atlas-w_delhi_real_forecasts", version="Atlas-W Delhi (T-B, real forecasts)", datasets=[DELHI, "ECMWF day-before forecasts (Open-Meteo previous runs)"],
    source_run="Kaggle atlas-tb-s320, 2026-11-16", source_glob="atlas-tb-s320/out/atlas_wi1_s320.pt", weights_key="B,C", extra_keys=["stations", "first"],
    date="2026-11-16", result="Delhi winter 2024-25 MAE 28.19 vs 31.27 for the no-weather Atlas (-9.85%, p = 0.0009; stage B, 3 seeds)",
    improvement="weather gain holds with real forecasts", status="reported", **A)
W = dict(family="Atlas", task="next 24 h of temperature, dew point, wind direction, wind speed, sea-level pressure at stations")
add(name="atlas-5k-v1", file="atlas-5k_v1_weather5k", version="Atlas-5K v1", datasets=[W5K], source_run="Kaggle atlas-w5k-atlas1m-h24, 2026-11-16",
    source_glob="atlas-w5k-atlas1m-h24/out/w5k_atlas_1m_h24_s600.pt", weights_key="sd", date="2026-11-16",
    result="WEATHER-5K test 2023 MAE: T 1.553, Td 1.596, WS 1.228, WD 56.46, SLP 1.664; level with PhysicsFormer (19.3M) on T/Td; beats neither under the pre-registered rules",
    improvement="world benchmark entry", status="reported", **W)
add(name="atlas-5k-v2a", file="atlas-5k_v2a_weather5k", version="Atlas-5K v2a", datasets=[W5K], source_run="Kaggle atlas-w5k-v2a, 2026-11-16",
    source_glob="atlas-w5k-v2a/out/w5k_atlas_1m_h24_v2a_s600.pt", weights_key="sd", date="2026-11-16",
    result="validation E 0.28869 vs 0.29292 (-1.44%); not yet tested", improvement="150,000 training steps", status="validation only", **W)

plan = {"models": M, "commit_message": "Model series: every saved PWM model version with its dataset inside the file\n\n"
        "Built and verified on Kaggle (atlas-model-series): one file per version and dataset, the reported weights only,\n"
        "with a meta block (series number, name, version, family, task, datasets, parameters, result, source run and the\n"
        "source file's SHA-256). Index: models/series/README.md, SERIES.json, SHA256SUMS.\n\n"
        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
        "Claude-Session: https://claude.ai/code/session_01TCvEAwgYb9HyrCaEGd5YWa"}
json.dump(plan, open(os.path.join(HERE, "series_plan.json"), "w"), indent=1, ensure_ascii=False)
print(len(M), "models in the plan")
