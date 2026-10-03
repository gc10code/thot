"""Plain data containers shared across the engine and the front-ends."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: Optional[str] = None


@dataclass
class Transcript:
    source: Path
    language: str
    duration: float
    segments: list[Segment] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(s.text for s in self.segments)
