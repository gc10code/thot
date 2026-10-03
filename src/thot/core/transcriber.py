"""Whisper-based transcription pipeline."""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from thot.config import Device, ModelSize, SAMPLE_RATE
from thot.core.audio import load_audio
from thot.core.diarization import assign_speakers
from thot.core.grammar import GrammarCorrector
from thot.core.models import Segment, Transcript

log = logging.getLogger(__name__)

#: ``callback(fraction, stage)`` with ``fraction`` in [0, 1].
ProgressCallback = Callable[[float, str], None]

# Share of the progress bar given to Whisper inference; the rest covers post-processing.
_INFERENCE_SHARE = 0.9


class TranscriptionCancelled(Exception):
    """Raised when a cancel event is set while a file is being transcribed."""


@dataclass(frozen=True)
class TranscriptionOptions:
    language: Optional[str] = "it"  # None or "auto" -> automatic detection
    diarize: bool = False
    num_speakers: int = 2
    grammar: bool = False
    vad: bool = True
    beam_size: int = 5


class Transcriber:
    """Holds a loaded Whisper model; reuse one instance for many files."""

    def __init__(
        self,
        model_size: ModelSize | str = ModelSize.SMALL,
        device: Device | str = Device.AUTO,
        compute_type: str = "auto",
        cpu_threads: int = 0,
        download_root: Optional[str] = None,
    ) -> None:
        from faster_whisper import WhisperModel

        self.model_size = ModelSize(model_size)
        self.device = Device(device)
        self._model = WhisperModel(
            self.model_size.value,
            device=self.device.value,
            compute_type=compute_type,
            cpu_threads=cpu_threads or os.cpu_count() or 4,
            download_root=download_root,
        )
        self._grammar = GrammarCorrector()

    def transcribe(
        self,
        path: Path,
        options: TranscriptionOptions = TranscriptionOptions(),
        on_progress: Optional[ProgressCallback] = None,
        cancel: Optional[threading.Event] = None,
    ) -> Transcript:
        def report(fraction: float, stage: str) -> None:
            if on_progress:
                on_progress(min(max(fraction, 0.0), 1.0), stage)

        def check_cancel() -> None:
            if cancel is not None and cancel.is_set():
                raise TranscriptionCancelled(str(path))

        report(0.0, "decoding audio")
        audio = load_audio(path)
        duration = audio.size / SAMPLE_RATE
        check_cancel()

        language = None if options.language in (None, "", "auto") else options.language
        raw_segments, info = self._model.transcribe(
            audio,
            language=language,
            beam_size=options.beam_size,
            vad_filter=options.vad,
            vad_parameters={"min_silence_duration_ms": 500},
        )

        # Segments are produced lazily: consuming the generator runs inference,
        # so progress can follow each segment's end time.
        segments: list[Segment] = []
        for raw in raw_segments:
            check_cancel()
            text = raw.text.strip()
            if text:
                segments.append(Segment(start=raw.start, end=raw.end, text=text))
            if duration:
                report(raw.end / duration * _INFERENCE_SHARE, "transcribing")

        if options.diarize:
            check_cancel()
            report(_INFERENCE_SHARE, "detecting speakers")
            assign_speakers(audio, segments, options.num_speakers)

        if options.grammar and segments:
            check_cancel()
            if info.language != "en":
                log.warning("Grammar correction model is English-only (detected: %s)", info.language)
            report(_INFERENCE_SHARE + 0.05, "correcting grammar")
            for seg, fixed in zip(segments, self._grammar.correct([s.text for s in segments])):
                seg.text = fixed

        report(1.0, "done")
        return Transcript(source=path, language=info.language, duration=duration, segments=segments)
