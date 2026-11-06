from typing import ClassVar

import pytest
from yt_dlp.utils import DownloadError

from media_transcribe import sources


def test_slugify_keeps_cyrillic_and_appends_id():
    assert (
        sources.slugify("Созвон клуба: AI-Harness!", "abc/123") == "Созвон-клуба-AI-Harness-abc123"
    )


def test_slugify_truncates_long_titles_and_handles_empty():
    assert len(sources.slugify("я" * 200)) == 80
    assert sources.slugify("!!!") == "untitled"


def test_options_do_not_use_cookies_unless_a_browser_is_given():
    assert "cookiesfrombrowser" not in sources.build_options(None, 1)
    assert sources.build_options("firefox", 1)["cookiesfrombrowser"] == ("firefox",)


def test_options_select_the_requested_item():
    assert sources.build_options(None, 3)["playlist_items"] == "3"


def test_pick_entry_unwraps_playlists_and_passes_single_items():
    video = {"id": "a"}
    assert sources.pick_entry(video) is video
    assert sources.pick_entry({"entries": [None, video]}) is video


def test_pick_entry_reports_an_empty_playlist():
    with pytest.raises(sources.SourceError):
        sources.pick_entry({"entries": []})


def test_boosty_title_comes_from_the_post_for_a_single_video():
    # The shape yt-dlp really returns: one video is not wrapped in a playlist.
    info = {"title": "Video", "alt_title": "Созвон", "extractor_key": "Boosty"}
    assert sources.pick_title(info, info) == "Созвон"


def test_boosty_title_comes_from_the_post_for_several_videos():
    entry = {"title": "Video", "alt_title": "Созвон", "extractor_key": "Boosty"}
    assert sources.pick_title({"title": "Созвон", "entries": [entry]}, entry) == "Созвон"


def test_feed_title_comes_from_the_episode():
    entry = {"title": "Episode 5", "extractor_key": "Generic"}
    assert sources.pick_title({"title": "The Show", "entries": [entry]}, entry) == "Episode 5"


def test_fetch_uses_a_local_file_without_downloading(tmp_path, monkeypatch):
    def fail(*args):
        raise AssertionError("must not download")

    monkeypatch.setattr(sources, "_download", fail)
    audio = tmp_path / "my call.m4a"
    audio.write_bytes(b"x")
    media = sources.fetch(str(audio), tmp_path / "out")
    assert media.path == audio.resolve()
    assert media.title == "my call"
    assert media.folder == tmp_path / "out" / "my-call"


def test_fetch_rejects_what_is_neither_file_nor_url(tmp_path):
    with pytest.raises(sources.SourceError, match="Not an existing file"):
        sources.fetch("no-such-file.mp3", tmp_path)


class FakeYoutubeDL:
    """Stands in for yt-dlp: reports one item and writes a file on download."""

    info: ClassVar[dict] = {}

    def __init__(self, options):
        self.options = options

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def extract_info(self, url, download):
        return self.info

    def download(self, urls):
        template = self.options["outtmpl"]["default"]
        with open(template.replace("%(ext)s", "m4a"), "wb") as file:
            file.write(b"x")


def test_download_puts_the_file_in_a_folder_named_after_the_title(tmp_path, monkeypatch):
    FakeYoutubeDL.info = {"id": "abc", "title": "Episode", "extractor_key": "Youtube"}
    monkeypatch.setattr(sources, "YoutubeDL", FakeYoutubeDL)
    media = sources.fetch("https://example.com/x", tmp_path)
    assert media.title == "Episode"
    assert media.folder == tmp_path / "Episode-abc"
    assert media.path == tmp_path / "Episode-abc" / "source.m4a"


def test_download_warns_when_a_link_has_several_items(tmp_path, monkeypatch, capsys):
    entry = {"id": "abc", "title": "Episode"}
    FakeYoutubeDL.info = {"title": "Feed", "entries": [entry], "playlist_count": 40}
    monkeypatch.setattr(sources, "YoutubeDL", FakeYoutubeDL)
    sources.fetch("https://example.com/feed", tmp_path, item=2)
    assert "40 items; using item 2" in capsys.readouterr().err


def test_paid_content_error_suggests_browser_only_when_none_was_given(tmp_path, monkeypatch):
    class Denied(FakeYoutubeDL):
        def extract_info(self, url, download):
            raise DownloadError("ERROR: This post requires a subscription. Use --cookies")

    monkeypatch.setattr(sources, "YoutubeDL", Denied)
    with pytest.raises(sources.SourceError, match="--browser firefox"):
        sources.fetch("https://boosty.to/a/posts/b", tmp_path)
    with pytest.raises(sources.SourceError) as caught:
        sources.fetch("https://boosty.to/a/posts/b", tmp_path, browser="firefox")
    assert "--browser" not in str(caught.value)
    assert not str(caught.value).startswith("ERROR")
