from __future__ import annotations

from dataclasses import dataclass
from app.events.models import EventWindow
from app.ingest.frame_source import Frame


@dataclass(slots=True)
class ExtractorConfig:
    event_gap_seconds: float
    min_event_seconds: float


class EventExtractor:
    def __init__(self, config: ExtractorConfig) -> None:
        self.config = config

    def merge_frames_into_events(self, frames: list[Frame]) -> list[EventWindow]:
        if not frames:
            return []

        events: list[EventWindow] = []
        current_frames: list[Frame] = [frames[0]]
        start_s = frames[0].timestamp_s

        for previous, current in zip(frames, frames[1:]):
            if current.timestamp_s - previous.timestamp_s <= self.config.event_gap_seconds:
                current_frames.append(current)
                continue

            event = EventWindow(
                event_id=f"event-{len(events)+1}",
                start_s=start_s,
                end_s=previous.timestamp_s,
                frames=current_frames.copy(),
            )
            if event.duration_s >= self.config.min_event_seconds:
                events.append(event)

            current_frames = [current]
            start_s = current.timestamp_s

        final_event = EventWindow(
            event_id=f"event-{len(events)+1}",
            start_s=start_s,
            end_s=frames[-1].timestamp_s,
            frames=current_frames.copy(),
        )
        if final_event.duration_s >= self.config.min_event_seconds:
            events.append(final_event)
        return events
