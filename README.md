# epub-builder — Build W3C-compliant EPUB 3.3 ebooks from raw chapters

> Assemble polished EPUB 3.3 ebooks from a folder of chapters, a cover, and metadata. Pure Python with lxml and zipfile — no heavy EPUB dependencies.

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blueviolet)](https://github.com/NachaFromMars)

## Overview
epub-builder creates EPUB 3.3 ebooks from almost any source format using only lxml and Python's standard `zipfile`. Point it at an input directory with your chapters, cover image, optional assets, and metadata — it handles the rest. Chapter filenames determine reading order via numeric prefix convention.

## Features
- **EPUB 3.3 + W3C compliant** output
- **No external EPUB libs** — just lxml + zipfile
- **Input formats** — `.xhtml`, `.html`, `.md`, `.txt`
- **Full asset support** — cover, `images/`, `style.css`, `fonts/`, `metadata.json`
- **Deterministic order** — `001_`, `002_` filename prefixes

## Usage / Quick Start
```bash
python3 scripts/build_epub.py   --title "Book Title"   --author "Author Name"   --language vi   --input /path/to/content/   --output book.epub
```
Input directory layout: `chapters/` + `cover.jpg` + `images/` + `style.css` + `fonts/` + `metadata.json`

## Trigger Keywords (OpenClaw)
epub, ebook, e-book, electronic book, publish digitally, make this a book, package as ebook

## Related Skills
- [epub-forge](https://github.com/NachaFromMars/epub-forge) — Markdown + YAML pipeline alternative
- [epub-reader](https://github.com/NachaFromMars/epub-reader) — read and convert EPUB files

---
Part of the [NachaFromMars](https://github.com/NachaFromMars) OpenClaw skill ecosystem.
