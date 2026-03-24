from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    event_id TEXT PRIMARY KEY,
    camera_id TEXT NOT NULL,
    captured_at TEXT,
    start_s REAL,
    end_s REAL,
    duration_s REAL,
    frame_count INTEGER,
    predicted_label TEXT,
    should_alert INTEGER NOT NULL DEFAULT 0,
    decision_score REAL NOT NULL DEFAULT 0,
    decision_reasons TEXT NOT NULL DEFAULT '',
    clip_path TEXT NOT NULL,
    snapshot_path TEXT NOT NULL,
    metadata_path TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'pending',
    review_label TEXT NOT NULL DEFAULT '',
    review_notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_reviews_camera_id ON reviews(camera_id);
CREATE INDEX IF NOT EXISTS idx_reviews_review_status ON reviews(review_status);
CREATE INDEX IF NOT EXISTS idx_reviews_review_label ON reviews(review_label);
"""


def initialize_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def connect(db_path: Path):
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
    finally:
        conn.close()
