#!/usr/bin/env python3
"""Generate and verify per-layer catalog pages that list every content file."""

from __future__ import annotations

import argparse
from collections import Counter
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.content_inventory import LAYERS
from tools.validate_frontmatter import parse_frontmatter

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n?", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
CATALOG_LINK_RE = re.compile(r"\]\((papers/[^)#?]+\.md)(?:#[^)]+)?\)")
START_MARKER = "<!-- layer-catalog:start -->"
END_MARKER = "<!-- layer-catalog:end -->"


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _strip_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    visible: list[str] = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                return "".join(visible), True
            cursor = end + 3
            in_comment = False
            continue
        start = line.find("<!--", cursor)
        if start < 0:
            visible.append(line[cursor:])
            break
        visible.append(line[cursor:start])
        cursor = start + 4
        in_comment = True
    return "".join(visible), in_comment


def _first_body_h1(text: str) -> str | None:
    opened: tuple[str, int] | None = None
    in_comment = False
    for raw_line in text.splitlines():
        line, in_comment = _strip_html_comments(raw_line, in_comment)
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group("fence")
            info = fence.group("info").strip()
            if opened is None:
                opened = (marker[0], len(marker))
            elif (
                marker[0] == opened[0]
                and len(marker) >= opened[1]
                and not info
            ):
                opened = None
            continue
        if opened is not None:
            continue
        match = H1_RE.match(line)
        if match:
            return match.group(1).strip()
    return None


def _title_for(path: Path) -> str:
    payload, issues = parse_frontmatter(path)
    relative = _display_path(path)
    if payload is None:
        detail = issues[0].message if issues else "missing frontmatter"
        raise ValueError(f"{relative}: cannot read title: {detail}")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"{relative}: frontmatter title must be a non-empty string")

    text = FRONTMATTER_RE.sub("", path.read_text(encoding="utf-8"), count=1)
    h1 = _first_body_h1(text)
    if h1 is None:
        raise ValueError(f"{relative}: missing body H1 for frontmatter title {title!r}")
    if title.strip() != h1:
        raise ValueError(
            f"{relative}: title/H1 mismatch: frontmatter={title.strip()!r} body_h1={h1!r}"
        )
    return title.strip()


def render_catalog(
    *,
    layer_id: int,
    slug: str,
    name: str,
    paper_paths: list[Path],
) -> str:
    lines = [
        f"# Layer {layer_id}：{name} · 全部目录",
        "",
        "> 本页由 `python tools/generate_layer_catalogs.py --write` 自动生成；请勿手工编辑链接列表。",
        "",
        START_MARKER,
        "| # | 标题 | 文件 |",
        "| --- | --- | --- |",
    ]
    for index, path in enumerate(sorted(paper_paths, key=lambda item: item.name), 1):
        title = _title_for(path)
        lines.append(f"| {index} | {title} | [{path.stem}](papers/{path.name}) |")
    lines.extend([END_MARKER, ""])
    return "\n".join(lines)


def catalog_path(slug: str) -> Path:
    return ROOT / "docs" / slug / "catalog.md"


def expected_catalogs() -> dict[str, str]:
    rendered: dict[str, str] = {}
    for layer_id, slug, name, _plan in LAYERS:
        papers = sorted((ROOT / "docs" / slug / "papers").glob("*.md"))
        rendered[slug] = render_catalog(
            layer_id=layer_id,
            slug=slug,
            name=name,
            paper_paths=papers,
        )
    return rendered


def write_catalogs() -> int:
    rendered = expected_catalogs()
    for slug, text in rendered.items():
        path = catalog_path(slug)
        path.write_text(text, encoding="utf-8")
    return len(rendered)


def check_catalogs() -> list[str]:
    errors: list[str] = []
    rendered = expected_catalogs()
    for slug, expected in rendered.items():
        path = catalog_path(slug)
        relative = path.relative_to(ROOT).as_posix()
        if not path.is_file():
            errors.append(f"missing catalog: {relative}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual == expected:
            continue

        expected_links = set(CATALOG_LINK_RE.findall(expected))
        actual_link_list = CATALOG_LINK_RE.findall(actual)
        actual_links = set(actual_link_list)
        missing = sorted(expected_links - actual_links)
        unexpected = sorted(actual_links - expected_links)
        duplicates = sorted(
            link for link, count in Counter(actual_link_list).items() if count > 1
        )
        if missing:
            errors.append(f"catalog missing links: {relative}: {', '.join(missing)}")
        if unexpected:
            errors.append(f"catalog unexpected links: {relative}: {', '.join(unexpected)}")
        if duplicates:
            errors.append(f"catalog duplicate links: {relative}: {', '.join(duplicates)}")
        if not missing and not unexpected and not duplicates:
            errors.append(f"catalog title/content drift: {relative}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write docs/<layer>/catalog.md")
    mode.add_argument("--check", action="store_true", help="fail if catalogs drift")
    args = parser.parse_args(argv)
    try:
        if args.write:
            count = write_catalogs()
            print(f"LAYER_CATALOGS_UPDATED layers={count}")
            return 0
        errors = check_catalogs()
        if errors:
            print("LAYER_CATALOGS_STALE", file=sys.stderr)
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"LAYER_CATALOGS_OK layers={len(LAYERS)}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"LAYER_CATALOGS_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
