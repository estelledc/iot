#!/usr/bin/env python3
"""Mechanically insert content frontmatter without rewriting article bodies."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from tools.validate_frontmatter import LAYER_BY_SLUG, load_schema, validate_file

ROOT = Path(__file__).resolve().parents[1]
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n?", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
META_RE = re.compile(
    r"^\s*>\s*\*\*难度\*\*\s*[：:]\s*(?P<body>.+)$",
    re.MULTILINE,
)
DIFFICULTY_MAP = {
    "零基础": "zero_base",
    "入门": "beginner",
    "初级": "beginner",
    "中级": "intermediate",
    "进阶": "advanced",
    "高级": "advanced",
    "前沿": "frontier",
}
READING_TIME_RE = re.compile(r"\*{0,2}阅读时间\*{0,2}\s*[：:]\s*约?\s*(\d+)\s*分钟")


def body_bytes(text: str) -> bytes:
    return FRONTMATTER_RE.sub("", text, count=1).encode("utf-8")


def _has_frontmatter(text: str) -> bool:
    if not text.startswith("---\n"):
        return False
    closing = text.find("\n---\n", 4)
    return closing != -1 or text.rstrip().endswith("\n---")


def extract_meta(path: Path, text: str) -> dict[str, Any]:
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        relative = path
    parts = relative.parts
    if len(parts) >= 4 and parts[0] == "docs" and parts[2] == "papers":
        layer_slug = parts[1]
    else:
        layer_slug = path.parent.parent.name
    layer = LAYER_BY_SLUG[layer_slug]
    body_text = FRONTMATTER_RE.sub("", text, count=1)
    h1 = H1_RE.search(body_text)
    title = h1.group(1).strip() if h1 else path.stem
    difficulty: str | int = "UNKNOWN"
    reading_time: str | int = "UNKNOWN"
    meta_line = META_RE.search(body_text)
    if meta_line:
        body = meta_line.group("body")
        for label, enum_value in DIFFICULTY_MAP.items():
            if label in body:
                difficulty = enum_value
                break
        time_match = READING_TIME_RE.search(body)
        if time_match:
            reading_time = int(time_match.group(1))
    return {
        "schema_version": "1.0",
        "id": path.stem,
        "title": title,
        "layer": layer,
        "content_type": "UNKNOWN",
        "difficulty": difficulty,
        "reading_time": reading_time,
        "prerequisites": "UNKNOWN",
        "tags": [],
        "source_status": "UNVERIFIED",
        "review_status": "UNREVIEWED",
        "last_reviewed": "UNKNOWN",
    }


def render_frontmatter(meta: dict[str, Any]) -> str:
    dumped = yaml.safe_dump(
        meta,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip() + "\n"
    return f"---\n{dumped}---\n"


def insert_frontmatter(path: Path, text: str) -> str:
    if _has_frontmatter(text):
        return text
    meta = extract_meta(path, text)
    return render_frontmatter(meta) + text


def migrate_path(path: Path, *, dry_run: bool = False) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")
    before_hash = hashlib.sha256(body_bytes(original)).hexdigest()
    updated = insert_frontmatter(path, original)
    after_hash = hashlib.sha256(body_bytes(updated)).hexdigest()
    if before_hash != after_hash:
        raise ValueError(f"body hash changed for {path}")
    changed = updated != original
    if changed and not dry_run:
        path.write_text(updated, encoding="utf-8")
    return changed, before_hash


def _paper_paths() -> list[Path]:
    return sorted(ROOT.glob("docs/*/papers/*.md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="migrate all docs/*/papers/*.md")
    parser.add_argument("--path", action="append", default=[], help="migrate one repository-relative file")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    args = parser.parse_args(argv)
    if not args.all and not args.path:
        parser.error("use --all or --path")

    paths = _paper_paths() if args.all else [(ROOT / item).resolve() for item in args.path]
    changed_count = 0
    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            errors.append(f"{path}: file not found")
            continue
        try:
            changed, _ = migrate_path(path, dry_run=args.dry_run)
        except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if changed:
            changed_count += 1

    if errors:
        print("FRONTMATTER_MIGRATE_FAILED", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    mode = "dry_run" if args.dry_run else "written"
    print(f"FRONTMATTER_MIGRATE_OK mode={mode} changed={changed_count} checked={len(paths)}")

    if not args.dry_run and paths:
        schema = load_schema()
        validation_errors: list[str] = []
        for path in paths:
            for issue in validate_file(path, schema):
                validation_errors.append(issue.render())
        if validation_errors:
            print("FRONTMATTER_INVALID", file=sys.stderr)
            for error in validation_errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
