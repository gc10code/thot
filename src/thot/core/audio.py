"""Audio decoding and input discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np

from thot.config import AUDIO_EXTENSIONS, SAMPLE_RATE


def load_audio(path: Path) -> np.ndarray:
    """Decode the first audio stream of any FFmpeg-supported file to mono float32 at :data:`SAMPLE_RATE`."""
    import av

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    resampler = av.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
    chunks: list[np.ndarray] = []
    with av.open(str(path)) as container:
        if not container.streams.audio:
            raise ValueError(f"No audio stream in {path.name}")
        stream = container.streams.audio[0]
        for frame in container.decode(stream):
            chunks.extend(f.to_ndarray().reshape(-1) for f in resampler.resample(frame))
        chunks.extend(f.to_ndarray().reshape(-1) for f in resampler.resample(None))

    return np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)


def is_audio_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS


def collect_audio_files(paths: Iterable[Path], recursive: bool = False) -> list[Path]:
    """Expand files and directories into a sorted, de-duplicated list of audio files."""
    found: dict[Path, None] = {}
    for path in paths:
        if path.is_dir():
            candidates = path.rglob("*") if recursive else path.iterdir()
            for child in sorted(candidates):
                if is_audio_file(child):
                    found[child.resolve()] = None
        elif path.is_file():
            found[path.resolve()] = None
        else:
            raise FileNotFoundError(f"No such file or directory: {path}")
    return list(found)
