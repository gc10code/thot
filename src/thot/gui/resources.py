"""Access to files bundled in ``thot/resources``."""

from __future__ import annotations

from pathlib import Path

_RESOURCES = Path(__file__).resolve().parent.parent / "resources"


def resource_path(name: str) -> Path:
    return _RESOURCES / name
