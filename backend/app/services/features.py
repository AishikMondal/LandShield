from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import MODEL_DIR

DEFAULTS = json.loads((MODEL_DIR / "feature_defaults.json").read_text())

# Human labels + units for every feature we surface in the UI.
FEATURE_LABELS = {
    "Rainfall_mm": "Rainfall 24h",
    "Rainfall_3Day": "Rainfall 3-day",
    "Rainfall_7Day": "Rainfall 7-day",
    "Temperature_C": "Temperature",
    "Humidity_percent": "Humidity",
    "Soil_Temperature_C": "Soil temperature",
    "Soil_Moisture_Content": "Soil moisture",
    "Soil_Saturation": "Soil saturation",
    "Elevation_m": "Elevation",
    "Slope_Angle": "Slope angle",
    "Aspect": "Aspect",
    "Distance_to_Road_m": "Distance to road",
    "Proximity_to_Water": "Proximity to water",
    "Land_Use_Urban": "Urban land use",
    "Land_Use_Forest": "Forest land use",
    "Land_Use_Agriculture": "Agricultural land use",
    "Clay_Content": "Clay content",
    "Sand_Content": "Sand content",
    "Silt_Content": "Silt content",
    "Soil_pH": "Soil pH",
    "Soil_Erosion_Rate": "Soil erosion rate",
    "Soil_Type_Gravel": "Gravel soil texture",
    "Soil_Type_Sand": "Sand soil texture",
    "Soil_Type_Silt": "Silt soil texture",
    "Soil_Type_Clay": "Clay soil texture",
    "NDVI_Index": "NDVI",
    "Vegetation_Cover": "Vegetation cover",
    "Earthquake_Activity": "Earthquake activity",
    "Historical_Landslide_Count": "Historical landslide count",
    "Pore_Water_Pressure_kPa": "Pore water pressure",
    "Microseismic_Activity": "Microseismic activity",
    "Acoustic_Emission_dB": "Acoustic emission",
    "Soil_Strain": "Soil strain",
    "TDR_Reflection_Index": "TDR reflection index",
}

FEATURE_UNITS = {
    "Rainfall_mm": "mm",
    "Rainfall_3Day": "mm",
    "Rainfall_7Day": "mm",
    "Temperature_C": "°C",
    "Humidity_percent": "%",
    "Soil_Temperature_C": "°C",
    "Soil_Moisture_Content": "fraction",
    "Soil_Saturation": "fraction",
    "Elevation_m": "m",
    "Slope_Angle": "°",
    "Aspect": "°",
    "Distance_to_Road_m": "m",
    "Proximity_to_Water": "n/a",
    "Land_Use_Urban": "fraction",
    "Land_Use_Forest": "fraction",
    "Land_Use_Agriculture": "fraction",
    "Clay_Content": "%",
    "Sand_Content": "%",
    "Silt_Content": "%",
    "Soil_pH": "pH",
    "Soil_Erosion_Rate": "t/ha/yr",
    "Soil_Type_Gravel": "0/1",
    "Soil_Type_Sand": "0/1",
    "Soil_Type_Silt": "0/1",
    "Soil_Type_Clay": "0/1",
    "NDVI_Index": "n/a",
    "Vegetation_Cover": "fraction",
    "Earthquake_Activity": "n/a",
    "Historical_Landslide_Count": "count",
    "Pore_Water_Pressure_kPa": "kPa",
    "Microseismic_Activity": "n/a",
    "Acoustic_Emission_dB": "dB",
    "Soil_Strain": "µε",
    "TDR_Reflection_Index": "n/a",
}

# Features that can only come from local instrumentation (no public API).
SENSOR_FEATURES = [
    "Pore_Water_Pressure_kPa",
    "Microseismic_Activity",
    "Acoustic_Emission_dB",
    "Soil_Strain",
    "TDR_Reflection_Index",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FeatureBuilder:
    """Builds a model-ready feature vector while tracking provenance.

    Priority per feature: live API -> DEM/GIS -> calculated proxy -> cached ->
    dataset default (last resort). Every feature records its source_type so the
    UI can label LIVE / GIS / MODEL-DERIVED / PROXY / DATASET DEFAULT /
    SENSOR_UNAVAILABLE honestly.
    """

    def build(self, weather, terrain, surroundings, earthquakes=None, scenario=None, soil=None):
        values = {k: float(v) for k, v in DEFAULTS.items()}
        meta: dict[str, dict[str, Any]] = {
            k: {
                "name": FEATURE_LABELS.get(k, k),
                "value": values[k],
                "unit": FEATURE_UNITS.get(k, ""),
                "source": "training-set median",
                "source_type": "DATASET_DEFAULT",
                "timestamp": None,
                "fallback_used": True,
            }
            for k in values
        }
        warnings: list[str] = []
        scenario = scenario or {}

        # -------------------------------------------------------------------
        # Weather (live API)
        # -------------------------------------------------------------------
        if weather:
            rm_mul = float(scenario.get("rainfall_multiplier", 1.0))
            for key, src_key in (("Rainfall_mm", "rainfall_24h_mm"),
                                 ("Rainfall_3Day", "rainfall_3d_mm"),
                                 ("Rainfall_7Day", "rainfall_7d_mm")):
                val = weather.get(src_key)
                if val is not None:
                    values[key] = float(val) * rm_mul
                    meta[key].update({
                        "value": values[key],
                        "source": weather.get("data_source", "Open-Meteo"),
                        "source_type": weather.get("source_type", "LIVE_API"),
                        "timestamp": weather.get("observed_at"),
                        "fallback_used": False,
                    })
            if weather.get("temperature_c") is not None:
                values["Temperature_C"] = float(weather["temperature_c"])
                meta["Temperature_C"].update({"value": values["Temperature_C"], "source": weather.get("data_source", "Open-Meteo"),
                                              "source_type": weather.get("source_type", "LIVE_API"),
                                              "timestamp": weather.get("observed_at"), "fallback_used": False})
            if weather.get("humidity_percent") is not None:
                values["Humidity_percent"] = float(weather["humidity_percent"])
                meta["Humidity_percent"].update({"value": values["Humidity_percent"], "source": weather.get("data_source", "Open-Meteo"),
                                                 "source_type": weather.get("source_type", "LIVE_API"),
                                                 "timestamp": weather.get("observed_at"), "fallback_used": False})
            if weather.get("soil_temperature_c") is not None:
                values["Soil_Temperature_C"] = float(weather["soil_temperature_c"])
                meta["Soil_Temperature_C"].update({"value": values["Soil_Temperature_C"], "source": weather.get("data_source", "Open-Meteo"),
                                                   "source_type": weather.get("source_type", "LIVE_API"),
                                                   "timestamp": weather.get("observed_at"), "fallback_used": False})
            sm = weather.get("soil_moisture_fraction")
            if sm is not None:
                sm = max(0.0, min(1.0, float(sm) + float(scenario.get("soil_moisture_delta", 0.0))))
                # Open-Meteo returns a 0-1 volumetric fraction. The supplied
                # models' RobustScaler expects these two features on a 0-1
                # fraction scale (centers ~0.30 / 0.70). We keep the fraction.
                values["Soil_Moisture_Content"] = sm
                values["Soil_Saturation"] = sm
                for key in ("Soil_Moisture_Content", "Soil_Saturation"):
                    meta[key].update({
                        "value": sm,
                        "source": "Open-Meteo soil moisture model",
                        "source_type": "PROXY_DERIVED",
                        "timestamp": weather.get("observed_at"),
                        "fallback_used": False,
                    })
                warnings.append("Soil moisture is weather-model-derived (0-1 fraction) mapped directly to the training scale; it is NOT a field sensor reading.")
        else:
            warnings.append("Weather source unavailable; training-set medians were used for weather features.")

        # -------------------------------------------------------------------
        # Terrain (DEM)
        # -------------------------------------------------------------------
        if terrain:
            for key, tsrc in (("Elevation_m", "elevation_m"),
                              ("Slope_Angle", "slope_deg"),
                              ("Aspect", "aspect_deg")):
                values[key] = float(terrain[tsrc])
                meta[key].update({"value": values[key], "source": terrain.get("source", "DEM"),
                                  "source_type": terrain.get("source_type", "DEM_DERIVED"),
                                  "timestamp": terrain.get("observed_at"), "fallback_used": False})
        else:
            warnings.append("Terrain source unavailable; training-set medians were used for terrain features.")

        # -------------------------------------------------------------------
        # GIS surroundings (land use, road distance, water proximity)
        # -------------------------------------------------------------------
        if surroundings and surroundings.get("assets"):
            roads = [a for a in surroundings["assets"] if a["type"] == "road"]
            if roads:
                values["Distance_to_Road_m"] = float(roads[0]["distance_m"])
                meta["Distance_to_Road_m"].update({
                    "value": values["Distance_to_Road_m"],
                    "source": "OpenStreetMap/Overpass",
                    "source_type": "GIS",
                    "timestamp": surroundings.get("observed_at"),
                    "fallback_used": False,
                })
                warnings.append("Distance_to_Road_m uses the nearest OSM highway segment (training definition approximated).")
        if surroundings and surroundings.get("landuse"):
            lu = surroundings["landuse"]
            for key, lkey in (("Land_Use_Urban", "urban"), ("Land_Use_Forest", "forest"), ("Land_Use_Agriculture", "agriculture")):
                v = lu.get(lkey)
                if v is not None:
                    values[key] = float(v)
                    meta[key].update({"value": values[key], "source": "OpenStreetMap landuse",
                                      "source_type": "GIS", "timestamp": surroundings.get("observed_at"),
                                      "fallback_used": False})
            warnings.append("Land-use codes are approximated from OSM landuse fractions (training one-hot definition approximated).")
        if surroundings and surroundings.get("water_distance_m") is not None:
            # Normalize distance to water into [0,1] as a transparent proxy.
            prox = max(0.0, min(1.0, 1.0 - surroundings["water_distance_m"] / 1000.0))
            values["Proximity_to_Water"] = prox
            meta["Proximity_to_Water"].update({"value": prox, "source": "OpenStreetMap water features",
                                               "source_type": "PROXY_DERIVED",
                                               "timestamp": surroundings.get("observed_at"), "fallback_used": False})
            warnings.append("Proximity_to_Water is a normalized proxy (1 - min_dist/1000m) because the training definition is undocumented.")

        # -------------------------------------------------------------------
        # Soil (SoilGrids GIS)
        # -------------------------------------------------------------------
        sogrid = soil or ((surroundings or {}).get("soil"))
        if sogrid and (sogrid.get("clay_percent") is not None or sogrid.get("sand_percent") is not None):
            for key, s_key in (("Clay_Content", "clay_percent"), ("Sand_Content", "sand_percent"), ("Silt_Content", "silt_percent")):
                v = sogrid.get(s_key)
                if v is not None:
                    values[key] = float(v)
                    meta[key].update({"value": values[key], "source": sogrid.get("source", "ISRIC SoilGrids"),
                                      "source_type": "GIS", "timestamp": sogrid.get("observed_at"), "fallback_used": False})
            if sogrid.get("soil_ph") is not None:
                values["Soil_pH"] = float(sogrid["soil_ph"])
                meta["Soil_pH"].update({"value": values["Soil_pH"], "source": sogrid.get("source", "ISRIC SoilGrids"),
                                        "source_type": "GIS", "timestamp": sogrid.get("observed_at"), "fallback_used": False})
            # Dominant texture -> one-hot soil type (Gravel not available).
            tex = {"Soil_Type_Clay": values.get("Clay_Content", 0), "Soil_Type_Sand": values.get("Sand_Content", 0),
                   "Soil_Type_Silt": values.get("Silt_Content", 0)}
            dominant = max(tex, key=lambda k: tex[k])
            for key in ("Soil_Type_Clay", "Soil_Type_Sand", "Soil_Type_Silt"):
                values[key] = 1.0 if key == dominant else 0.0
                meta[key].update({"value": values[key], "source": sogrid.get("source", "ISRIC SoilGrids"),
                                  "source_type": "GIS", "timestamp": sogrid.get("observed_at"), "fallback_used": False})
            warnings.append("Soil texture/pH sourced from ISRIC SoilGrids (0-5cm topsoil).")
        else:
            warnings.append("Soil composition unavailable or zero-confidence; training-set medians used.")

        # Sensor + unresolved features
        for key in SENSOR_FEATURES:
            meta[key].update({"source": "no public sensor feed", "source_type": "SENSOR_UNAVAILABLE",
                              "timestamp": None, "fallback_used": True})
        for key in ("NDVI_Index", "Vegetation_Cover"):
            meta[key].update({"source": "Copernicus/Sentinel not configured",
                              "source_type": "DATASET_DEFAULT", "fallback_used": True})
        for key in ("Earthquake_Activity", "Historical_Landslide_Count"):
            meta[key].update({"source_type": "UNRESOLVED" if key == "Earthquake_Activity" else "DATASET_DEFAULT",
                              "fallback_used": True})
        if earthquakes:
            warnings.append(f"USGS earthquake context available ({len(earthquakes)} event(s) in 14 days) but NOT mapped "
                            "into the Earthquake_Activity model feature because the training transformation is undocumented.")

        default_count = sum(1 for k, v in meta.items() if v["source_type"] in ("DATASET_DEFAULT", "SENSOR_UNAVAILABLE", "UNRESOLVED"))
        sensor_count = sum(1 for k in SENSOR_FEATURES if meta[k]["source_type"] == "SENSOR_UNAVAILABLE")
        if sensor_count:
            warnings.append(f"{sensor_count} sensor-only features have no live feed and use training-set medians (SENSOR_UNAVAILABLE).")
        if default_count:
            warnings.append(f"{default_count} model features use training-set median defaults; output is degraded/demo-grade.")
        return values, meta, warnings