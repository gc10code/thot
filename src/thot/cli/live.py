"""``thot live`` — real-time microphone transcription with Vosk."""

from __future__ import annotations

import argparse
import json
import logging
import queue
import shutil
import sys
from pathlib import Path
from typing import Optional, TextIO

from thot.config import SAMPLE_RATE, default_vosk_model

log = logging.getLogger("thot")


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "live",
        help="real-time transcription from the microphone (Vosk)",
        description="Transcribe microphone input in real time with an offline Vosk model.",
    )
    p.add_argument("-M", "--vosk-model", type=Path, default=None,
                   help="Vosk model folder (default: $THOT_VOSK_MODEL or models/vosk-model-small-it-0.22)")
    p.add_argument("-i", "--input-device", default=None,
                   help="input device index or name substring (see --list-devices)")
    p.add_argument("-o", "--output", type=Path, help="also append final text to this file")
    p.add_argument("--list-devices", action="store_true", help="list audio devices and exit")
    p.set_defaults(func=run)


def _parse_device(value: Optional[str]):
    return int(value) if value is not None and value.isdigit() else value


class _LinePrinter:
    """Overwrites the current terminal line with partial results, commits final ones."""

    def __init__(self, stream: TextIO = sys.stdout) -> None:
        self.stream = stream
        self.interactive = stream.isatty()

    def partial(self, text: str) -> None:
        if self.interactive and text:
            width = shutil.get_terminal_size().columns - 1
            self.stream.write("\r\033[K" + ("… " + text)[-width:])
            self.stream.flush()

    def final(self, text: str) -> None:
        if self.interactive:
            self.stream.write("\r\033[K")
        if text:
            self.stream.write(text + "\n")
        self.stream.flush()


def run(args: argparse.Namespace) -> int:
    try:
        import sounddevice as sd
        import vosk
    except ImportError:
        log.error("Live mode requires the 'live' extra: pip install 'thot[live]'")
        return 2

    if args.list_devices:
        print(sd.query_devices())
        return 0

    model_dir = args.vosk_model or default_vosk_model()
    if not model_dir.is_dir():
        log.error("Vosk model not found: %s\nRun scripts/download_vosk_model.sh or see "
                  "https://alphacephei.com/vosk/models", model_dir)
        return 2

    vosk.SetLogLevel(-1)
    log.info("Loading Vosk model %s…", model_dir.name)
    model = vosk.Model(str(model_dir))
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    blocks: "queue.Queue[bytes]" = queue.Queue()

    def on_audio(indata, frames, time, status) -> None:
        if status:
            log.warning(str(status))
        blocks.put(bytes(indata))

    printer = _LinePrinter()
    transcript = args.output.open("a", encoding="utf-8") if args.output else None
    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=SAMPLE_RATE // 2, dtype="int16",
                               channels=1, device=_parse_device(args.input_device), callback=on_audio):
            log.info("Listening… press Ctrl+C to stop.")
            while True:
                data = blocks.get()
                if recognizer.AcceptWaveform(data):
                    text = json.loads(recognizer.Result()).get("text", "")
                    printer.final(text)
                    if transcript and text:
                        transcript.write(text + "\n")
                        transcript.flush()
                else:
                    printer.partial(json.loads(recognizer.PartialResult()).get("partial", ""))
    except KeyboardInterrupt:
        text = json.loads(recognizer.FinalResult()).get("text", "")
        printer.final(text)
        if transcript and text:
            transcript.write(text + "\n")
    finally:
        if transcript:
            transcript.close()
    return 0
