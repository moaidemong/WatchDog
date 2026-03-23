from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class Frame:
    index: int
    timestamp_s: float
    camera_id: str = "default"
    payload: object | None = None


class FrameSource:
    def read_frames(self) -> Iterable[Frame]:
        raise NotImplementedError
