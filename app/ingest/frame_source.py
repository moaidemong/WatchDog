from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class Frame:
    index: int
    timestamp_s: float
    payload: bytes | None = None


class FrameSource:
    def read_frames(self) -> Iterable[Frame]:
        raise NotImplementedError
