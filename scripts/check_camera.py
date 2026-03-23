from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import load_settings
from app.ingest.factory import build_frame_source


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture one frame from the configured camera backend")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--camera-id", help="Optional camera ID override")
    parser.add_argument("--output", default="exports/camera_check.jpg", help="Snapshot output path")
    args = parser.parse_args()

    settings = load_settings(args.config)
    if args.camera_id is not None:
        settings.ingest.camera_id = args.camera_id
    frame_source = build_frame_source(settings.ingest, settings.cameras)
    first_frame = next(iter(frame_source.read_frames()))
    image = first_frame.payload
    if image is None:
        raise RuntimeError("camera backend returned a frame without image payload")

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required to write the camera check snapshot") from exc

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), image):
        raise RuntimeError(f"failed to write snapshot to {output_path}")

    print(f"captured frame {first_frame.index} at {first_frame.timestamp_s:.3f}s -> {output_path}")


if __name__ == "__main__":
    main()
