"""Terminal logging with optional ANSI colours."""

from __future__ import annotations

import logging
import sys

_COLORS = {
    logging.DEBUG: "\033[90m",
    logging.INFO: "\033[96m",
    logging.WARNING: "\033[93m",
    logging.ERROR: "\033[91m",
    logging.CRITICAL: "\033[91m",
}
_RESET = "\033[0m"


class _ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return f"{_COLORS.get(record.levelno, '')}{super().format(record)}{_RESET}"


def setup_logging(verbose: bool = False) -> None:
    handler = logging.StreamHandler(sys.stderr)
    fmt = "%(message)s"
    handler.setFormatter(_ColorFormatter(fmt) if sys.stderr.isatty() else logging.Formatter(fmt))
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, handlers=[handler])
    # Third-party libraries are chatty at INFO level.
    for name in ("faster_whisper", "httpx", "huggingface_hub"):
        logging.getLogger(name).setLevel(logging.WARNING)


def format_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
