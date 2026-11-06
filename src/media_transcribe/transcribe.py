"""Run Whisper locally and write the Transcript files."""

import json
from pathlib import Path

MODELS = {
    "tiny": "mlx-community/whisper-tiny",
    "turbo": "mlx-community/whisper-large-v3-turbo",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
}


def run(path: Path, model: str, language: str | None) -> dict:
    # Imported here because mlx-whisper takes seconds to load and --help should not wait.
    import mlx_whisper

    return mlx_whisper.transcribe(
        str(path),
        path_or_hf_repo=MODELS[model],
        language=language,
        # Without earlier text as a prompt, one misheard phrase cannot repeat in a loop.
        condition_on_previous_text=False,
        verbose=False,
    )


def stamp(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"


def format_text(segments: list[dict]) -> str:
    return "".join(f"[{stamp(s['start'])}] {s['text'].strip()}\n" for s in segments)


def write_outputs(result: dict, folder: Path, metadata: dict) -> Path:
    """Write transcript.txt and transcript.json, and return the path of the text file."""
    folder.mkdir(parents=True, exist_ok=True)
    text_path = folder / "transcript.txt"
    text_path.write_text(format_text(result["segments"]), encoding="utf-8")
    (folder / "transcript.json").write_text(
        json.dumps({**metadata, **result}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return text_path
