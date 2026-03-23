from app.core.schemas import EventFeatureVector
from app.rules.rise_failure_rules import RiseFailureRuleConfig, RiseFailureRuleEngine


def test_rules_threshold_behavior() -> None:
    features = EventFeatureVector(
        event_id="e1",
        duration_s=14.0,
        attempt_count=3,
        body_lift_ratio=0.18,
        progress_ratio=0.35,
        pose_confidence_mean=0.93,
    )
    engine = RiseFailureRuleEngine(
        RiseFailureRuleConfig(
            failed_attempt_min_attempts=2,
            failed_attempt_min_duration_seconds=10.0,
            min_body_lift_ratio=0.15,
            max_progress_ratio=0.50,
        )
    )
    decision = engine.evaluate(features)
    assert decision.should_alert is True
    assert decision.should_review is True
    assert decision.label == "failed_get_up_attempt"
