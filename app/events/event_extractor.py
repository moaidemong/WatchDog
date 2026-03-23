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
        self._current_frames: list[Frame] = []
        self._event_counter = 0

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

    def add_detected_frame(self, frame: Frame) -> list[EventWindow]:
        if not self._current_frames:
            self._current_frames = [frame]
            return []

        previous = self._current_frames[-1]
        if frame.timestamp_s - previous.timestamp_s <= self.config.event_gap_seconds:
            self._current_frames.append(frame)
            return []

        completed = self._finalize_current_event()
        self._current_frames = [frame]
        return [completed] if completed else []

    def observe_timestamp(self, timestamp_s: float) -> list[EventWindow]:
        if not self._current_frames:
            return []

        previous = self._current_frames[-1]
        if timestamp_s - previous.timestamp_s <= self.config.event_gap_seconds:
            return []

        completed = self._finalize_current_event()
        return [completed] if completed else []

    def flush(self) -> list[EventWindow]:
        completed = self._finalize_current_event()
        return [completed] if completed else []

    def _finalize_current_event(self) -> EventWindow | None:
        if not self._current_frames:
            return None

        self._event_counter += 1
        event = EventWindow(
            event_id=f"event-{self._event_counter}",
            start_s=self._current_frames[0].timestamp_s,
            end_s=self._current_frames[-1].timestamp_s,
            frames=self._current_frames.copy(),
        )
        self._current_frames = []
        if event.duration_s >= self.config.min_event_seconds:
            return event
        return None
