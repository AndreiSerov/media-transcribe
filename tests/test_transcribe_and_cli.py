import json

from media_transcribe import cli, sources, transcribe

RESULT = {"language": "ru", "segments": [{"start": 3725.9, "end": 3727.0, "text": "  Привет. "}]}


def test_stamp_formats_hours_minutes_seconds():
    assert transcribe.stamp(3725.9) == "01:02:05"


def test_write_outputs_writes_text_and_json_with_metadata(tmp_path):
    path = transcribe.write_outputs(RESULT, tmp_path / "new", {"title": "T"})
    assert path.read_text(encoding="utf-8") == "[01:02:05] Привет.\n"
    saved = json.loads((tmp_path / "new" / "transcript.json").read_text(encoding="utf-8"))
    assert saved["title"] == "T"
    assert saved["language"] == "ru"


def test_main_prints_only_the_transcript_path_to_stdout(tmp_path, monkeypatch, capsys):
    audio = tmp_path / "call.mp3"
    audio.write_bytes(b"x")
    calls = []

    def fake_run(path, model, language):
        calls.append((path, model, language))
        return RESULT

    monkeypatch.setattr(transcribe, "run", fake_run)
    code = cli.main([str(audio), "-o", str(tmp_path / "out"), "-m", "tiny", "-l", "ru"])
    assert code == 0
    assert capsys.readouterr().out.strip() == str(tmp_path / "out" / "call" / "transcript.txt")
    assert calls == [(audio.resolve(), "tiny", "ru")]


def test_main_reports_a_source_error_and_exits_non_zero(tmp_path, monkeypatch, capsys):
    def denied(*args):
        raise sources.SourceError("needs a subscription")

    monkeypatch.setattr(sources, "fetch", denied)
    assert cli.main(["https://example.com/x", "-o", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert "needs a subscription" in captured.err
    assert captured.out == ""


def test_main_requires_ffmpeg(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli.shutil, "which", lambda name: None)
    assert cli.main(["x.mp3", "-o", str(tmp_path)]) == 1
    assert "ffmpeg" in capsys.readouterr().err
