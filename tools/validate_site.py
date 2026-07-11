#!/usr/bin/env python3
"""Validate structural contracts in a built MkDocs HTML page."""

from __future__ import annotations

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]


class PageFacts(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.counts: dict[str, int] = {}
        self.links: list[dict[str, str]] = []
        self.meta_tags: list[dict[str, str]] = []
        self.canonical_links: list[str] = []
        self.json_ld_documents: list[str] = []
        self.text_parts: list[str] = []
        self._json_ld_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.counts[tag] = self.counts.get(tag, 0) + 1
        data = {key: value or "" for key, value in attrs}
        if tag == "a":
            self.links.append(data)
        elif tag == "meta":
            self.meta_tags.append(data)
        elif tag == "link" and "canonical" in data.get("rel", "").split():
            self.canonical_links.append(data.get("href", ""))
        elif tag == "script" and data.get("type") == "application/ld+json":
            self._json_ld_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_ld_parts is not None:
            self.json_ld_documents.append("".join(self._json_ld_parts).strip())
            self._json_ld_parts = None

    def handle_data(self, data: str) -> None:
        if self._json_ld_parts is not None:
            self._json_ld_parts.append(data)
        if data.strip():
            self.text_parts.append(data.strip())

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def validate_page(
    page: Path,
    *,
    single_main: bool = False,
    single_footer: bool = False,
    single_h1: bool = False,
    expected_text: list[str] | None = None,
    expected_links: list[str] | None = None,
    expected_canonical: str | None = None,
    expected_meta: list[str] | None = None,
    expected_json_ld_types: list[str] | None = None,
    expected_robots: str | None = None,
    forbid_json_ld: bool = False,
    external_link_rel: bool = False,
) -> list[str]:
    if not page.is_file():
        return [f"built page does not exist: {page}"]
    parser = PageFacts()
    parser.feed(page.read_text(encoding="utf-8"))
    errors: list[str] = []

    for enabled, tag in ((single_main, "main"), (single_footer, "footer"), (single_h1, "h1")):
        if enabled and parser.counts.get(tag, 0) != 1:
            errors.append(f"expected exactly one <{tag}>, found {parser.counts.get(tag, 0)}")

    for text in expected_text or []:
        if text not in parser.text:
            errors.append(f"missing rendered text: {text}")

    hrefs = {link.get("href", "") for link in parser.links}
    for href in expected_links or []:
        if href not in hrefs:
            errors.append(f"missing rendered link: {href}")

    if expected_canonical and expected_canonical not in parser.canonical_links:
        errors.append(f"missing canonical link: {expected_canonical}")

    for key in expected_meta or []:
        match = next(
            (
                meta
                for meta in parser.meta_tags
                if (meta.get("name") == key or meta.get("property") == key)
                and bool(meta.get("content"))
            ),
            None,
        )
        if match is None:
            errors.append(f"missing metadata with non-empty content: {key}")

    json_ld_types: set[str] = set()

    def collect_types(value: object) -> None:
        if isinstance(value, dict):
            schema_type = value.get("@type")
            if isinstance(schema_type, str):
                json_ld_types.add(schema_type)
            elif isinstance(schema_type, list):
                json_ld_types.update(item for item in schema_type if isinstance(item, str))
            for nested in value.values():
                collect_types(nested)
        elif isinstance(value, list):
            for nested in value:
                collect_types(nested)

    for document in parser.json_ld_documents:
        try:
            payload = json.loads(document)
        except json.JSONDecodeError:
            errors.append("invalid application/ld+json document")
            continue
        collect_types(payload)
    for expected_type in expected_json_ld_types or []:
        if expected_type not in json_ld_types:
            errors.append(f"missing JSON-LD @type: {expected_type}")
    if expected_robots:
        robots = next((meta.get("content") for meta in parser.meta_tags if meta.get("name") == "robots"), None)
        if robots != expected_robots:
            errors.append(f"robots metadata mismatch: expected {expected_robots!r}, found {robots!r}")
    if forbid_json_ld and parser.json_ld_documents:
        errors.append(f"expected no JSON-LD documents, found {len(parser.json_ld_documents)}")

    if external_link_rel:
        for link in parser.links:
            href = link.get("href", "")
            if link.get("target") != "_blank":
                continue
            parsed = urlsplit(href)
            if parsed.scheme not in {"http", "https"}:
                continue
            rel = set(link.get("rel", "").split())
            if not {"noopener", "noreferrer"}.issubset(rel):
                errors.append(f"target=_blank link lacks noopener noreferrer: {href}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", required=True)
    parser.add_argument("--page", default="index.html")
    parser.add_argument("--assert-single-main", action="store_true")
    parser.add_argument("--assert-single-footer", action="store_true")
    parser.add_argument("--assert-single-h1", action="store_true")
    parser.add_argument("--assert-text", action="append", default=[])
    parser.add_argument("--assert-link", action="append", default=[])
    parser.add_argument("--assert-canonical")
    parser.add_argument("--assert-meta", action="append", default=[])
    parser.add_argument("--assert-json-ld-type", action="append", default=[])
    parser.add_argument("--assert-robots")
    parser.add_argument("--forbid-json-ld", action="store_true")
    parser.add_argument("--external-link-rel", action="store_true")
    args = parser.parse_args(argv)

    page = (ROOT / args.site_dir / args.page).resolve()
    errors = validate_page(
        page,
        single_main=args.assert_single_main,
        single_footer=args.assert_single_footer,
        single_h1=args.assert_single_h1,
        expected_text=args.assert_text,
        expected_links=args.assert_link,
        expected_canonical=args.assert_canonical,
        expected_meta=args.assert_meta,
        expected_json_ld_types=args.assert_json_ld_type,
        expected_robots=args.assert_robots,
        forbid_json_ld=args.forbid_json_ld,
        external_link_rel=args.external_link_rel,
    )
    if errors:
        print("SITE_VALIDATION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"SITE_VALIDATION_OK page={page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
