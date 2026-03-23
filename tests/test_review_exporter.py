import json
from pathlib import Path

from app.core.config import StorageSettings
from app.review.exporter import ReviewQueueExporter


def test_review_queue_exporter_writes_csv_and_jsonl(tmp_path: Path) -> None:
    review_queue_dir = tmp_path / "review_queue"
    review_queue_dir.mkdir()
    payload = {
        "captured_at": "2026-03-21T00:00:00Z",
        "event": {
            "event_id": "event-1",
            "start_s": 1.0,
            "end_s": 6.0,
            "duration_s": 5.0,
            "frame_count": 7,
        },
        "media": {
            "event_dir": str(tmp_path / "artifacts" / "event-1"),
            "clip_path": str(tmp_path / "artifacts" / "event-1" / "clip.mp4"),
            "snapshot_path": str(tmp_path / "artifacts" / "event-1" / "snapshot.jpg"),
        },
        "decision": {
            "label": "failed_get_up_attempt",
            "should_alert": True,
            "score": 0.93,
            "reasons": ["attempt_count>=2", "progress_ratio<=0.5"],
        },
    }
    (review_queue_dir / "event-1.json").write_text(json.dumps(payload), encoding="utf-8")

    exporter = ReviewQueueExporter(
        StorageSettings(
            artifacts_dir=tmp_path / "artifacts",
            review_queue_dir=review_queue_dir,
            exports_dir=tmp_path / "exports",
        )
    )

    result = exporter.export()

    assert result.row_count == 1
    assert result.csv_path.exists()
    assert result.jsonl_path.exists()
    csv_text = result.csv_path.read_text(encoding="utf-8")
    jsonl_text = result.jsonl_path.read_text(encoding="utf-8")
    assert "event-1" in csv_text
    assert "failed_get_up_attempt" in csv_text
    assert "event-1" in jsonl_text
