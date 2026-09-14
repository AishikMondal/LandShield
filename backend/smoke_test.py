"""LandShield backend smoke test.

Exercises the full API surface against a live server process (TestClient
in-process). Network-touching calls (predict, assets, hotspots) can take a few
seconds to a minute depending on public OpenWeather/DEM/Overpass/USGS latency.

Run:  .venv\\Scripts\\python.exe backend\\smoke_test.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from app.main import app


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label} {detail}")
    if not ok:
        sys.exit(1)


with TestClient(app) as client:
    health = client.get('/api/health')
    health.raise_for_status()
    h = health.json()
    check('health/api', h['api'] == 'healthy', f"(models: m1={h.get('model_1')}, m3={h.get('model_3')})")
    check('health/models-declared', all(k in h.get('models', {}) for k in ('model1', 'model2', 'model3', 'model4', 'fusion')))

    status = client.get('/api/models/status')
    status.raise_for_status()
    ms = status.json()['models']
    check('models/status', ms.get('model1', {}).get('status') == 'ACTIVE'
          and ms.get('model3', {}).get('status') == 'ACTIVE')

    report = client.post('/api/reports', data={
        'latitude': '27.3314', 'longitude': '88.6139', 'hazard_type': 'Rockfall',
        'severity': 'moderate', 'description': 'Smoke test report', 'reporter_type': 'TEST',
    })
    report.raise_for_status()
    rid = report.json()['report']['id']
    check('reports/create', rid > 0)

    verified = client.post(f'/api/reports/{rid}/verify', json={'status': 'VERIFIED'})
    verified.raise_for_status()
    check('reports/verify', verified.json()['report']['verification_status'] == 'VERIFIED')

    listing = client.get('/api/reports')
    listing.raise_for_status()
    check('reports/list', any(r['id'] == rid for r in listing.json()['reports']))

    alerts = client.get('/api/alerts')
    alerts.raise_for_status()
    check('alerts/list', 'alerts' in alerts.json() and 'stream_clients' in alerts.json())

    bc = client.post('/api/alerts/broadcast', json={
        'latitude': 27.3314, 'longitude': 88.6139, 'location_name': 'SmokeTest',
        'risk_level': 'HIGH', 'risk_score': 68,
        'primary_factors': ['smoke-test factor'],
    })
    bc.raise_for_status()
    bj = bc.json()
    check('alerts/broadcast', bj['status'] in ('broadcast', 'deduplicated'),
          f"({bj['status']}, clients={bj.get('connected_clients')})")

    print('Network-dependent checks (expect 5-60 s):')
    pred = client.post('/api/risk/predict', json={'latitude': 27.3314, 'longitude': 88.6139})
    pred.raise_for_status()
    p = pred.json()
    check('predict', 0 <= p['risk_score'] <= 100 and p['risk_level'] in ('LOW', 'MODERATE', 'HIGH', 'CRITICAL'),
          f"(score={p['risk_score']}, level={p['risk_level']}, assets={len(p['impacted_assets'])})")
    check('predict/never-fullunless-huge', p['risk_score'] < 80 or p['risk_level'] == 'CRITICAL')

    assets = client.get('/api/location/assets?latitude=27.3314&longitude=88.6139')
    assets.raise_for_status()
    check('location/assets', 'assets' in assets.json())

    hotspots = client.get('/api/risk/hotspots')
    hotspots.raise_for_status()
    hj = hotspots.json()
    check('risk/hotspots', 'hotspots' in hj, f"(status={hj.get('status')})")

print('\nSmoke test passed. Remove backend/data/landshield.db for a clean database.')