from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml


@dataclass(slots=True)
class StorageSettings:
    artifacts_dir: Path
    review_queue_dir: Path
    exports_dir: Path


@dataclass(slots=True)
class PipelineSettings:
    frame_window_size: int
    detector_confidence_threshold: float
    event_gap_seconds: float
    min_event_seconds: float
    alert_cooldown_seconds: float


@dataclass(slots=True)
class RuleSettings:
    failed_attempt_min_attempts: int
    failed_attempt_min_duration_seconds: float
    min_body_lift_ratio: float
    max_progress_ratio: float


@dataclass(slots=True)
class TelegramSettings:
    bot_token_env: str
    chat_id_env: str


@dataclass(slots=True)
class NotifierSettings:
    backend: str
    telegram: TelegramSettings


@dataclass(slots=True)
class Settings:
    app_name: str
    storage: StorageSettings
    pipeline: PipelineSettings
    rules: RuleSettings
    notifier: NotifierSettings


def _read_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings(path: str | Path) -> Settings:
    raw = _read_yaml(path)
    storage = raw["storage"]
    pipeline = raw["pipeline"]
    rules = raw["rules"]
    notifier = raw["notifier"]
    return Settings(
        app_name=raw.get("app_name", "dog-rise-alert"),
        storage=StorageSettings(
            artifacts_dir=Path(storage["artifacts_dir"]),
            review_queue_dir=Path(storage["review_queue_dir"]),
            exports_dir=Path(storage["exports_dir"]),
        ),
        pipeline=PipelineSettings(**pipeline),
        rules=RuleSettings(**rules),
        notifier=NotifierSettings(
            backend=notifier["backend"],
            telegram=TelegramSettings(**notifier["telegram"]),
        ),
    )
