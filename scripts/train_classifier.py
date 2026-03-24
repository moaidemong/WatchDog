from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.classifier.train import train_classifier
from app.core.config import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Load reviewed classifier dataset and print summary")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument(
        "--feature-dataset",
        help="Optional feature dataset CSV override",
    )
    parser.add_argument(
        "--reviewed-labels",
        help="Optional reviewed labels CSV override",
    )
    parser.add_argument(
        "--output-model",
        help="Optional model output path override",
    )
    parser.add_argument(
        "--min-samples-per-label",
        type=int,
        default=5,
        help="Minimum approved samples required for a label to be included in the prototype model",
    )
    args = parser.parse_args()

    settings = load_settings(args.config)
    feature_dataset_path = args.feature_dataset or (settings.storage.exports_dir / "feature_dataset.csv")
    reviewed_labels_path = args.reviewed_labels or (settings.storage.exports_dir / "labels" / "clips.csv")
    summary = train_classifier(
        feature_dataset_path,
        reviewed_labels_path,
        min_samples_per_label=max(1, args.min_samples_per_label),
    )
    model = summary.pop("model")
    output_model = args.output_model or (settings.storage.exports_dir / "models" / "prototype_classifier.json")
    model_path = model.save(output_model)
    summary["model_path"] = str(model_path)
    summary["prototype_count"] = len(model.prototypes)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
