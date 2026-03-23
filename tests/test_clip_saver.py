import numpy as np

from app.events.clip_saver import EventClipSaver
from app.events.models import EventWindow
from app.ingest.frame_source import Frame


def test_clip_saver_skips_media_when_payloads_are_missing(tmp_path) -> None:
    event = EventWindow(
        event_id="event-1",
        start_s=0.0,
        end_s=2.0,
        frames=[
            Frame(index=0, timestamp_s=0.0, payload=None),
            Frame(index=1, timestamp_s=1.0, payload=None),
        ],
    )

    artifacts = EventClipSaver().save(tmp_path, event)

    assert artifacts.event_dir.exists()
    assert artifacts.clip_path is None
    assert artifacts.snapshot_path is None


def test_clip_saver_writes_clip_and_snapshot(tmp_path) -> None:
    frame_a = np.zeros((32, 32, 3), dtype=np.uint8)
    frame_b = np.full((32, 32, 3), 255, dtype=np.uint8)
    event = EventWindow(
        event_id="event-2",
        start_s=0.0,
        end_s=1.0,
        frames=[
            Frame(index=0, timestamp_s=0.0, payload=frame_a),
            Frame(index=1, timestamp_s=1.0, payload=frame_b),
        ],
    )

    artifacts = EventClipSaver().save(tmp_path, event)

    assert artifacts.clip_path is not None
    assert artifacts.snapshot_path is not None
    assert artifacts.clip_path.exists()
    assert artifacts.snapshot_path.exists()
