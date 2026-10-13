# Canvas Slides Downloader

[![CI](https://github.com/furkanselimozkan07/canvas-slides-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/furkanselimozkan07/canvas-slides-downloader/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Your course puts its lecture slides on a Canvas (or Moodle, or any other LMS) page as an
**embedded Google Slides viewer**, and there is no download button. This tool saves those
slides to your computer as **PDF**, **PowerPoint (PPTX)** and **PNG images** so you can
study offline, print, or annotate them.

```text
$ slides-dl https://canvas.example.edu/courses/123/pages/lecture-02-slides -o ~/Downloads
Opening https://canvas.example.edu/courses/123/pages/lecture-02-slides
Found 1 Google Slides deck(s).
Capturing https://docs.google.com/presentation/d/e/2PACX-.../embed?start=false
  slide 1
  ...
  slide 22
Done: 22 slides
  /home/you/Downloads/lecture-02-slides/lecture-02-slides.pdf
  /home/you/Downloads/lecture-02-slides/lecture-02-slides.pptx
  /home/you/Downloads/lecture-02-slides (PNG images)
```

## Features

- **Works with LMS pages.** Paste the page URL. A browser window opens, you sign in once, and
  the login is remembered for later runs.
- **Also accepts Google Slides links** directly (published `/pub` or `/embed` links, or
  decks shared with "anyone with the link").
- **Animation aware.** Slides with step-by-step animations are saved once, in their final,
  fully built state.
- **Several links at once**, and pages with more than one embedded deck.
- **No extra browser download needed.** Uses Playwright's Chromium if it is installed and
  falls back to your installed Google Chrome or Microsoft Edge otherwise.
- **Clear errors.** If your account cannot open a page (for example, you are not enrolled in
  the course), it tells you right away instead of waiting.

## Quick start

You need **Python 3.10 or newer** ([download](https://www.python.org/downloads/)). On
Windows, tick **"Add python.exe to PATH"** during setup.

Download this repository (green **Code** button → **Download ZIP**, then extract it, or
`git clone https://github.com/furkanselimozkan07/canvas-slides-downloader.git`).

### Windows

1. Double-click **`install.bat`**. You only do this once.
2. Double-click **`run.bat`**, paste one or more links, and press Enter.
3. If a browser window opens, sign in to your LMS there.

The files are saved to your **Downloads** folder.

### macOS / Linux

```sh
./install.sh
./run.sh https://canvas.example.edu/courses/123/pages/lecture-02-slides
```

Files are saved to `~/Downloads` unless you pass `-o`.

### Install as a command (any OS)

```sh
pip install git+https://github.com/furkanselimozkan07/canvas-slides-downloader.git
python -m playwright install chromium   # optional if Chrome or Edge is installed
slides-dl <link> [<link> ...]
```

## Usage

```text
slides-dl URL [URL ...] [options]
```

| Option | Default | Description |
| --- | --- | --- |
| `-o, --output-dir DIR` | current directory | Where the output folders are created |
| `-n, --name NAME` | taken from the URL | Folder/file name (single URL only) |
| `-f, --formats LIST` | `pdf,pptx,png` | Any comma-separated mix of `pdf`, `pptx`, `png` |
| `-b, --browser NAME` | `auto` | `auto`, `chromium`, `chrome` or `msedge` |
| `--profile-dir DIR` | `~/.slides-downloader/browser-profile` | Browser profile that stores your LMS login |
| `--login-timeout SEC` | `300` | How long to wait for you to sign in |
| `--delay SEC` | `1.2` | Wait after each slide step. Increase it on slow connections |
| `--scale N` | `1.5` | Screenshot scale. Higher values give sharper images |
| `--max-steps N` | `600` | Safety limit on slide/animation steps per deck |
| `-v, --verbose` | | Debug output |

Examples:

```sh
# Several lectures at once, PDF only
slides-dl -f pdf -o ~/Downloads \
  https://canvas.example.edu/courses/123/pages/lecture-02-slides \
  https://canvas.example.edu/courses/123/pages/lecture-03-slides

# A published Google Slides link, custom name, extra sharp
slides-dl "https://docs.google.com/presentation/d/e/2PACX-.../pub" -n Week5 --scale 2
```

With `run.bat` you can also pass the same options on the command line:
`run.bat <link> -o D:\Notes -f pdf`.

### Docker (direct Google Slides links only)

Signing in to an LMS needs a visible browser, so **LMS page URLs do not work in Docker**.

```sh
docker build -t slides-dl .
docker run --rm -v "$(pwd)/output:/output" slides-dl "<Google Slides link>"
```

On Windows (cmd) use `-v "%cd%\output:/output"`.

## How it works

```text
LMS page URL ──► discover.py ──► Google Slides embed URL(s) ──► capture.py ──► export.py
                 (visible browser,                              (headless,      (PDF, PPTX,
                  persistent login)                              one shot per    PNG)
                                                                 slide)
```

1. **Discover**: opens the page in a browser with a persistent profile, waits for you to sign
   in if needed, and reads the `src` of every embedded Google Slides `<iframe>`.
2. **Capture**: opens each deck headlessly, steps through it with the arrow keys and
   screenshots only the slide area. Animation steps share a slide id, so only the last state
   of each slide is kept. Capture stops once the image no longer changes.
3. **Export**: writes the screenshots as PNGs, a multi-page PDF, and a PPTX with one
   full-size image per slide.

The slides are saved as **images**, so the PDF/PPTX text cannot be selected or edited.

```text
src/slides_downloader/
├── cli.py        # argument parsing and orchestration
├── discover.py   # find embedded decks on an LMS page (handles login)
├── capture.py    # step through a deck and screenshot each slide
├── export.py     # PNG / PDF / PPTX writers
├── browser.py    # browser launch with Chromium → Chrome → Edge fallback
├── urls.py       # pure URL helpers
└── errors.py     # user-facing exception types
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Your account is not allowed to view ...` | You are not enrolled in that course, or the page is unpublished. The tool cannot (and will not) get around LMS permissions. Ask your instructor or a classmate for the Google Slides link and pass that instead. |
| `No embedded Google Slides deck found` | You did not sign in before the timeout (`--login-timeout`), or the page embeds something else, such as a PDF or a video. |
| `Could not start a browser` / Chromium download times out | Install Google Chrome or Microsoft Edge, or run `python -m playwright install chromium` on another network. |
| Some slides are missing or half-loaded | Increase `--delay`, for example `--delay 2.5`. |
| `No slides were captured` for a Google link | The deck must be *published to the web* or shared with *anyone with the link*. |
| Want to sign in with a different account | Delete `~/.slides-downloader/browser-profile` or pass another `--profile-dir`. |

## Development

```sh
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
ruff check .
pytest
```

Unit tests cover URL handling, exporting and CLI parsing. They do not launch a browser.
Issues and pull requests are welcome.

## Responsible use

Use this tool only for material **you are allowed to access**, for your own study.
Lecture slides are usually the instructor's or university's copyrighted work. Do not
redistribute them without permission, and follow your institution's policies. The tool uses
your own login and never bypasses access controls.

## License

[MIT](LICENSE)
