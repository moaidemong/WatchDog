from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

from app.classifier.dataset import append_labeled_feature_row
from app.core.config import Settings
from app.core.time_utils import utc_now_iso
from app.detection.mock_detector import MockDogDetector
from app.events.event_extractor import EventExtractor, ExtractorConfig
from app.features.extractor import FeatureExtractor
from app.ingest.mock_source import MockFrameSource
from app.notify.factory import build_notifier
from app.pose.mock_pose_estimator import MockPoseEstimator
from app.rules.rise_failure_rules import RiseFailureRuleConfig, RiseFailureRuleEngine
from app.storage.alert_deduplicator import AlertDeduplicator
from app.storage.local_store import JsonFileStore

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(
        self,
        frame_source: MockFrameSource,
        detector: MockDogDetector,
        extractor: EventExtractor,
        pose_estimator: MockPoseEstimator,
        feature_extractor: FeatureExtractor,
        rule_engine: RiseFailureRuleEngine,
        notifier,
        store: JsonFileStore,
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
        self.deduplicator = deduplicator
        self.settings = settings

    @classmethod
    def from_settings(cls, settings: Settings) -> "PipelineOrchestrator":
        frame_source = MockFrameSource(total_frames=60, fps=2.0)
        detector = MockDogDetector()
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

        detected_frames = []
        for frame in self.frame_source.read_frames():
            detections = self.detector.detect(frame)
            if any(d.label == "dog" and d.confidence >= self.settings.pipeline.detector_confidence_threshold for d in detections):
                detected_frames.append(frame)

        events = self.extractor.merge_frames_into_events(detected_frames)
        logger.info("detected %s candidate events", len(events))

        for event in events:
            pose_frames = self.pose_estimator.estimate(event)
            features = self.feature_extractor.extract(event, pose_frames)
            decision = self.rule_engine.evaluate(features)

            artifact = {
                "captured_at": utc_now_iso(),
                "event": {
                    "event_id": event.event_id,
                    "start_s": event.start_s,
                    "end_s": event.end_s,
                    "duration_s": event.duration_s,
                    "frame_count": len(event.frames),
                },
                "features": features.to_dict(),
                "decision": asdict(decision),
            }
            self.store.write(self.settings.storage.artifacts_dir / f"{event.event_id}.json", artifact)

            label = decision.label
            append_labeled_feature_row(self.settings.storage.exports_dir / "feature_dataset.csv", features, label)

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
                self.store.write(self.settings.storage.review_queue_dir / f"{event.event_id}.json", artifact)
