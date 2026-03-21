import pytest
from app.events.models import EventWindow
from app.features.extractor import FeatureExtractor


def test_malformed_input_handling() -> None:
    extractor = FeatureExtractor()
    event = EventWindow(event_id="e1", start_s=0.0, end_s=1.0, frames=[])
    with pytest.raises(ValueError):
        extractor.extract(event, [])
