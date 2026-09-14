import asyncio

import pytest

from app.services import hotspots
from app.services.features import FeatureBuilder


def test_feature_builder_maps_dem_slope_into_model_feature_vector():
    weather = None
    terrain = {
        "elevation_m": 1280.4,
        "slope_deg": 33.7,
        "aspect_deg": 142.2,
        "source": "Copernicus DEM via Open-Meteo elevation service",
        "source_type": "DEM_DERIVED",
        "observed_at": "2026-09-14T00:00:00+00:00",
    }
    surroundings = {
        "assets": [],
        "water_distance_m": None,
        "landuse": None,
        "source": "OpenStreetMap/Overpass",
        "source_type": "GIS",
        "observed_at": "2026-09-14T00:00:00+00:00",
    }

    values, meta, warnings = FeatureBuilder().build(weather, terrain, surroundings)

    assert values["Slope_Angle"] == pytest.approx(33.7)
    assert meta["Slope_Angle"]["value"] == pytest.approx(33.7)
    assert meta["Slope_Angle"]["source_type"] == "DEM_DERIVED"
    assert meta["Slope_Angle"]["name"] == "Slope angle"


def test_compute_all_truncates_ranked_hotspots_to_top_five(monkeypatch):
    candidates = []
    for i in range(8):
        candidates.append({
            "name": f"Town {i}",
            "district": "District",
            "state": "State",
            "lat": float(i),
            "lon": float(i),
        })

    monkeypatch.setattr(hotspots, "HOTSPOT_CANDIDATES", candidates, raising=False)

    async def fake_assess(lat, lon):
        return {
            "risk_score": 10.0 + lat,
            "risk_level": "LOW",
            "generated_at": "2026-09-14T00:00:00+00:00",
            "provenance": {"weather": {"observed_at": "2026-09-14T00:00:00+00:00"}, "terrain": {"source_type": "DEM_DERIVED"}},
            "why_high_risk": [],
        }

    monkeypatch.setattr(hotspots, "assess", fake_assess)

    items = asyncio.run(hotspots._compute_all())

    assert len(items) == 5
    assert [item["location_name"] for item in items] == [
        "Town 7",
        "Town 6",
        "Town 5",
        "Town 4",
        "Town 3",
    ]
