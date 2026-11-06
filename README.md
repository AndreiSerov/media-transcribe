# media-transcribe

Transcribes a Boosty post, YouTube video, podcast episode or local file. Downloads go through [yt-dlp](https://github.com/yt-dlp/yt-dlp), which covers many more sites. Transcription runs locally with `mlx-whisper`, so it needs Apple Silicon and `ffmpeg`.

## Usage

```sh
uv run media-transcribe 'https://www.youtube.com/watch?v=jNQXAC9IVRw'
uv run media-transcribe 'https://boosty.to/<blog>/posts/<id>' --browser firefox -l ru
uv run media-transcribe 'https://example.com/podcast/feed.xml' --item 2
uv run media-transcribe ~/Downloads/call.m4a -m large-v3
```

To run it from any folder, install it with `uv tool install --editable .`.

| Option | Meaning |
|---|---|
| `-o`, `--out` | Output folder, `./transcripts` by default |
| `-m`, `--model` | `turbo` (default), `large-v3` (slower) or `tiny` (for quick checks) |
| `-l`, `--language` | Language code such as `ru`; detected if omitted |
| `--browser` | Browser to read cookies from, needed for paid content |
| `--item` | Item number in a multi-video post or feed, `1` by default |

Each source gets its own folder, `transcripts/<title>-<id>/`, holding:

- `source.<ext>`: the downloaded media. A rerun reuses it. Local files stay where they are and aren't copied.
- `transcript.txt`: the text with timestamps.
- `transcript.json`: segments with timings, plus the source, title and model.

The Transcript path goes to stdout and everything else to stderr, so `less "$(uv run media-transcribe <url>)"` works.

## Limits

- There are no speaker labels.
- `--browser` makes yt-dlp read that browser's cookie store and send the matching cookies to the site. Without the flag, no cookies are read.
- Spotify's own shows use DRM and can't be downloaded. Use the show's RSS feed when it has one.
- Models download from Hugging Face on first use. Audio and Transcripts never leave the machine.

## Development

```sh
uv run pytest && uv run ruff check && uv run ruff format --check
```
