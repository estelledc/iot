#!/usr/bin/env python3
"""Check Markdown code fences for unclosed blocks and swallowed headings."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", ".tmp", "site"}
FENCE_RE = re.compile(r"^(?P<indent>\s*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
HEADING_RE = re.compile(r"^\s*#{2,6}\s+\S")


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
    )


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    opened: tuple[str, int, int, str] | None = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group("fence")
            info = match.group("info").strip()
            if opened is None:
                opened = (marker[0], len(marker), line_number, info)
            elif marker[0] == opened[0] and len(marker) >= opened[1] and not info:
                opened = None
            continue

        if opened is not None and not opened[3] and HEADING_RE.match(line):
            errors.append(
                f"{path.relative_to(ROOT)}:{line_number}: Markdown heading is swallowed by "
                f"a bare fence opened at line {opened[2]}"
            )

    if opened is not None:
        errors.append(
            f"{path.relative_to(ROOT)}:{opened[2]}: unclosed {opened[0] * opened[1]} fence"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="check all repository Markdown files")
    parser.add_argument("--file", action="append", default=[], help="check one repository-relative file")
    args = parser.parse_args(argv)
    if not args.all and not args.file:
        parser.error("use --all or --file")

    paths = markdown_files() if args.all else [ROOT / item for item in args.file]
    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: file not found")
            continue
        errors.extend(check_file(path))

    if errors:
        print("MARKDOWN_FENCES_INVALID", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"MARKDOWN_FENCES_OK files={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
