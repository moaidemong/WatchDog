import numpy as np

from app.core.config import MotionGateSettings
from app.ingest.frame_source import Frame
from app.ingest.motion_gate import MotionGate


def test_motion_gate_allows_first_frame() -> None:
    gate = MotionGate(
        MotionGateSettings(
            enabled=True,
            roi=None,
            pixel_diff_threshold=10.0,
            min_changed_ratio=0.01,
        )
    )

    frame = Frame(index=0, timestamp_s=0.0, payload=np.zeros((8, 8, 3), dtype=np.uint8))
    decision = gate.evaluate(frame)

    assert decision.should_process is True


def test_motion_gate_blocks_static_second_frame() -> None:
    gate = MotionGate(
        MotionGateSettings(
            enabled=True,
            roi=None,
            pixel_diff_threshold=10.0,
            min_changed_ratio=0.05,
        )
    )
    image = np.zeros((8, 8, 3), dtype=np.uint8)

    gate.evaluate(Frame(index=0, timestamp_s=0.0, payload=image))
    decision = gate.evaluate(Frame(index=1, timestamp_s=1.0, payload=image.copy()))

    assert decision.should_process is False
    assert decision.changed_ratio == 0.0


def test_motion_gate_uses_roi() -> None:
    gate = MotionGate(
        MotionGateSettings(
            enabled=True,
            roi=(0.0, 0.0, 0.5, 0.5),
            pixel_diff_threshold=10.0,
            min_changed_ratio=0.01,
        )
    )
    first = np.zeros((10, 10, 3), dtype=np.uint8)
    second = np.zeros((10, 10, 3), dtype=np.uint8)
    second[8:, 8:] = 255

    gate.evaluate(Frame(index=0, timestamp_s=0.0, payload=first))
    decision = gate.evaluate(Frame(index=1, timestamp_s=1.0, payload=second))

    assert decision.should_process is False
