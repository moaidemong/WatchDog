from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import load_settings
from app.detection.factory import build_detector


def main() -> None:
    parser = argparse.ArgumentParser(description="Run detector on a single snapshot image")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--image", required=True, help="Path to input image")
    args = parser.parse_args()

    settings = load_settings(args.config)
    detector = build_detector(settings.detection)

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required to read snapshot images") from exc

    image = cv2.imread(args.image)
    if image is None:
        raise RuntimeError(f"failed to read image: {args.image}")

    if not hasattr(detector, "detect_image"):
        raise RuntimeError(
            f"detector backend '{settings.detection.backend}' does not support direct snapshot detection"
        )

    detections = detector.detect_image(image)
    payload = [
        {
            "label": detection.label,
            "confidence": detection.confidence,
            "bbox": {
                "x1": detection.bbox.x1,
                "y1": detection.bbox.y1,
                "x2": detection.bbox.x2,
                "y2": detection.bbox.y2,
            },
        }
        for detection in detections
    ]
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
