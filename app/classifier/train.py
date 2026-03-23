from __future__ import annotations

from pathlib import Path

from app.classifier.dataset import load_reviewed_training_rows, summarize_reviewed_training_rows
from app.classifier.model import FEATURE_NAMES, Prototype, PrototypeModel


def train_classifier(
    feature_dataset_path: str | Path,
    reviewed_labels_path: str | Path,
) -> dict[str, object]:
    rows = load_reviewed_training_rows(feature_dataset_path, reviewed_labels_path)
    summary = summarize_reviewed_training_rows(rows)
    prototypes = _build_prototypes(rows)
    summary["model"] = PrototypeModel(
        model_type="nearest_prototype",
        feature_names=FEATURE_NAMES.copy(),
        prototypes=prototypes,
    )
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
