import pytest

from app.core.config import CameraSettings, IngestSettings
from app.ingest.factory import build_frame_source
from app.ingest.mock_source import MockFrameSource
from app.ingest.opencv_source import OpenCVFrameSource
from app.ingest.picamera2_source import Picamera2FrameSource


def test_build_frame_source_returns_mock_source() -> None:
    source = build_frame_source(
        IngestSettings(
            backend="mock",
            camera_id="mock-camera",
            camera_index=0,
            device_path=None,
            rtsp_url=None,
            sample_fps=1.0,
            max_frames=10,
            frame_width=None,
            frame_height=None,
        )
    )

    assert isinstance(source, MockFrameSource)


def test_build_frame_source_returns_opencv_source() -> None:
    source = build_frame_source(
        IngestSettings(
            backend="opencv",
            camera_id="a",
            camera_index=0,
            device_path="/dev/video0",
            rtsp_url=None,
            sample_fps=1.0,
            max_frames=10,
            frame_width=None,
            frame_height=None,
        )
    )

    assert isinstance(source, OpenCVFrameSource)


def test_build_frame_source_uses_selected_rtsp_camera() -> None:
    source = build_frame_source(
        IngestSettings(
            backend="opencv",
            camera_id="2",
            camera_index=0,
            device_path=None,
            rtsp_url=None,
            sample_fps=1.0,
            max_frames=10,
            frame_width=None,
            frame_height=None,
        ),
        cameras=[
            CameraSettings(camera_id="a", rtsp_url="rtsp://a", aliases=["1"], enabled=True),
            CameraSettings(camera_id="b", rtsp_url="rtsp://b", aliases=["2"], enabled=True),
        ],
    )

    assert isinstance(source, OpenCVFrameSource)
    assert source.config.rtsp_url == "rtsp://b"
    assert source.config.camera_id == "b"


def test_build_frame_source_returns_picamera2_source() -> None:
    source = build_frame_source(
        IngestSettings(
            backend="picamera2",
            camera_id="pi-cam",
            camera_index=0,
            device_path=None,
            rtsp_url=None,
            sample_fps=1.0,
            max_frames=10,
            frame_width=1280,
            frame_height=720,
        )
    )

    assert isinstance(source, Picamera2FrameSource)


def test_build_frame_source_rejects_unknown_backend() -> None:
    with pytest.raises(ValueError):
        build_frame_source(
            IngestSettings(
                backend="unknown",
                camera_id="unknown",
                camera_index=0,
                device_path=None,
                rtsp_url=None,
                sample_fps=1.0,
                max_frames=10,
                frame_width=None,
                frame_height=None,
            )
        )
