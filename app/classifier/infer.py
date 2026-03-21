from __future__ import annotations

from app.core.schemas import EventFeatureVector


def infer_label(features: EventFeatureVector) -> tuple[str, float]:
    # Placeholder baseline. Rules-first strategy remains primary.
    if features.attempt_count >= 2 and features.progress_ratio < 0.5:
        return "failed_get_up_attempt", 0.65
    return "no_alert", 0.35
