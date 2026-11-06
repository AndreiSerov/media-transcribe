"""Command line entry point. The Transcript path goes to stdout, everything else to stderr."""

import argparse
import shutil
import sys
from pathlib import Path

from media_transcribe import sources, transcribe


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="media-transcribe",
        description="Transcribe a Boosty post, YouTube video, podcast episode or local file.",
    )
    parser.add_argument("source", help="URL (including a podcast RSS feed) or local file")
    parser.add_argument("-o", "--out", type=Path, default=Path("transcripts"), help="output folder")
    parser.add_argument("-m", "--model", choices=transcribe.MODELS, default="turbo")
    parser.add_argument("-l", "--language", help="language code such as ru; detected if omitted")
    parser.add_argument(
        "--browser",
        help="read this browser's cookies for paid content, e.g. firefox; off unless set",
    )
    parser.add_argument(
        "--item",
        type=int,
        default=1,
        help="which item of a multi-video post or feed; feeds usually list the newest first",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if shutil.which("ffmpeg") is None:
        print("ffmpeg is required: brew install ffmpeg", file=sys.stderr)
        return 1
    try:
        media = sources.fetch(args.source, args.out, args.browser, args.item)
    except sources.SourceError as error:
        print(error, file=sys.stderr)
        return 1

    print(f"Transcribing with {args.model}: {media.path.name}", file=sys.stderr)
    result = transcribe.run(media.path, args.model, args.language)
    metadata = {"source": args.source, "title": media.title, "model": args.model}
    print(transcribe.write_outputs(result, media.folder, metadata))
    return 0


if __name__ == "__main__":
    sys.exit(main())
