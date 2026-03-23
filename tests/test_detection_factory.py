import pytest

from app.core.config import DetectionSettings
from app.detection.factory import build_detector
from app.detection.mock_detector import MockDogDetector
from app.detection.opencv_dnn_detector import OpenCVDnnDogDetector, OpenCVDnnDogDetectorConfig


def test_build_detector_returns_mock_detector() -> None:
    detector = build_detector(
        DetectionSettings(
            backend="mock",
            confidence_threshold=0.5,
            model_path=None,
            config_path=None,
            labels_path=None,
            dog_class_names=["dog"],
            input_width=640,
            input_height=640,
            scale_factor=1.0 / 255.0,
            swap_rb=True,
            stream_interface="PCIe",
        )
    )

    assert isinstance(detector, MockDogDetector)


def test_opencv_dnn_detector_requires_model_path() -> None:
    with pytest.raises(ValueError):
        OpenCVDnnDogDetector(
            OpenCVDnnDogDetectorConfig(
                model_path=None,
                config_path=None,
                labels_path=None,
                dog_class_names=["dog"],
                confidence_threshold=0.5,
            )
        )
