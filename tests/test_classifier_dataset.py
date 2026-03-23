import csv
from pathlib import Path

from app.classifier.dataset import load_reviewed_training_rows, summarize_reviewed_training_rows


def test_load_reviewed_training_rows_joins_features_with_reviewed_labels(tmp_path: Path) -> None:
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
                "end_s": "3.0",
                "duration_s": "1.0",
                "predicted_label": "no_alert",
                "review_label": "rest_normal",
                "review_status": "pending",
                "review_notes": "",
                "clip_path": "clip2.mp4",
                "snapshot_path": "snapshot2.jpg",
            }
        )

    rows = load_reviewed_training_rows(feature_path, labels_path)

    assert len(rows) == 1
    assert rows[0].event_id == "event-1"
    assert rows[0].review_label == "get_up_fail"
    assert rows[0].feature_dict()["attempt_count"] == 2.0


def test_summarize_reviewed_training_rows_counts_labels(tmp_path: Path) -> None:
    feature_path = tmp_path / "feature_dataset.csv"
    labels_path = tmp_path / "clips.csv"
    feature_path.write_text(
        "event_id,duration_s,attempt_count,body_lift_ratio,progress_ratio,pose_confidence_mean,label\n"
        "event-1,5.0,2,0.15,0.30,0.91,failed_get_up_attempt\n"
        "event-2,4.0,1,0.05,0.90,0.88,no_alert\n",
        encoding="utf-8",
    )
    labels_path.write_text(
        "event_id,captured_at,start_s,end_s,duration_s,predicted_label,review_label,review_status,review_notes,clip_path,snapshot_path\n"
        "event-1,2026-03-21T00:00:00Z,1.0,6.0,5.0,failed_get_up_attempt,get_up_fail,approved,confirmed,clip.mp4,snapshot.jpg\n"
        "event-2,2026-03-21T00:00:00Z,2.0,6.0,4.0,no_alert,rest_normal,approved,confirmed,clip2.mp4,snapshot2.jpg\n",
        encoding="utf-8",
    )

    summary = summarize_reviewed_training_rows(load_reviewed_training_rows(feature_path, labels_path))

    assert summary["row_count"] == 2
    assert summary["label_counts"] == {"get_up_fail": 1, "rest_normal": 1}
