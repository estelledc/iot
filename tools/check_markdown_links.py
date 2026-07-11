#!/usr/bin/env python3
"""Validate repository-relative Markdown links and optional heading anchors."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown.inlinepatterns import BACKTICK_RE


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
EXCLUDED_PARTS = {".git", ".venv", ".tmp", "site"}
FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\((?P<target>[^)]+)\)")
REFERENCE_LINK_RE = re.compile(
    r"!?\[(?P<label>[^\]]+)\]\[(?P<reference>[^\]]*)\]"
)
SHORTCUT_REFERENCE_RE = re.compile(r"(?<!\\)!?\[(?P<label>[^\[\]\n]+)\]")
REFERENCE_DEFINITION_RE = re.compile(
    r"^\s{0,3}\[(?P<label>[^\]]+)\]:\s*(?P<target><[^>]*>|\S+)(?:\s+.*)?$"
)
HEADING_RE = re.compile(r"^\s*#{1,6}\s+(?P<title>.+?)\s*#*\s*$")
INLINE_CODE_RE = re.compile(BACKTICK_RE, re.DOTALL)


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
            info = match.group("info").strip()
            if opened is None:
                opened = (marker[0], len(marker))
            elif (
                marker[0] == opened[0]
                and len(marker) >= opened[1]
                and not info
            ):
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


def _candidate_path(source: Path, raw_path: str) -> Path:
    decoded = unquote(raw_path).strip()
    if not decoded:
        return source.resolve()
    if decoded.startswith("/iot/"):
        candidate = DOCS_ROOT / decoded.removeprefix("/iot/")
    elif decoded.startswith("/"):
        candidate = DOCS_ROOT / decoded.lstrip("/")
    else:
        candidate = source.parent / decoded
    return candidate.resolve()


def _target_path(source: Path, raw_path: str) -> Path | None:
    candidate = _candidate_path(source, raw_path)

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


def _reference_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def _mask_inline_code_text(text: str) -> str:
    """Mask code spans with the same regex used by Python-Markdown/MkDocs."""

    masked = list(text)
    for match in INLINE_CODE_RE.finditer(text):
        if match.group(3) is None:
            continue
        start, end = match.span()
        for index in range(start, end):
            if masked[index] not in "\r\n":
                masked[index] = " "
    return "".join(masked)


def _mask_inline_code_lines(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    masked_lines: list[tuple[int, str]] = []
    segment: list[tuple[int, str]] = []

    def flush() -> None:
        if not segment:
            return
        masked = _mask_inline_code_text("\n".join(line for _number, line in segment))
        parts = masked.split("\n")
        masked_lines.extend(
            (line_number, part)
            for (line_number, _line), part in zip(segment, parts, strict=True)
        )
        segment.clear()

    previous_line = 0
    for line_number, line in lines:
        if segment and (line_number != previous_line + 1 or not line.strip()):
            flush()
        if not line.strip():
            masked_lines.append((line_number, line))
        else:
            segment.append((line_number, line))
        previous_line = line_number
    flush()
    return masked_lines


def _is_lexically_within(path: Path, directory: Path) -> bool:
    try:
        path.absolute().relative_to(directory.absolute())
    except ValueError:
        return False
    return True


def check_file(
    path: Path,
    check_anchors: bool,
    *,
    published: bool = False,
) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    text = path.read_text(encoding="utf-8")
    visible_lines = _strip_fenced_lines(text)
    scannable_lines = _mask_inline_code_lines(visible_lines)
    definitions: dict[str, str] = {}
    for _line_number, line in scannable_lines:
        match = REFERENCE_DEFINITION_RE.match(line)
        if match:
            definitions.setdefault(
                _reference_label(match.group("label")),
                _clean_target(match.group("target")),
            )

    def validate_target(raw_target: str, line_number: int) -> None:
        if not raw_target or raw_target.startswith(
            ("http://", "https://", "mailto:", "tel:", "data:")
        ):
            return
        if raw_target.startswith("{{"):
            return
        parsed = urlsplit(raw_target)
        if parsed.scheme or parsed.netloc:
            return
        candidate = _candidate_path(path, parsed.path)
        if published and _is_lexically_within(path, DOCS_ROOT):
            docs_root = DOCS_ROOT.resolve()
            try:
                candidate.relative_to(docs_root)
            except ValueError:
                try:
                    display = candidate.relative_to(ROOT.resolve())
                except ValueError:
                    display = "<outside repository>"
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    f"published link target outside docs_dir: {raw_target} -> {display}"
                )
                return
        target = _target_path(path, parsed.path)
        if target is None:
            errors.append(
                f"{path.relative_to(ROOT)}:{line_number}: unsafe link target: {raw_target}"
            )
            return
        if not target.is_file():
            try:
                display = target.relative_to(ROOT)
            except ValueError:
                display = target
            errors.append(
                f"{path.relative_to(ROOT)}:{line_number}: "
                f"missing link target: {raw_target} -> {display}"
            )
            return
        if check_anchors and parsed.fragment and target.suffix.lower() == ".md":
            expected = unquote(parsed.fragment).lower()
            available = anchor_cache.setdefault(target, _anchors(target))
            if expected not in available:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: missing anchor #{parsed.fragment} "
                    f"in {target.relative_to(ROOT)}"
                )

    for line_number, line in scannable_lines:
        inline_matches = list(LINK_RE.finditer(line))
        reference_matches = list(REFERENCE_LINK_RE.finditer(line))
        for match in inline_matches:
            validate_target(_clean_target(match.group("target")), line_number)
        for match in reference_matches:
            reference = match.group("reference") or match.group("label")
            target = definitions.get(_reference_label(reference))
            if target is not None:
                validate_target(target, line_number)
        if REFERENCE_DEFINITION_RE.match(line):
            continue
        covered = [match.span() for match in inline_matches + reference_matches]
        for match in SHORTCUT_REFERENCE_RE.finditer(line):
            start, end = match.span()
            if any(start < covered_end and end > covered_start for covered_start, covered_end in covered):
                continue
            target = definitions.get(_reference_label(match.group("label")))
            if target is not None:
                validate_target(target, line_number)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="check all repository Markdown files")
    parser.add_argument("--file", action="append", default=[], help="check one repository-relative file")
    parser.add_argument("--anchors", action="store_true", help="also verify Markdown heading anchors")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also enforce that links from docs/ stay inside the published docs_dir",
    )
    args = parser.parse_args(argv)
    if not args.all and not args.file:
        parser.error("use --all or --file")

    paths = markdown_files() if args.all else [ROOT / item for item in args.file]
    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: file not found")
            continue
        errors.extend(check_file(path, args.anchors, published=args.strict))

    if errors:
        print("MARKDOWN_LINKS_INVALID", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"MARKDOWN_LINKS_OK files={len(paths)} anchors={str(args.anchors).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
