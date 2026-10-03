import pytest

from thot.cli.main import build_parser, main


def test_transcribe_defaults():
    args = build_parser().parse_args(["transcribe", "a.mp3"])
    assert args.model == "small"
    assert args.language == "it"
    assert args.device == "auto"
    assert args.speakers == 0
    assert args.formats is None


def test_command_is_required():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_missing_input_returns_error(tmp_path):
    assert main(["transcribe", str(tmp_path / "missing.mp3")]) == 2


def test_empty_folder_returns_error(tmp_path):
    assert main(["transcribe", str(tmp_path)]) == 2
