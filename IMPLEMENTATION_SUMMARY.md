# Implementation summary

## Added

- `backend/` FastAPI service with model registry, risk engine, live-data adapters, SQLite persistence and alert deduplication.
- Real coordinate-driven risk API and what-if simulation API.
- Open-Meteo weather adapter and DEM-derived terrain adapter.
- Nominatim reverse geocoding and OSM Overpass nearby-asset discovery.
- Model artifact packaging for Models 1–3 and fusion.
- Explicit provenance/fallback tracking for model features.
- Persistent citizen reports with browser GPS and validated image upload.
- Persistent alert records with demo-only send state.
- Frontend API client and backend health integration.
- `.env.example` files and complete README/run instructions.

## Reworked

- Risk map now analyzes clicked coordinates instead of displaying fake live overlays.
- Model section now describes the supplied artifacts accurately.
- Hero removes unsupported accuracy/realtime/edge-deployment claims.
- Citizen reporting is no longer mock-only.
- Alert section shows persisted alert state rather than claiming SMS delivery.
- Risk thresholds now follow the fusion config: 25 / 55 / 80.

## Removed

- Unused legacy `src/components/RiskMap.tsx` hardcoded map implementation.
- Unused hardcoded chart/displacement/impact exports from `mockData.ts`.

## Intentionally not claimed as real

- Model 4 spatial vulnerability (wrong supplied artifact).
- Full fusion output by default.
- Local WSN sensor readings where no sensor feed exists.
- InSAR displacement / satellite micro-crack detection.
- Real SMS delivery.
- Real relief-camp occupancy.

See `README.md` for exact setup commands and remaining model inputs needed.
