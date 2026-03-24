from __future__ import annotations

import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import load_settings
from app.review.exporter import ReviewQueueExporter


def main() -> None:
    parser = argparse.ArgumentParser(description="Export review queue manifests")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--output-dir", help="Optional output directory override")
    parser.add_argument(
        "--auto-triage",
        action="store_true",
        help="Pre-fill review_status/review_label/review_notes with conservative auto-triage",
    )
    args = parser.parse_args()

    settings = load_settings(args.config)
    result = ReviewQueueExporter(settings.storage).export(
        export_dir=args.output_dir,
        auto_triage=args.auto_triage,
    )
    print(
        f"exported {result.row_count} review items to "
        f"{result.csv_path} and {result.jsonl_path}"
    )


if __name__ == "__main__":
    main()
