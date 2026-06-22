# EPUB 3.3 Reference Guide

## Table of Contents
1. OPF Metadata Complete Reference
2. NCX Backward Compatibility
3. Font Embedding
4. CSS for E-Readers
5. Accessibility (WCAG / EPUB Accessibility 1.1)
6. ISBN and Registration
7. EPUBCheck
8. Distribution Platforms
9. Troubleshooting
10. EPUB 3.3 vs 3.2 vs 2.0

---

## 1. OPF Metadata Complete Reference

### Required (EPUB 3.3)
```xml
<dc:identifier id="BookId">urn:uuid:...</dc:identifier>
<dc:title>Title</dc:title>
<dc:language>vi</dc:language>
<meta property="dcterms:modified">2026-03-19T00:00:00Z</meta>
```

### Recommended
```xml
<dc:creator id="creator">Author Name</dc:creator>
<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>

<dc:publisher>Publisher Name</dc:publisher>
<dc:date>2026</dc:date>
<dc:description>Book description</dc:description>
<dc:subject>Subject</dc:subject>
<dc:rights>© 2026 All rights reserved</dc:rights>
<dc:source>urn:isbn:978-xxx (if based on print edition)</dc:source>
<dc:type>Text</dc:type>
<dc:format>application/epub+zip</dc:format>
```

### Multiple Authors
```xml
<dc:creator id="author1">Author One</dc:creator>
<meta refines="#author1" property="role" scheme="marc:relators">aut</meta>
<meta refines="#author1" property="display-seq">1</meta>

<dc:creator id="author2">Author Two</dc:creator>
<meta refines="#author2" property="role" scheme="marc:relators">aut</meta>
<meta refines="#author2" property="display-seq">2</meta>
```

### Series Information
```xml
<meta property="belongs-to-collection" id="series">Series Name</meta>
<meta refines="#series" property="collection-type">series</meta>
<meta refines="#series" property="group-position">1</meta>
```

---

## 2. NCX Backward Compatibility

EPUB 2 readers require a `toc.ncx` file. The build script generates this automatically.

Full NCX structure:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:..."/>
    <meta name="dtb:depth" content="2"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>Book Title</text></docTitle>
  <docAuthor><text>Author</text></docAuthor>
  <navMap>
    <navPoint id="navPoint-1" playOrder="1">
      <navLabel><text>Chapter 1</text></navLabel>
      <content src="text/chapter001.xhtml"/>
      <!-- Nested navPoints for sub-sections -->
      <navPoint id="navPoint-1-1" playOrder="2">
        <navLabel><text>Section 1.1</text></navLabel>
        <content src="text/chapter001.xhtml#section-1-1"/>
      </navPoint>
    </navPoint>
  </navMap>
</ncx>
```

---

## 3. Font Embedding

### Supported Formats
- TTF (.ttf) — most compatible
- OTF (.otf) — well supported
- WOFF (.woff) — smaller size
- WOFF2 (.woff2) — smallest, newer readers only

### CSS @font-face
```css
@font-face {
    font-family: "NotoSerif";
    src: url("../fonts/NotoSerifVN-Regular.ttf") format("truetype");
    font-weight: normal;
    font-style: normal;
}

@font-face {
    font-family: "NotoSerif";
    src: url("../fonts/NotoSerifVN-Bold.ttf") format("truetype");
    font-weight: bold;
    font-style: normal;
}

body {
    font-family: "NotoSerif", serif;
}
```

### Recommended Fonts for Vietnamese/Hán-Việt
- Noto Serif Vietnamese (Google Fonts, free)
- Noto Sans Vietnamese (Google Fonts, free)
- Source Han Serif (Adobe, free, CJK + Vietnamese)
- Be Vietnam Pro (Google Fonts, free)

### Font Obfuscation
EPUB supports font obfuscation (not encryption) for licensing:
- IDPF method: algorithm using book identifier
- Adobe method: separate algorithm
Most open-source fonts don't need this.

---

## 4. CSS for E-Readers

### Compatibility Notes
```css
/* Kindle */
/* Kindle ignores: position, float, columns, transforms */
/* Kindle requires: explicit font-size on body */

/* Apple Books */
/* Supports most CSS3 including columns and transforms */

/* Kobo */
/* Good CSS support, similar to WebKit */
/* May override user font-size settings */

/* Google Play Books */
/* WebKit-based, good CSS3 support */
```

### Safe CSS Properties (works everywhere)
```css
/* Typography */
font-family, font-size, font-weight, font-style
line-height, text-align, text-indent, text-decoration
letter-spacing, word-spacing
color

/* Box Model */
margin, padding, border
width, max-width, height (use sparingly)

/* Display */
display: block | inline | none
page-break-before, page-break-after, page-break-inside

/* Lists */
list-style-type, list-style-position
```

### Problematic CSS (avoid or use fallbacks)
```css
/* Avoid these */
position: fixed | absolute  /* unreliable */
float                        /* Kindle issues */
columns                      /* limited support */
transform                    /* limited support */
flexbox                      /* limited support */
grid                         /* very limited */
```

### Vietnamese-specific CSS
```css
/* Vietnamese diacritics need extra line-height */
:lang(vi) {
    line-height: 1.8;
}

/* Classical Chinese needs even more */
:lang(zh-Hant) {
    line-height: 2.0;
}
```

---

## 5. Accessibility (EPUB Accessibility 1.1)

### Required Metadata
```xml
<!-- Conformance -->
<meta property="dcterms:conformsTo">
  EPUB Accessibility 1.1 - WCAG 2.1 Level AA
</meta>

<!-- Access modes -->
<meta property="schema:accessMode">textual</meta>
<meta property="schema:accessModeSufficient">textual</meta>

<!-- Features -->
<meta property="schema:accessibilityFeature">structuredNavigation</meta>
<meta property="schema:accessibilityFeature">readingOrder</meta>
<meta property="schema:accessibilityFeature">alternativeText</meta>
<meta property="schema:accessibilityFeature">tableOfContents</meta>

<!-- Hazards -->
<meta property="schema:accessibilityHazard">none</meta>

<!-- Summary -->
<meta property="schema:accessibilitySummary">
  This publication conforms to WCAG 2.1 Level AA.
</meta>
```

### Content Requirements
- Proper heading hierarchy (h1 → h2 → h3, no skipping)
- `lang` attribute on content in different languages
- `alt` text on all images
- Semantic HTML (section, article, aside, nav)
- ARIA landmarks and labels
- Logical reading order in spine

---

## 6. ISBN and Registration

### When You Need an ISBN
- Required for commercial distribution on most platforms
- Different ISBN for EPUB vs print vs audiobook
- Free ISBNs available in some countries

### Vietnam
- Register through: Cục Xuất bản, In và Phát hành (Ministry of Information)
- Apply for ISBN at: https://www.isbn.gov.vn (if available)
- Alternative: Use a UUID as identifier for non-commercial distribution

### Without ISBN
Use a UUID:
```xml
<dc:identifier id="BookId">urn:uuid:550e8400-e29b-41d4-a716-446655440000</dc:identifier>
```

---

## 7. EPUBCheck

EPUBCheck is the official W3C validation tool.

### Install (requires Java)
```bash
# Download from: https://github.com/w3c/epubcheck/releases
# Run:
java -jar epubcheck.jar book.epub
```

### Common Errors and Fixes
| Error | Fix |
|-------|-----|
| mimetype not first | Ensure mimetype is written first to ZIP |
| mimetype compressed | Use ZIP_STORED for mimetype |
| Missing dcterms:modified | Add `<meta property="dcterms:modified">` |
| Invalid XHTML | Fix self-closing tags, add namespaces |
| Missing nav document | Add toc.xhtml with epub:type="toc" |
| Duplicate IDs | Ensure unique IDs in manifest |

---

## 8. Distribution Platforms

### Amazon Kindle (KDP)
- Convert EPUB to KPF using Kindle Previewer
- Or upload EPUB directly (auto-converted)
- Requires: cover image at least 1600x2560px

### Apple Books
- Upload via iTunes Connect / Apple Books for Authors
- Accepts EPUB 3 directly
- Best CSS support among e-readers

### Google Play Books
- Upload via Google Play Books Partner Center
- Accepts EPUB 3 directly
- Good EPUB 3 support

### Kobo
- Upload via Kobo Writing Life
- Accepts EPUB directly
- Good EPUB 3 support

### Cover Image Requirements
| Platform | Minimum Size | Recommended | Aspect Ratio |
|----------|-------------|-------------|--------------|
| Kindle | 625x1000 | 1600x2560 | 1:1.6 |
| Apple Books | 1400x1873 | 1600x2400 | ~1:1.5 |
| Kobo | 1400x1873 | 1600x2400 | ~1:1.5 |
| General | 1400x2100 | 1600x2400 | 2:3 |

---

## 9. Troubleshooting

### File won't open in reader
1. Validate with EPUBCheck or validate_epub.py
2. Check mimetype is first and uncompressed
3. Verify all XHTML is valid XML
4. Check file paths are case-sensitive

### Vietnamese diacritics not displaying
1. Embed a Vietnamese-compatible font
2. Ensure UTF-8 encoding in all files
3. Add `<meta charset="utf-8"/>` in XHTML head

### Table of Contents not showing
1. Verify `epub:type="toc"` on nav element
2. Check nav item has `properties="nav"` in manifest
3. Ensure toc.xhtml is well-formed XHTML

### Images not displaying
1. Check relative paths from XHTML to images
2. Verify media-type in manifest matches actual format
3. Ensure images are listed in manifest

### Large file size
1. Compress images before embedding (JPEG quality 80%)
2. Subset fonts (only include needed glyphs)
3. Use WOFF2 instead of TTF for fonts

---

## 10. EPUB 3.3 vs 3.2 vs 2.0

| Feature | EPUB 2.0 | EPUB 3.2 | EPUB 3.3 |
|---------|----------|----------|----------|
| Standard | IDPF | IDPF/W3C | W3C |
| Content | XHTML 1.1 | XHTML5 | XHTML5 |
| Navigation | NCX only | NCX + nav | nav (NCX optional) |
| Accessibility | None | Recommended | Required metadata |
| MathML | No | Yes | Yes |
| SVG | Limited | Yes | Yes |
| Audio/Video | No | Yes | Yes |
| JavaScript | No | Yes | Yes |
| CSS | CSS 2.1 | CSS3 | CSS3 |
| Fixed layout | No | Yes | Yes |
