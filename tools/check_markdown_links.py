#!/usr/bin/env python3
"""Validate repository-relative Markdown links and optional heading anchors."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
EXCLUDED_PARTS = {".git", ".venv", ".tmp", "site"}
FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})")
LINK_RE = re.compile(r"!?\[[^\]]*\]\((?P<target>[^)]+)\)")
HEADING_RE = re.compile(r"^\s*#{1,6}\s+(?P<title>.+?)\s*#*\s*$")


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
    )


def _strip_fenced_lines(text: str) -> list[tuple[int, str]]:
    visible: list[tuple[int, str]] = []
    opened: tuple[str, int] | None = None
    for line_number, line in enumerate(text.splitlines(), 1):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group("fence")
            if opened is None:
                opened = (marker[0], len(marker))
            elif marker[0] == opened[0] and len(marker) >= opened[1]:
                opened = None
            continue
        if opened is None:
            visible.append((line_number, line))
    return visible


def _slugify(title: str) -> str:
    title = re.sub(r"<[^>]+>", "", title)
    title = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", title)
    title = unicodedata.normalize("NFKC", title).strip().lower()
    title = re.sub(r"[^\w\-\s\u3400-\u9fff]", "", title, flags=re.UNICODE)
    title = re.sub(r"[\s\-]+", "-", title).strip("-")
    return title


def _anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for _, line in _strip_fenced_lines(path.read_text(encoding="utf-8")):
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = _slugify(match.group("title"))
        if not base:
            continue
        index = counts.get(base, 0)
        counts[base] = index + 1
        anchors.add(base if index == 0 else f"{base}_{index}")
    return anchors


def _target_path(source: Path, raw_path: str) -> Path | None:
    decoded = unquote(raw_path).strip()
    if not decoded:
        return source
    if decoded.startswith("/iot/"):
        candidate = DOCS_ROOT / decoded.removeprefix("/iot/")
    elif decoded.startswith("/"):
        candidate = DOCS_ROOT / decoded.lstrip("/")
    else:
        candidate = source.parent / decoded

    candidate = candidate.resolve()
    root = ROOT.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None

    options = [candidate]
    if candidate.suffix == ".html":
        options.extend((candidate.with_suffix(".md"), candidate.with_suffix("") / "index.md"))
    elif not candidate.suffix:
        options.extend((candidate.with_suffix(".md"), candidate / "index.md"))
    elif candidate.is_dir():
        options.append(candidate / "index.md")

    for option in options:
        if option.is_dir() and (option / "index.md").is_file():
            return option / "index.md"
        if option.is_file():
            return option
    return candidate


def _clean_target(value: str) -> str:
    value = value.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    # Remove an optional Markdown link title after a whitespace separator.
    return re.split(r"\s+[\"']", value, maxsplit=1)[0]


def check_file(path: Path, check_anchors: bool) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    text = path.read_text(encoding="utf-8")
    for line_number, line in _strip_fenced_lines(text):
        for match in LINK_RE.finditer(line):
            raw_target = _clean_target(match.group("target"))
            if not raw_target or raw_target.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            if raw_target.startswith("{{"):
                continue
            parsed = urlsplit(raw_target)
            if parsed.scheme or parsed.netloc:
                continue
            target = _target_path(path, parsed.path)
            if target is None:
                errors.append(f"{path.relative_to(ROOT)}:{line_number}: unsafe link target: {raw_target}")
                continue
            if not target.is_file():
                try:
                    display = target.relative_to(ROOT)
                except ValueError:
                    display = target
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: missing link target: {raw_target} -> {display}"
                )
                continue
            if check_anchors and parsed.fragment and target.suffix.lower() == ".md":
                expected = unquote(parsed.fragment).lower()
                available = anchor_cache.setdefault(target, _anchors(target))
                if expected not in available:
                    errors.append(
                        f"{path.relative_to(ROOT)}:{line_number}: missing anchor #{parsed.fragment} "
                        f"in {target.relative_to(ROOT)}"
                    )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="check all repository Markdown files")
    parser.add_argument("--file", action="append", default=[], help="check one repository-relative file")
    parser.add_argument("--anchors", action="store_true", help="also verify Markdown heading anchors")
    parser.add_argument("--strict", action="store_true", help="reserved for CI; all current findings are errors")
    args = parser.parse_args(argv)
    if not args.all and not args.file:
        parser.error("use --all or --file")

    paths = markdown_files() if args.all else [ROOT / item for item in args.file]
    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: file not found")
            continue
        errors.extend(check_file(path, args.anchors))

    if errors:
        print("MARKDOWN_LINKS_INVALID", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"MARKDOWN_LINKS_OK files={len(paths)} anchors={str(args.anchors).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
