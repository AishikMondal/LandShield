from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
MODEL_DIR = BASE_DIR / "model_artifacts"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = Path(os.getenv("LANDSHIELD_DB_PATH", str(DATA_DIR / "landshield.db")))

# ---------------------------------------------------------------------------
# Global switches
# ---------------------------------------------------------------------------
DEMO_MODE = os.getenv("LANDSHIELD_DEMO_MODE", "false").lower() == "true"
ENABLE_EXPERIMENTAL_FUSION = os.getenv("ENABLE_EXPERIMENTAL_FUSION", "false").lower() == "true"
ENABLE_RECONSTRUCTED_MODEL2 = os.getenv("ENABLE_RECONSTRUCTED_MODEL2", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Risk policy (kept out of React — single source of truth in the backend)
# ---------------------------------------------------------------------------
# Canonical thresholds follow the supplied fusion model_config.json.
RISK_THRESHOLDS = {
    "MODERATE": float(os.getenv("RISK_THRESHOLD_MODERATE", "25")),
    "HIGH": float(os.getenv("RISK_THRESHOLD_HIGH", "55")),
    "CRITICAL": float(os.getenv("RISK_THRESHOLD_CRITICAL", "80")),
}

# Risk influence radius (metres) per risk level.
# This is a transparent, configurable policy — NOT a validated runout model.
INFLUENCE_RADIUS_M = {
    "LOW": float(os.getenv("INFLUENCE_RADIUS_LOW_M", "250")),
    "MODERATE": float(os.getenv("INFLUENCE_RADIUS_MODERATE_M", "500")),
    "HIGH": float(os.getenv("INFLUENCE_RADIUS_HIGH_M", "1000")),
    "CRITICAL": float(os.getenv("INFLUENCE_RADIUS_CRITICAL_M", "2500")),
}

# Radius used to collect spatial context / OSM assets before risk is computed.
ASSET_QUERY_RADIUS_M = float(os.getenv("ASSET_QUERY_RADIUS_M", "3500"))
MAX_ASSETS_RETURNED = int(os.getenv("MAX_ASSETS_RETURNED", "20"))

# ---------------------------------------------------------------------------
# Alert policy
# ---------------------------------------------------------------------------
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "55"))
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "30"))
# Re-broadcast same-zone/same-level alert only when the score jumps by >= this.
ALERT_SCORE_SIGNIFICANT_DELTA = float(os.getenv("ALERT_SCORE_SIGNIFICANT_DELTA", "10"))
ALERT_SCORE_BUCKET_SIZE = float(os.getenv("ALERT_SCORE_BUCKET_SIZE", "10"))

# ---------------------------------------------------------------------------
# Hotspots
# ---------------------------------------------------------------------------
HOTSPOT_REFRESH_MINUTES = int(os.getenv("HOTSPOT_REFRESH_MINUTES", "15"))
HOTSPOT_TOP_N = int(os.getenv("HOTSPOT_TOP_N", "5"))
HOTSPOT_MIN_SCORE = float(os.getenv("HOTSPOT_MIN_SCORE", "0"))
HOTSPOT_MAX_CONCURRENCY = int(os.getenv("HOTSPOT_MAX_CONCURRENCY", "5"))

# ---------------------------------------------------------------------------
# HTTP / API behaviour
# ---------------------------------------------------------------------------
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))
HTTP_RETRIES = int(os.getenv("HTTP_RETRIES", "2"))
OVERVIEW_OVERALL_TIMEOUT = float(os.getenv("OVERVIEW_OVERALL_TIMEOUT_SECONDS", "35"))
USER_AGENT = os.getenv("LANDSHIELD_USER_AGENT", "Mozilla/5.0 LandShield-SIH/1.0 (SIH26001 prototype; contact: demo@example.com)")

# Cache lifetimes (seconds). Terrain/DEM, geocodes, soil are static -> long TTL.
CACHE_TTL_SECONDS = {
    "weather": int(os.getenv("CACHE_TTL_WEATHER_SECONDS", "900")),
    "terrain": int(os.getenv("CACHE_TTL_TERRAIN_SECONDS", "21600")),
    "geocode": int(os.getenv("CACHE_TTL_GEOCODE_SECONDS", "21600")),
    "osm": int(os.getenv("CACHE_TTL_OSM_SECONDS", "900")),
    "earthquake": int(os.getenv("CACHE_TTL_EARTHQUAKE_SECONDS", "1800")),
    "nasa": int(os.getenv("CACHE_TTL_NASA_SECONDS", "900")),
    "soil": int(os.getenv("CACHE_TTL_SOIL_SECONDS", "86400")),
}

OVERPASS_ENDPOINTS = [v.strip() for v in os.getenv(
    "OVERPASS_ENDPOINTS",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter,"
    "https://overpass.osm.ch/api/interpreter,"
    "https://overpass-api.de/api/interpreter,"
    "https://overpass.kumi.systems/api/interpreter,"
    "https://overpass.nchc.org.tw/api/interpreter,"
    "http://overpass.private.coffee/api/interpreter",
).split(",") if v.strip()]

# ---------------------------------------------------------------------------
# Optional providers (all optional — app must run without them)
# ---------------------------------------------------------------------------
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
COPERNICUS_CLIENT_ID = os.getenv("COPERNICUS_CLIENT_ID", "").strip()
COPERNICUS_CLIENT_SECRET = os.getenv("COPERNICUS_CLIENT_SECRET", "").strip()
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "").strip()
SMS_API_KEY = os.getenv("SMS_API_KEY", "").strip()
SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "").strip()
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587") or "587")
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
EMAIL_FROM = os.getenv("EMAIL_FROM", "").strip()

CORS_ORIGINS = [v.strip() for v in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if v.strip()]

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)