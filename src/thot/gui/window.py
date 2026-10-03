"""Main application window."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QSettings, Qt, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from thot import __version__
from thot.cli.console import format_duration
from thot.config import AUDIO_EXTENSIONS, COMMON_LANGUAGES, Device, ModelSize, OutputFormat
from thot.core import Transcriber, TranscriptionOptions
from thot.core.audio import collect_audio_files
from thot.gui.resources import resource_path
from thot.gui.worker import Job, TranscriptionWorker

_AUDIO_FILTER = "Audio/Video ({})".format(" ".join(f"*{ext}" for ext in sorted(AUDIO_EXTENSIONS)))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("thot", "thot")
        self.files: list[Path] = []
        self.worker: Optional[TranscriptionWorker] = None
        self._cached: Optional[tuple[tuple[ModelSize, Device], Transcriber]] = None
        self._started_at = 0.0
        self._clock = QTimer(self, interval=1000, timeout=self._tick)

        self.setWindowTitle(f"THOT {__version__}")
        self.setWindowIcon(QIcon(str(resource_path("icon.png"))))
        self.setAcceptDrops(True)
        self.resize(900, 720)
        self._build_ui()
        self._restore_settings()

    # ---------------------------------------------------------------- layout
    def _build_ui(self) -> None:
        root = QVBoxLayout()
        root.addLayout(self._header())
        root.addWidget(self._files_box(), stretch=2)
        root.addWidget(self._options_box())

        run_row = QHBoxLayout()
        self.start_button = QPushButton("Transcribe", objectName="primary", clicked=self._start)
        self.cancel_button = QPushButton("Cancel", enabled=False, clicked=self._cancel)
        self.progress_bar = QProgressBar(textVisible=True)
        self.clock_label = QLabel("00:00:00", objectName="clock")
        run_row.addWidget(self.start_button)
        run_row.addWidget(self.cancel_button)
        run_row.addWidget(self.progress_bar, stretch=1)
        run_row.addWidget(self.clock_label)
        root.addLayout(run_row)

        self.log_view = QPlainTextEdit(readOnly=True, objectName="log")
        self.log_view.setMaximumBlockCount(5000)
        root.addWidget(self.log_view, stretch=1)

        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

    def _header(self) -> QHBoxLayout:
        logo = QLabel()
        logo.setPixmap(QPixmap(str(resource_path("icon.png"))).scaledToHeight(56, Qt.SmoothTransformation))
        title = QLabel("THOT", objectName="title")
        subtitle = QLabel("Offline speech-to-text", objectName="subtitle")
        text = QVBoxLayout()
        text.setSpacing(0)
        text.addWidget(title)
        text.addWidget(subtitle)
        row = QHBoxLayout()
        row.addWidget(logo)
        row.addLayout(text)
        row.addStretch()
        return row

    def _files_box(self) -> QGroupBox:
        box = QGroupBox("Input files — drop audio here")
        self.files_list = QListWidget(selectionMode=QAbstractItemView.ExtendedSelection)
        buttons = QHBoxLayout()
        buttons.addWidget(QPushButton("Add files…", clicked=self._add_files_dialog))
        buttons.addWidget(QPushButton("Add folder…", clicked=self._add_folder_dialog))
        buttons.addWidget(QPushButton("Remove selected", clicked=self._remove_selected))
        buttons.addWidget(QPushButton("Clear", clicked=self._clear_files))
        buttons.addStretch()
        layout = QVBoxLayout(box)
        layout.addLayout(buttons)
        layout.addWidget(self.files_list)
        return box

    def _options_box(self) -> QGroupBox:
        box = QGroupBox("Options")
        form = QFormLayout(box)

        output_row = QHBoxLayout()
        self.output_edit = QLineEdit(placeholderText="Output folder")
        output_row.addWidget(self.output_edit)
        output_row.addWidget(QPushButton("Browse…", clicked=self._choose_output))
        form.addRow("Output", output_row)

        engine_row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems([m.value for m in ModelSize])
        self.device_combo = QComboBox()
        self.device_combo.addItems([d.value for d in Device])
        self.language_combo = QComboBox(editable=True)
        self.language_combo.addItems(COMMON_LANGUAGES)
        for label, widget in (("Model", self.model_combo), ("Device", self.device_combo),
                              ("Language", self.language_combo)):
            engine_row.addWidget(QLabel(label))
            engine_row.addWidget(widget, stretch=1)
        form.addRow("Engine", engine_row)

        format_row = QHBoxLayout()
        self.format_checks = {fmt: QCheckBox(fmt.value.upper()) for fmt in OutputFormat}
        for check in self.format_checks.values():
            format_row.addWidget(check)
        format_row.addStretch()
        form.addRow("Formats", format_row)

        extra_row = QHBoxLayout()
        self.diarize_check = QCheckBox("Label speakers")
        self.speakers_spin = QSpinBox(minimum=2, maximum=10, enabled=False)
        self.diarize_check.toggled.connect(self.speakers_spin.setEnabled)
        self.grammar_check = QCheckBox("Grammar fix (English)")
        extra_row.addWidget(self.diarize_check)
        extra_row.addWidget(self.speakers_spin)
        extra_row.addSpacing(24)
        extra_row.addWidget(self.grammar_check)
        extra_row.addStretch()
        form.addRow("Extras", extra_row)
        return box

    # ------------------------------------------------------------- settings
    def _restore_settings(self) -> None:
        s = self.settings
        self.output_edit.setText(s.value("output", str(Path.home() / "THOT")))
        self.model_combo.setCurrentText(s.value("model", ModelSize.SMALL.value))
        self.device_combo.setCurrentText(s.value("device", Device.AUTO.value))
        self.language_combo.setCurrentText(s.value("language", "it"))
        saved_formats = s.value("formats", ["txt"], type=list)
        for fmt, check in self.format_checks.items():
            check.setChecked(fmt.value in saved_formats)
        self.diarize_check.setChecked(s.value("diarize", False, type=bool))
        self.speakers_spin.setValue(s.value("speakers", 2, type=int))
        self.grammar_check.setChecked(s.value("grammar", False, type=bool))

    def _save_settings(self) -> None:
        s = self.settings
        s.setValue("output", self.output_edit.text())
        s.setValue("model", self.model_combo.currentText())
        s.setValue("device", self.device_combo.currentText())
        s.setValue("language", self.language_combo.currentText())
        s.setValue("formats", [f.value for f, c in self.format_checks.items() if c.isChecked()])
        s.setValue("diarize", self.diarize_check.isChecked())
        s.setValue("speakers", self.speakers_spin.value())
        s.setValue("grammar", self.grammar_check.isChecked())

    # ---------------------------------------------------------------- files
    def _add_paths(self, paths: list[Path]) -> None:
        try:
            new = collect_audio_files(paths)
        except FileNotFoundError as exc:
            self._log(f"✗ {exc}")
            return
        known = set(self.files)
        for path in new:
            if path not in known:
                self.files.append(path)
                item = QListWidgetItem(path.name)
                item.setToolTip(str(path))
                self.files_list.addItem(item)

    def _add_files_dialog(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(self, "Select audio files", "", _AUDIO_FILTER)
        self._add_paths([Path(n) for n in names])

    def _add_folder_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder:
            self._add_paths([Path(folder)])

    def _remove_selected(self) -> None:
        for row in sorted((self.files_list.row(i) for i in self.files_list.selectedItems()), reverse=True):
            self.files_list.takeItem(row)
            del self.files[row]

    def _clear_files(self) -> None:
        self.files.clear()
        self.files_list.clear()

    def _choose_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder", self.output_edit.text())
        if folder:
            self.output_edit.setText(folder)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        self._add_paths([Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()])

    # ------------------------------------------------------------------ run
    def _build_job(self) -> Optional[Job]:
        if not self.files:
            QMessageBox.warning(self, "THOT", "Add at least one audio file.")
            return None
        output = self.output_edit.text().strip()
        if not output:
            QMessageBox.warning(self, "THOT", "Choose an output folder.")
            return None
        formats = tuple(f for f, c in self.format_checks.items() if c.isChecked())
        if not formats:
            QMessageBox.warning(self, "THOT", "Select at least one output format.")
            return None
        return Job(
            files=tuple(self.files),
            output_dir=Path(output).expanduser(),
            model=ModelSize(self.model_combo.currentText()),
            device=Device(self.device_combo.currentText()),
            formats=formats,
            options=TranscriptionOptions(
                language=self.language_combo.currentText().strip() or "auto",
                diarize=self.diarize_check.isChecked(),
                num_speakers=self.speakers_spin.value(),
                grammar=self.grammar_check.isChecked(),
            ),
        )

    def _start(self) -> None:
        job = self._build_job()
        if job is None:
            return
        self._save_settings()

        key = (job.model, job.device)
        cached = self._cached[1] if self._cached and self._cached[0] == key else None
        self.worker = TranscriptionWorker(job, cached)
        self.worker.log.connect(self._log)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.file_started.connect(self.files_list.setCurrentRow)
        self.worker.model_loaded.connect(lambda t: setattr(self, "_cached", (key, t)))
        self.worker.done.connect(self._finished)

        self.log_view.clear()
        self.progress_bar.setValue(0)
        self._set_running(True)
        self._started_at = time.monotonic()
        self._clock.start()
        self.worker.start()

    def _cancel(self) -> None:
        if self.worker:
            self.cancel_button.setEnabled(False)
            self._log("Cancelling after the current segment…")
            self.worker.cancel()

    def _finished(self, succeeded: int, total: int) -> None:
        self._clock.stop()
        self._tick()
        self._set_running(False)
        self.worker = None
        self._log(f"Finished: {succeeded}/{total} files.")
        if succeeded == total:
            self.progress_bar.setValue(100)

    def _set_running(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        for box in self.centralWidget().findChildren(QGroupBox):
            box.setEnabled(not running)

    def _tick(self) -> None:
        self.clock_label.setText(format_duration(time.monotonic() - self._started_at))

    def _log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            answer = QMessageBox.question(self, "THOT", "A transcription is running. Quit anyway?")
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.worker.cancel()
            self.worker.wait(5000)
        self._save_settings()
        event.accept()
