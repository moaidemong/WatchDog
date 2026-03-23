import csv
import json
from pathlib import Path

from app.core.config import StorageSettings
from app.review.importer import ReviewLabelImporter


def test_review_label_importer_updates_labels_and_metadata(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    event_dir = artifacts_dir / "event-1"
    event_dir.mkdir(parents=True)
    metadata_path = event_dir / "metadata.json"
    metadata_path.write_text(json.dumps({"event": {"event_id": "event-1"}}), encoding="utf-8")

    review_queue_dir = tmp_path / "review_queue"
    review_queue_dir.mkdir()
    queue_path = review_queue_dir / "event-1.json"
    queue_path.write_text(json.dumps({"event": {"event_id": "event-1"}}), encoding="utf-8")

    exports_dir = tmp_path / "exports"
    manifest_path = exports_dir / "review_export" / "review_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=[
                "event_id",
                "captured_at",
                "start_s",
                "end_s",
                "duration_s",
                "frame_count",
                "predicted_label",
                "should_alert",
                "decision_score",
                "decision_reasons",
                "clip_path",
                "snapshot_path",
                "metadata_path",
                "review_status",
                "review_label",
                "review_notes",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "event_id": "event-1",
                "captured_at": "2026-03-21T00:00:00Z",
                "start_s": "1.0",
                "end_s": "6.0",
                "duration_s": "5.0",
                "frame_count": "7",
                "predicted_label": "failed_get_up_attempt",
                "should_alert": "True",
                "decision_score": "0.93",
                "decision_reasons": "attempt_count>=2",
                "clip_path": str(event_dir / "clip.mp4"),
                "snapshot_path": str(event_dir / "snapshot.jpg"),
                "metadata_path": str(event_dir),
                "review_status": "approved",
                "review_label": "get_up_fail",
                "review_notes": "confirmed by human review",
            }
        )

    importer = ReviewLabelImporter(
        StorageSettings(
            artifacts_dir=artifacts_dir,
            review_queue_dir=review_queue_dir,
            exports_dir=exports_dir,
        )
    )

    result = importer.import_manifest(manifest_path)

    assert result.imported_count == 1
    labels_path = exports_dir / "labels" / "clips.csv"
    assert labels_path.exists()
    labels_text = labels_path.read_text(encoding="utf-8")
    assert "get_up_fail" in labels_text

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    queue_payload = json.loads(queue_path.read_text(encoding="utf-8"))
    assert metadata["review"]["label"] == "get_up_fail"
    assert queue_payload["review"]["status"] == "approved"
