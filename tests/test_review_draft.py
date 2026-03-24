from app.review.draft import build_review_draft


def test_build_review_draft_auto_approves_strong_failed_get_up_attempt() -> None:
    decision = build_review_draft(
        {
            "predicted_label": "failed_get_up_attempt",
            "should_alert": True,
            "decision_score": 1.0,
            "duration_s": 19.6,
            "decision_reasons": (
                "multiple rise attempts detected|long-duration struggle|"
                "body lift effort observed|insufficient progress to standing"
            ),
        }
    )

    assert decision.review_status == "approved"
    assert decision.review_label == "failed_get_up_attempt"


def test_build_review_draft_auto_approves_short_calm_non_alert() -> None:
    decision = build_review_draft(
        {
            "predicted_label": "no_alert",
            "should_alert": False,
            "decision_score": 0.0,
            "duration_s": 1.1,
            "decision_reasons": "",
        }
    )

    assert decision.review_status == "approved"
    assert decision.review_label == "normal_rest"


def test_build_review_draft_marks_low_severity_restlessness_pending() -> None:
    decision = build_review_draft(
        {
            "predicted_label": "no_alert",
            "should_alert": False,
            "decision_score": 0.4,
            "duration_s": 3.2,
            "decision_reasons": "body lift effort observed|insufficient progress to standing",
        }
    )

    assert decision.review_status == "pending"
    assert decision.review_label == "restless_while_lying"
