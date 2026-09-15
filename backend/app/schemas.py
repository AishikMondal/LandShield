from __future__ import annotations
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

SourceType = Literal[
    "LIVE_API",
    "DEM_DERIVED",
    "GIS",
    "MODEL_DERIVED",
    "DATASET_DEFAULT",
    "PROXY_DERIVED",
    "USER_INPUT",
    "DEMO",
    "UNAVAILABLE",
    "SENSOR_UNAVAILABLE",
    "UNRESOLVED",
]

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]


class CoordinateRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ScenarioRequest(CoordinateRequest):
    rainfall_multiplier: float = Field(default=1.0, ge=0, le=5)
    soil_moisture_delta: float = Field(default=0.0, ge=-1, le=1)

class SlopeScenarioRequest(CoordinateRequest):
    slope_angle: float = Field(ge=0, le=90)


class HotspotResponseItem(BaseModel):
    rank: int
    latitude: float
    longitude: float
    location_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    risk_score: float
    risk_level: RiskLevel
    generated_at: str
    data_freshness: str
    primary_factors: list[dict[str, Any]]


class BroadcastRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str = Field(default="Selected location", max_length=200)
    risk_level: RiskLevel = "HIGH"
    risk_score: float = Field(ge=0, le=100, default=60)
    message: str = Field(default="", max_length=2000)
    channels: list[str] = Field(default_factory=lambda: ["local_realtime"])
    primary_factors: list[str] = Field(default_factory=list)


class VerifyReportRequest(BaseModel):
    status: Literal["VERIFIED", "REJECTED", "UNVERIFIED"]


class DataPoint(BaseModel):
    value: Optional[float] = None
    unit: str = ""
    source: str
    source_type: SourceType
    observed_at: Optional[str] = None


class RiskResponse(BaseModel):
    location: dict[str, Any]
    risk_score: float
    risk_level: RiskLevel
    score_basis: str
    confidence: Optional[float] = None
    prediction_horizon: str
    factors: list[dict[str, Any]]
    terrain: list[dict[str, Any]]
    model_evidence: dict[str, Any]
    model_status: dict[str, Any]
    fusion_status: dict[str, Any]
    degraded_inputs: list[dict[str, Any]]
    why_high_risk: list[str]
    influence_radius_m: int
    impacted_assets: list[dict[str, Any]]
    earthquake_context: list[dict[str, Any]]
    recommended_actions: list[str]
    model_outputs: dict[str, Any]
    provenance: dict[str, Any]
    generated_at: str
    degraded: bool
    warnings: list[str]