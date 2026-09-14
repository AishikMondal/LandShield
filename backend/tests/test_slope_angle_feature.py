import pytest

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
