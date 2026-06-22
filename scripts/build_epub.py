#!/usr/bin/env python3
"""
EPUB 3.3 Builder — W3C International Standard Compliant
Converts a content directory into a valid EPUB 3.3 file.

Usage:
    python3 build_epub.py --input ./content/ --output ./book.epub
    python3 build_epub.py --title "My Book" --author "Author" --language "vi" --input ./content/ --output ./book.epub

Input directory structure:
    content/
    ├── chapters/          # .xhtml, .html, .md, or .txt files (sorted = reading order)
    ├── metadata.json      # Optional metadata overrides
    ├── cover.jpg/.png     # Optional cover image
    ├── style.css          # Optional custom stylesheet
    └── fonts/             # Optional font files (.ttf, .otf, .woff, .woff2)
"""

import argparse
import json
import os
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from html import escape as html_escape

try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


# ============================================================================
# Constants
# ============================================================================

EPUB_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
NCX_NS = "http://www.daisy.org/z3986/2005/ncx/"
XHTML_NS = "http://www.w3.org/1999/xhtml"
EPUB_OPS_NS = "http://www.idpf.org/2007/ops"

MEDIA_TYPES = {
    '.xhtml': 'application/xhtml+xml',
    '.html': 'application/xhtml+xml',
    '.css': 'text/css',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ttf': 'font/ttf',
    '.otf': 'font/otf',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ncx': 'application/x-dtbncx+xml',
    '.js': 'application/javascript',
}

DEFAULT_CSS = """/* EPUB 3.3 Default Stylesheet — Optimized for Vietnamese/Hán-Việt */
@charset "UTF-8";

/* === Base Reset === */
body {
    font-family: "Noto Serif", "Noto Sans", "Source Han Serif", Georgia, "Times New Roman", serif;
    font-size: 1em;
    line-height: 1.8;
    margin: 1em;
    padding: 0;
    color: #1a1a1a;
    text-align: justify;
    -webkit-hyphens: auto;
    hyphens: auto;
}

/* === Headings === */
h1 {
    font-size: 1.8em;
    text-align: center;
    margin: 1.5em 0 1em;
    line-height: 1.3;
    page-break-before: always;
    page-break-after: avoid;
}

h2 {
    font-size: 1.4em;
    margin: 1.2em 0 0.6em;
    line-height: 1.4;
    page-break-after: avoid;
}

h3 {
    font-size: 1.2em;
    margin: 1em 0 0.5em;
    line-height: 1.4;
    page-break-after: avoid;
}

h4 {
    font-size: 1.1em;
    margin: 0.8em 0 0.4em;
    font-style: italic;
}

/* === Paragraphs === */
p {
    margin: 0.5em 0;
    text-indent: 1.5em;
    orphans: 2;
    widows: 2;
}

p.no-indent {
    text-indent: 0;
}

p.first-paragraph {
    text-indent: 0;
}

/* === Buddhist Scripture Formatting === */
.kinh-van {
    font-style: italic;
    margin: 1em 1.5em;
    line-height: 2;
    text-indent: 0;
}

.han-viet {
    font-weight: bold;
    font-size: 1.05em;
    line-height: 2;
}

.kien-giai {
    margin: 0.5em 0 0.5em 1em;
    font-size: 0.95em;
}

.ke-tung {
    text-align: center;
    margin: 1em 2em;
    line-height: 2.2;
    font-style: italic;
}

.ke-tung p {
    text-indent: 0;
    margin: 0.2em 0;
}

/* === Verse / Poetry === */
.verse {
    margin: 1em 2em;
    text-indent: 0;
}

.verse p {
    text-indent: 0;
    margin: 0.2em 0;
}

/* === Lists === */
ul, ol {
    margin: 0.5em 0 0.5em 1.5em;
    padding: 0;
}

li {
    margin: 0.3em 0;
}

/* === Blockquote === */
blockquote {
    margin: 1em 1.5em;
    font-style: italic;
    border-left: 3px solid #999;
    padding-left: 1em;
}

/* === Cover === */
.cover-page {
    text-align: center;
    padding: 0;
    margin: 0;
}

.cover-page img {
    max-width: 100%;
    max-height: 100%;
    height: auto;
}

/* === Title Page === */
.title-page {
    text-align: center;
    padding-top: 20%;
}

.title-page h1 {
    font-size: 2em;
    margin-bottom: 0.5em;
    page-break-before: avoid;
}

.title-page .author {
    font-size: 1.3em;
    margin-top: 2em;
    font-style: italic;
}

.title-page .publisher {
    font-size: 1em;
    margin-top: 3em;
    color: #666;
}

/* === Table of Contents === */
nav#toc ol {
    list-style-type: none;
    padding-left: 0;
}

nav#toc ol ol {
    padding-left: 1.5em;
}

nav#toc a {
    text-decoration: none;
    color: #333;
}

nav#toc a:hover {
    color: #000;
    text-decoration: underline;
}

/* === Separator === */
hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 2em auto;
    width: 30%;
}

/* === Emphasis === */
em {
    font-style: italic;
}

strong {
    font-weight: bold;
}

/* === Images === */
img {
    max-width: 100%;
    height: auto;
}

figure {
    margin: 1em 0;
    text-align: center;
}

figcaption {
    font-size: 0.9em;
    color: #666;
    margin-top: 0.5em;
}

/* === Footnotes === */
.footnote {
    font-size: 0.85em;
    vertical-align: super;
    line-height: 0;
}

aside[epub|type="footnote"] {
    font-size: 0.85em;
    margin: 0.5em 1em;
    padding: 0.5em;
    border-top: 1px solid #ccc;
}

/* === Colophon === */
.colophon {
    text-align: center;
    font-size: 0.9em;
    margin-top: 3em;
}

/* === Page break control === */
.page-break-before {
    page-break-before: always;
}

.page-break-after {
    page-break-after: always;
}

/* === Print-like styling for classical texts === */
.classical-text {
    font-size: 1.1em;
    line-height: 2.2;
    letter-spacing: 0.02em;
}
"""


# ============================================================================
# Helper Functions
# ============================================================================

def generate_uuid():
    """Generate a URN UUID identifier."""
    return f"urn:uuid:{uuid.uuid4()}"


def get_modified_time():
    """Get current UTC time in W3C format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize_id(text):
    """Create a valid XML ID from text."""
    text = re.sub(r'[^\w\-]', '_', text)
    if text and text[0].isdigit():
        text = 'id_' + text
    return text


def fix_html_entities(content):
    """Convert HTML named entities to Unicode characters (XHTML only allows 5: &amp; &lt; &gt; &quot; &apos;)."""
    ENTITY_MAP = {
        '&mdash;': '\u2014', '&ndash;': '\u2013', '&hellip;': '\u2026',
        '&lsquo;': '\u2018', '&rsquo;': '\u2019', '&ldquo;': '\u201C',
        '&rdquo;': '\u201D', '&nbsp;': '\u00A0', '&bull;': '\u2022',
        '&copy;': '\u00A9', '&reg;': '\u00AE', '&trade;': '\u2122',
        '&diams;': '\u2666', '&hearts;': '\u2665', '&spades;': '\u2660',
        '&clubs;': '\u2663', '&larr;': '\u2190', '&rarr;': '\u2192',
        '&uarr;': '\u2191', '&darr;': '\u2193', '&laquo;': '\u00AB',
        '&raquo;': '\u00BB', '&deg;': '\u00B0', '&plusmn;': '\u00B1',
        '&times;': '\u00D7', '&divide;': '\u00F7', '&micro;': '\u00B5',
        '&para;': '\u00B6', '&sect;': '\u00A7', '&cent;': '\u00A2',
        '&pound;': '\u00A3', '&yen;': '\u00A5', '&euro;': '\u20AC',
        '&frac12;': '\u00BD', '&frac14;': '\u00BC', '&frac34;': '\u00BE',
        '&iquest;': '\u00BF', '&iexcl;': '\u00A1', '&ordf;': '\u00AA',
        '&ordm;': '\u00BA', '&not;': '\u00AC', '&shy;': '\u00AD',
        '&macr;': '\u00AF', '&sup1;': '\u00B9', '&sup2;': '\u00B2',
        '&sup3;': '\u00B3', '&acute;': '\u00B4', '&cedil;': '\u00B8',
        '&middot;': '\u00B7', '&ensp;': '\u2002', '&emsp;': '\u2003',
        '&thinsp;': '\u2009', '&zwnj;': '\u200C', '&zwj;': '\u200D',
        '&lrm;': '\u200E', '&rlm;': '\u200F',
    }
    for entity, char in ENTITY_MAP.items():
        content = content.replace(entity, char)
    # Convert numeric entities (&#123; and &#x1F; forms)
    content = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), content)
    content = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), content)
    return content


def extract_title_from_xhtml(content):
    """Extract the first h1/h2 text from XHTML content using lxml if available, regex fallback."""
    if HAS_LXML:
        try:
            # Parse and extract properly
            tree = etree.fromstring(content.encode('utf-8') if isinstance(content, str) else content)
            ns = {'x': XHTML_NS}
            for tag in ['h1', 'h2']:
                elem = tree.find(f'.//x:{tag}', ns)
                if elem is None:
                    elem = tree.find(f'.//{tag}')
                if elem is not None:
                    text = ''.join(elem.itertext()).strip()
                    if text:
                        return text
        except Exception:
            pass
    # Regex fallback
    match = re.search(r'<h[12][^>]*>(.*?)</h[12]>', content, re.DOTALL)
    if match:
        return re.sub(r'<[^>]+>', '', match.group(1)).strip()
    return None


def text_to_xhtml(text, title="Untitled", lang="vi"):
    """Convert plain text to XHTML5."""
    paragraphs = text.strip().split('\n\n')
    body_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Heading heuristic: short, single line, no trailing punctuation, no newlines
        if len(p) < 80 and '\n' not in p and not p.endswith(('.', ',', ':', ';', '!', '?', '。', '…')):
            body_parts.append(f'  <h2>{html_escape(p)}</h2>')
        else:
            lines = p.split('\n')
            body_parts.append(f'  <p>{html_escape(chr(10).join(lines))}</p>')

    body_html = '\n'.join(body_parts)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">
<head>
  <title>{html_escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
</head>
<body>
  <section epub:type="chapter" aria-label="{html_escape(title)}">
  <h1>{html_escape(title)}</h1>
{body_html}
  </section>
</body>
</html>'''


def markdown_to_xhtml(md_text, title="Untitled", lang="vi"):
    """Convert Markdown to XHTML5."""
    if not HAS_MARKDOWN:
        # Fallback: treat as plain text
        return text_to_xhtml(md_text, title, lang)

    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    # Fix entities from markdown output
    html_body = fix_html_entities(html_body)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">
<head>
  <title>{html_escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
</head>
<body>
  <section epub:type="chapter" aria-label="{html_escape(title)}">
{html_body}
  </section>
</body>
</html>'''


def html_to_xhtml(html_content, lang="vi"):
    """Convert HTML to valid XHTML5 using lxml when available, regex fallback."""
    # Step 0: Fix HTML entities FIRST (before any XML parsing)
    html_content = fix_html_entities(html_content)

    if HAS_LXML:
        try:
            from lxml import html as lhtml
            # Parse as HTML (tolerant) then serialize as XHTML (strict)
            doc = lhtml.fromstring(html_content)
            # Ensure it's a full html document
            if doc.tag != 'html':
                doc = lhtml.document_fromstring(html_content)
            # Set namespaces and lang
            html_elem = doc if doc.tag == 'html' else doc.find('.//html')
            if html_elem is None:
                html_elem = doc
            html_elem.set('xmlns', XHTML_NS)
            html_elem.set('xmlns:epub', EPUB_OPS_NS)
            if not html_elem.get('lang'):
                html_elem.set('lang', lang)
            if not html_elem.get('{http://www.w3.org/XML/1998/namespace}lang'):
                html_elem.set('xml:lang', lang)
            # Serialize as XHTML
            result = etree.tostring(doc, encoding='unicode', method='xml', xml_declaration=False)
            # Add XML declaration and DOCTYPE
            result = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n' + result
            return result
        except Exception:
            pass  # Fall through to regex method

    # Regex fallback (original logic + entity fix)
    if not html_content.strip().startswith('<?xml'):
        html_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + html_content

    if '<!DOCTYPE' not in html_content.upper():
        html_content = html_content.replace('<?xml version="1.0" encoding="UTF-8"?>',
            '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>')

    if 'xmlns="http://www.w3.org/1999/xhtml"' not in html_content:
        html_content = html_content.replace('<html', f'<html xmlns="http://www.w3.org/1999/xhtml"', 1)

    if 'xmlns:epub' not in html_content:
        html_content = html_content.replace('xmlns="http://www.w3.org/1999/xhtml"',
            'xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"')

    if f'lang="{lang}"' not in html_content:
        html_content = re.sub(r'<html([^>]*?)>', f'<html\\1 lang="{lang}" xml:lang="{lang}">', html_content, 1)

    # Self-close void elements for XHTML compliance
    void_elements = ['br', 'hr', 'img', 'input', 'meta', 'link', 'col', 'area', 'base', 'embed', 'source', 'track', 'wbr']
    for elem in void_elements:
        html_content = re.sub(
            rf'<({elem}\b[^/>]*?)(?<!/)\s*>',
            r'<\1/>',
            html_content
        )

    return html_content


def ensure_xhtml(filepath, lang="vi"):
    """Read a file and ensure it's valid XHTML5. Returns (xhtml_content, title)."""
    ext = Path(filepath).suffix.lower()

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = Path(filepath).stem
    # Clean filename for title
    title = re.sub(r'^\d+[_\-\s]*', '', filename).replace('_', ' ').replace('-', ' ').strip()
    if not title:
        title = filename

    if ext == '.xhtml':
        xhtml = html_to_xhtml(content, lang)  # also fixes entities
        extracted = extract_title_from_xhtml(xhtml)
        if extracted:
            title = extracted
        return xhtml, title

    elif ext == '.html':
        xhtml = html_to_xhtml(content, lang)  # also fixes entities
        extracted = extract_title_from_xhtml(xhtml)
        if extracted:
            title = extracted
        return xhtml, title

    elif ext == '.md':
        # Try to extract title from first heading
        md_title_match = re.match(r'^#\s+(.+)', content)
        if md_title_match:
            title = md_title_match.group(1).strip()
        return markdown_to_xhtml(content, title, lang), title

    elif ext == '.txt':
        # Try first line as title
        first_line = content.strip().split('\n')[0].strip()
        if len(first_line) < 100:
            title = first_line
        return text_to_xhtml(content, title, lang), title

    else:
        return text_to_xhtml(content, title, lang), title


# ============================================================================
# EPUB Components Generators
# ============================================================================

def generate_container_xml():
    """Generate META-INF/container.xml."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''


def generate_cover_xhtml(cover_image_path, title, lang="vi"):
    """Generate cover page XHTML."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">
<head>
  <title>Cover</title>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
</head>
<body>
  <section epub:type="cover" class="cover-page">
    <img src="../images/{cover_image_path}" alt="{html_escape(title)} — Cover"/>
  </section>
</body>
</html>'''


def generate_titlepage_xhtml(metadata, lang="vi"):
    """Generate title page XHTML."""
    title = html_escape(metadata.get('title', 'Untitled'))
    author = html_escape(metadata.get('author', ''))
    publisher = html_escape(metadata.get('publisher', ''))
    date = html_escape(metadata.get('date', ''))

    author_block = f'\n    <p class="author">{author}</p>' if author else ''
    publisher_block = f'\n    <p class="publisher">{publisher}</p>' if publisher else ''
    date_block = f'\n    <p class="date">{date}</p>' if date else ''

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">
<head>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
</head>
<body>
  <section epub:type="titlepage" class="title-page">
    <h1>{title}</h1>{author_block}{publisher_block}{date_block}
  </section>
</body>
</html>'''


def generate_opf(metadata, manifest_items, spine_items):
    """Generate content.opf (Package Document) — EPUB 3.3 compliant."""
    identifier = metadata.get('identifier', generate_uuid())
    title = html_escape(metadata.get('title', 'Untitled'))
    lang = metadata.get('language', 'vi')
    author = metadata.get('author', '')
    publisher = metadata.get('publisher', '')
    date = metadata.get('date', '')
    description = metadata.get('description', '')
    subject = metadata.get('subject', '')
    rights = metadata.get('rights', '')
    modified = metadata.get('modified', get_modified_time())

    # Build metadata section
    meta_lines = [
        f'    <dc:identifier id="BookId">{html_escape(identifier)}</dc:identifier>',
        f'    <dc:title>{title}</dc:title>',
        f'    <dc:language>{lang}</dc:language>',
    ]

    if author:
        meta_lines.append(f'    <dc:creator>{html_escape(author)}</dc:creator>')
    if publisher:
        meta_lines.append(f'    <dc:publisher>{html_escape(publisher)}</dc:publisher>')
    if date:
        meta_lines.append(f'    <dc:date>{html_escape(date)}</dc:date>')
    if description:
        meta_lines.append(f'    <dc:description>{html_escape(description)}</dc:description>')
    if subject:
        meta_lines.append(f'    <dc:subject>{html_escape(subject)}</dc:subject>')
    if rights:
        meta_lines.append(f'    <dc:rights>{html_escape(rights)}</dc:rights>')

    meta_lines.append(f'    <meta property="dcterms:modified">{modified}</meta>')

    # Accessibility metadata (EPUB 3.3)
    meta_lines.extend([
        '    <meta property="schema:accessMode">textual</meta>',
        '    <meta property="schema:accessModeSufficient">textual</meta>',
        '    <meta property="schema:accessibilityFeature">structuredNavigation</meta>',
        '    <meta property="schema:accessibilityFeature">readingOrder</meta>',
        '    <meta property="schema:accessibilityFeature">alternativeText</meta>',
        '    <meta property="schema:accessibilityHazard">none</meta>',
        '    <meta property="schema:accessibilitySummary">Structured text with table of contents navigation</meta>',
    ])

    metadata_xml = '\n'.join(meta_lines)

    # Build manifest
    manifest_lines = []
    for item in manifest_items:
        props = f' properties="{item["properties"]}"' if item.get("properties") else ''
        manifest_lines.append(
            f'    <item id="{item["id"]}" href="{item["href"]}" media-type="{item["media_type"]}"{props}/>'
        )
    manifest_xml = '\n'.join(manifest_lines)

    # Build spine
    spine_lines = []
    for item_id in spine_items:
        spine_lines.append(f'    <itemref idref="{item_id}"/>')
    spine_xml = '\n'.join(spine_lines)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <metadata>
{metadata_xml}
  </metadata>
  <manifest>
{manifest_xml}
  </manifest>
  <spine toc="ncx">
{spine_xml}
  </spine>
</package>'''


def generate_nav_xhtml(chapters, title="Mục Lục", lang="vi"):
    """Generate navigation document (toc.xhtml) — EPUB 3 required."""
    toc_items = []
    for ch in chapters:
        toc_items.append(f'      <li><a href="text/{ch["filename"]}">{html_escape(ch["title"])}</a></li>')
    toc_list = '\n'.join(toc_items)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">
<head>
  <title>{html_escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="styles/style.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc" role="doc-toc" aria-label="Table of Contents">
    <h1>{html_escape(title)}</h1>
    <ol>
{toc_list}
    </ol>
  </nav>
</body>
</html>'''


def generate_ncx(chapters, metadata):
    """Generate toc.ncx for EPUB 2 backward compatibility."""
    identifier = metadata.get('identifier', generate_uuid())
    title = html_escape(metadata.get('title', 'Untitled'))

    nav_points = []
    for i, ch in enumerate(chapters):
        nav_points.append(f'''    <navPoint id="navPoint-{i+1}" playOrder="{i+1}">
      <navLabel><text>{html_escape(ch["title"])}</text></navLabel>
      <content src="text/{ch["filename"]}"/>
    </navPoint>''')
    nav_xml = '\n'.join(nav_points)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{html_escape(identifier)}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{title}</text></docTitle>
  <navMap>
{nav_xml}
  </navMap>
</ncx>'''


# ============================================================================
# Main Build Function
# ============================================================================

def build_epub(input_dir, output_path, metadata_overrides=None):
    """
    Build an EPUB 3.3 file from an input directory.

    Args:
        input_dir: Path to input directory containing chapters/ and optional files
        output_path: Path for output .epub file
        metadata_overrides: Dict of metadata to override metadata.json
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    # ---- Load metadata ----
    metadata = {}
    meta_file = input_dir / 'metadata.json'
    if meta_file.exists():
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    if metadata_overrides:
        metadata.update(metadata_overrides)

    # Ensure required metadata
    if 'identifier' not in metadata:
        metadata['identifier'] = generate_uuid()
    if 'language' not in metadata:
        metadata['language'] = 'vi'
    if 'title' not in metadata:
        metadata['title'] = 'Untitled'
    metadata['modified'] = get_modified_time()

    lang = metadata['language']

    # ---- Find chapters ----
    chapters_dir = input_dir / 'chapters'
    if not chapters_dir.exists():
        # Try input_dir itself for chapter files
        chapters_dir = input_dir

    chapter_extensions = {'.xhtml', '.html', '.md', '.txt'}
    chapter_files = sorted([
        f for f in chapters_dir.iterdir()
        if f.is_file() and f.suffix.lower() in chapter_extensions
        and f.name not in ('metadata.json', 'style.css')
    ])

    if not chapter_files:
        print("ERROR: No chapter files found!")
        print(f"Looked in: {chapters_dir}")
        print(f"Supported formats: {', '.join(chapter_extensions)}")
        sys.exit(1)

    # ---- Process chapters ----
    chapters = []
    for i, filepath in enumerate(chapter_files):
        xhtml_content, title = ensure_xhtml(filepath, lang)
        filename = f"chapter{i+1:03d}.xhtml"
        chapters.append({
            'filename': filename,
            'title': title,
            'content': xhtml_content,
            'id': f'chapter{i+1:03d}',
        })

    print(f"Found {len(chapters)} chapters")

    # ---- Find cover image ----
    cover_image = None
    cover_image_name = None
    for ext in ['.jpg', '.jpeg', '.png']:
        cover_path = input_dir / f'cover{ext}'
        if cover_path.exists():
            cover_image = cover_path
            cover_image_name = cover_path.name
            break

    # ---- Find content images ----
    images_dir = input_dir / 'images'
    content_images = []
    if images_dir.exists():
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.svg'}
        content_images = [f for f in images_dir.iterdir()
                         if f.is_file() and f.suffix.lower() in image_extensions
                         and f.name != cover_image_name]

    # ---- Load or use default CSS ----
    custom_css = input_dir / 'style.css'
    if custom_css.exists():
        with open(custom_css, 'r', encoding='utf-8') as f:
            css_content = f.read()
    else:
        css_content = DEFAULT_CSS

    # ---- Find fonts ----
    fonts_dir = input_dir / 'fonts'
    font_files = []
    if fonts_dir.exists():
        font_extensions = {'.ttf', '.otf', '.woff', '.woff2'}
        font_files = [f for f in fonts_dir.iterdir() if f.suffix.lower() in font_extensions]

    # ---- Build manifest items ----
    manifest_items = []
    spine_items = []

    # Navigation document
    manifest_items.append({
        'id': 'nav',
        'href': 'toc.xhtml',
        'media_type': 'application/xhtml+xml',
        'properties': 'nav',
    })

    # NCX
    manifest_items.append({
        'id': 'ncx',
        'href': 'toc.ncx',
        'media_type': 'application/x-dtbncx+xml',
        'properties': None,
    })

    # CSS
    manifest_items.append({
        'id': 'style-css',
        'href': 'styles/style.css',
        'media_type': 'text/css',
        'properties': None,
    })

    # Cover image
    if cover_image:
        ext = cover_image.suffix.lower()
        manifest_items.append({
            'id': 'cover-image',
            'href': f'images/{cover_image_name}',
            'media_type': MEDIA_TYPES.get(ext, 'image/jpeg'),
            'properties': 'cover-image',
        })

        # Cover XHTML page
        manifest_items.append({
            'id': 'cover-page',
            'href': 'text/cover.xhtml',
            'media_type': 'application/xhtml+xml',
            'properties': None,
        })
        spine_items.append('cover-page')

    # Title page
    manifest_items.append({
        'id': 'titlepage',
        'href': 'text/titlepage.xhtml',
        'media_type': 'application/xhtml+xml',
        'properties': None,
    })
    spine_items.append('titlepage')

    # Chapters
    for ch in chapters:
        manifest_items.append({
            'id': ch['id'],
            'href': f'text/{ch["filename"]}',
            'media_type': 'application/xhtml+xml',
            'properties': None,
        })
        spine_items.append(ch['id'])

    # Fonts
    for font_file in font_files:
        font_id = sanitize_id(font_file.stem)
        ext = font_file.suffix.lower()
        manifest_items.append({
            'id': f'font-{font_id}',
            'href': f'fonts/{font_file.name}',
            'media_type': MEDIA_TYPES.get(ext, 'application/octet-stream'),
            'properties': None,
        })

    # Content images
    for img_file in content_images:
        img_id = sanitize_id(f'img-{img_file.stem}')
        ext = img_file.suffix.lower()
        manifest_items.append({
            'id': img_id,
            'href': f'images/{img_file.name}',
            'media_type': MEDIA_TYPES.get(ext, 'image/jpeg'),
            'properties': None,
        })

    # ---- Write EPUB ----
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(str(output_path), 'w') as epub:
        # 1. mimetype MUST be first, uncompressed
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/container.xml
        epub.writestr('META-INF/container.xml', generate_container_xml(),
                      compress_type=zipfile.ZIP_DEFLATED)

        # 3. content.opf
        epub.writestr('OEBPS/content.opf',
                      generate_opf(metadata, manifest_items, spine_items),
                      compress_type=zipfile.ZIP_DEFLATED)

        # 4. toc.xhtml (Navigation Document)
        epub.writestr('OEBPS/toc.xhtml',
                      generate_nav_xhtml(chapters, lang=lang),
                      compress_type=zipfile.ZIP_DEFLATED)

        # 5. toc.ncx (backward compat)
        epub.writestr('OEBPS/toc.ncx',
                      generate_ncx(chapters, metadata),
                      compress_type=zipfile.ZIP_DEFLATED)

        # 6. CSS
        epub.writestr('OEBPS/styles/style.css', css_content,
                      compress_type=zipfile.ZIP_DEFLATED)

        # 7. Cover page
        if cover_image:
            epub.writestr('OEBPS/text/cover.xhtml',
                         generate_cover_xhtml(cover_image_name, metadata['title'], lang),
                         compress_type=zipfile.ZIP_DEFLATED)
            epub.write(str(cover_image), f'OEBPS/images/{cover_image_name}',
                      compress_type=zipfile.ZIP_DEFLATED)

        # 8. Title page
        epub.writestr('OEBPS/text/titlepage.xhtml',
                      generate_titlepage_xhtml(metadata, lang),
                      compress_type=zipfile.ZIP_DEFLATED)

        # 9. Chapters
        for ch in chapters:
            epub.writestr(f'OEBPS/text/{ch["filename"]}', ch['content'],
                         compress_type=zipfile.ZIP_DEFLATED)

        # 10. Fonts
        for font_file in font_files:
            epub.write(str(font_file), f'OEBPS/fonts/{font_file.name}',
                      compress_type=zipfile.ZIP_DEFLATED)

        # 11. Content images
        for img_file in content_images:
            epub.write(str(img_file), f'OEBPS/images/{img_file.name}',
                      compress_type=zipfile.ZIP_DEFLATED)

    file_size = output_path.stat().st_size
    print(f"EPUB created successfully: {output_path}")
    print(f"File size: {file_size:,} bytes")
    print(f"Chapters: {len(chapters)}")
    print(f"Cover: {'Yes' if cover_image else 'No'}")
    print(f"Images: {len(content_images)}")
    print(f"Fonts: {len(font_files)}")

    return str(output_path)


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Build EPUB 3.3 from content directory')
    parser.add_argument('--input', '-i', required=True, help='Input directory with chapters/')
    parser.add_argument('--output', '-o', required=True, help='Output .epub file path')
    parser.add_argument('--title', '-t', help='Book title')
    parser.add_argument('--author', '-a', help='Author name')
    parser.add_argument('--language', '-l', default='vi', help='Language code (default: vi)')
    parser.add_argument('--identifier', help='Book identifier (ISBN or UUID)')
    parser.add_argument('--publisher', help='Publisher name')
    parser.add_argument('--description', help='Book description')
    parser.add_argument('--subject', help='Subject/category')
    parser.add_argument('--rights', help='Copyright statement')
    parser.add_argument('--date', help='Publication date')

    args = parser.parse_args()

    overrides = {}
    if args.title:
        overrides['title'] = args.title
    if args.author:
        overrides['author'] = args.author
    if args.language:
        overrides['language'] = args.language
    if args.identifier:
        overrides['identifier'] = args.identifier
    if args.publisher:
        overrides['publisher'] = args.publisher
    if args.description:
        overrides['description'] = args.description
    if args.subject:
        overrides['subject'] = args.subject
    if args.rights:
        overrides['rights'] = args.rights
    if args.date:
        overrides['date'] = args.date

    build_epub(args.input, args.output, overrides)


if __name__ == '__main__':
    main()
