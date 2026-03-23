from app.detection.opencv_dnn_detector import OpenCVDnnDogDetector, OpenCVDnnDogDetectorConfig


def test_decode_outputs_filters_to_dog_class() -> None:
    detector = object.__new__(OpenCVDnnDogDetector)
    detector.config = OpenCVDnnDogDetectorConfig(
        model_path="dummy.onnx",
        config_path=None,
        labels_path=None,
        dog_class_names=["dog"],
        confidence_threshold=0.5,
    )
    detector._labels = ["person", "dog"]

    detections = detector._decode_outputs(
        [
            [10, 20, 110, 220, 0.8, 1],
            [5, 5, 25, 25, 0.9, 0],
        ],
        image_width=200,
        image_height=400,
    )

    assert len(detections) == 1
    assert detections[0].label == "dog"
    assert detections[0].confidence == 0.8


def test_decode_outputs_ignores_low_confidence() -> None:
    detector = object.__new__(OpenCVDnnDogDetector)
    detector.config = OpenCVDnnDogDetectorConfig(
        model_path="dummy.onnx",
        config_path=None,
        labels_path=None,
        dog_class_names=["dog"],
        confidence_threshold=0.5,
    )
    detector._labels = ["dog"]

    detections = detector._decode_outputs(
        [[10, 20, 110, 220, 0.2, 0]],
        image_width=200,
        image_height=400,
    )

    assert detections == []
