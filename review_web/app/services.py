from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import load_settings
from app.review.exporter import REVIEW_EXPORT_COLUMNS, ReviewQueueExporter
from review_web.app.translations import REVIEW_LABEL_OPTIONS, REVIEW_STATUS_OPTIONS


def bootstrap_or_sync_from_watchdog(
    conn,
    *,
    watchdog_root: Path,
    config_path: Path,
) -> int:
    settings = load_settings(config_path)
    ReviewQueueExporter(settings.storage).export(auto_triage=True)
    manifest_path = watchdog_root / settings.storage.exports_dir / "review_export" / "review_manifest.csv"
    rows = _read_manifest_rows(manifest_path)
    return sync_rows_into_db(conn, rows)


def sync_rows_into_db(conn, rows: list[dict[str, str]]) -> int:
    now = _utc_now()
    inserted = 0
    for row in rows:
        event_id = row.get("event_id", "")
        if not event_id:
            continue
        camera_id = event_id.split("-", 1)[0]
        existing = conn.execute(
            "SELECT review_status, review_label, review_notes FROM reviews WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        review_status = row.get("review_status", "pending") or "pending"
        review_label = row.get("review_label", "")
        review_notes = row.get("review_notes", "")
        if existing is not None:
            if existing["review_status"] != "pending" or existing["review_label"] or existing["review_notes"]:
                review_status = existing["review_status"]
                review_label = existing["review_label"]
                review_notes = existing["review_notes"]
            conn.execute(
                """
                UPDATE reviews
                SET camera_id = ?, captured_at = ?, start_s = ?, end_s = ?, duration_s = ?, frame_count = ?,
                    predicted_label = ?, should_alert = ?, decision_score = ?, decision_reasons = ?,
                    clip_path = ?, snapshot_path = ?, metadata_path = ?,
                    review_status = ?, review_label = ?, review_notes = ?, updated_at = ?
                WHERE event_id = ?
                """,
                (
                    camera_id,
                    row.get("captured_at", ""),
                    _to_float(row.get("start_s")),
                    _to_float(row.get("end_s")),
                    _to_float(row.get("duration_s")),
                    _to_int(row.get("frame_count")),
                    row.get("predicted_label", ""),
                    _to_bool_int(row.get("should_alert")),
                    _to_float(row.get("decision_score")),
                    row.get("decision_reasons", ""),
                    row.get("clip_path", ""),
                    row.get("snapshot_path", ""),
                    row.get("metadata_path", ""),
                    review_status,
                    review_label,
                    review_notes,
                    now,
                    event_id,
                ),
            )
            continue

        conn.execute(
            """
            INSERT INTO reviews (
                event_id, camera_id, captured_at, start_s, end_s, duration_s, frame_count,
                predicted_label, should_alert, decision_score, decision_reasons,
                clip_path, snapshot_path, metadata_path,
                review_status, review_label, review_notes, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                event_id,
                camera_id,
                row.get("captured_at", ""),
                _to_float(row.get("start_s")),
                _to_float(row.get("end_s")),
                _to_float(row.get("duration_s")),
                _to_int(row.get("frame_count")),
                row.get("predicted_label", ""),
                _to_bool_int(row.get("should_alert")),
                _to_float(row.get("decision_score")),
                row.get("decision_reasons", ""),
                row.get("clip_path", ""),
                row.get("snapshot_path", ""),
                row.get("metadata_path", ""),
                review_status,
                review_label,
                review_notes,
                now,
                now,
            ),
        )
        inserted += 1
    return inserted


def export_db_to_manifest(conn, manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    rows = conn.execute(
        """
        SELECT
            event_id,
            captured_at,
            start_s,
            end_s,
            duration_s,
            frame_count,
            predicted_label,
            should_alert,
            decision_score,
            decision_reasons,
            clip_path,
            snapshot_path,
            metadata_path,
            review_status,
            review_label,
            review_notes
        FROM reviews
        ORDER BY captured_at DESC, event_id DESC
        """
    ).fetchall()
    with manifest_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=REVIEW_EXPORT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def query_reviews(
    conn,
    *,
    offset: int,
    limit: int,
    camera_id: str | None,
    review_status: str | None,
    review_label: str | None,
    q: str | None,
) -> tuple[int, list[dict[str, Any]]]:
    clauses: list[str] = []
    params: list[Any] = []
    if camera_id:
        clauses.append("camera_id = ?")
        params.append(camera_id)
    if review_status:
        clauses.append("review_status = ?")
        params.append(review_status)
    if review_label:
        clauses.append("review_label = ?")
        params.append(review_label)
    if q:
        clauses.append(
            "(event_id LIKE ? OR review_notes LIKE ? OR decision_reasons LIKE ? OR predicted_label LIKE ?)"
        )
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern, pattern])

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    total = conn.execute(f"SELECT COUNT(*) FROM reviews {where_sql}", params).fetchone()[0]
    rows = conn.execute(
        f"""
        SELECT *
        FROM reviews
        {where_sql}
        ORDER BY captured_at DESC, event_id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()
    return total, [dict(row) for row in rows]


def update_review(
    conn,
    *,
    event_id: str,
    version: int,
    review_status: str,
    review_label: str,
    review_notes: str,
) -> dict[str, Any] | None:
    if review_status not in REVIEW_STATUS_OPTIONS:
        raise ValueError(f"unsupported review_status: {review_status}")
    if review_label and review_label not in REVIEW_LABEL_OPTIONS:
        raise ValueError(f"unsupported review_label: {review_label}")

    now = _utc_now()
    cursor = conn.execute(
        """
        UPDATE reviews
        SET review_status = ?, review_label = ?, review_notes = ?, updated_at = ?, version = version + 1
        WHERE event_id = ? AND version = ?
        """,
        (review_status, review_label, review_notes, now, event_id, version),
    )
    if cursor.rowcount == 0:
        return None
    row = conn.execute("SELECT * FROM reviews WHERE event_id = ?", (event_id,)).fetchone()
    return dict(row) if row is not None else None


def media_path_for_event(conn, *, event_id: str, kind: str, watchdog_root: Path) -> Path | None:
    if kind not in {"clip", "snapshot"}:
        return None
    column = "clip_path" if kind == "clip" else "snapshot_path"
    row = conn.execute(f"SELECT {column} FROM reviews WHERE event_id = ?", (event_id,)).fetchone()
    if row is None or not row[column]:
        return None
    path = (watchdog_root / row[column]).resolve()
    if kind == "clip":
        browser_path = path.with_name("clip.browser.mp4")
        if browser_path.exists():
            path = browser_path
    try:
        path.relative_to(watchdog_root.resolve())
    except ValueError:
        return None
    return path if path.exists() else None


def manifest_path_from_config(watchdog_root: Path, config_path: Path) -> Path:
    settings = load_settings(config_path)
    return watchdog_root / settings.storage.exports_dir / "review_export" / "review_manifest.csv"


def _read_manifest_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def _to_float(value: Any) -> float:
    if value in {None, ""}:
        return 0.0
    return float(value)


def _to_int(value: Any) -> int:
    if value in {None, ""}:
        return 0
    return int(float(value))


def _to_bool_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    return int(str(value).strip().lower() in {"true", "1", "yes", "on"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
