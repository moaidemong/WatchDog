from app.core.logging_utils import configure_logging
from app.core.config import load_settings
from app.pipeline.orchestrator import PipelineOrchestrator


def main(config_path: str) -> None:
    configure_logging()
    settings = load_settings(config_path)
    orchestrator = PipelineOrchestrator.from_settings(settings)
    orchestrator.run_once()
