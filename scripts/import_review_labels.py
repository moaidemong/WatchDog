from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import load_settings
from app.review.importer import ReviewLabelImporter


def main() -> None:
    parser = argparse.ArgumentParser(description="Import reviewed labels from manifest CSV")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--manifest", required=True, help="Path to review manifest CSV")
    args = parser.parse_args()

    settings = load_settings(args.config)
    result = ReviewLabelImporter(settings.storage).import_manifest(args.manifest)
    print(f"imported {result.imported_count} reviewed items into {result.labels_path}")


if __name__ == "__main__":
    main()
