import numpy as np

from app.detection.hailo_hef_detector import HailoHefDogDetector, HailoHefDogDetectorConfig


def test_hailo_decoder_filters_to_dog_class() -> None:
    detector = object.__new__(HailoHefDogDetector)
    detector.config = HailoHefDogDetectorConfig(
        model_path="dummy.hef",
        labels_path=None,
        dog_class_names=["dog"],
        confidence_threshold=0.5,
    )
    detector._labels = ["person", "dog"]

    tensor = np.zeros((2, 5, 100), dtype=np.float32)
    tensor[1, :, 0] = [20.0, 40.0, 120.0, 140.0, 0.9]
    detections = detector._decode_nms_tensor("output", tensor, image_width=200, image_height=200)

    assert len(detections) == 1
    assert detections[0].label == "dog"
    assert round(detections[0].confidence, 4) == 0.9


def test_hailo_decoder_handles_transposed_layout() -> None:
    detector = object.__new__(HailoHefDogDetector)
    detector.config = HailoHefDogDetectorConfig(
        model_path="dummy.hef",
        labels_path=None,
        dog_class_names=["dog"],
        confidence_threshold=0.5,
    )
    detector._labels = ["dog"]

    tensor = np.zeros((1, 100, 5), dtype=np.float32)
    tensor[0, 0, :] = [10.0, 20.0, 30.0, 40.0, 0.8]
    detections = detector._decode_nms_tensor("output", tensor, image_width=100, image_height=100)

    assert len(detections) == 1
    assert detections[0].bbox.x1 == 0.2


def test_hailo_decoder_handles_ragged_class_outputs() -> None:
    detector = object.__new__(HailoHefDogDetector)
    detector.config = HailoHefDogDetectorConfig(
        model_path="dummy.hef",
        labels_path=None,
        dog_class_names=["dog"],
        confidence_threshold=0.5,
    )
    detector._labels = ["person", "dog"]

    tensor = [[[]], [[[10.0, 20.0, 30.0, 40.0, 0.95]]]]
    detections = detector._decode_nms_tensor("output", tensor, image_width=100, image_height=100)

    assert len(detections) == 1
    assert detections[0].label == "dog"


def test_hailo_decoder_keeps_normalized_coordinates() -> None:
    detector = object.__new__(HailoHefDogDetector)
    detector.config = HailoHefDogDetectorConfig(
        model_path="dummy.hef",
        labels_path=None,
        dog_class_names=["dog"],
        confidence_threshold=0.5,
    )
    detector._labels = ["dog"]

    tensor = [[[0.1, 0.2, 0.8, 0.9, 0.7]]]
    detections = detector._decode_nms_tensor("output", tensor, image_width=100, image_height=100)

    assert len(detections) == 1
    assert detections[0].bbox.x1 == 0.2
    assert detections[0].bbox.y2 == 0.8
