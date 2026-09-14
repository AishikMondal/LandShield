from __future__ import annotations
import asyncio
import time
from datetime import datetime, timezone

from .risk import assess, risk_level
from ..config import (
    HOTSPOT_REFRESH_MINUTES,
    HOTSPOT_TOP_N,
    HOTSPOT_MAX_CONCURRENCY,
)
from ..ner import HOTSPOT_CANDIDATES

# In-memory cache of ranked hotspots.
_cache: dict = {"status": "idle", "started_at": None, "finished_at": None, "items": [], "raw": {}}
_refresh_task: asyncio.Task | None = None
_lock = asyncio.Lock()

_REFRESH_TTL_SECONDS = HOTSPOT_REFRESH_MINUTES * 60


def _fresh() -> bool:
    finished = _cache.get("finished_at")
    if not finished:
        return False
    return (time.monotonic() - finished) < _REFRESH_TTL_SECONDS


async def _compute_all():
    sem = asyncio.Semaphore(HOTSPOT_MAX_CONCURRENCY)

    async def one(c):
        async with sem:
            try:
                r = await assess(c["lat"], c["lon"])
                return {**c, "result": r}
            except Exception as e:  # noqa: BLE001 - keep the grid going
                return {**c, "error": str(e)[:200]}

    results = await asyncio.gather(*[one(c) for c in HOTSPOT_CANDIDATES], return_exceptions=False)
    items_raw = []
    for r in results:
        if r.get("error"):
            continue
        res = r["result"]
        score = res.get("risk_score", 0.0)
        items_raw.append({
            "rank": 0,
            "latitude": r["lat"],
            "longitude": r["lon"],
            "location_name": r["name"],
            "district": r["district"],
            "state": r["state"],
            "risk_score": score,
            "risk_level": res.get("risk_level") or risk_level(score),
            "generated_at": res.get("generated_at"),
            "data_freshness": _freshness_label(res),
            "primary_factors": res.get("why_high_risk", [])[:4],
        })
    items_raw.sort(key=lambda x: (-x["risk_score"], x["location_name"]))
    for i, item in enumerate(items_raw[:HOTSPOT_TOP_N], start=1):
        item["rank"] = i
    return items_raw


def _freshness_label(res: dict) -> str:
    prov = res.get("provenance", {})
    w = prov.get("weather") or {}
    t = prov.get("terrain") or {}
    parts = []
    if w.get("observed_at"):
        parts.append(f"weather {w.get('observed_at', '')[:16].replace('T', ' ')} UTC")
    if t.get("source_type") == "DEM_DERIVED":
        parts.append("terrain DEM-derived")
    return "; ".join(parts) or "no live data"


async def refresh_hotspots(force: bool = False) -> None:
    global _refresh_task
    async with _lock:
        if _fresh() and not force:
            return
        if _refresh_task and not _refresh_task.done():
            return
        _cache["status"] = "refreshing"
        _cache["started_at"] = time.monotonic()
        _refresh_task = asyncio.create_task(_run_refresh())


async def _run_refresh() -> None:
    try:
        items = await _compute_all()
        _cache["items"] = items
        _cache["status"] = "ready"
        _cache["finished_at"] = time.monotonic()
    except Exception as e:  # noqa: BLE001
        _cache["status"] = "error"
        _cache["last_error"] = str(e)


def hotspot_payload() -> dict:
    """Return the current hotspot state without blocking on a live refresh."""
    items = _cache.get("items", [])
    finished = _cache.get("finished_at")
    last_refresh = datetime.now(timezone.utc).isoformat()
    freshness = "no data yet"
    if finished:
        minutes = int((time.monotonic() - finished) // 60)
        freshness = f"updated {minutes} min ago" if minutes < 120 else f"updated {minutes // 60} h ago"
        last_refresh = datetime.fromtimestamp(finished, timezone.utc).isoformat()
    return {
        "status": _cache.get("status", "idle"),
        "last_refresh": last_refresh,
        "refresh_interval_minutes": HOTSPOT_REFRESH_MINUTES,
        "candidates_evaluated": len(_cache.get("items", [])),
        "total_candidates": len(HOTSPOT_CANDIDATES),
        "hotspots": items,
        "freshness": freshness,
    }