from app.events.event_extractor import EventExtractor, ExtractorConfig
from app.ingest.frame_source import Frame


def test_event_merge_logic_splits_on_large_gap() -> None:
    frames = [
        Frame(index=0, timestamp_s=0.0, camera_id="cam-a"),
        Frame(index=1, timestamp_s=1.0, camera_id="cam-a"),
        Frame(index=2, timestamp_s=2.0, camera_id="cam-a"),
        Frame(index=3, timestamp_s=8.0, camera_id="cam-a"),
        Frame(index=4, timestamp_s=9.0, camera_id="cam-a"),
        Frame(index=5, timestamp_s=10.0, camera_id="cam-a"),
    ]
    extractor = EventExtractor(ExtractorConfig(event_gap_seconds=2.0, min_event_seconds=2.0))
    events = extractor.merge_frames_into_events(frames)
    assert len(events) == 2
    assert events[0].start_s == 0.0
    assert events[1].start_s == 8.0
    assert events[0].event_id == "cam-a-0000000000-0001"
    assert events[1].event_id == "cam-a-0000008000-0002"


def test_streaming_event_extractor_finalizes_after_gap() -> None:
    extractor = EventExtractor(ExtractorConfig(event_gap_seconds=2.0, min_event_seconds=2.0))

    assert extractor.add_detected_frame(Frame(index=0, timestamp_s=0.0, camera_id="c")) == []
    assert extractor.add_detected_frame(Frame(index=1, timestamp_s=2.0, camera_id="c")) == []

    completed = extractor.observe_timestamp(5.0)

    assert len(completed) == 1
    assert completed[0].start_s == 0.0
    assert completed[0].end_s == 2.0
    assert completed[0].event_id == "c-0000000000-0001"
