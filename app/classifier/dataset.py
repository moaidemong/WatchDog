from __future__ import annotations

import csv
from pathlib import Path
from app.core.schemas import EventFeatureVector


FEATURE_COLUMNS = [
    "event_id",
    "duration_s",
    "attempt_count",
    "body_lift_ratio",
    "progress_ratio",
    "pose_confidence_mean",
    "label",
]


def append_labeled_feature_row(path: str | Path, features: EventFeatureVector, label: str) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    exists = file_path.exists()
    with file_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FEATURE_COLUMNS)
        if not exists:
            writer.writeheader()
        row = features.to_dict() | {"label": label}
        writer.writerow(row)
