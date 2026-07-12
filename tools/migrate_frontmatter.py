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

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.iot_domain.content import canonical_body_bytes, first_body_h1
from tools.iot_domain.paths import content_identity, iter_content_paths
from tools.validate_frontmatter import load_schema, validate_file

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
    return canonical_body_bytes(text.encode("utf-8"))


def _has_frontmatter(text: str) -> bool:
    raw = text.encode("utf-8")
    return canonical_body_bytes(raw) != raw


def extract_meta(path: Path, text: str) -> dict[str, Any]:
    layer, content_id = content_identity(path, repo_root=ROOT)
    canonical = body_bytes(text)
    body_text = canonical.decode("utf-8")
    h1 = first_body_h1(canonical)
    title = h1 if h1 is not None else content_id
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
        "id": content_id,
        "title": title,
        "layer": layer.id,
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
    content_identity(path, repo_root=ROOT)
    original_bytes = path.read_bytes()
    before_body = canonical_body_bytes(original_bytes, path=path.as_posix())
    before_hash = hashlib.sha256(before_body).hexdigest()
    original = original_bytes.decode("utf-8")
    updated_bytes = insert_frontmatter(path, original).encode("utf-8")
    after_hash = hashlib.sha256(
        canonical_body_bytes(updated_bytes, path=path.as_posix())
    ).hexdigest()
    if before_hash != after_hash:
        raise ValueError(f"body hash changed for {path}")
    changed = updated_bytes != original_bytes
    if changed and not dry_run:
        path.write_bytes(updated_bytes)
    return changed, before_hash


def _paper_paths() -> list[Path]:
    return list(iter_content_paths(repo_root=ROOT))


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return "<outside repository>"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="migrate all docs/*/papers/*.md")
    parser.add_argument("--path", action="append", default=[], help="migrate one repository-relative file")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    args = parser.parse_args(argv)
    if not args.all and not args.path:
        parser.error("use --all or --path")

    paths = _paper_paths() if args.all else [(ROOT / item).absolute() for item in args.path]
    changed_count = 0
    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            errors.append(f"{_display_path(path)}: file not found")
            continue
        try:
            changed, _ = migrate_path(path, dry_run=args.dry_run)
        except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
            errors.append(f"{_display_path(path)}: {exc}")
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
