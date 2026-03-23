from pathlib import Path

from app.core.config import load_settings


def test_load_settings_applies_ingest_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "app_name: dog-rise-alert",
                "storage:",
                "  artifacts_dir: artifacts",
                "  review_queue_dir: review_queue",
                "  exports_dir: exports",
                "pipeline:",
                "  frame_window_size: 30",
                "  detector_confidence_threshold: 0.5",
                "  event_gap_seconds: 2.0",
                "  min_event_seconds: 3.0",
                "  alert_cooldown_seconds: 300.0",
                "rules:",
                "  failed_attempt_min_attempts: 2",
                "  failed_attempt_min_duration_seconds: 10.0",
                "  min_body_lift_ratio: 0.07",
                "  max_progress_ratio: 0.5",
                "notifier:",
                "  backend: stdout",
                "  telegram:",
                "    bot_token_env: TELEGRAM_BOT_TOKEN",
                "    chat_id_env: TELEGRAM_CHAT_ID",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert settings.ingest.backend == "mock"
    assert settings.ingest.camera_index == 0
    assert settings.ingest.sample_fps == 2.0
    assert settings.ingest.max_frames == 60
    assert settings.ingest.frame_width is None
    assert settings.ingest.frame_height is None
    assert settings.detection.backend == "mock"
    assert settings.detection.dog_class_names == ["dog"]
    assert settings.motion_gate.enabled is False
    assert settings.motion_gate.roi is None
