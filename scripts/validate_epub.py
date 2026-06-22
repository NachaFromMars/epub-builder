#!/usr/bin/env python3
"""
EPUB 3.3 Validator — Checks structural compliance without EPUBCheck.
Validates: mimetype, container.xml, OPF, navigation, XHTML, and metadata.

Usage:
    python3 validate_epub.py book.epub
"""

import json
import sys
import zipfile
from pathlib import Path

try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


class EPUBValidator:
    def __init__(self, epub_path):
        self.epub_path = Path(epub_path)
        self.errors = []
        self.warnings = []
        self.info = []

    def error(self, msg):
        self.errors.append(f"ERROR: {msg}")

    def warn(self, msg):
        self.warnings.append(f"WARNING: {msg}")

    def ok(self, msg):
        self.info.append(f"OK: {msg}")

    def validate(self):
        """Run all validation checks."""
        print(f"Validating: {self.epub_path}")
        print("=" * 60)

        if not self.epub_path.exists():
            self.error(f"File not found: {self.epub_path}")
            return self._report()

        if not zipfile.is_zipfile(str(self.epub_path)):
            self.error("Not a valid ZIP archive")
            return self._report()

        with zipfile.ZipFile(str(self.epub_path), 'r') as zf:
            self._check_mimetype(zf)
            self._check_container(zf)
            opf_path = self._find_opf(zf)
            if opf_path:
                self._check_opf(zf, opf_path)
            self._check_nav(zf)
            self._check_xhtml_files(zf)
            self._check_entities(zf)
            self._check_file_references(zf, opf_path)

        return self._report()

    def _check_mimetype(self, zf):
        """Check mimetype is first entry, uncompressed, and correct."""
        names = zf.namelist()

        if not names:
            self.error("EPUB is empty")
            return

        if names[0] != 'mimetype':
            self.error(f"'mimetype' must be the first file in ZIP (found: '{names[0]}')")
        elif 'mimetype' in names:
            info = zf.getinfo('mimetype')
            if info.compress_type != zipfile.ZIP_STORED:
                self.error("'mimetype' must be stored without compression (ZIP_STORED)")
            content = zf.read('mimetype').decode('ascii', errors='replace').strip()
            if content != 'application/epub+zip':
                self.error(f"mimetype content should be 'application/epub+zip', got: '{content}'")
            else:
                self.ok("mimetype is correct and uncompressed")
        else:
            self.error("'mimetype' file is missing")

    def _check_container(self, zf):
        """Check META-INF/container.xml exists and is valid."""
        if 'META-INF/container.xml' not in zf.namelist():
            self.error("META-INF/container.xml is missing")
            return

        content = zf.read('META-INF/container.xml')
        if HAS_LXML:
            try:
                tree = etree.fromstring(content)
                rootfiles = tree.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
                if not rootfiles:
                    self.error("container.xml has no <rootfile> element")
                else:
                    self.ok(f"container.xml valid, points to {rootfiles[0].get('full-path')}")
            except etree.XMLSyntaxError as e:
                self.error(f"container.xml XML parse error: {e}")
        else:
            if b'rootfile' in content:
                self.ok("container.xml present (install lxml for deeper validation)")
            else:
                self.error("container.xml missing <rootfile> element")

    def _find_opf(self, zf):
        """Find the OPF file path from container.xml."""
        if 'META-INF/container.xml' not in zf.namelist():
            return None

        content = zf.read('META-INF/container.xml')
        if HAS_LXML:
            tree = etree.fromstring(content)
            rootfiles = tree.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
            if rootfiles:
                return rootfiles[0].get('full-path')
        else:
            import re
            match = re.search(rb'full-path="([^"]+)"', content)
            if match:
                return match.group(1).decode('utf-8')
        return None

    def _check_opf(self, zf, opf_path):
        """Check Package Document (content.opf) for EPUB 3.3 compliance."""
        if opf_path not in zf.namelist():
            self.error(f"OPF file not found: {opf_path}")
            return

        content = zf.read(opf_path)

        if HAS_LXML:
            try:
                tree = etree.fromstring(content)
            except etree.XMLSyntaxError as e:
                self.error(f"OPF XML parse error: {e}")
                return

            ns = {'opf': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}

            # Check version
            version = tree.get('version')
            if version and version.startswith('3'):
                self.ok(f"EPUB version: {version}")
            else:
                self.warn(f"Expected EPUB 3.x, found version: {version}")

            # Check required metadata
            metadata = tree.find('opf:metadata', ns)
            if metadata is None:
                self.error("No <metadata> element in OPF")
                return

            # dc:identifier
            ident = metadata.find('dc:identifier', ns)
            if ident is not None and ident.text:
                self.ok(f"dc:identifier: {ident.text[:50]}")
            else:
                self.error("Missing required dc:identifier")

            # dc:title
            title = metadata.find('dc:title', ns)
            if title is not None and title.text:
                self.ok(f"dc:title: {title.text}")
            else:
                self.error("Missing required dc:title")

            # dc:language
            lang = metadata.find('dc:language', ns)
            if lang is not None and lang.text:
                self.ok(f"dc:language: {lang.text}")
            else:
                self.error("Missing required dc:language")

            # dcterms:modified
            modified_found = False
            for meta in metadata.findall('opf:meta', ns):
                if meta.get('property') == 'dcterms:modified':
                    modified_found = True
                    self.ok(f"dcterms:modified: {meta.text}")
                    break
            if not modified_found:
                self.error("Missing required meta property='dcterms:modified'")

            # Accessibility metadata check
            access_props = set()
            for meta in metadata.findall('opf:meta', ns):
                prop = meta.get('property', '')
                if prop.startswith('schema:access'):
                    access_props.add(prop)

            if access_props:
                self.ok(f"Accessibility metadata found: {len(access_props)} properties")
            else:
                self.warn("No accessibility metadata (recommended for EPUB 3.3)")

            # Check manifest
            manifest = tree.find('opf:manifest', ns)
            if manifest is None:
                self.error("No <manifest> element")
            else:
                items = manifest.findall('opf:item', ns)
                self.ok(f"Manifest: {len(items)} items")

                # Check for nav document
                nav_found = False
                for item in items:
                    props = item.get('properties', '')
                    if 'nav' in props:
                        nav_found = True
                        break
                if nav_found:
                    self.ok("Navigation document declared in manifest")
                else:
                    self.error("No navigation document (properties='nav') in manifest")

            # Check spine
            spine = tree.find('opf:spine', ns)
            if spine is None:
                self.error("No <spine> element")
            else:
                itemrefs = spine.findall('opf:itemref', ns)
                self.ok(f"Spine: {len(itemrefs)} items in reading order")

        else:
            # Basic checks without lxml
            content_str = content.decode('utf-8', errors='replace')
            checks = {
                'dc:identifier': b'dc:identifier' in content,
                'dc:title': b'dc:title' in content,
                'dc:language': b'dc:language' in content,
                'dcterms:modified': b'dcterms:modified' in content,
                'manifest': b'<manifest' in content,
                'spine': b'<spine' in content,
            }
            for check, passed in checks.items():
                if passed:
                    self.ok(f"{check} present")
                else:
                    self.error(f"{check} missing from OPF")

    def _check_nav(self, zf):
        """Check for navigation document."""
        nav_files = [n for n in zf.namelist() if n.endswith('toc.xhtml') or n.endswith('nav.xhtml')]
        if nav_files:
            content = zf.read(nav_files[0])
            if b'epub:type="toc"' in content:
                self.ok(f"Navigation document found: {nav_files[0]}")
                # Verify toc hrefs point to existing files
                import re
                nav_dir = str(Path(nav_files[0]).parent)
                content_str = content.decode('utf-8', errors='replace')
                hrefs = re.findall(r'href="([^"]+)"', content_str)
                all_names = zf.namelist()
                for href in hrefs:
                    if href.startswith('#') or href.startswith('http'):
                        continue
                    # Resolve relative to nav file location
                    if nav_dir and nav_dir != '.':
                        full = f"{nav_dir}/{href}"
                    else:
                        full = href
                    # Strip fragment
                    full = full.split('#')[0]
                    if full not in all_names:
                        self.error(f"TOC href points to missing file: {href} (resolved: {full})")
            else:
                self.warn(f"Navigation file found ({nav_files[0]}) but missing epub:type='toc'")
        else:
            self.error("No navigation document (toc.xhtml) found")

        # Check NCX for backward compat
        ncx_files = [n for n in zf.namelist() if n.endswith('.ncx')]
        if ncx_files:
            self.ok(f"NCX backward compatibility: {ncx_files[0]}")
        else:
            self.warn("No NCX file for EPUB 2 reader backward compatibility")

    def _check_xhtml_files(self, zf):
        """Check XHTML files for basic validity."""
        xhtml_files = [n for n in zf.namelist() if n.endswith('.xhtml')]
        valid = 0
        invalid = 0

        for xf in xhtml_files:
            content = zf.read(xf)
            if HAS_LXML:
                try:
                    etree.fromstring(content)
                    valid += 1
                except etree.XMLSyntaxError as e:
                    self.error(f"Invalid XHTML in {xf}: {e}")
                    invalid += 1
            else:
                if b'<html' in content and b'xmlns="http://www.w3.org/1999/xhtml"' in content:
                    valid += 1
                else:
                    self.warn(f"XHTML in {xf} may not have proper namespace")
                    invalid += 1

        self.ok(f"XHTML files: {valid} valid, {invalid} issues out of {len(xhtml_files)} total")

    def _check_entities(self, zf):
        """Check XHTML files for illegal HTML entities (only &amp; &lt; &gt; &quot; &apos; allowed)."""
        import re
        LEGAL_ENTITIES = {'amp', 'lt', 'gt', 'quot', 'apos'}
        xhtml_files = [n for n in zf.namelist() if n.endswith('.xhtml')]
        total_illegal = 0

        for xf in xhtml_files:
            content = zf.read(xf).decode('utf-8', errors='replace')
            # Find all named entities &word;
            entities = re.findall(r'&([a-zA-Z]+);', content)
            illegal = [e for e in entities if e not in LEGAL_ENTITIES]
            if illegal:
                unique = sorted(set(illegal))
                total_illegal += len(illegal)
                self.error(f"Illegal entities in {xf}: {', '.join('&'+e+';' for e in unique[:10])} ({len(illegal)} total)")

        if total_illegal == 0:
            self.ok("No illegal HTML entities found in XHTML files")

    def _check_file_references(self, zf, opf_path):
        """Check that all files in manifest actually exist in ZIP."""
        if not opf_path or not HAS_LXML:
            return

        content = zf.read(opf_path)
        try:
            tree = etree.fromstring(content)
        except:
            return

        ns = {'opf': 'http://www.idpf.org/2007/opf'}
        manifest = tree.find('opf:manifest', ns)
        if manifest is None:
            return

        opf_dir = str(Path(opf_path).parent)
        if opf_dir == '.':
            opf_dir = ''

        missing = []
        for item in manifest.findall('opf:item', ns):
            href = item.get('href', '')
            if opf_dir:
                full_path = f"{opf_dir}/{href}"
            else:
                full_path = href

            if full_path not in zf.namelist():
                missing.append(full_path)

        if missing:
            for m in missing:
                self.error(f"Manifest references missing file: {m}")
        else:
            self.ok("All manifest files present in archive")

    def _report(self):
        """Print validation report."""
        print()
        for msg in self.info:
            print(f"  ✓ {msg}")
        for msg in self.warnings:
            print(f"  ⚠ {msg}")
        for msg in self.errors:
            print(f"  ✗ {msg}")

        print()
        print(f"Results: {len(self.info)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors")

        if not self.errors:
            print("✓ EPUB validation PASSED")
            return True
        else:
            print("✗ EPUB validation FAILED")
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_epub.py <file.epub>")
        sys.exit(1)

    validator = EPUBValidator(sys.argv[1])
    passed = validator.validate()
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
