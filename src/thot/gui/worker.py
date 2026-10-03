"""Background thread that loads the model and transcribes a queue of files."""

from __future__ import annotations

import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

from thot.config import Device, ModelSize, OutputFormat
from thot.core import Transcriber, TranscriptionCancelled, TranscriptionOptions
from thot.core.formatters import save


@dataclass(frozen=True)
class Job:
    files: tuple[Path, ...]
    output_dir: Path
    model: ModelSize
    device: Device
    formats: tuple[OutputFormat, ...]
    options: TranscriptionOptions


class TranscriptionWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)  # overall percentage
    file_started = pyqtSignal(int)  # index into job.files
    model_loaded = pyqtSignal(object)  # Transcriber, cached by the window
    done = pyqtSignal(int, int)  # succeeded, total

    def __init__(self, job: Job, transcriber: Optional[Transcriber] = None) -> None:
        super().__init__()
        self.job = job
        self.transcriber = transcriber
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:
        job = self.job
        succeeded = 0
        try:
            if self.transcriber is None:
                self.log.emit(f"Loading model '{job.model.value}' ({job.device.value})…")
                self.transcriber = Transcriber(job.model, job.device)
                self.model_loaded.emit(self.transcriber)

            total = len(job.files)
            for index, path in enumerate(job.files):
                if self._cancel.is_set():
                    break
                self.file_started.emit(index)
                self.log.emit(f"▶ [{index + 1}/{total}] {path.name}")

                def on_progress(fraction: float, stage: str, index: int = index) -> None:
                    self.progress.emit(int((index + fraction) / total * 100))

                try:
                    transcript = self.transcriber.transcribe(path, job.options, on_progress, self._cancel)
                except TranscriptionCancelled:
                    break
                except Exception as exc:
                    self.log.emit(f"✗ {path.name}: {exc}")
                    continue

                for written in save(transcript, job.output_dir, list(job.formats)):
                    self.log.emit(f"  ✓ {written}")
                succeeded += 1

            if self._cancel.is_set():
                self.log.emit("■ Cancelled.")
        except Exception:
            self.log.emit(f"✗ Unexpected error:\n{traceback.format_exc()}")
        finally:
            self.done.emit(succeeded, len(job.files))
