from __future__ import annotations

from app.core.config import IngestSettings
from app.ingest.frame_source import FrameSource
from app.ingest.mock_source import MockFrameSource
from app.ingest.opencv_source import OpenCVFrameSource, OpenCVFrameSourceConfig
from app.ingest.picamera2_source import Picamera2FrameSource, Picamera2FrameSourceConfig


def build_frame_source(settings: IngestSettings) -> FrameSource:
    if settings.backend == "mock":
        total_frames = settings.max_frames if settings.max_frames is not None else 60
        return MockFrameSource(total_frames=total_frames, fps=settings.sample_fps)

    if settings.backend == "opencv":
        return OpenCVFrameSource(
            OpenCVFrameSourceConfig(
                camera_index=settings.camera_index,
                device_path=settings.device_path,
                sample_fps=settings.sample_fps,
                max_frames=settings.max_frames,
            )
        )

    if settings.backend == "picamera2":
        return Picamera2FrameSource(
            Picamera2FrameSourceConfig(
                sample_fps=settings.sample_fps,
                max_frames=settings.max_frames,
                frame_width=settings.frame_width,
                frame_height=settings.frame_height,
            )
        )

    raise ValueError(f"unsupported ingest backend: {settings.backend}")
