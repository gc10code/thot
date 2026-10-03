import pytest

from thot.core.audio import collect_audio_files


def test_collect_filters_dedupes_and_recurses(tmp_path):
    (tmp_path / "b.mp3").touch()
    (tmp_path / "a.WAV").touch()
    (tmp_path / "notes.txt").touch()
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.flac").touch()

    flat = collect_audio_files([tmp_path, tmp_path / "b.mp3"])
    assert [p.name for p in flat] == ["a.WAV", "b.mp3"]

    deep = collect_audio_files([tmp_path], recursive=True)
    assert [p.name for p in deep] == ["a.WAV", "b.mp3", "c.flac"]


def test_explicit_file_is_kept_regardless_of_extension(tmp_path):
    clip = tmp_path / "clip.unknown"
    clip.touch()
    assert collect_audio_files([clip]) == [clip.resolve()]


def test_missing_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        collect_audio_files([tmp_path / "nope.mp3"])
