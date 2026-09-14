# LandShield — SIH26001 Landslide Risk Intelligence Prototype

LandShield is a React + FastAPI prototype for **SIH26001 — AI-Based Early Warning and Landslide Risk Monitoring System in the North Eastern Region (NER)**.

The revision repairs the biggest defect in the previous build (a universal `100/CRITICAL` score caused by feeding a percentage where 0–1 fractions were expected) and adds the requested live intelligence:

`Map coordinate (click or double-click) → live public data → feature builder → supplied ML models → risk → influence radius → nearby OSM assets → top-5 NER hotspots → SSE alert broadcast → action guidance`

## What is real in this ZIP

- OpenStreetMap/Leaflet basemap, pan/zoom, **click or double-click anywhere** to run a full analysis.
- **Repaired Model 1 scoring** — soil moisture/saturation are now fed as 0–1 fractions (the preprocessor was trained on fractions), so realistic conditions score LOW/MODERATE/HIGH and only near-maximal inputs approach CRITICAL.
- Open-Meteo **live weather** (temperature, humidity, rainfall 24h/3d/7d, soil moisture/temperature).
- Copernicus DEM elevation via Open-Meteo with local slope/aspect derived from sampled elevations.
- Nominatim reverse geocoding with an NER-bounds fallback (`app/ner.py` covers 8 NER states).
- OpenStreetMap/Overpass **nearby assets** — roads, settlements, hospitals, schools, police, fire stations, clinics — with distances and an exposure classification inside the risk-influence radius.
- **Top-5 dynamic NER hotspots** (`GET /api/risk/hotspots`) refreshed in the background over 39 real NER candidate towns, ranked by live risk score, rendered as numbered badges on the map.
- **Live alert broadcast**: `POST /api/alerts/broadcast` fans out over a real SSE channel (`GET /api/alerts/stream`) to every open dashboard; the UI shows a live alert banner + browser Notification. A second browser tab is the demo "recipient".
- Provided **Model 1** (calibrated scikit-learn classifier) and **Model 3** (IsolationForest anomaly evidence) are ACTIVE; **Model 2** (reconstructed state dict) and **Model 4**/**fusion** are DISABLED and surfaced honestly through `/api/health`, `/api/models/status` and per-response `fusion_status`.
- Each feature carries **provenance** (`LIVE_API`, `DEM_DERIVED`, `GIS`, `PROXY_DERIVED`, `DATASET_DEFAULT`, `SENSOR_UNAVAILABLE`, …). The UI renders the source badge next to every value; nothing missing is presented as a live measurement.
- SQLite persistence for predictions, citizen reports (with **verify/reject** workflow) and **deduplicated** alerts (zone + level + score bucket + cooldown).
- What-if rainfall simulator reruns the real backend pipeline — no frontend score arithmetic.

## Intentionally limited / not faked

- The supplied **Model 4** is a 5-class climate classifier, not the `spatial_vulnerability_score` required by the fusion network, so it is excluded from scoring. Fusion stays off by default; `ENABLE_EXPERIMENTAL_FUSION=true` only substitutes an explicit GIS exposure proxy and the response is still labelled experimental.
- Sensor-only features (pore pressure, seismic, acoustic emission, strain, TDR …) use training-set medians and the response is marked degraded for those fields.
- SMS/email are **reportedly NOT_CONFIGURED** unless real credentials exist — the backend never claims a delivery it did not make.
- Original reference polygons remain as demo/dataset context, clearly labelled.
- Emergency contact numbers are reference content — verify before operational use.
- Public Overpass mirrors are frequently slow or overloaded. When every configured mirror times out, the pipeline completes with OSM unavailable and marks the inputs degraded — it never shows fake assets.

## Architecture

```text
React + Vite + Leaflet (click/double-click, hotspots, alert banner)
        |
        | HTTP (REST + SSE for alerts)
        v
FastAPI modular backend (app/)
  |-- services/data_sources.py  Open-Meteo weather · DEM terrain · Nominatim · Overpass · USGS · SoilGrids
  |-- services/features.py      Feature builder + per-feature provenance
  |-- services/models.py        ModelRegistry: m1 ACTIVE, m3 ACTIVE, m2/m4/fusion DISABLED
  |-- services/risk.py          assess() engine, score, level, radius, actions, why-high-risk
  |-- services/exposure.py      risk-influence radius policy + GIS exposure proxy
  |-- services/hotspots.py      Top-5 NER hotspot ranking + background refresh
  |-- realtime.py               SSE fan-out bus + NotificationProviders
  |-- db.py                     SQLite reports / predictions / deduplicated alerts
  |-- ner.py                    NER state bounds + 39 hotspot candidates
```

## Requirements

- Node.js 20+, npm 10+
- Python 3.11+ (this machine: Python 3.13.5, torch 2.14.0+cpu, scikit-learn 1.6.1)

## Install and run

### 1. Backend (port 8000)

Windows PowerShell (from project root):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item backend\.env.example backend\.env
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Backend: `http://localhost:8000` · Health: `http://localhost:8000/api/health`

### 2. Frontend (port 5173)

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend: `http://localhost:5173`

## Live-alert demo over the LAN

1. Start the backend, then open the dashboard in **two browser tabs** (same or different machines).
2. In one tab, go to **Broadcast Alert Console**, set level/score/location, and click **Broadcast Alert**.
3. The other tab immediately shows the SSE alert banner and Notification; both tabs show it in the realtime feed. `connected_clients` + `delivered_local` in the response confirm real delivery.

For a second machine, point its frontend at the backend host, e.g. `.env` with `VITE_API_BASE_URL=http://<backend-LAN-IP>:8000`. Python/uvicorn binds `127.0.0.1` by default, so run:

```powershell
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

## Environment variables (all optional)

| Variable | Default | Purpose |
|---|---:|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend → backend base URL |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins (comma-separated) |
| `ENABLE_EXPERIMENTAL_FUSION` | `false` | Proxy-based fusion; keep off for a defensible demo |
| `ENABLE_RECONSTRUCTED_MODEL2` | `false` | Inferred Model 2 architecture; keep off until original class is supplied |
| `ALERT_THRESHOLD` | `55` | Creates an alert record at/above this score |
| `ALERT_COOLDOWN_MINUTES` | `30` | Alert deduplication window |
| `RISK_THRESHOLDS` (code) | `25 / 55 / 80` | MODERATE / HIGH / CRITICAL |
| `HTTP_TIMEOUT_SECONDS` | `10` | Per-request timeout to public APIs |
| `HTTP_RETRIES` | `2` | Retry count with backoff |
| `OVERVIEW_OVERALL_TIMEOUT_SECONDS` | `35` | Hard cap for the Overpass mirror fan-out |
| `OVERPASS_ENDPOINTS` | mail.ru, osm.ch, api.de, kumi | Overpass mirror order (comma-separated) |
| `LANDSHIELD_USER_AGENT` | `Mozilla/5.0 LandShield-SIH/1.0 …` | Nominatim requires a browser-like UA (keep the prefix) |
| `SMS_PROVIDER` / `SMS_API_KEY` / `SMTP_*` / `EMAIL_FROM` | *(unset)* | Optional adapters — absent ⇒ NOT_CONFIGURED |
| `COPERNICUS_CLIENT_ID` / `_SECRET` | *(unset)* | NDVI / vegetation coverage — absent ⇒ DATASET_DEFAULT |
| `OPENWEATHER_API_KEY` | *(unset)* | Cross-check for Open-Meteo primary weather |

**No API key is required for the default demo.**

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | API/db/model/dependency readiness |
| GET | `/api/models/status` | Per-model load status + fusion reason |
| POST | `/api/risk/predict` | Full live-data risk assessment `{latitude, longitude}` |
| POST | `/api/risk/simulate` | What-if `{latitude, longitude, rainfall_multiplier, soil_moisture_delta}` |
| GET | `/api/risk/hotspots` | Top-5 NER hotspots + freshness (`?force=1` to refresh) |
| GET | `/api/location/assets` | Nearby OSM assets with exposure labels |
| GET/POST | `/api/reports` | List / create citizen reports (multipart, optional image) |
| POST | `/api/reports/{id}/verify` | `{status: VERIFIED|REJECTED|UNVERIFIED}` |
| GET | `/api/alerts` | Persisted alerts + connected SSE clients |
| GET | `/api/alerts/stream` | SSE feed (`event: alert`, JSON data) |
| POST | `/api/alerts/broadcast` | Create + deliver an alert across channels |

## Model notes

- **Model 1** — `CalibratedClassifierCV(LogisticRegression)` on 30 features, preprocessed by `SimpleImputer → RobustScaler`. ACTIVE. Feeding fractions for `Soil_Moisture_Content`/`Soil_Saturation` fixed the saturation bug.
- **Model 2** — PyTorch state dict implies `34 → 64 → 32 → 16 → 1`; reconstruction-enabled path is opt-in, OFF by default.
- **Model 3** — IsolationForest anomaly evidence, ACTIVE as supporting evidence only.
- **Model 4 / Fusion** — Model 4 is a 5-class climate classifier; not compatible with the fusion spatial-vulnerability input. Fusion DISABLED by default.

Bonus: model-check `backend/scripts/check_models.py` (or your own probe) prints the real pipeline shapes/scaler centers used to diagnose the fraction bug.

## Testing

Frontend:

```bash
npm run typecheck
npm run lint
npm run build
```

Backend:

```bash
.\.venv\Scripts\python.exe -m compileall backend\app
.\.venv\Scripts\python.exe backend\smoke_test.py        # exercises all endpoints incl. predict
```

## SIH demo walkthrough

1. Launch backend + frontend (see above); two browser tabs is best.
2. **Pick a coordinate** (click or double-click) — watch source badges: live weather, DEM terrain, OSM assets.
3. Show the score can change across the NER (coastal plains LOW vs. hills HIGH/Moderate) and that it is no longer pinned at 100.
4. Open **Model Stack** and `/api/models/status` — m1/m3 ACTIVE, m2/m4/fusion honestly disabled.
5. Show **Top-5 NER hotspots** — numbered badges, click one to fly to its analysis.
6. Show **nearby assets** with distance + exposure + the influence-radius circle.
7. Run the **rainfall what-if** slider and compare current vs scenario.
8. Submit a citizen report from your browser GPS with an image; verify/reject it as an authority.
9. **Broadcast an alert** from the console and watch it appear instantly in the other tab (SSE + Notification).
10. Check `/api/health` for live dependency statuses.

## Important disclaimer

LandShield in this ZIP is an SIH research/prototype system. It must not be used as the sole basis for evacuation, road closure, or emergency decisions without validation against official observations and competent authorities.