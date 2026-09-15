from __future__ import annotations
import asyncio
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import CORS_ORIGINS, UPLOAD_DIR, DB_PATH, DEMO_MODE, ALERT_THRESHOLD, HTTP_TIMEOUT_SECONDS
from .db import init_db, create_report, list_reports, verify_report, list_alerts, maybe_create_alert
from .schemas import CoordinateRequest, ScenarioRequest, SlopeScenarioRequest, BroadcastRequest, VerifyReportRequest
from .services.risk import assess, registry, risk_level, slope_sensitivity as slope_sensitivity_probe
from .services.hotspots import refresh_hotspots, hotspot_payload
from .services.exposure import assets_for_location
from .services.data_sources import fetch_weather, fetch_elevation_and_terrain, fetch_surroundings
from .realtime import deliver_alert, stream

app = FastAPI(title="LandShield Risk Intelligence API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(refresh_hotspots())


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
_HEALTH_CACHE: dict = {}


async def _probe(name: str, nearer: tuple, ttl: int = 60) -> str:
    import httpx

    now = datetime.now(timezone.utc).timestamp()
    cached = _HEALTH_CACHE.get(name)
    if cached and (now - cached[0]) < ttl:
        return cached[1]
    status = "unreachable"
    try:
        async with httpx.AsyncClient(timeout=min(5, HTTP_TIMEOUT_SECONDS)) as client:
            r = await client.get(**nearer)
            status = "healthy" if r.status_code < 400 else f"http_{r.status_code}"
    except Exception:
        status = "unreachable"
    _HEALTH_CACHE[name] = (now, status)
    return status


@app.get("/api/health")
async def health():
    return {
        "api": "healthy",
        "database": "connected" if DB_PATH.parent.exists() else "unavailable",
        "model_1": registry.status["model1"].get("status", "ERROR"),
        "model_2": registry.status["model2"].get("status", "ERROR"),
        "model_3": registry.status["model3"].get("status", "ERROR"),
        "model_4": registry.status["model4"].get("status", "ERROR"),
        "fusion": registry.status["fusion"].get("status", "ERROR"),
        "weather": await _probe("weather", {"url": "https://api.open-meteo.com/v1/forecast",
                                            "params": {"latitude": 26.14, "longitude": 91.73, "current": "temperature_2m"}}),
        "elevation": await _probe("elevation", {"url": "https://api.open-meteo.com/v1/elevation",
                                                "params": {"latitude": 26.14, "longitude": 91.73}}),
        "osm": await _probe("osm", {"url": "https://www.openstreetmap.org/" }),
        "nominatim": "adapter_configured",
        "realtime_alerts": "available",
        "alert_threshold": ALERT_THRESHOLD,
        "demand": {"stream_clients": stream.connected_clients()},
        "demo_mode": DEMO_MODE,
        "models": registry.status,
    }


# ---------------------------------------------------------------------------
# Model status
# ---------------------------------------------------------------------------
@app.get("/api/models/status")
def models_status():
    return {
        "fusion": registry.status["fusion"],
        "models": {
            "model1": registry.status["model1"],
            "model2": registry.status["model2"],
            "model3": registry.status["model3"],
            "model4": registry.status["model4"],
        },
        "note": "Scan the full inference chain before trusting the displayed risk score.",
    }


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------
@app.post("/api/risk/predict")
async def predict(req: CoordinateRequest):
    return await assess(req.latitude, req.longitude)


@app.post("/api/risk/simulate")
async def simulate(req: ScenarioRequest):
    return await assess(req.latitude, req.longitude,
                        {"rainfall_multiplier": req.rainfall_multiplier, "soil_moisture_delta": req.soil_moisture_delta})

@app.post("/api/risk/simulate-slope")
async def simulate_slope(req: SlopeScenarioRequest):
    return await assess(req.latitude, req.longitude, {"slope_angle": req.slope_angle})


@app.get("/api/risk/hotspots")
async def hotspots(_force: int = 0):
    await refresh_hotspots(force=bool(_force))
    return hotspot_payload()


@app.get("/api/risk/slope-sensitivity")
async def slope_sensitivity_route(latitude: float, longitude: float):
    return await slope_sensitivity_probe(latitude, longitude)


@app.get("/api/location/assets")
async def location_assets(latitude: float, longitude: float, radius_m: int = 0):
    return await assets_for_location(latitude, longitude, radius_m or None)


# ---------------------------------------------------------------------------
# Citizen reports
# ---------------------------------------------------------------------------
@app.get("/api/reports")
def reports():
    return {"reports": list_reports()}


@app.post("/api/reports")
async def submit_report(
    latitude: float = Form(...), longitude: float = Form(...), hazard_type: str = Form(...),
    severity: str = Form(...), description: str = Form(""), reporter_type: str = Form("RESIDENT"),
    image: UploadFile | None = File(None),
):
    if severity not in {"minor", "moderate", "major", "severe"}:
        raise HTTPException(400, "Invalid severity")
    image_path = None
    if image:
        allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
        if image.content_type not in allowed:
            raise HTTPException(400, "Only JPG, PNG or WebP images are accepted")
        content = await image.read(10 * 1024 * 1024 + 1)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(413, "Image exceeds 10MB")
        name = f"{uuid.uuid4().hex}{allowed[image.content_type]}"
        (UPLOAD_DIR / name).write_bytes(content)
        image_path = f"/uploads/{name}"
    row = create_report(latitude, longitude, hazard_type[:80], severity, description[:1000], reporter_type[:40], image_path)
    return {"report": row}


@app.post("/api/reports/{report_id}/verify")
def verify(report_id: int, req: VerifyReportRequest):
    row = verify_report(report_id, req.status)
    if not row:
        raise HTTPException(404, "Report not found")
    return {"report": row}


# ---------------------------------------------------------------------------
# Alerts + realtime
# ---------------------------------------------------------------------------
@app.get("/api/alerts")
def alerts():
    return {"alerts": list_alerts(), "stream_clients": stream.connected_clients()}


@app.get("/api/alerts/stream")
async def alert_stream():
    queue = await stream.subscribe()

    async def _gen():
        try:
            yield "retry: 3000\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield payload
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await stream.unsubscribe(queue)

    return StreamingResponse(_gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _compose_message(req: BroadcastRequest) -> str:
    if req.message and req.message.strip():
        return req.message.strip()
    lines = [
        f"{req.risk_level} LANDSLIDE RISK",
        f"Location: {req.location_name} ({req.latitude:.4f}, {req.longitude:.4f})",
        f"Risk: {req.risk_score:.0f}/100",
    ]
    if req.primary_factors:
        lines.append("Primary drivers: " + "; ".join(req.primary_factors[:5]))
    lines.append("Avoid the marked area. Follow local authority instructions.")
    return "\n".join(lines)


@app.post("/api/alerts/broadcast")
async def broadcast_alert(req: BroadcastRequest):
    message = _compose_message(req)
    created, deduped = maybe_create_alert(
        req.latitude, req.longitude, req.risk_score, req.risk_level, message, req.location_name
    )
    delivery: dict = {}
    if not created and deduped:
        return {
            "status": "deduplicated",
            "message": "An identical alert for this zone/level/score bucket is already active within the cooldown window.",
            "connected_clients": stream.connected_clients(),
            "alert": None,
        }
    if not created:
        return {"status": "rejected", "message": "Alert could not be stored.", "connected_clients": stream.connected_clients()}

    event = {
        "alert_id": created["id"],
        "title": f"{req.risk_level} LANDSLIDE RISK",
        "message": message,
        "location_name": req.location_name,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "risk_level": req.risk_level,
        "risk_score": req.risk_score,
        "primary_factors": req.primary_factors,
        "status": "BROADCAST",
        "created_at": created["created_at"],
    }
    delivery = await deliver_alert(event, req.channels)

    from .db import update_alert_status
    if delivery.get("local_realtime", {}).get("clients", 0) > 0:
        update_alert_status(created["id"], "SENT", "SSE")

    sms = delivery.get("sms", {}).get("status", "NOT_CONFIGURED")
    return {
        "status": "broadcast",
        "alert_id": created["id"],
        "alert": event,
        "connected_clients": stream.connected_clients(),
        "delivered_local": delivery.get("local_realtime", {}).get("clients", 0),
        "sms": "SENT" if sms == "DELIVERED" else "NOT_CONFIGURED" if sms == "NOT_CONFIGURED" else sms,
        "email": delivery.get("email", {}).get("status", "NOT_CONFIGURED"),
        "channels": delivery,
        "deduplicated": False,
    }