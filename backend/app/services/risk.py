from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from .data_sources import (
    fetch_weather,
    fetch_elevation_and_terrain,
    reverse_geocode,
    fetch_surroundings,
    fetch_earthquakes,
    fetch_soil_gird,
)
from .features import FeatureBuilder
from .exposure import classify_exposure, spatial_exposure_proxy
from .models import ModelRegistry
from ..config import (
    ALERT_THRESHOLD,
    ASSET_QUERY_RADIUS_M,
    INFLUENCE_RADIUS_M,
    RISK_THRESHOLDS,
    MAX_ASSETS_RETURNED,
    ENABLE_EXPERIMENTAL_FUSION,
)
from ..db import save_prediction, maybe_create_alert

registry = ModelRegistry()
builder = FeatureBuilder()

DEGRADED_SOURCE_TYPES = ("DATASET_DEFAULT", "SENSOR_UNAVAILABLE", "UNRESOLVED")


def risk_level(score: float) -> str:
    if score >= RISK_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    if score >= RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    if score >= RISK_THRESHOLDS["MODERATE"]:
        return "MODERATE"
    return "LOW"


async def _fetch_inputs(lat: float, lon: float) -> tuple:
    warnings: list[str] = []

    async def safe(coro, label, default, exc_ok: tuple = (Exception,)):
        try:
            return await coro
        except exc_ok as e:
            warnings.append(f"{label} unavailable: {type(e).__name__}")
            return default

    weather, terrain, location, surroundings, earthquakes, soil = await asyncio.gather(
        safe(fetch_weather(lat, lon), "Weather", None),
        safe(fetch_elevation_and_terrain(lat, lon), "Terrain", None),
        safe(reverse_geocode(lat, lon), "Reverse geocoding",
             {"display_name": "Selected location", "district": None, "state": None, "country": "India",
              "source_type": "UNAVAILABLE", "source": "UNAVAILABLE"}),
        safe(fetch_surroundings(lat, lon, ASSET_QUERY_RADIUS_M), "OSM surroundings",
             {"assets": [], "water_distance_m": None, "landuse": None, "error": True}),
        safe(fetch_earthquakes(lat, lon), "USGS earthquakes", []),
        safe(fetch_soil_gird(lat, lon), "SoilGrids", None),
    )
    return weather, terrain, location, surroundings, earthquakes, soil, warnings


def _spatial_proxy(assets: list[dict]) -> float:
    return spatial_exposure_proxy(assets)


def _classify_exposure(dist_m: float, radius_m: float) -> str:
    return classify_exposure(dist_m, radius_m)


async def slope_sensitivity(lat: float, lon: float) -> dict:
    weather, terrain, location, surroundings, earthquakes, soil, _warnings = await _fetch_inputs(lat, lon)
    values, meta, feature_warnings = builder.build(weather, terrain, surroundings, earthquakes, None, soil=soil)

    # Keep all fields constant except the DEM-derived slope feature passed through the existing model.
    base_slope = float(values.get("Slope_Angle", 30.0))
    slopes = [15.0, 30.0, 45.0]
    sensitivity = []
    for slope in slopes:
        values_for_run = values.copy()
        meta_for_run = meta.copy()
        values_for_run["Slope_Angle"] = float(slope)
        meta_for_run["Slope_Angle"] = {**meta_for_run.get("Slope_Angle", {}), "value": float(slope)}

        # Build the model input exactly as the retrained artifact expects.
        proxy = _spatial_proxy(surroundings.get("assets", []))
        outputs = registry.predict(values_for_run, proxy)
        if "susceptibility_prob" in outputs:
            score = max(0.0, min(100.0, outputs["susceptibility_prob"] * 100))
            level = risk_level(score)
        else:
            score = 0.0
            level = "LOW"

        sensitivity.append({
            "slope_angle": round(float(slope), 2),
            "model_output_probability": round(float(outputs.get("susceptibility_prob", 0.0)), 6),
            "risk_score": round(float(score), 2),
            "risk_level": level,
        })

    # restore the current slope baseline from the live DEM branch
    values["Slope_Angle"] = base_slope
    return {
        "slope_sensitivity": sensitivity,
        "model_input_received": {
            "feature": "Slope_Angle",
            "units": "degrees",
            "base_features_constant": True,
            "static_terrain_inputs": ["Elevation_m", "Slope_Angle", "Aspect"],
            "dynamic_inputs": ["Rainfall_mm", "Rainfall_3Day", "Rainfall_7Day", "Soil_Moisture_Content", "Soil_Saturation"],
        },
        "note": "What-if slope sensitivity check. The model output is shown without forcing the score to rise with slope.",
        "terrain_source": terrain.get("source") if terrain else None,
        "terrain_source_type": terrain.get("source_type") if terrain else None,
    }


def _explain(meta: dict, values: dict, anomaly: Optional[float], earthquakes: list[dict], water_dist: Optional[float]) -> list[str]:
    reasons: list[str] = []
    rain = values.get("Rainfall_mm")
    rain3 = values.get("Rainfall_3Day")
    rain7 = values.get("Rainfall_7Day")
    slope = values.get("Slope_Angle")
    elev = values.get("Elevation_m")
    sm = values.get("Soil_Saturation")
    if rain is not None and rain >= 60:
        reasons.append(f"High recent rainfall ({rain:.1f} mm in 24h)")
    if rain3 is not None and rain3 >= 150:
        reasons.append(f"Heavy 3-day rainfall accumulation ({rain3:.1f} mm)")
    if rain7 is not None and rain7 >= 300:
        reasons.append(f"Heavy 7-day rainfall accumulation ({rain7:.1f} mm)")
    if slope is not None and slope >= 30:
        reasons.append(f"Steep terrain ({slope:.1f}°)")
    elif slope is not None and slope >= 18:
        reasons.append(f"Moderately steep terrain ({slope:.1f}°)")
    if elev is not None and elev >= 2000:
        reasons.append(f"High-elevation slope ({elev:.0f} m)")
    if sm is not None and sm >= 0.45:
        reasons.append(f"Elevated soil moisture/saturation ({sm * 100:.0f}% of fraction scale)")
    if proxy := meta.get("Proximity_to_Water"):
        if water_dist is not None and water_dist <= 500:
            reasons.append(f"Close to a water body/stream (~{water_dist:.0f} m)")
    if anomaly is not None and anomaly >= 0.6:
        reasons.append(f"Anomalous environmental pattern flagged (anomaly score {anomaly:.2f})")
    if earthquakes:
        near = max(0, min(earthquakes, key=lambda e: e.get("distance_km", 1e9)))
        if near.get("distance_km", 1e9) <= 120:
            reasons.append(f"Recent seismic activity {near.get('distance_km')} km away (M{near.get('magnitude')})")
    return reasons[:6]


async def assess(lat: float, lon: float, scenario: Optional[dict] = None) -> dict:
    warnings: list[str] = []

    async def safe(coro, label, default, exc_ok: tuple = (Exception,)):
        try:
            return await coro
        except exc_ok as e:
            warnings.append(f"{label} unavailable: {type(e).__name__}")
            return default

    weather, terrain, location, surroundings, earthquakes, soil = await asyncio.gather(
        safe(fetch_weather(lat, lon), "Weather", None),
        safe(fetch_elevation_and_terrain(lat, lon), "Terrain", None),
        safe(reverse_geocode(lat, lon), "Reverse geocoding",
             {"display_name": "Selected location", "district": None, "state": None, "country": "India",
              "source_type": "UNAVAILABLE", "source": "UNAVAILABLE"}),
        safe(fetch_surroundings(lat, lon, ASSET_QUERY_RADIUS_M), "OSM surroundings",
             {"assets": [], "water_distance_m": None, "landuse": None, "error": True}),
        safe(fetch_earthquakes(lat, lon), "USGS earthquakes", []),
        safe(fetch_soil_gird(lat, lon), "SoilGrids", None),
    )

    values, meta, feature_warnings = builder.build(weather, terrain, surroundings, earthquakes, scenario, soil=soil)
    warnings.extend(feature_warnings)

    assets = surroundings.get("assets", [])
    proxy = _spatial_proxy(assets)
    outputs = registry.predict(values, proxy)

    degraded_inputs = [
        {**meta[k], "feature": k}
        for k, m in meta.items()
        if m["source_type"] in DEGRADED_SOURCE_TYPES
    ]

    fusion_enabled = ENABLE_EXPERIMENTAL_FUSION and bool(outputs.get("fusion_prob"))
    if "fusion_prob" in outputs:
        score = max(0.0, min(100.0, outputs["fusion_prob"] * 100))
        basis = "experimental_fusion_with_gis_exposure_proxy"
        warnings.append("Experimental fusion used (GIS exposure proxy substitutes the missing Model 4 spatial-vulnerability input).")
    elif "susceptibility_prob" in outputs:
        score = max(0.0, min(100.0, outputs["susceptibility_prob"] * 100))
        basis = "model1_susceptibility_calibrated_probability"
    else:
        score = 0.0
        basis = "no_model_available"
        warnings.append("No compatible predictive model loaded; no score produced.")

    score = round(score, 2)
    level = risk_level(score)
    radius = int(INFLUENCE_RADIUS_M.get(level, 500))

    for a in assets:
        a["exposure"] = _classify_exposure(a["distance_m"], radius)
        if "subtype" in a:
            a["category"] = a.pop("subtype")
    assets.sort(key=lambda x: (0 if x["exposure"] == "HIGH" else 1 if x["exposure"] == "MODERATE" else 2, x["distance_m"]))
    assets = assets[:MAX_ASSETS_RETURNED]

    weather_factors = []
    for key in ("Rainfall_mm", "Rainfall_3Day", "Rainfall_7Day", "Soil_Moisture_Content", "Temperature_C", "Humidity_percent"):
        m = meta[key]
        weather_factors.append({**m, "feature": key})

    terrain_factors = []
    for key in ("Elevation_m", "Slope_Angle", "Aspect"):
        m = meta[key]
        terrain_factors.append({**m, "feature": key})

    anomaly = outputs.get("anomaly_score")
    why = _explain(meta, values, anomaly, earthquakes, surroundings.get("water_distance_m"))

    actions = []
    if level in ("HIGH", "CRITICAL"):
        actions += [
            "Prioritize field verification of the selected slope and nearby roads.",
            f"Check assets within the {radius} m risk influence radius and prepare community warnings.",
        ]
    if level == "CRITICAL":
        actions.append("Escalate to the responsible disaster-management authority before any public evacuation instruction.")
    if not actions:
        actions.append("Continue monitoring; re-run assessment when rainfall or field conditions materially change.")

    model_evidence = {
        "model1": {"label": "Susceptibility probability",
                   "value": round(outputs.get("susceptibility_prob", 0.0), 4),
                   "status": registry.status["model1"].get("status")},
        "model3": {"label": "Environmental anomaly evidence",
                   "value": round(outputs.get("anomaly_score", 0.0), 4),
                   "status": registry.status["model3"].get("status")},
        "earthquake_context": earthquakes[:5],
    }

    result = {
        "location": {"latitude": lat, "longitude": lon, **location},
        "risk_score": score,
        "risk_level": level,
        "score_basis": basis,
        "confidence": None,
        "prediction_horizon": "6h (fusion config; model outputs reflect current environmental conditioning, not a time-to-failure forecast)",
        "factors": weather_factors,
        "terrain": terrain_factors,
        "model_evidence": model_evidence,
        "model_status": {k: {kk: vv for kk, vv in v.items() if kk != "error"} for k, v in registry.status.items()},
        "fusion_status": {
            "enabled": bool(fusion_enabled),
            "available": registry.status["fusion"].get("loaded", False),
            "status": registry.status["fusion"].get("status"),
            "reason": registry.status["fusion"].get("reason"),
        },
        "degraded_inputs": degraded_inputs,
        "why_high_risk": why,
        "influence_radius_m": radius,
        "impacted_assets": assets,
        "earthquake_context": earthquakes[:5],
        "recommended_actions": actions,
        "model_outputs": {**outputs, "registry": registry.status},
        "provenance": {
            "weather": weather,
            "terrain": terrain,
            "surroundings": surroundings,
            "soil": soil,
            "feature_sources": {k: m["source_type"] for k, m in meta.items()},
            "location": location,
            "scenario": scenario,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "degraded": bool(degraded_inputs) or not all((weather, terrain)),
        "warnings": warnings,
    }

    degraded_flag = bool(degraded_inputs) or (weather is None) or (terrain is None) or (not outputs)

    # Alerts are created for HIGH/CRITICAL and for MODERATE at/above threshold.
    if score >= ALERT_THRESHOLD:
        message = (
            f"{level} landslide risk ({score:.0f}/100) near {location.get('display_name', 'selected location')}. "
            + (" ".join(why) if why else "Verify conditions before public action.")
        )
        created, deduped = maybe_create_alert(lat, lon, score, level, message, location.get("display_name", ""))
        result["alert_record"] = {"created": bool(created), "deduped": deduped, "alert": created}

    save_prediction(lat, lon, score, level, basis, json.dumps(result, default=str))
    result["degraded"] = degraded_flag
    return result