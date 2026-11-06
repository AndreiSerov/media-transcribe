# media-transcribe

A CLI that downloads media through `yt-dlp` and transcribes it locally with `mlx-whisper`. See `README.md` for usage and options.

## Done means

`uv run pytest && uv run ruff check && uv run ruff format --check` all pass.

Tests fake `yt-dlp` and Whisper, so a change to downloading or transcription also needs a real run on a short public clip, such as `uv run media-transcribe 'https://www.youtube.com/watch?v=jNQXAC9IVRw' -m tiny`. Build fakes from what `yt-dlp` really returns: a guessed result shape once let the tests pass while Boosty folders were named `Video-...`. Report anything you could not run as not run.

## Running on a Linux VPS

Development and every real run so far happened on an Apple Silicon Mac. Treat Linux as untested, and confirm these on the VPS before relying on it:

1. **Install:** `uv sync --frozen`. `mlx` publishes Linux wheels only for glibc 2.35 or newer, so check `ldd --version` first.
2. **System tools:** `ffmpeg` and Node.js. `yt-dlp` uses Node for YouTube.
3. **Transcription:** run the short clip above. `mlx` has no Metal on Linux, so measure the speed as well. If it fails or is too slow, report the result and propose `faster-whisper` behind `transcribe.run`.
4. **YouTube:** datacenter IPs are often challenged for sign-in. Report that error as it stands.

## Paid content

Boosty posts need a logged-in session, and `--browser` is the only way to pass cookies. On the VPS, log in through a headless browser that `yt-dlp` can read:

- **Browser:** use Chromium or Firefox. `--browser` takes only a name from `yt_dlp.cookies.SUPPORTED_BROWSERS`, which leaves out PhantomJS.
- **Profile:** use that browser's default profile, for example `--browser chromium`. Profile paths such as `firefox:/path` are rejected, and a temporary automation profile is never read. To use a custom profile, add support in `build_options`.

This flow is untested. Confirm it on a Boosty post the account can access, and report a captcha or login challenge to the user. Credentials stay out of the repository, logs and command-line arguments.

## Private data

This repository is public. Audio and Transcripts stay in the gitignored `transcripts/` folder, because they can hold paid content and private conversations. Before each commit, check that `git status` lists only code and docs.

## Conventions

- The Transcript path is the only thing on stdout, so scripts can capture it. Everything else goes to stderr.
- Commit messages end at the body, with no `Co-Authored-By` line.
