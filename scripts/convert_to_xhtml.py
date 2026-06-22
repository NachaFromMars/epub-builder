#!/usr/bin/env python3
"""
Convert text, Markdown, or HTML files to EPUB-ready XHTML5.

Usage:
    python3 convert_to_xhtml.py input.txt -o output.xhtml
    python3 convert_to_xhtml.py input.md -o output.xhtml --lang vi
    python3 convert_to_xhtml.py input.html -o output.xhtml
"""

import argparse
import sys
from pathlib import Path

# Import from build_epub
sys.path.insert(0, str(Path(__file__).parent))
from build_epub import ensure_xhtml, text_to_xhtml, markdown_to_xhtml, html_to_xhtml


def main():
    parser = argparse.ArgumentParser(description='Convert files to EPUB-ready XHTML5')
    parser.add_argument('input', help='Input file (.txt, .md, .html)')
    parser.add_argument('-o', '--output', help='Output .xhtml file (default: input_name.xhtml)')
    parser.add_argument('--lang', default='vi', help='Language code (default: vi)')
    parser.add_argument('--title', help='Chapter/section title')

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    output_path = args.output or input_path.with_suffix('.xhtml')

    xhtml_content, detected_title = ensure_xhtml(str(input_path), args.lang)

    if args.title:
        # Replace detected title in content
        xhtml_content = xhtml_content.replace(
            f'<title>{detected_title}</title>',
            f'<title>{args.title}</title>'
        )
        xhtml_content = xhtml_content.replace(
            f'aria-label="{detected_title}"',
            f'aria-label="{args.title}"'
        )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xhtml_content)

    print(f"Converted: {input_path} → {output_path}")
    print(f"Title: {args.title or detected_title}")
    print(f"Language: {args.lang}")


if __name__ == '__main__':
    main()
