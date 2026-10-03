"""Shared constants and enumerations."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

#: Sample rate expected by Whisper and Vosk models.
SAMPLE_RATE = 16_000

#: File extensions accepted as audio/video input (decoded through FFmpeg/PyAV).
AUDIO_EXTENSIONS = frozenset(
    {".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma", ".webm", ".mp4", ".mkv"}
)

#: Grammar-correction model (English only).
GRAMMAR_MODEL = "flexudy/t5-small-wav2vec2-grammar-fixer"

#: Vosk model used by ``thot live`` when none is given.
DEFAULT_VOSK_MODEL_NAME = "vosk-model-small-it-0.22"


def default_vosk_model() -> Path:
    """First existing of: $THOT_VOSK_MODEL, ./models, the repository's models/, user data dir."""
    if env := os.environ.get("THOT_VOSK_MODEL"):
        return Path(env).expanduser()
    candidates = [
        Path.cwd() / "models" / DEFAULT_VOSK_MODEL_NAME,
        Path(__file__).resolve().parents[2] / "models" / DEFAULT_VOSK_MODEL_NAME,
        Path.home() / ".local" / "share" / "thot" / "models" / DEFAULT_VOSK_MODEL_NAME,
    ]
    return next((c for c in candidates if c.is_dir()), candidates[0])


class ModelSize(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large-v3"
    TURBO = "turbo"


class Device(str, Enum):
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class OutputFormat(str, Enum):
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"


#: Languages offered in the GUI; the CLI accepts any Whisper language code.
COMMON_LANGUAGES = ("auto", "it", "en", "es", "fr", "de", "pt", "nl", "ru", "zh", "ja", "ar")
