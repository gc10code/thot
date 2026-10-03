import numpy as np

from thot.config import SAMPLE_RATE
from thot.core.diarization import assign_speakers
from thot.core.models import Segment


def _voice(freq: float, seconds: float, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    harmonics = sum(np.sin(2 * np.pi * freq * k * t) / k for k in range(1, 6))
    return (0.3 * harmonics + 0.01 * rng.standard_normal(t.size)).astype(np.float32)


def test_two_distinct_voices_are_separated():
    rng = np.random.default_rng(0)
    pattern = [110, 110, 320, 110, 320, 320]  # low / high "speakers" alternating
    audio = np.concatenate([_voice(f, 1.0, rng) for f in pattern])
    segments = [Segment(float(i), float(i + 1), "x") for i in range(len(pattern))]

    assign_speakers(audio, segments, num_speakers=2)

    labels = [s.speaker for s in segments]
    assert labels[0] == "SPEAKER_1"  # numbered by first appearance
    expected = ["SPEAKER_1" if f == 110 else "SPEAKER_2" for f in pattern]
    assert labels == expected


def test_single_speaker_and_short_input():
    segments = [Segment(0.0, 0.01, "a")]
    assign_speakers(np.zeros(SAMPLE_RATE, dtype=np.float32), segments, num_speakers=3)
    assert segments[0].speaker == "SPEAKER_1"
    assign_speakers(np.zeros(1, dtype=np.float32), [], num_speakers=2)  # no-op
