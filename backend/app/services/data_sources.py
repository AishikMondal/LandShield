from __future__ import annotations
import asyncio
import math
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Awaitable, Callable

import httpx

from ..config import (
    ASSET_QUERY_RADIUS_M,
    CACHE_TTL_SECONDS,
    OPENWEATHER_API_KEY,
    OVERPASS_ENDPOINTS,
    OVERVIEW_OVERALL_TIMEOUT,
    USER_AGENT,
    HTTP_TIMEOUT_SECONDS,
    HTTP_RETRIES,
)

# ---------------------------------------------------------------------------
# Small TTL cache. Keys are (kind, rounded lat/lon, extra).
# ---------------------------------------------------------------------------
_CACHE: dict[str, tuple[float, Any]] = {}

# Mirrors that recently answered (or failed) this process; avoids re-hitting
# dead public Overpass instances on every call. Both maps use time.monotonic().
_OVERPASS_GOOD: dict[str, float] = {}
_OVERPASS_BAD: dict[str, float] = {}
_MIRROR_MEMO_TTL = 300.0  # seconds
_MIRROR_BLACKLIST_TTL = 30.0  # seconds


def _cache_key(kind: str, lat: float, lon: float, extra: str = "") -> str:
    return f"{kind}|{lat:.4f}|{lon:.4f}|{extra}"


def _cached(key: str, ttl: int, coro: Callable[[], Awaitable[Any]]) -> Awaitable[Any]:
    async def _run():
        hit = _CACHE.get(key)
        now = time.monotonic()
        if hit and (now - hit[0]) < ttl:
            return hit[1]
        value = await coro()
        _CACHE[key] = (now, value)
        return value

    return _run()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _past_days_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")


def _fmt(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# HTTP helper with retries
# ---------------------------------------------------------------------------
async def _request(
    method: str,
    url: str,
    *,
    params: dict | None = None,
    data: dict | None = None,
    headers: dict | None = None,
    timeout: float | None = None,
    retries: int | None = None,
) -> httpx.Response:
    timeout = timeout or HTTP_TIMEOUT_SECONDS
    retries = HTTP_RETRIES if retries is None else retries
    last: Exception | None = None
    async with httpx.AsyncClient(timeout=timeout, headers=headers, http2=False) as client:
        for attempt in range(retries + 1):
            try:
                if method.upper() == "GET":
                    r = await client.get(url, params=params)
                else:
                    r = await client.post(url, params=params, data=data)
                if r.status_code == 429 and attempt < retries:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                r.raise_for_status()
                return r
            except Exception as e:  # noqa: BLE001 - network/timeout retry
                last = e
                if attempt < retries:
                    await asyncio.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"Request failed after {retries + 1} attempts: {type(last).__name__}") from last


# ---------------------------------------------------------------------------
# Weather — Open-Meteo primary, NASA POWER secondary, OpenWeather optional
# ---------------------------------------------------------------------------
async def fetch_weather(lat: float, lon: float) -> dict | None:
    try:
        return await _cached(_cache_key("weather", lat, lon), CACHE_TTL_SECONDS["weather"], lambda: _open_meteo_weather(lat, lon))
    except Exception:
        pass
    try:
        return await _cached(_cache_key("nasa", lat, lon), CACHE_TTL_SECONDS["nasa"], lambda: _nasa_power(lat, lon))
    except Exception:
        pass
    return None


async def _open_meteo_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code",
        "hourly": "precipitation,soil_moisture_0_to_1cm,soil_temperature_0cm,relative_humidity_2m,temperature_2m",
        "daily": "precipitation_sum",
        "past_days": 7,
        "forecast_days": 1,
        "timezone": "auto",
    }
    r = await _request("GET", "https://api.open-meteo.com/v1/forecast", params=params)
    data = r.json()
    current = data.get("current", {})
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    idx = max(0, len(times) - 1)
    current_time = current.get("time")
    if current_time and times:
        try:
            idx = min(range(len(times)), key=lambda i: abs(_iso_to_epoch(times[i]) - _iso_to_epoch(current_time)))
        except Exception:
            idx = max(0, len(times) - 1)

    precip = hourly.get("precipitation", [])

    def rolling_sum(hours: int) -> float:
        if not precip:
            return 0.0
        start = max(0, idx - hours + 1)
        return float(sum((v or 0) for v in precip[start:idx + 1]))

    def hv(name: str):
        values = hourly.get(name, [])
        if idx < len(values) and values[idx] is not None:
            return float(values[idx])
        return None

    sources = {
        "rainfall_24h_mm": "Open-Meteo",
        "rainfall_3d_mm": "Open-Meteo",
        "rainfall_7d_mm": "Open-Meteo",
        "temperature_c": "Open-Meteo",
        "humidity_percent": "Open-Meteo",
        "soil_moisture_fraction": "Open-Meteo",
        "soil_temperature_c": "Open-Meteo",
    }
    # If a fresher OpenWeather key exists, cross-validate current temp/humidity.
    if OPENWEATHER_API_KEY:
        try:
            ow = await _openweather_current(lat, lon)
            if ow and ow.get("temperature_c") is not None:
                current["temperature_2m"] = ow["temperature_c"]
                sources["temperature_c"] = "OpenWeather"
            if ow and ow.get("humidity_percent") is not None:
                current["relative_humidity_2m"] = ow["humidity_percent"]
                sources["humidity_percent"] = "OpenWeather"
            if ow and ow.get("rain_1h_mm") is not None:
                sources["rainfall_24h_mm"] = f"Open-Meteo+OpenWeather(cross-check rain={ow['rain_1h_mm']}mm)"
        except Exception:
            pass

    return {
        "temperature_c": _fmt(current.get("temperature_2m")),
        "humidity_percent": _fmt(current.get("relative_humidity_2m")),
        "rainfall_24h_mm": rolling_sum(24),
        "rainfall_3d_mm": rolling_sum(72),
        "rainfall_7d_mm": rolling_sum(168),
        "soil_moisture_fraction": hv("soil_moisture_0_to_1cm"),
        "soil_temperature_c": hv("soil_temperature_0cm"),
        "observed_at": current_time or _now_iso(),
        "data_source": "Open-Meteo",
        "source_type": "LIVE_API",
        "sources": sources,
    }


async def _openweather_current(lat: float, lon: float) -> dict | None:
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    r = await _request("GET", "https://api.openweathermap.org/data/2.5/weather", params=params, timeout=6)
    d = r.json()
    rain1h = (d.get("rain") or {}).get("1h")
    return {
        "temperature_c": _fmt(d.get("main", {}).get("temp")),
        "humidity_percent": _fmt(d.get("main", {}).get("humidity")),
        "rain_1h_mm": _fmt(rain1h),
        "observed_at": _now_iso(),
    }


async def _nasa_power(lat: float, lon: float) -> dict:
    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M",
        "community": "ag",
        "longitude": round(lon, 2),
        "latitude": round(lat, 2),
        "start": _past_days_iso(8),
        "end": _past_days_iso(0),
        "format": "JSON",
    }
    r = await _request("GET", "https://power.larc.nasa.gov/api/temporal/daily/point", params=params, timeout=15)
    d = r.json()
    daily = d.get("properties", {}).get("parameter", {})
    t2m = daily.get("T2M") or {}
    pre = daily.get("PRECTOTCORR") or {}
    rh = daily.get("RH2M") or {}
    days = sorted(k for k in t2m.keys() if isinstance(k, str) and k.startswith("20"))
    last3 = days[-3:] if len(days) >= 3 else days
    try:
        temp = _fmt(t2m.get(days[-1]))
        hum = _fmt(rh.get(days[-1]))
    except Exception:
        temp = hum = None
    daily_precip = {}
    for i, day in enumerate(last3):
        cur = pre.get(day)
        if i == 0:
            daily_precip[day] = _fmt(cur)
        else:
            prev = pre.get(last3[i - 1])
            daily_precip[day] = _fmt(cur - prev) if (cur is not None and prev is not None) else None
    mm_vals = [v for v in daily_precip.values() if v is not None]
    return {
        "temperature_c": temp,
        "humidity_percent": hum,
        "rainfall_24h_mm": mm_vals[-1] if mm_vals else None,
        "rainfall_3d_mm": sum(mm_vals[-3:]) if mm_vals else None,
        "rainfall_7d_mm": None,
        "soil_moisture_fraction": None,
        "soil_temperature_c": None,
        "observed_at": days[-1] if days else _now_iso(),
        "data_source": "NASA POWER (secondary/fallback)",
        "source_type": "LIVE_API",
        "sources": {},
        "is_fallback": True,
    }


# ---------------------------------------------------------------------------
# Terrain — Open-Meteo DEM + local slope/aspect derivation
# ---------------------------------------------------------------------------
async def fetch_elevation_and_terrain(lat: float, lon: float) -> dict | None:
    try:
        return await _cached(_cache_key("terrain", lat, lon), CACHE_TTL_SECONDS["terrain"], lambda: _open_meteo_dem(lat, lon))
    except Exception:
        return None


async def _open_meteo_dem(lat: float, lon: float) -> dict:
    step = 0.001
    points = [(lat, lon), (lat + step, lon), (lat - step, lon), (lat, lon + step), (lat, lon - step)]
    params = {
        "latitude": ",".join(f"{p[0]:.5f}" for p in points),
        "longitude": ",".join(f"{p[1]:.5f}" for p in points),
    }
    r = await _request("GET", "https://api.open-meteo.com/v1/elevation", params=params)
    data = r.json()
    elevations = data.get("elevation", [])
    if len(elevations) < 5:
        raise RuntimeError("Elevation service returned insufficient samples")
    center, north, south, east, west = map(float, elevations[:5])
    dy = 111_320 * step
    dx = 111_320 * math.cos(math.radians(lat)) * step
    dzdx = (east - west) / (2 * dx) if dx else 0.0
    dzdy = (north - south) / (2 * dy) if dy else 0.0
    slope = math.degrees(math.atan(math.sqrt(dzdx * dzdx + dzdy * dzdy)))
    aspect = (math.degrees(math.atan2(dzdx, -dzdy)) + 360) % 360
    return {
        "elevation_m": center,
        "slope_deg": slope,
        "aspect_deg": aspect,
        "source": "Copernicus DEM via Open-Meteo elevation service",
        "source_type": "DEM_DERIVED",
        "observed_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Reverse geocoding — Nominatim (cached, gracefully degrades)
# ---------------------------------------------------------------------------
async def reverse_geocode(lat: float, lon: float) -> dict:
    try:
        return await _cached(_cache_key("geocode", lat, lon), CACHE_TTL_SECONDS["geocode"], lambda: _nominatim_reverse(lat, lon))
    except Exception:
        return _fallback_location(lat, lon)


async def _nominatim_reverse(lat: float, lon: float) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    params = {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 12, "addressdetails": 1, "accept-language": "en"}
    r = await _request("GET", "https://nominatim.openstreetmap.org/reverse", params=params, headers=headers, timeout=max(8, HTTP_TIMEOUT_SECONDS))
    d = r.json()
    a = d.get("address", {})
    return {
        "display_name": d.get("display_name") or "Selected location",
        "district": a.get("state_district") or a.get("county") or a.get("district"),
        "state": a.get("state"),
        "country": a.get("country"),
        "country_code": a.get("country_code"),
        "source": "Nominatim",
        "source_type": "LIVE_API",
        "observed_at": _now_iso(),
    }


def _fallback_location(lat: float, lon: float) -> dict:
    from ..ner import state_for  # local import to avoid a cycle at import time

    return {
        "display_name": "Selected location",
        "district": None,
        "state": state_for(lat, lon),
        "country": "India" if state_for(lat, lon) else None,
        "source": "NER_BOUNDS",
        "source_type": "DERIVED",
        "observed_at": _now_iso(),
    }


# ---------------------------------------------------------------------------
# OSM / Overpass — nearby infrastructure, water, land use
# ---------------------------------------------------------------------------
async def fetch_surroundings(lat: float, lon: float, radius_m: int | None = None) -> dict:
    radius_m = max(500, min(radius_m or ASSET_QUERY_RADIUS_M, 7000))
    try:
        return await _cached(
            _cache_key("osm", lat, lon, str(radius_m)),
            CACHE_TTL_SECONDS["osm"],
            lambda: asyncio.wait_for(_overpass_surroundings(lat, lon, radius_m), timeout=OVERVIEW_OVERALL_TIMEOUT),
        )
    except Exception:
        return {"assets": [], "water_distance_m": None, "landuse": None, "source": "UNAVAILABLE", "error": True}


async def _overpass(url: str, query: str) -> dict:
    r = await _request("POST", url, data={"data": query}, timeout=15, retries=0)
    return r.json()


async def _overpass_surroundings(lat: float, lon: float, radius_m: int) -> dict:
    q = f"""[out:json][timeout:15];
( nwr(around:{radius_m},{lat:.5f},{lon:.5f})[amenity~"hospital|clinic|school|college|fire_station|police|pharmacy|doctors|community_centre"];
  nwr(around:{radius_m},{lat:.5f},{lon:.5f})[place~"village|town|hamlet|suburb|neighbourhood"];
  nwr(around:{radius_m},{lat:.5f},{lon:.5f})[highway~"motorway|trunk|primary|secondary|tertiary|unclassified|residential|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link"];
  nwr(around:{radius_m},{lat:.5f},{lon:.5f})[landuse~"residential|industrial|commercial|forest|farmland|farmyard|meadow|grass"];
); out center tags 150;"""
    # Some public mirrors only host regional extracts (e.g. Switzerland) and
    # return an empty set for NER coordinates. Only a response that actually
    # contains elements counts as success; otherwise we would falsely report
    # "no roads here". Single attempt per mirror, short timeout, memoised.
    def _ordered_endpoints():
        now = time.monotonic()
        good = [u for u, ts in _OVERPASS_GOOD.items() if now - ts < _MIRROR_MEMO_TTL]
        bad = {u for u, ts in _OVERPASS_BAD.items() if now - ts < _MIRROR_BLACKLIST_TTL}
        rest = [u for u in OVERPASS_ENDPOINTS if u not in good and u not in bad]
        return good + rest

    chosen: dict | None = None
    for endpoint in _ordered_endpoints():
        try:
            data = await _overpass(endpoint, q)
            if not isinstance(data, dict) or not data.get("elements"):
                continue
            chosen = data
            _OVERPASS_GOOD[endpoint] = time.monotonic()
            break
        except Exception:  # noqa: BLE001 - try next mirror
            _OVERPASS_BAD[endpoint] = time.monotonic()
            continue
    if chosen is None:
        raise RuntimeError("No Overpass endpoint returned usable data")
    return await asyncio.to_thread(lambda: _parse_overpass(chosen, lat, lon))


def _classify(tags: dict) -> str:
    amenity = tags.get("amenity")
    if amenity:
        return {
            "hospital": "hospital",
            "clinic": "clinic",
            "school": "school",
            "college": "school",
            "fire_station": "fire_station",
            "police": "police",
            "pharmacy": "clinic",
            "doctors": "clinic",
            "community_centre": "public_building",
        }.get(amenity, "emergency")
    if tags.get("place"):
        return "settlement"
    if tags.get("bridge"):
        return "bridge"
    if tags.get("highway"):
        return "road"
    return "feature"


def _asset_name(tags: dict, kind: str) -> str:
    name = tags.get("name") or tags.get("ref") or ""
    if kind == "road":
        ref = tags.get("ref") or ""
        highway = tags.get("highway", "")
        label = (ref or (tags.get("name") or highway.replace("_", " ").title()))
        return f"{label} ({highway.replace('_', ' ').title()})" if highway and ref else label
    if name:
        return name
    return kind.replace("_", " ").title()


def _parse_overpass(data: dict, lat: float, lon: float) -> dict:
    assets: list[dict] = []
    water_distance: float | None = None
    landuse_counts: dict[str, int] = {}

    for el in data.get("elements", []):
        tags = el.get("tags", {})
        c = el.get("center", {})
        alat = el.get("lat", c.get("lat"))
        alon = el.get("lon", c.get("lon"))
        if alat is None or alon is None:
            continue
        dist = haversine_m(lat, lon, alat, alon)

        kind = _classify(tags)
        if tags.get("natural") == "water" or tags.get("waterway"):
            water_distance = dist if water_distance is None else min(water_distance, dist)
            continue
        landuse = tags.get("landuse")
        natural = tags.get("natural")
        if landuse or natural in ("wood", "scrub", "grassland"):
            key = landuse or natural
            landuse_counts[key] = landuse_counts.get(key, 0) + 1
            continue

        assets.append({
            "type": kind,
            "subtype": tags.get("highway") or tags.get("amenity") or tags.get("place") or ("bridge" if tags.get("bridge") else ""),
            "name": _asset_name(tags, kind),
            "latitude": float(alat),
            "longitude": float(alon),
            "distance_m": round(dist),
        })

    assets.sort(key=lambda x: x["distance_m"])
    if assets:
        seen = set()
        deduped = []
        for a in assets:
            key = (a["type"], round(a["latitude"], 4), round(a["longitude"], 4))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(a)
        assets = deduped

    landuse = _landuse_summary(landuse_counts)
    return {
        "assets": assets,
        "water_distance_m": round(water_distance) if water_distance is not None else None,
        "landuse": landuse,
        "source": "OpenStreetMap/Overpass",
        "source_type": "GIS",
        "observed_at": _now_iso(),
    }


def _landuse_summary(counts: dict[str, int]) -> dict | None:
    if not counts:
        return None
    total = sum(counts.values()) or 1
    urban = counts.get("residential", 0) + counts.get("industrial", 0) + counts.get("commercial", 0)
    forest = counts.get("forest", 0) + counts.get("wood", 0) + counts.get("scrub", 0) + counts.get("grassland", 0)
    agriculture = counts.get("farmland", 0) + counts.get("farmyard", 0) + counts.get("meadow", 0) + counts.get("grass", 0)
    return {
        "urban": round(urban / total, 4),
        "forest": round(forest / total, 4),
        "agriculture": round(agriculture / total, 4),
    }


# ---------------------------------------------------------------------------
# USGS earthquakes — contextual evidence only
# ---------------------------------------------------------------------------
async def fetch_earthquakes(lat: float, lon: float, radius_km: int = 180) -> list[dict]:
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        day = datetime.now(timezone.utc) - timedelta(days=14)
        params = {
            "format": "geojson",
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": radius_km,
            "starttime": day.strftime("%Y-%m-%d"),
            "orderby": "time",
        }
        r = await _request("GET", url, params=params, timeout=12)
        d = r.json()
        feats = (d.get("features") or [])[:10]
        out = []
        for f in feats:
            p = f.get("properties", {})
            geo = f.get("geometry", {})
            coords = geo.get("coordinates", [])
            if len(coords) < 2:
                continue
            out.append({
                "latitude": float(coords[1]),
                "longitude": float(coords[0]),
                "depth_km": _fmt(coords[2]) if len(coords) > 2 else None,
                "magnitude": _fmt(p.get("mag")),
                "place": p.get("place"),
                "time": p.get("time"),
                "distance_km": round(haversine_m(lat, lon, coords[1], coords[0]) / 1000, 1),
                "source": "USGS",
                "source_type": "LIVE_API",
            })
        return out
    except Exception:
        return []


# ---------------------------------------------------------------------------
# SoilGrids — clay/sand/silt/pH from real soil data (no API key)
# ---------------------------------------------------------------------------
_SEARCH_CODES = {"clay": "clay", "sand": "sand", "silt": "silt"}


async def fetch_soil_gird(lat: float, lon: float) -> dict | None:
    try:
        return await _cached(_cache_key("soil", lat, lon), CACHE_TTL_SECONDS["soil"], lambda: _soilgrids(lat, lon))
    except Exception:
        return None


async def _soilgrids(lat: float, lon: float) -> dict:
    params = {
        "lon": lon,
        "lat": lat,
        "property": "clay",
        "property": "sand",
        "property": "silt",
        "property": "phh2o",
        "depth": "0-5cm",
        "value": "mean",
    }
    r = await _request("GET", "https://rest.isric.org/soilgrids/v2.0/properties/query", params=params, timeout=15, retries=1)
    d = r.json()
    layers = d.get("properties", {}).get("layers", [])
    result: dict[str, Any] = {"source": "ISRIC SoilGrids REST", "source_type": "GIS", "observed_at": _now_iso()}
    for layer in layers:
        name = layer.get("name")
        value = None
        depths = layer.get("depths") or []
        if depths:
            for depth in depths:
                vals = depth.get("values", {})
                value = vals.get("mean")
                if value is not None:
                    break
        if name in ("clay", "sand", "silt"):
            result[f"{name}_percent"] = _fmt(value)
        elif name == "phh2o":
            result["soil_ph"] = _fmt(value)
    if result.get("clay_percent") is None and result.get("sand_percent") is None:
        raise RuntimeError("No usable soil measurements returned")
    return result


# ---------------------------------------------------------------------------
# GIS helpers
# ---------------------------------------------------------------------------
def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _iso_to_epoch(value: str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0