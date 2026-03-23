from types import SimpleNamespace

from app.pipeline.orchestrator import PipelineOrchestrator
from app.rules.rise_failure_rules import RuleDecision


def test_is_target_detection_accepts_temporary_aliases() -> None:
    orchestrator = object.__new__(PipelineOrchestrator)
    orchestrator.settings = SimpleNamespace(
        detection=SimpleNamespace(dog_class_names=["dog", "horse"]),
        pipeline=SimpleNamespace(detector_confidence_threshold=0.5),
    )

    assert orchestrator._is_target_detection(SimpleNamespace(label="horse", confidence=0.7)) is True
    assert orchestrator._is_target_detection(SimpleNamespace(label="dog", confidence=0.7)) is True
    assert orchestrator._is_target_detection(SimpleNamespace(label="cat", confidence=0.9)) is False
    assert orchestrator._is_target_detection(SimpleNamespace(label="horse", confidence=0.2)) is False


def test_process_event_always_marks_saved_events_for_review(tmp_path) -> None:
    orchestrator = object.__new__(PipelineOrchestrator)
    writes: list[tuple[str, dict]] = []

    orchestrator.settings = SimpleNamespace(
        storage=SimpleNamespace(
            artifacts_dir=tmp_path / "artifacts",
            review_queue_dir=tmp_path / "review_queue",
            exports_dir=tmp_path / "exports",
        ),
    )
    orchestrator.clip_saver = SimpleNamespace(
        save=lambda artifacts_dir, event: SimpleNamespace(
            event_dir=tmp_path / "artifacts" / event.event_id,
            clip_path=tmp_path / "artifacts" / event.event_id / "clip.mp4",
            snapshot_path=tmp_path / "artifacts" / event.event_id / "snapshot.jpg",
        )
    )
    orchestrator.pose_estimator = SimpleNamespace(estimate=lambda event: [])
    orchestrator.feature_extractor = SimpleNamespace(
        extract=lambda event, pose_frames: SimpleNamespace(
            event_id=event.event_id,
            duration_s=event.duration_s,
            attempt_count=0,
            body_lift_ratio=0.0,
            progress_ratio=1.0,
            pose_confidence_mean=0.93,
            to_dict=lambda: {
                "event_id": event.event_id,
                "duration_s": event.duration_s,
                "attempt_count": 0,
                "body_lift_ratio": 0.0,
                "progress_ratio": 1.0,
                "pose_confidence_mean": 0.93,
            },
        )
    )
    orchestrator.rule_engine = SimpleNamespace(
        evaluate=lambda features: RuleDecision(
            should_alert=False,
            should_review=False,
            label="no_alert",
            reasons=[],
            score=0.0,
        )
    )
    orchestrator.store = SimpleNamespace(write=lambda path, payload: writes.append((str(path), payload)))
    orchestrator.deduplicator = SimpleNamespace(should_send=lambda key, timestamp: False)
    orchestrator.notifier = SimpleNamespace(send=lambda title, body: None)

    from app.events.models import EventWindow

    event = EventWindow(event_id="c-0000001000-0001", start_s=1.0, end_s=2.5, camera_id="c", frames=[])

    orchestrator._process_event(event)

    review_writes = [item for item in writes if item[0].endswith("review_queue/c-0000001000-0001.json")]
    assert len(review_writes) == 1
    assert review_writes[0][1]["decision"]["should_review"] is True
