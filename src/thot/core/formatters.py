"""Render a :class:`Transcript` as plain text, SubRip, WebVTT or JSON."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from thot.config import OutputFormat
from thot.core.models import Transcript


def _timestamp(seconds: float, decimal: str) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{decimal}{millis:03d}"


def _cue_text(text: str, speaker: str | None) -> str:
    return f"[{speaker}] {text}" if speaker else text


def to_txt(transcript: Transcript) -> str:
    """One paragraph per speaker turn; a single paragraph when diarization is off."""
    paragraphs: list[str] = []
    current: str | None = None
    for seg in transcript.segments:
        if not paragraphs or seg.speaker != current:
            current = seg.speaker
            paragraphs.append(f"[{current}]: {seg.text}" if current else seg.text)
        else:
            paragraphs[-1] += f" {seg.text}"
    return "\n\n".join(paragraphs) + "\n"


def to_srt(transcript: Transcript) -> str:
    cues = (
        f"{i}\n{_timestamp(s.start, ',')} --> {_timestamp(s.end, ',')}\n{_cue_text(s.text, s.speaker)}\n"
        for i, s in enumerate(transcript.segments, 1)
    )
    return "\n".join(cues)


def to_vtt(transcript: Transcript) -> str:
    cues = (
        f"{_timestamp(s.start, '.')} --> {_timestamp(s.end, '.')}\n{_cue_text(s.text, s.speaker)}\n"
        for s in transcript.segments
    )
    return "WEBVTT\n\n" + "\n".join(cues)


def to_json(transcript: Transcript) -> str:
    data = asdict(transcript)
    data["source"] = str(transcript.source)
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


FORMATTERS: dict[OutputFormat, Callable[[Transcript], str]] = {
    OutputFormat.TXT: to_txt,
    OutputFormat.SRT: to_srt,
    OutputFormat.VTT: to_vtt,
    OutputFormat.JSON: to_json,
}


def save(transcript: Transcript, output_dir: Path, formats: list[OutputFormat]) -> list[Path]:
    """Write the transcript in every requested format; returns the created paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in formats:
        path = output_dir / f"{transcript.source.stem}.{fmt.value}"
        path.write_text(FORMATTERS[fmt](transcript), encoding="utf-8")
        written.append(path)
    return written
