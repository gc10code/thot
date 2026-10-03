"""Lightweight speaker diarization.

Each transcribed segment is summarised by the mean and standard deviation of its
MFCCs, then segments are grouped with agglomerative clustering. Clustering a few
hundred segment vectors (instead of every audio frame) keeps memory and time
linear in the audio length and yields speaker labels that are consistent across
the whole file.
"""

from __future__ import annotations

import numpy as np

from thot.config import SAMPLE_RATE
from thot.core.models import Segment

_N_MFCC = 20
_N_FFT = 512  # 32 ms window
_HOP = 160  # 10 ms hop


def _speaker_label(index: int) -> str:
    return f"SPEAKER_{index + 1}"


def _segment_features(audio: np.ndarray, segments: list[Segment], sr: int) -> np.ndarray:
    import librosa

    features = np.empty((len(segments), 2 * _N_MFCC), dtype=np.float32)
    for i, seg in enumerate(segments):
        chunk = audio[int(seg.start * sr) : int(seg.end * sr)]
        if chunk.size < _N_FFT:
            chunk = np.pad(chunk, (0, _N_FFT - chunk.size))
        mfcc = librosa.feature.mfcc(y=chunk, sr=sr, n_mfcc=_N_MFCC, n_fft=_N_FFT, hop_length=_HOP)
        features[i, :_N_MFCC] = mfcc.mean(axis=1)
        features[i, _N_MFCC:] = mfcc.std(axis=1)
    return features


def assign_speakers(
    audio: np.ndarray, segments: list[Segment], num_speakers: int, sr: int = SAMPLE_RATE
) -> None:
    """Set ``segment.speaker`` in place; labels are numbered by order of first appearance."""
    if not segments:
        return
    if num_speakers <= 1 or len(segments) < num_speakers:
        for seg in segments:
            seg.speaker = _speaker_label(0)
        return

    from sklearn.cluster import AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler

    features = StandardScaler().fit_transform(_segment_features(audio, segments, sr))
    labels = AgglomerativeClustering(n_clusters=num_speakers, linkage="ward").fit_predict(features)

    order: dict[int, int] = {}
    for seg, label in zip(segments, labels):
        seg.speaker = _speaker_label(order.setdefault(int(label), len(order)))
