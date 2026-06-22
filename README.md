---
name: epub-builder
description: Use this skill whenever the user wants to create, build, convert, or package EPUB files (.epub). This includes converting documents (PDF, DOCX, Markdown, HTML, TXT, or any text content) into EPUB 3.3 format, creating ebooks from scratch, packaging content into standards-compliant EPUB, adding metadata (ISBN, author, language, accessibility), building table of contents, or validating EPUB files. Trigger whenever the user mentions 'epub', 'ebook', 'electronic book', 'e-book', asks to 'publish digitally', wants a 'readable book format', or references any .epub file. Also trigger when the user wants to convert any document into a book-like format for e-readers (Kindle, Kobo, Apple Books, Google Play Books). Even if the user just says 'make this into a book' or 'package this as an ebook', use this skill.
---

# EPUB 3.3 Builder Skill

## Overview

This skill creates **EPUB 3.3** files that comply with the W3C international standard. It uses Python with `lxml` and `zipfile` — no external EPUB libraries needed.

## Quick Start

For any EPUB creation task, run the build script:

```bash
python3 /path/to/skill/scripts/build_epub.py \
  --title "Book Title" \
  --author "Author Name" \
  --language "vi" \
  --input /path/to/content/ \
  --output /path/to/output.epub
```

The input directory should contain:
- `chapters/` — folder of `.xhtml`, `.html`, `.md`, or `.txt` files (sorted alphabetically = reading order)
- `cover.jpg` or `cover.png` — cover image (optional)
- `images/` — folder of inline images referenced by chapters (optional)
- `metadata.json` — metadata overrides (optional)
- `style.css` — custom stylesheet (optional, default provided)
- `fonts/` — embedded font files (optional)

## Workflow

### Step 1: Prepare Content

Convert source material to chapter files. The build script accepts:

- **XHTML** (.xhtml) — used as-is
- **HTML** (.html) — auto-converted to valid XHTML5
- **Markdown** (.md) — converted to XHTML via Python markdown lib
- **Plain text** (.txt) — wrapped in XHTML with paragraph tags

Each file = one chapter. Filename determines reading order (e.g., `001_introduction.xhtml`, `002_chapter1.xhtml`).

### Step 2: Prepare Metadata

Create `metadata.json` in the input directory (or pass via CLI flags):

```json
{
  "title": "Chỉ Giới Đại Đại Kinh",
  "author": "Đại Mông Đồ",
  "language": "vi",
  "identifier": "urn:isbn:978-xxx-xxx",
  "publisher": "Publisher Name",
  "date": "2026",
  "description": "Bộ kinh Chỉ Giới thuộc pháp môn Đại Đại",
  "subject": "Buddhism, Vietnamese Buddhist Scripture",
  "rights": "© 2026 All rights reserved",
  "cover_image": "cover.jpg"
}
```

If no identifier is provided, a UUID is auto-generated.

### Step 3: Build EPUB

```bash
python3 scripts/build_epub.py --input ./content/ --output ./book.epub
```

### Step 4: Validate

```bash
python3 scripts/validate_epub.py ./book.epub
```

## EPUB 3.3 File Structure

```
book.epub (ZIP archive)
├── mimetype                          # First file, uncompressed
├── META-INF/
│   └── container.xml                 # Points to content.opf
├── OEBPS/
│   ├── content.opf                   # Package document
│   ├── toc.xhtml                     # Navigation document (EPUB 3)
│   ├── toc.ncx                       # NCX backward compat (EPUB 2)
│   ├── styles/
│   │   └── style.css                 # Stylesheet
│   ├── images/
│   │   └── cover.jpg                 # Cover image
│   ├── text/
│   │   ├── cover.xhtml               # Cover page
│   │   ├── titlepage.xhtml           # Title page
│   │   ├── chapter001.xhtml          # Chapters...
│   │   └── ...
│   └── fonts/                        # Embedded fonts (optional)
```

## Critical EPUB 3.3 Rules

1. **mimetype** MUST be the first entry in the ZIP, stored without compression
2. All content files MUST be valid XHTML5 with proper XML namespaces
3. `lang` AND `xml:lang` attributes required on `<html>` element
4. Navigation document (`toc.xhtml`) with `epub:type="toc"` is mandatory
5. Package document MUST include `dcterms:modified` meta
6. Accessibility metadata is strongly recommended (required for some distributors)

## Multi-language support (Hán-Việt)

For texts mixing Vietnamese and Classical Chinese:
```xml
<p lang="vi" xml:lang="vi">Kiến giải:</p>
<p lang="zh-Hant" xml:lang="zh-Hant">大大離二邊</p>
```

## Accessibility (EPUB 3.3)

The build script automatically includes:
- Structural navigation via `<nav epub:type="toc">`
- Proper heading hierarchy (h1 → h2 → h3)
- `lang` and `xml:lang` on all content
- ARIA labels on sections
- Reading order in spine
- Full accessibility metadata in OPF

## Scripts

- `scripts/build_epub.py` — Main builder: content directory → .epub
- `scripts/validate_epub.py` — Validates EPUB structure
- `scripts/convert_to_xhtml.py` — Converts text/markdown → XHTML5

## Reference

See `references/REFERENCE.md` for complete OPF metadata options, NCX format, font embedding, CSS for e-readers, ISBN info, and troubleshooting.
