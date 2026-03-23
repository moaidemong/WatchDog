from pathlib import Path

from app.classifier.model import Prototype, PrototypeModel


def test_prototype_model_predicts_nearest_label() -> None:
    model = PrototypeModel(
        model_type="nearest_prototype",
        feature_names=[
            "duration_s",
            "attempt_count",
            "body_lift_ratio",
            "progress_ratio",
            "pose_confidence_mean",
        ],
        prototypes=[
            Prototype(
                label="get_up_fail",
                center={
                    "duration_s": 10.0,
                    "attempt_count": 3.0,
                    "body_lift_ratio": 0.2,
                    "progress_ratio": 0.2,
                    "pose_confidence_mean": 0.9,
                },
                sample_count=4,
            ),
            Prototype(
                label="rest_normal",
                center={
                    "duration_s": 3.0,
                    "attempt_count": 0.0,
                    "body_lift_ratio": 0.02,
                    "progress_ratio": 0.9,
                    "pose_confidence_mean": 0.95,
                },
                sample_count=5,
            ),
        ],
    )

    label, score = model.predict(
        {
            "duration_s": 9.0,
            "attempt_count": 2.0,
            "body_lift_ratio": 0.18,
            "progress_ratio": 0.25,
            "pose_confidence_mean": 0.91,
        }
    )

    assert label == "get_up_fail"
    assert 0.0 < score <= 1.0


def test_prototype_model_roundtrip(tmp_path: Path) -> None:
    model = PrototypeModel(
        model_type="nearest_prototype",
        feature_names=["duration_s"],
        prototypes=[
            Prototype(
                label="rest_normal",
                center={"duration_s": 3.0},
                sample_count=2,
            )
        ],
    )

    path = model.save(tmp_path / "prototype_classifier.json")
    loaded = PrototypeModel.load(path)

    assert loaded.model_type == "nearest_prototype"
    assert loaded.prototypes[0].label == "rest_normal"
