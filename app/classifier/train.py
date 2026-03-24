from __future__ import annotations

from pathlib import Path

from app.classifier.dataset import load_reviewed_training_rows, summarize_reviewed_training_rows
from app.classifier.model import FEATURE_NAMES, Prototype, PrototypeModel


def train_classifier(
    feature_dataset_path: str | Path,
    reviewed_labels_path: str | Path,
    *,
    min_samples_per_label: int = 1,
) -> dict[str, object]:
    rows = load_reviewed_training_rows(feature_dataset_path, reviewed_labels_path)
    summary = summarize_reviewed_training_rows(rows)
    label_counts = dict(summary["label_counts"])
    included_labels = sorted([label for label, count in label_counts.items() if count >= min_samples_per_label])
    excluded_labels = {
        label: count for label, count in label_counts.items() if count < min_samples_per_label
    }
    filtered_rows = [row for row in rows if row.review_label in set(included_labels)]
    prototypes = _build_prototypes(filtered_rows)
    summary["model"] = PrototypeModel(
        model_type="nearest_prototype",
        feature_names=FEATURE_NAMES.copy(),
        prototypes=prototypes,
    )
    summary["min_samples_per_label"] = min_samples_per_label
    summary["included_labels"] = included_labels
    summary["excluded_labels"] = excluded_labels
    summary["training_row_count"] = len(filtered_rows)
    return summary


def _build_prototypes(rows) -> list[Prototype]:
    grouped: dict[str, list[dict[str, float]]] = {}
    for row in rows:
        grouped.setdefault(row.review_label, []).append(row.feature_dict())

    prototypes: list[Prototype] = []
    for label, feature_rows in grouped.items():
        center = {
            feature_name: sum(row[feature_name] for row in feature_rows) / len(feature_rows)
            for feature_name in FEATURE_NAMES
        }
        prototypes.append(
            Prototype(
                label=label,
                center={name: round(value, 6) for name, value in center.items()},
                sample_count=len(feature_rows),
            )
        )
    prototypes.sort(key=lambda item: item.label)
    return prototypes
