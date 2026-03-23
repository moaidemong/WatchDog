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
    assert settings.ingest.camera_id == "default"
    assert settings.ingest.camera_index == 0
    assert settings.ingest.rtsp_url is None
    assert settings.ingest.sample_fps == 2.0
    assert settings.ingest.max_frames == 60
    assert settings.ingest.frame_width is None
    assert settings.ingest.frame_height is None
    assert settings.cameras == []
    assert settings.detection.backend == "mock"
    assert settings.detection.dog_class_names == ["dog"]
    assert settings.motion_gate.enabled is False
    assert settings.motion_gate.roi is None


def test_load_settings_expands_camera_env_vars(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TAPO_USERNAME", "user1")
    monkeypatch.setenv("TAPO_PASSWORD", "pass1")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "app_name: dog-rise-alert",
                "storage:",
                "  artifacts_dir: artifacts",
                "  review_queue_dir: review_queue",
                "  exports_dir: exports",
                "ingest:",
                "  backend: opencv",
                "  camera_id: livingroom_a",
                "  camera_index: 0",
                "  device_path:",
                "  rtsp_url:",
                "  sample_fps: 1.0",
                "  max_frames: 10",
                "  frame_width:",
                "  frame_height:",
                "cameras:",
                "  - camera_id: a",
                "    aliases: [1, livingroom_a]",
                "    rtsp_url: rtsp://${TAPO_USERNAME}:${TAPO_PASSWORD}@192.168.0.10:554/stream1",
                "    enabled: true",
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

    assert settings.cameras[0].rtsp_url == "rtsp://user1:pass1@192.168.0.10:554/stream1"
    assert settings.cameras[0].camera_id == "a"
    assert settings.cameras[0].aliases == ["1", "livingroom_a"]
