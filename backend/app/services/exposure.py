from __future__ import annotations

from .data_sources import fetch_surroundings
from ..config import ASSET_QUERY_RADIUS_M, MAX_ASSETS_RETURNED


def classify_exposure(dist_m: float, radius_m: float) -> str:
    """Exposure classification inside a configurable 'risk influence radius'.

    This is a transparent policy (HIGH <= radius; MODERATE <= 2x radius; else
    LOW) — it is NOT a validated landslide runout prediction.
    """
    if dist_m <= radius_m:
        return "HIGH"
    if dist_m <= radius_m * 2:
        return "MODERATE"
    return "LOW"


def spatial_exposure_proxy(assets: list[dict]) -> float:
    """Normalised 0-1 GIS exposure proxy from nearest asset + local density."""
    if not assets:
        return 0.0
    nearest = min(a["distance_m"] for a in assets)
    count_near = sum(1 for a in assets if a["distance_m"] <= 1500)
    return max(0.0, min(1.0, 0.6 * (1 - nearest / 3000) + 0.4 * min(count_near / 10, 1)))


async def assets_for_location(lat: float, lon: float, radius_m: int | None = None) -> dict:
    radius = max(500, min(radius_m or ASSET_QUERY_RADIUS_M, 7000))
    surroundings = await fetch_surroundings(lat, lon, radius)
    assets = surroundings.get("assets", [])
    for a in assets:
        a["exposure"] = classify_exposure(a["distance_m"], radius)
        a["source"] = "OpenStreetMap"
    assets.sort(key=lambda x: (0 if x["exposure"] == "HIGH" else 1 if x["exposure"] == "MODERATE" else 2, x["distance_m"]))
    return {
        "latitude": lat,
        "longitude": lon,
        "query_radius_m": radius,
        "influence_policy": "risk influence radius (not modelled runout)",
        "assets": assets[:MAX_ASSETS_RETURNED],
        "total_found": len(assets),
        "source": surroundings.get("source", "OpenStreetMap"),
        "source_type": surroundings.get("source_type", "UNAVAILABLE"),
        "generated_at": surroundings.get("observed_at"),
    }