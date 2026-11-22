"""Atlas-Delhi live log (PREREG_DELHI.md, part B): every run saves, with the time it was fetched,
  1. IMD's official city forecasts for Delhi stations (7 days of max / min temperature and weather, e.g. fog), and the
     past-24-hour observations IMD prints on the same page (city.imd.gov.in, public pages, no account);
  2. the latest forecast of every global system Open-Meteo serves, at the same stations (hourly, 3 days);
  3. METAR reports from the Delhi airports for the past 2 days (Iowa Environmental Mesonet ASOS archive);
  4. Delhi living twin layers: CAMS air-quality forecasts at six CPCB / DPCC station positions, and (morning run)
     yesterday's Delhi SLDC electricity load curve for Delhi and each discom.
Each file is committed by GitHub Actions the moment it is fetched, so the git history proves what every forecaster had
said before the weather happened. That is the only fair way to score IMD, which keeps no public forecast archive.

  python atlas/delhi_live/log_live.py --out delhi_live
Standard library only. Never stores keys; IMD pages are kept as parsed numbers, the page text and its SHA-256.
"""
import argparse, datetime as dt, hashlib, html, json, os, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "ParadoxAI-Lab-research-log (contact.paradoxailab@gmail.com)"}
IMD = {"42182": "New Delhi-Safdarjung", "42181": "New Delhi-Palam", "42184": "New Delhi-Ridge", "99923": "New Delhi-Lodi Road"}
IMD_URL = "https://city.imd.gov.in/citywx/citywxnew.php?id={}"
POINTS = {"Safdarjung": (28.5845, 77.2058), "Palam": (28.5665, 77.1031)}        # = WEATHER-5K / ISD station positions
OM_URL = "https://api.open-meteo.com/v1/forecast"
OM_MODELS = ["best_match", "ecmwf_ifs025", "ecmwf_ifs", "ecmwf_aifs025_single", "gfs_global", "gfs_graphcast025", "ncep_aigfs025",
             "icon_global", "ukmo_global_deterministic_10km", "meteofrance_arpege_world", "jma_gsm", "cma_grapes_global", "gem_global"]
OM_HOURLY = ["temperature_2m", "dew_point_2m", "relative_humidity_2m", "wind_speed_10m", "wind_direction_10m", "pressure_msl",
             "precipitation", "visibility", "cloud_cover"]
OM_DAILY = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"]
# Delhi living twin, layer 2 (air quality): CAMS forecasts (Copernicus, via Open-Meteo's air-quality API, no account)
# at CPCB / DPCC station positions; the observed truth comes later from CPCB archives (OpenAQ / data.gov.in)
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
AQ_POINTS = {"Anand Vihar": (28.6469, 77.3159), "ITO": (28.6286, 77.2410), "Punjabi Bagh": (28.6740, 77.1310),
             "RK Puram": (28.5632, 77.1869), "Safdarjung": (28.5845, 77.2058), "Dwarka": (28.5708, 77.0717)}
AQ_HOURLY = ["pm2_5", "pm10", "nitrogen_dioxide", "ozone", "carbon_monoxide", "sulphur_dioxide", "aerosol_optical_depth", "dust"]
# layer 3 (electricity): Delhi SLDC load curve for yesterday (public page, Delhi and each discom)
SLDC_URL = "https://www.delhisldc.org/Loaddata.aspx?mode={}"
METAR = ["VIDP", "VIDD", "VIDX"]
# Keyed sources: keys come ONLY from environment variables (GitHub Actions / Colab secrets set by the lab owner); they
# are never written to any file, log or error message. A source whose key is missing is skipped.
KEYS = {k: os.environ.get(k, "").strip() for k in ("OPENAQ_API_KEY", "DATAGOV_API_KEY", "OTD_API_KEY")}
OPENAQ = "https://api.openaq.org/v3"
DATAGOV_AQ = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"   # CPCB real-time AQ, all stations
OTD_VP = "https://otd.delhi.gov.in/api/realtime/VehiclePositions.pb"


def scrub(msg):
    for v in KEYS.values():
        if v:
            msg = msg.replace(v, "***")
    return msg                                                   # Palam, Safdarjung, Hindon
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"


def get(url, tries=4, timeout=60):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:
            err = str(e)[:200]
            time.sleep(5 * (k + 1))
    raise RuntimeError(err)


def text(b):
    s = b.decode("utf-8", "replace")
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</(tr|p|div|h\d)>", "\n", s)
    s = re.sub(r"(?i)</t[dh]>", " | ", s)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return "\n".join(re.sub(r"[ \t\xa0]+", " ", l).strip() for l in s.splitlines() if l.strip())


def parse_imd(t):
    """IMD city page text -> 7-day forecast rows and the past-24-hour observations (cells are separated by '|')."""
    f = re.sub(r"\s*\n\s*", " ", t)                                          # one line: rows may span lines
    num = lambda x: None if x is None or x.strip().upper() in ("NA", "") else float(x)
    rows = []
    for m in re.finditer(r"(\d{1,2}-[A-Z][a-z]{2}) \| ([\d.]+|NA) \| ([\d.]+|NA) \|((?: [^|]*\|){0,2})", f):
        cells = [c.strip() for c in m.group(4).split("|") if c.strip()]          # an icon cell may come first
        rows.append(dict(date=m.group(1), tmin=num(m.group(2)), tmax=num(m.group(3)), weather=cells[-1] if cells else ""))
    def obs(label):
        m = re.search(re.escape(label) + r"[^|]*\|\s*([\d.]+|NA|NIL)", f, re.I)
        return None if not m else m.group(1)
    def rec(label):
        m = re.search(re.escape(label) + r"[^|]*?Recorded\.? on (\d{2}/\d{2}/\d{2})", f, re.I)
        return None if not m else m.group(1)
    dated = re.search(r"Dated\s*:?\s*([A-Z][a-z]{2} \d{1,2}, \d{4})", f)
    observed = dict(max_temp=obs("Maximum Temp"), max_recorded_on=rec("Maximum Temp"), min_temp=obs("Minimum Temp"),
                    min_recorded_on=rec("Minimum Temp"), rain_24h=obs("24 Hours Rainfall"), rh_0830=obs("R.H. at 0830"),
                    rh_1730=obs("R.H. at 1730"))
    return rows[:7], observed, dated.group(1) if dated else None


def imd(sid):
    b = get(IMD_URL.format(sid))
    t = text(b)
    rows, observed, dated = parse_imd(t)
    return dict(station=sid, name=IMD[sid], url=IMD_URL.format(sid), sha256=hashlib.sha256(b).hexdigest(),
                dated=dated, forecast=rows, observed=observed, parsed_ok=len(rows) >= 5, text=t[:6000])


def openmeteo(model, la, lo):
    q = dict(latitude=la, longitude=lo, hourly=",".join(OM_HOURLY), daily=",".join(OM_DAILY), models=model,
             forecast_days=3, past_days=1, timezone="Asia/Kolkata", wind_speed_unit="ms")
    j = json.loads(get(OM_URL + "?" + urllib.parse.urlencode(q)))
    return j


def airquality(la, lo):
    q = dict(latitude=la, longitude=lo, hourly=",".join(AQ_HOURLY), forecast_days=4, past_days=1, timezone="Asia/Kolkata",
             domains="cams_global")
    return json.loads(get(AQ_URL + "?" + urllib.parse.urlencode(q)))


def sldc(day):
    b = get(SLDC_URL.format(day.strftime("%d/%m/%Y")), tries=1, timeout=45)  # timed out from GitHub's US runners (22 Nov)
    t = text(b)
    rows = re.findall(r"(\d{2}:\d{2})((?:\s*\|\s*[\d.]+){3,})", re.sub(r"\s*\n\s*", " ", t))
    table = [[r[0]] + [float(x) for x in re.findall(r"[\d.]+", r[1])] for r in rows]
    head = re.search(r"TIMESLOT[^\n]{0,200}", t, re.I)
    return dict(date=day.isoformat(), url=SLDC_URL.format(day.strftime("%d/%m/%Y")), sha256=hashlib.sha256(b).hexdigest(),
                header=head.group(0) if head else None, rows=table, parsed_ok=len(table) >= 200, text=t[:3000] if len(table) < 200 else "")


def openaq_delhi():
    """Latest readings of every OpenAQ location within 25 km of central Delhi (CPCB / DPCC and others)."""
    h = {"X-API-Key": KEYS["OPENAQ_API_KEY"], **UA}
    def j(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
            return json.loads(r.read())
    locs = j(f"{OPENAQ}/locations?coordinates=28.6139,77.2090&radius=25000&limit=1000")["results"]
    out = []
    for L in locs:
        try:
            out.append(dict(location=L, latest=j(f"{OPENAQ}/locations/{L['id']}/latest")["results"]))
        except Exception as e:
            out.append(dict(location=L, error=scrub(str(e))[:200]))
        time.sleep(0.3)
    return out


def datagov_delhi():
    q = dict(format="json", limit=2000, **{"filters[state]": "Delhi"})
    url = DATAGOV_AQ + "?" + urllib.parse.urlencode(dict(q, **{"api-key": KEYS["DATAGOV_API_KEY"]}))
    j = json.loads(get(url))
    j.pop("api_key", None)
    return j


def otd_positions():
    return get(OTD_VP + "?" + urllib.parse.urlencode({"key": KEYS["OTD_API_KEY"]}), timeout=60)


def metar(station, now):
    a = now - dt.timedelta(days=2)
    q = dict(station=station, data="all", year1=a.year, month1=a.month, day1=a.day, year2=now.year, month2=now.month,
             day2=now.day, tz="Etc/UTC", format="onlycomma", latlon="no", missing="M", trace="T", direct="no", report_type="3,4")
    return get(IEM + "?" + urllib.parse.urlencode(q), timeout=120).decode("utf-8", "replace")


def main(a):
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    d = os.path.join(a.out, now.strftime("%Y/%m/%d"), now.strftime("%H%M"))
    os.makedirs(d, exist_ok=True)
    log = dict(fetched_utc=now.isoformat(), ok={}, errors={})
    for sid in IMD:
        try:
            r = imd(sid); json.dump(r, open(os.path.join(d, f"imd_{sid}.json"), "w"), indent=1)
            log["ok"][f"imd_{sid}"] = r["parsed_ok"]
        except Exception as e:
            log["errors"][f"imd_{sid}"] = str(e)[:300]
    for name, (la, lo) in POINTS.items():
        for m in OM_MODELS:
            try:
                j = openmeteo(m, la, lo)
                json.dump(j, open(os.path.join(d, f"om_{name}_{m}.json"), "w"))
                log["ok"][f"om_{name}_{m}"] = True
            except Exception as e:
                log["errors"][f"om_{name}_{m}"] = str(e)[:300]
    for name, (la, lo) in AQ_POINTS.items():
        try:
            json.dump(airquality(la, lo), open(os.path.join(d, f"aq_cams_{name.replace(' ', '_')}.json"), "w"))
            log["ok"][f"aq_{name}"] = True
        except Exception as e:
            log["errors"][f"aq_{name}"] = str(e)[:300]
    if now.hour < 6 or os.environ.get("FORCE_SLDC") == "true":                # once a day: yesterday's load curve (IST)
        y = (now + dt.timedelta(hours=5, minutes=30)).date() - dt.timedelta(days=1)
        try:
            r = sldc(y); json.dump(r, open(os.path.join(d, "sldc_load.json"), "w"), indent=0); log["ok"]["sldc"] = r["parsed_ok"]
        except Exception as e:
            log["errors"]["sldc"] = str(e)[:300]
    for name, need, fn, ext in (("openaq_delhi", "OPENAQ_API_KEY", openaq_delhi, "json"),
                                ("cpcb_datagov_delhi", "DATAGOV_API_KEY", datagov_delhi, "json"),
                                ("otd_vehicle_positions", "OTD_API_KEY", otd_positions, "pb")):
        if not KEYS[need]:
            log["errors"][name] = f"skipped: {need} not set"; continue
        try:
            r = fn(); fn_out = os.path.join(d, f"{name}.{ext}")
            open(fn_out, "wb").write(r) if ext == "pb" else json.dump(r, open(fn_out, "w"))
            log["ok"][name] = True
        except Exception as e:
            log["errors"][name] = scrub(str(e))[:300]
    for s in METAR:
        try:
            open(os.path.join(d, f"metar_{s}.csv"), "w").write(metar(s, now)); log["ok"][f"metar_{s}"] = True
        except Exception as e:
            log["errors"][f"metar_{s}"] = scrub(str(e))[:300]
    json.dump(log, open(os.path.join(d, "log.json"), "w"), indent=1)
    print(json.dumps(dict(dir=d, ok=sum(bool(v) for v in log["ok"].values()), errors=len(log["errors"]),
                          error_keys=list(log["errors"])[:20])), flush=True)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="delhi_live")
    sys.exit(main(ap.parse_args()))
