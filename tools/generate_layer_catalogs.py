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

from tools.iot_domain import LAYERS, content_title, parse_document
from tools.iot_domain.paths import REPO_ROOT, content_identity, iter_content_paths

CATALOG_LINK_RE = re.compile(r"\]\((papers/[^)#?]+\.md)(?:#[^)]+)?\)")
START_MARKER = "<!-- layer-catalog:start -->"
END_MARKER = "<!-- layer-catalog:end -->"


def _title_for(path: Path, *, validate_identity: bool = False) -> str:
    repo_root = ROOT
    try:
        path.resolve(strict=False).relative_to(ROOT.resolve())
    except (OSError, RuntimeError, ValueError):
        if len(path.parents) >= 4:
            repo_root = path.parents[3]
    return content_title(
        parse_document(
            path,
            repo_root=repo_root,
            validate_identity=validate_identity,
        )
    )


def render_catalog(
    *,
    layer_id: int,
    slug: str,
    name: str,
    paper_paths: list[Path],
    validate_identity: bool = False,
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
        title = _title_for(path, validate_identity=validate_identity)
        lines.append(f"| {index} | {title} | [{path.stem}](papers/{path.name}) |")
    lines.extend([END_MARKER, ""])
    return "\n".join(lines)


def catalog_path(slug: str) -> Path:
    return ROOT / "docs" / slug / "catalog.md"


def expected_catalogs() -> dict[str, str]:
    rendered: dict[str, str] = {}
    validate_identity = ROOT.resolve() == REPO_ROOT.resolve()
    papers_by_layer = {layer[1]: [] for layer in LAYERS}
    for path in iter_content_paths(repo_root=ROOT):
        layer, _content_id = content_identity(path, repo_root=ROOT)
        papers_by_layer[layer.slug].append(path)
    for layer_id, slug, name, _plan in LAYERS:
        papers = papers_by_layer[slug]
        rendered[slug] = render_catalog(
            layer_id=layer_id,
            slug=slug,
            name=name,
            paper_paths=papers,
            validate_identity=validate_identity,
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
