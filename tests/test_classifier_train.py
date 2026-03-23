import csv
from pathlib import Path

from app.classifier.train import train_classifier


def test_train_classifier_builds_prototype_model(tmp_path: Path) -> None:
    feature_path = tmp_path / "feature_dataset.csv"
    with feature_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=[
                "event_id",
                "duration_s",
                "attempt_count",
                "body_lift_ratio",
                "progress_ratio",
                "pose_confidence_mean",
                "label",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "event_id": "event-1",
                "duration_s": "5.0",
                "attempt_count": "2",
                "body_lift_ratio": "0.15",
                "progress_ratio": "0.30",
                "pose_confidence_mean": "0.91",
                "label": "failed_get_up_attempt",
            }
        )
        writer.writerow(
            {
                "event_id": "event-2",
                "duration_s": "3.0",
                "attempt_count": "0",
                "body_lift_ratio": "0.03",
                "progress_ratio": "0.92",
                "pose_confidence_mean": "0.95",
                "label": "no_alert",
            }
        )

    labels_path = tmp_path / "clips.csv"
    with labels_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=[
                "event_id",
                "captured_at",
                "start_s",
                "end_s",
                "duration_s",
                "predicted_label",
                "review_label",
                "review_status",
                "review_notes",
                "clip_path",
                "snapshot_path",
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
                "predicted_label": "failed_get_up_attempt",
                "review_label": "get_up_fail",
                "review_status": "approved",
                "review_notes": "confirmed",
                "clip_path": "clip.mp4",
                "snapshot_path": "snapshot.jpg",
            }
        )
        writer.writerow(
            {
                "event_id": "event-2",
                "captured_at": "2026-03-21T00:00:00Z",
                "start_s": "2.0",
                "end_s": "5.0",
                "duration_s": "3.0",
                "predicted_label": "no_alert",
                "review_label": "rest_normal",
                "review_status": "approved",
                "review_notes": "confirmed",
                "clip_path": "clip2.mp4",
                "snapshot_path": "snapshot2.jpg",
            }
        )

    summary = train_classifier(feature_path, labels_path)

    assert summary["row_count"] == 2
    assert len(summary["model"].prototypes) == 2
    assert {prototype.label for prototype in summary["model"].prototypes} == {
        "get_up_fail",
        "rest_normal",
    }
