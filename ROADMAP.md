# Roadmap

## Vision

Make it effortless for a student to turn the Google Slides decks embedded in LMS pages
(Canvas, Moodle, ...) into offline PDF/PPTX files: reliable, scriptable, and respectful of
LMS permissions.

## Backlog

- [x] Batch input: `--input-file` with one URL per line, plus `--skip-existing`
- [ ] Searchable PDFs: optional OCR text layer (`--ocr`)
- [ ] `--dry-run` that only lists the decks found on a page
- [ ] Course-level mode: crawl a Canvas modules page for all slide pages
- [ ] Retry failed slides with increasing delay
- [ ] Progress bar instead of per-slide log lines
- [ ] Config file (`~/.slides-downloader/config.toml`) for default options
- [ ] Moodle-specific discovery tests with saved HTML fixtures
- [ ] Optional PDF page size / compression settings
- [ ] Release workflow publishing to PyPI

## Changelog

- 2026-11-01: Added `-i/--input-file` (URL list files, `-` for stdin) and `--skip-existing`; tests added.
