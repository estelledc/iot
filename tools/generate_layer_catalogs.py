#!/usr/bin/env python3
"""Generate and verify per-layer catalog pages that list every content file."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.content_inventory import LAYERS

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n?", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
START_MARKER = "<!-- layer-catalog:start -->"
END_MARKER = "<!-- layer-catalog:end -->"


def _title_for(path: Path) -> str:
    text = FRONTMATTER_RE.sub("", path.read_text(encoding="utf-8"), count=1)
    match = H1_RE.search(text)
    return match.group(1).strip() if match else path.stem


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
        if path.read_text(encoding="utf-8") != expected:
            errors.append(f"stale catalog: {relative}")
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
