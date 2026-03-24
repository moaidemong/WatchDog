from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.events.models import EventWindow


@dataclass(slots=True)
class EventMediaArtifacts:
    event_dir: Path
    clip_path: Path | None
    snapshot_path: Path | None


class EventClipSaver:
    """Persist event clips and snapshots when frame payloads contain images."""

    def save(self, base_dir: str | Path, event: EventWindow) -> EventMediaArtifacts:
        event_dir = Path(base_dir) / event.event_id
        event_dir.mkdir(parents=True, exist_ok=True)

        image_frames = [frame.payload for frame in event.frames if self._is_image_payload(frame.payload)]
        if not image_frames:
            return EventMediaArtifacts(event_dir=event_dir, clip_path=None, snapshot_path=None)

        clip_path = event_dir / "clip.mp4"
        snapshot_path = event_dir / "snapshot.jpg"
        self._write_clip(clip_path, image_frames, fps=self._estimate_fps(event))
        self._write_snapshot(snapshot_path, image_frames[0])
        return EventMediaArtifacts(
            event_dir=event_dir,
            clip_path=clip_path,
            snapshot_path=snapshot_path,
        )

    def _estimate_fps(self, event: EventWindow) -> float:
        if len(event.frames) < 2:
            return 1.0

        deltas = [
            current.timestamp_s - previous.timestamp_s
            for previous, current in zip(event.frames, event.frames[1:])
            if (current.timestamp_s - previous.timestamp_s) > 0
        ]
        if not deltas:
            return 1.0
        return max(1.0, round(1.0 / (sum(deltas) / len(deltas)), 2))

    def _write_clip(self, path: Path, frames: list[Any], fps: float) -> None:
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover - depends on runtime environment
            raise RuntimeError("OpenCV is required to write event clips.") from exc

        height, width = frames[0].shape[:2]
        raw_path = path.with_suffix(".raw.mp4")
        writer = cv2.VideoWriter(
            str(raw_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            writer.release()
            raise RuntimeError(f"failed to open video writer for {raw_path}")

        try:
            for frame in frames:
                if frame.shape[:2] != (height, width):
                    raise ValueError("all frames in an event clip must have the same shape")
                writer.write(frame)
        finally:
            writer.release()

        self._finalize_clip(raw_path, path)

    def _finalize_clip(self, raw_path: Path, final_path: Path) -> None:
        """Transcode clips to browser-friendly H.264 when ffmpeg is available."""
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raw_path.replace(final_path)
            return

        command = [
            ffmpeg,
            "-y",
            "-i",
            str(raw_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(final_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raw_path.replace(final_path)
            return

        raw_path.unlink(missing_ok=True)

    def _write_snapshot(self, path: Path, image: Any) -> None:
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover - depends on runtime environment
            raise RuntimeError("OpenCV is required to write event snapshots.") from exc

        if not cv2.imwrite(str(path), image):
            raise RuntimeError(f"failed to write snapshot to {path}")

    def _is_image_payload(self, payload: object | None) -> bool:
        return hasattr(payload, "shape") and hasattr(payload, "dtype")
