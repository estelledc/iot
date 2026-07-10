#!/usr/bin/env python3
"""Validate structural contracts in a built MkDocs HTML page."""

from __future__ import annotations

import argparse
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
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.counts[tag] = self.counts.get(tag, 0) + 1
        if tag == "a":
            self.links.append({key: value or "" for key, value in attrs})

    def handle_data(self, data: str) -> None:
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
