"""Turn a local path or a URL into a media file on disk."""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


class SourceError(Exception):
    """The source could not be read; the message is meant for the user."""


@dataclass(frozen=True)
class Media:
    path: Path
    title: str
    folder: Path


def slugify(title: str, media_id: str = "", max_length: int = 80) -> str:
    """Make a folder name, keeping Cyrillic and adding the id so episodes never collide."""
    slug = re.sub(r"[^\w]+", "-", title, flags=re.UNICODE).strip("-_")[:max_length].rstrip("-_")
    safe_id = re.sub(r"[^\w-]+", "", media_id)[:12]
    return "-".join(part for part in (slug, safe_id) if part) or "untitled"


def build_options(browser: str | None, item: int, outtmpl: str | None = None) -> dict:
    options = {
        # The smallest video is enough when a site has no separate audio track.
        "format": "bestaudio/worst",
        "noplaylist": True,
        "playlist_items": str(item),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": _QuietLogger(),
        # YouTube needs a JS runtime, and yt-dlp only enables deno by default.
        "js_runtimes": {"node": {}},
    }
    if browser:
        options["cookiesfrombrowser"] = (browser,)
    if outtmpl:
        options["outtmpl"] = {"default": outtmpl}
    return options


def pick_entry(info: dict) -> dict:
    """Return the single media item from a yt-dlp result, which may wrap it in a playlist."""
    if "entries" not in info:
        return info
    entries = [entry for entry in info["entries"] if entry]
    if not entries:
        raise SourceError("No media found at this item number.")
    return entries[0]


def pick_title(info: dict, entry: dict) -> str:
    # Boosty calls every video "Video"; yt-dlp keeps the post's title in alt_title.
    if entry.get("extractor_key") == "Boosty" and entry.get("alt_title"):
        return entry["alt_title"]
    return entry.get("title") or info.get("title") or "untitled"


def fetch(source: str, out_root: Path, browser: str | None = None, item: int = 1) -> Media:
    local = Path(source).expanduser()
    if local.is_file():
        return Media(local.resolve(), local.stem, out_root / slugify(local.stem))
    if not re.match(r"https?://", source):
        raise SourceError(f"Not an existing file or an http(s) URL: {source}")
    return _download(source, out_root, browser, item)


def _download(url: str, out_root: Path, browser: str | None, item: int) -> Media:
    try:
        with YoutubeDL(build_options(browser, item)) as ydl:
            info = ydl.extract_info(url, download=False)
        entry = pick_entry(info)
        title = pick_title(info, entry)
        count = info.get("playlist_count") or 0
        if count > 1:
            print(f"This link has {count} items; using item {item} (see --item).", file=sys.stderr)

        folder = out_root / slugify(title, str(entry.get("id", "")))
        folder.mkdir(parents=True, exist_ok=True)
        print(f"Downloading: {title}", file=sys.stderr)
        # yt-dlp skips a finished file and resumes a partial one, so reruns stay cheap.
        with YoutubeDL(build_options(browser, item, str(folder / "source.%(ext)s"))) as ydl:
            ydl.download([url])
    except DownloadError as error:
        raise SourceError(_explain(error, browser)) from error

    return Media(_downloaded_file(folder), title, folder)


def _downloaded_file(folder: Path) -> Path:
    files = [path for path in folder.glob("source.*") if path.suffix != ".part"]
    if not files:
        raise SourceError(f"The download finished without a file in {folder}")
    return max(files, key=lambda path: path.stat().st_mtime)


def _explain(error: DownloadError, browser: str | None) -> str:
    message = re.sub(r"^ERROR:\s*", "", str(error))
    if "cookies" in message.lower() and not browser:
        return f"{message}\nIf you have access, retry with --browser firefox."
    return message


class _QuietLogger:
    """Keep yt-dlp's output off the terminal; errors reach the user through SourceError."""

    def debug(self, message: str) -> None:
        pass

    def info(self, message: str) -> None:
        pass

    def warning(self, message: str) -> None:
        pass

    def error(self, message: str) -> None:
        pass
