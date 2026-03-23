from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

from app.classifier.dataset import append_labeled_feature_row
from app.core.config import Settings
from app.core.time_utils import utc_now_iso
from app.detection.base import DogDetector
from app.detection.factory import build_detector
from app.events.clip_saver import EventClipSaver
from app.events.event_extractor import EventExtractor, ExtractorConfig
from app.features.extractor import FeatureExtractor
from app.ingest.factory import build_frame_source
from app.ingest.frame_source import FrameSource
from app.ingest.motion_gate import MotionGate
from app.notify.factory import build_notifier
from app.pose.base import PoseEstimator
from app.pose.mock_pose_estimator import MockPoseEstimator
from app.rules.rise_failure_rules import RiseFailureRuleConfig, RiseFailureRuleEngine
from app.storage.alert_deduplicator import AlertDeduplicator
from app.storage.local_store import JsonFileStore

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(
        self,
        frame_source: FrameSource,
        detector: DogDetector,
        extractor: EventExtractor,
        pose_estimator: PoseEstimator,
        feature_extractor: FeatureExtractor,
        rule_engine: RiseFailureRuleEngine,
        notifier,
        store: JsonFileStore,
        clip_saver: EventClipSaver,
        motion_gate: MotionGate,
        deduplicator: AlertDeduplicator,
        settings: Settings,
    ) -> None:
        self.frame_source = frame_source
        self.detector = detector
        self.extractor = extractor
        self.pose_estimator = pose_estimator
        self.feature_extractor = feature_extractor
        self.rule_engine = rule_engine
        self.notifier = notifier
        self.store = store
        self.clip_saver = clip_saver
        self.motion_gate = motion_gate
        self.deduplicator = deduplicator
        self.settings = settings

    @classmethod
    def from_settings(cls, settings: Settings) -> "PipelineOrchestrator":
        frame_source = build_frame_source(settings.ingest, settings.cameras)
        detector = build_detector(settings.detection)
        extractor = EventExtractor(
            ExtractorConfig(
                event_gap_seconds=settings.pipeline.event_gap_seconds,
                min_event_seconds=settings.pipeline.min_event_seconds,
            )
        )
        pose_estimator = MockPoseEstimator()
        feature_extractor = FeatureExtractor()
        rule_engine = RiseFailureRuleEngine(
            RiseFailureRuleConfig(
                failed_attempt_min_attempts=settings.rules.failed_attempt_min_attempts,
                failed_attempt_min_duration_seconds=settings.rules.failed_attempt_min_duration_seconds,
                min_body_lift_ratio=settings.rules.min_body_lift_ratio,
                max_progress_ratio=settings.rules.max_progress_ratio,
            )
        )
        notifier = build_notifier(settings.notifier)
        store = JsonFileStore()
        clip_saver = EventClipSaver()
        motion_gate = MotionGate(settings.motion_gate)
        deduplicator = AlertDeduplicator(cooldown_seconds=settings.pipeline.alert_cooldown_seconds)
        return cls(
            frame_source=frame_source,
            detector=detector,
            extractor=extractor,
            pose_estimator=pose_estimator,
            feature_extractor=feature_extractor,
            rule_engine=rule_engine,
            notifier=notifier,
            store=store,
            clip_saver=clip_saver,
            motion_gate=motion_gate,
            deduplicator=deduplicator,
            settings=settings,
        )

    def _ensure_directories(self) -> None:
        for path in (
            self.settings.storage.artifacts_dir,
            self.settings.storage.review_queue_dir,
            self.settings.storage.exports_dir,
        ):
            Path(path).mkdir(parents=True, exist_ok=True)

    def run_once(self) -> None:
        self._ensure_directories()

        for frame in self.frame_source.read_frames():
            for event in self.extractor.observe_timestamp(frame.timestamp_s):
                self._process_event(event)

            motion_decision = self.motion_gate.evaluate(frame)
            if not motion_decision.should_process:
                continue
            detections = self.detector.detect(frame)
            if any(self._is_target_detection(detection) for detection in detections):
                for event in self.extractor.add_detected_frame(frame):
                    self._process_event(event)

        for event in self.extractor.flush():
            self._process_event(event)

    def _process_event(self, event) -> None:
        logger.info("processing candidate event %s", event.event_id)
        media_artifacts = self.clip_saver.save(self.settings.storage.artifacts_dir, event)
        pose_frames = self.pose_estimator.estimate(event)
        features = self.feature_extractor.extract(event, pose_frames)
        decision = self.rule_engine.evaluate(features)
        should_review = True

        artifact = {
            "captured_at": utc_now_iso(),
            "event": {
                "event_id": event.event_id,
                "camera_id": event.camera_id,
                "start_s": event.start_s,
                "end_s": event.end_s,
                "duration_s": event.duration_s,
                "frame_count": len(event.frames),
            },
            "media": {
                "event_dir": str(media_artifacts.event_dir),
                "clip_path": str(media_artifacts.clip_path) if media_artifacts.clip_path else None,
                "snapshot_path": str(media_artifacts.snapshot_path) if media_artifacts.snapshot_path else None,
            },
            "features": features.to_dict(),
            "decision": {
                **asdict(decision),
                "should_review": should_review,
            },
        }
        self.store.write(media_artifacts.event_dir / "metadata.json", artifact)

        label = decision.label
        append_labeled_feature_row(self.settings.storage.exports_dir / "feature_dataset.csv", features, label)

        if should_review:
            self.store.write(self.settings.storage.review_queue_dir / f"{event.event_id}.json", artifact)

        if decision.should_alert and self.deduplicator.should_send("failed_get_up_attempt", event.end_s):
            title = "Dog Rise Alert"
            body = (
                f"event={event.event_id}\n"
                f"duration={features.duration_s:.1f}s\n"
                f"attempts={features.attempt_count}\n"
                f"progress_ratio={features.progress_ratio}\n"
                f"reasons={', '.join(decision.reasons)}"
            )
            self.notifier.send(title, body)

    def _is_target_detection(self, detection) -> bool:
        return (
            detection.label in set(self.settings.detection.dog_class_names)
            and detection.confidence >= self.settings.pipeline.detector_confidence_threshold
        )
