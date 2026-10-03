"""``thot transcribe`` — batch transcription of files and folders."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from thot.cli.console import format_duration
from thot.config import Device, ModelSize, OutputFormat

log = logging.getLogger("thot")


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "transcribe",
        help="transcribe audio/video files or folders",
        description="Transcribe audio/video files with Whisper, optionally labelling speakers.",
    )
    p.add_argument("inputs", nargs="+", type=Path, help="audio files and/or folders")
    p.add_argument("-o", "--output", type=Path, default=Path("transcripts"),
                   help="output folder (default: ./transcripts)")
    p.add_argument("-m", "--model", choices=[m.value for m in ModelSize], default=ModelSize.SMALL.value,
                   help="Whisper model size (default: small)")
    p.add_argument("-l", "--language", default="it",
                   help="language code such as it, en, fr, or 'auto' (default: it)")
    p.add_argument("-d", "--device", choices=[d.value for d in Device], default=Device.AUTO.value,
                   help="inference device (default: auto)")
    p.add_argument("-f", "--format", dest="formats", action="append",
                   choices=[f.value for f in OutputFormat],
                   help="output format, repeatable (default: txt)")
    p.add_argument("-s", "--speakers", type=int, metavar="N", default=0,
                   help="label N speakers (diarization); 0 disables it")
    p.add_argument("-g", "--grammar", action="store_true",
                   help="post-process text with the T5 grammar fixer (English only)")
    p.add_argument("-r", "--recursive", action="store_true", help="search folders recursively")
    p.add_argument("--no-vad", action="store_true", help="disable voice-activity filtering")
    p.add_argument("--beam-size", type=int, default=5, help="decoding beam size (default: 5)")
    p.set_defaults(func=run)


def _progress_printer(name: str):
    if not sys.stderr.isatty():
        return None
    width = 30

    def show(fraction: float, stage: str) -> None:
        filled = int(fraction * width)
        bar = "█" * filled + "░" * (width - filled)
        sys.stderr.write(f"\r  {bar} {fraction:6.1%}  {stage:<20.20} {name:.40}")
        sys.stderr.flush()
        if fraction >= 1.0:
            sys.stderr.write("\n")

    return show


def run(args: argparse.Namespace) -> int:
    from thot.core import Transcriber, TranscriptionOptions
    from thot.core.audio import collect_audio_files
    from thot.core.formatters import save

    try:
        files = collect_audio_files(args.inputs, recursive=args.recursive)
    except FileNotFoundError as exc:
        log.error(str(exc))
        return 2
    if not files:
        log.error("No audio files found.")
        return 2

    formats = [OutputFormat(f) for f in dict.fromkeys(args.formats or ["txt"])]
    options = TranscriptionOptions(
        language=args.language,
        diarize=args.speakers > 0,
        num_speakers=args.speakers,
        grammar=args.grammar,
        vad=not args.no_vad,
        beam_size=args.beam_size,
    )

    log.info("Loading model '%s' on %s…", args.model, args.device)
    transcriber = Transcriber(args.model, args.device)

    failures = 0
    started = time.monotonic()
    for index, path in enumerate(files, 1):
        log.info("[%d/%d] %s", index, len(files), path.name)
        try:
            transcript = transcriber.transcribe(path, options, _progress_printer(path.name))
        except Exception as exc:  # keep going with the remaining files
            failures += 1
            log.error("  failed: %s", exc)
            log.debug("traceback", exc_info=True)
            continue
        for written in save(transcript, args.output, formats):
            log.info("  → %s", written)

    log.info("Done: %d/%d files in %s", len(files) - failures, len(files),
             format_duration(time.monotonic() - started))
    return 1 if failures else 0
