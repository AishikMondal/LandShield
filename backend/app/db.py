import sqlite3
from datetime import datetime, timezone, timedelta

from .config import DB_PATH, ALERT_COOLDOWN_MINUTES, ALERT_SCORE_BUCKET_SIZE

SCHEMA = """
CREATE TABLE IF NOT EXISTS citizen_reports (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 latitude REAL NOT NULL,
 longitude REAL NOT NULL,
 hazard_type TEXT NOT NULL,
 severity TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 reporter_type TEXT NOT NULL DEFAULT 'RESIDENT',
 image_path TEXT,
 verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS predictions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 latitude REAL NOT NULL,
 longitude REAL NOT NULL,
 risk_score REAL NOT NULL,
 risk_level TEXT NOT NULL,
 score_basis TEXT NOT NULL,
 payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 dedupe_key TEXT NOT NULL,
 latitude REAL NOT NULL,
 longitude REAL NOT NULL,
 risk_score REAL NOT NULL,
 risk_level TEXT NOT NULL,
 message TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'CREATED',
 channel TEXT NOT NULL DEFAULT 'SSE',
 created_at TEXT NOT NULL,
 sent_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_alerts_dedupe_created ON alerts(dedupe_key, created_at);
CREATE INDEX IF NOT EXISTS idx_reports_created ON citizen_reports(created_at);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Citizen reports
# ---------------------------------------------------------------------------
def create_report(latitude, longitude, hazard_type, severity, description, reporter_type, image_path):
    now = _now().isoformat()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO citizen_reports(latitude,longitude,hazard_type,severity,description,reporter_type,image_path,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (latitude, longitude, hazard_type, severity, description, reporter_type, image_path, now),
        )
        row = conn.execute("SELECT * FROM citizen_reports WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_reports(limit=50):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM citizen_reports ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def verify_report(report_id: int, status: str):
    if status not in ("VERIFIED", "REJECTED", "UNVERIFIED"):
        raise ValueError("Invalid verification status")
    with connect() as conn:
        cur = conn.execute("UPDATE citizen_reports SET verification_status=? WHERE id=?", (status, report_id))
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM citizen_reports WHERE id=?", (report_id,)).fetchone()
    return dict(row)


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------
def save_prediction(latitude, longitude, score, level, basis, payload_json):
    now = _now().isoformat()
    with connect() as conn:
        conn.execute(
            "INSERT INTO predictions(latitude,longitude,risk_score,risk_level,score_basis,payload_json,created_at) VALUES(?,?,?,?,?,?,?)",
            (latitude, longitude, score, level, basis, payload_json, now),
        )


# ---------------------------------------------------------------------------
# Alerts (deduplicated + cooldown + score-bucket aware)
# ---------------------------------------------------------------------------
def _dedupe_key(lat, lon, level, score, location_name):
    bucket = int(score // ALERT_SCORE_BUCKET_SIZE)
    name_key = (location_name or "").strip().lower()[:24].replace(":", "").replace("|", "")
    return f"{lat:.2f}:{lon:.2f}|{name_key}|{level}|{bucket}"


def maybe_create_alert(latitude, longitude, score, level, message, location_name=""):
    """Create an alert only if it is not a redundant duplicate.

    Dedupe rule: same rounded zone + same level + same 10-point score bucket +
    same location within the cooldown window is skipped. A higher level or a
    >=bucket jump creates a new dedupe key, so escalation always rebroadcasts.
    """
    if score == 0 or level == "LOW":
        return None, False
    now = _now()
    key = _dedupe_key(latitude, longitude, level, score, location_name)
    cutoff = (now - timedelta(minutes=ALERT_COOLDOWN_MINUTES)).isoformat()
    with connect() as conn:
        existing = conn.execute(
            "SELECT id FROM alerts WHERE dedupe_key=? AND created_at>=? ORDER BY id DESC LIMIT 1",
            (key, cutoff),
        ).fetchone()
        if existing:
            return None, True
        cur = conn.execute(
            "INSERT INTO alerts(dedupe_key,latitude,longitude,risk_score,risk_level,message,channel,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (key, latitude, longitude, score, level, message, "SSE", now.isoformat()),
        )
        row = conn.execute("SELECT * FROM alerts WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row), False


def update_alert_status(alert_id, status, channel="SSE"):
    now = _now().isoformat()
    with connect() as conn:
        conn.execute("UPDATE alerts SET status=?, channel=?, sent_at=? WHERE id=?", (status, channel, now, alert_id))
        row = conn.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()
    return dict(row) if row else None


def list_alerts(limit=20):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]