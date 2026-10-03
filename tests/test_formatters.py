import json
from pathlib import Path

from thot.config import OutputFormat
from thot.core.formatters import save, to_json, to_srt, to_txt, to_vtt
from thot.core.models import Segment, Transcript


def make_transcript(speakers=False):
    a, b = ("SPEAKER_1", "SPEAKER_2") if speakers else (None, None)
    return Transcript(
        source=Path("/tmp/interview.mp3"),
        language="it",
        duration=3725.5,
        segments=[
            Segment(0.0, 1.5, "Buongiorno.", a),
            Segment(1.5, 3.25, "Come sta?", a),
            Segment(3661.001, 3725.5, "Bene, grazie.", b),
        ],
    )


def test_txt_without_speakers_is_single_paragraph():
    assert to_txt(make_transcript()) == "Buongiorno. Come sta? Bene, grazie.\n"


def test_txt_groups_speaker_turns():
    assert to_txt(make_transcript(speakers=True)) == (
        "[SPEAKER_1]: Buongiorno. Come sta?\n\n[SPEAKER_2]: Bene, grazie.\n"
    )


def test_srt_timestamps_and_numbering():
    srt = to_srt(make_transcript(speakers=True))
    assert srt.startswith("1\n00:00:00,000 --> 00:00:01,500\n[SPEAKER_1] Buongiorno.\n")
    assert "3\n01:01:01,001 --> 01:02:05,500\n[SPEAKER_2] Bene, grazie.\n" in srt


def test_vtt_header_and_separator():
    vtt = to_vtt(make_transcript())
    assert vtt.startswith("WEBVTT\n\n00:00:00.000 --> 00:00:01.500\nBuongiorno.\n")


def test_json_roundtrip():
    data = json.loads(to_json(make_transcript()))
    assert data["source"] == "/tmp/interview.mp3"
    assert data["segments"][1] == {"start": 1.5, "end": 3.25, "text": "Come sta?", "speaker": None}


def test_save_writes_each_format(tmp_path):
    written = save(make_transcript(), tmp_path / "out", [OutputFormat.TXT, OutputFormat.SRT])
    assert [p.name for p in written] == ["interview.txt", "interview.srt"]
    assert all(p.read_text(encoding="utf-8") for p in written)
