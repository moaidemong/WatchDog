from pathlib import Path

from app.core.config import load_settings
from app.onvif.probe import discover_wsdl_dir, resolve_probe_target


def test_resolve_probe_target_uses_camera_alias_and_rtsp_credentials(tmp_path: Path, monkeypatch) -> None:
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
                "cameras:",
                "  - camera_id: b",
                "    aliases: [2]",
                "    rtsp_url: rtsp://${TAPO_USERNAME}:${TAPO_PASSWORD}@192.168.219.112:554/stream1",
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
    target = resolve_probe_target(settings, "2")

    assert target.camera_id == "b"
    assert target.host == "192.168.219.112"
    assert target.username == "user1"
    assert target.password == "pass1"


def test_discover_wsdl_dir_prefers_explicit_directory(tmp_path: Path) -> None:
    wsdl_dir = tmp_path / "wsdl"
    wsdl_dir.mkdir()

    discovered = discover_wsdl_dir(str(wsdl_dir))

    assert discovered == wsdl_dir
