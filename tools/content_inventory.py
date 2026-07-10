#!/usr/bin/env python3
"""Build and verify the repository's deterministic content inventory.

The inventory deliberately measures repository facts only. A Markdown file being
present or buildable does not mean that its sources or technical claims were
reviewed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path("data/content-inventory.json")
REVIEW_BASELINE_COMMIT = "2a18aec69793494156ffca67848ca0639c145fe4"
START_MARKER = "<!-- content-inventory:start -->"
END_MARKER = "<!-- content-inventory:end -->"

LAYERS = (
    (1, "foundation", "感知与硬件", "layer1-foundation.json"),
    (2, "connectivity", "无线接入", "layer2-connectivity.json"),
    (3, "network", "网络协议", "layer3-network.json"),
    (4, "computing", "计算平台", "layer4-computing.json"),
    (5, "intelligence", "边缘智能", "layer5-intelligence.json"),
    (6, "security", "安全与隐私", "layer6-security.json"),
    (7, "applications", "综合应用", "layer7-applications.json"),
    (8, "frontier", "前沿方向", "layer8-frontier.json"),
)


def _load_plan(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"plan must be a JSON array: {path.relative_to(ROOT)}")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError(f"plan items must be objects: {path.relative_to(ROOT)}")
    return payload


def _nav_paper_paths() -> set[str]:
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    return set(
        re.findall(
            r"^\s*-\s+([a-z-]+/papers/[^\s#]+\.md)\s*$",
            text,
            flags=re.MULTILINE,
        )
    )


def _layer_index_paths(slug: str) -> set[str]:
    path = ROOT / "docs" / slug / "index.md"
    text = path.read_text(encoding="utf-8")
    return {
        f"{slug}/{target}"
        for target in re.findall(r"\]\((papers/[^)#?]+\.md)(?:#[^)]+)?\)", text)
    }


def _source_fingerprint(structural_paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(structural_paths, key=lambda item: item.as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        if path.suffix == ".md" and "/papers/" in f"/{relative}":
            # Inventory freshness depends on the set of content files, not on
            # their read-only bodies.
            continue
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def content_inventory() -> dict[str, Any]:
    nav_paths = _nav_paper_paths()
    layers: list[dict[str, Any]] = []
    structural_paths = [ROOT / "mkdocs.yml"]

    for layer_id, slug, name, plan_name in LAYERS:
        paper_paths = sorted((ROOT / "docs" / slug / "papers").glob("*.md"))
        plan_path = ROOT / "plans" / plan_name
        index_path = ROOT / "docs" / slug / "index.md"
        plan_topics = len(_load_plan(plan_path))
        index_paths = _layer_index_paths(slug)
        content_files = len(paper_paths)
        seed_files = min(content_files, 25)
        planned_capacity = max(content_files, seed_files + plan_topics)
        layer_nav_paths = {path for path in nav_paths if path.startswith(f"{slug}/")}

        layers.append(
            {
                "id": layer_id,
                "slug": slug,
                "name": name,
                "content_files": content_files,
                "explicit_nav_entries": len(layer_nav_paths),
                "layer_index_entries": len(index_paths),
                "plan_topics": plan_topics,
                "planned_capacity": planned_capacity,
                "source_audit": "NOT_TRACKED",
            }
        )
        structural_paths.extend(paper_paths)
        structural_paths.extend((plan_path, index_path))

    totals = {
        "content_files": sum(layer["content_files"] for layer in layers),
        "explicit_nav_entries": sum(layer["explicit_nav_entries"] for layer in layers),
        "layer_index_entries": sum(layer["layer_index_entries"] for layer in layers),
        "plan_topics": sum(layer["plan_topics"] for layer in layers),
        "planned_capacity": sum(layer["planned_capacity"] for layer in layers),
        "source_audited_files": None,
    }

    return {
        "schema_version": 1,
        "review_baseline_commit": REVIEW_BASELINE_COMMIT,
        "generated_by": "python tools/content_inventory.py --write",
        "source_fingerprint_sha256": _source_fingerprint(structural_paths),
        "definitions": {
            "content_files": "docs/<layer>/papers 下存在的 Markdown 文件；不代表来源或事实已审核",
            "explicit_nav_entries": "mkdocs.yml 的 nav 中显式列出的内容文件",
            "layer_index_entries": "八个层级 index.md 直接链接的内容文件",
            "plan_topics": "plans/*.json 中的条目；包含已完成扩展计划，不能与内容文件直接相加",
            "planned_capacity": "每层 max(现有文件数, 25 个种子文件 + plan 条目数) 的容量估计",
            "source_audited_files": "尚无机器可读的全量来源审计记录，因此为 null",
        },
        "totals": totals,
        "layers": layers,
    }


def _markdown_table(inventory: dict[str, Any], compact: bool = False) -> str:
    if compact:
        lines = [
            "| 层级 | 方向 | 内容文件 |",
            "| --- | --- | ---: |",
        ]
        for layer in inventory["layers"]:
            lines.append(
                f"| Layer {layer['id']} | [{layer['name']}]({layer['slug']}/index.md) | "
                f"{layer['content_files']} |"
            )
        lines.append(f"| **合计** | | **{inventory['totals']['content_files']}** |")
        return "\n".join(lines)

    lines = [
        "| 层级 | 方向 | 内容文件 | 显式导航 | 层级首页入口 | Plan 条目 | 目标容量 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for layer in inventory["layers"]:
        lines.append(
            f"| Layer {layer['id']} | {layer['name']} | {layer['content_files']} | "
            f"{layer['explicit_nav_entries']} | {layer['layer_index_entries']} | "
            f"{layer['plan_topics']} | {layer['planned_capacity']} |"
        )
    totals = inventory["totals"]
    lines.append(
        f"| **合计** | | **{totals['content_files']}** | "
        f"**{totals['explicit_nav_entries']}** | **{totals['layer_index_entries']}** | "
        f"**{totals['plan_topics']}** | **{totals['planned_capacity']}** |"
    )
    return "\n".join(lines)


def _render_readme(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    counts = "/".join(str(layer["content_files"]) for layer in inventory["layers"])
    return (
        "## 当前内容基线\n\n"
        f"- 内容文件：**{totals['content_files']}** 篇（八层依次为 {counts}）。\n"
        f"- 显式导航：**{totals['explicit_nav_entries']}** 篇；层级首页直接入口："
        f"**{totals['layer_index_entries']}** 篇。\n"
        f"- 扩展计划：`plans/*.json` 共 **{totals['plan_topics']}** 条；按当前口径的目标容量为 "
        f"**{totals['planned_capacity']}** 篇。\n"
        "- 来源审计：尚未建立全量机器可读记录，不能把“文件存在”表述为“技术事实已验证”。\n\n"
        "统计由 `python tools/content_inventory.py --write` 生成；"
        "`python tools/content_inventory.py --check` 用于检查漂移。\n\n"
        "配置的 Pages 地址：<https://estelledc.github.io/iot/>"
        "（运行状态必须针对目标 commit 单独验收）。"
    )


def _render_roadmap_root(inventory: dict[str, Any]) -> str:
    return (
        "### 当前内容基线（自动派生）\n\n"
        + _markdown_table(inventory)
        + "\n\n> “内容文件”只表示 Markdown 存在；来源审计状态尚未建立。"
        "继续扩展 Layer 3–8 前，先完成导航、内容 schema、来源抽样和可重复生产门禁。"
    )


def _render_reading_progress(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    return (
        f"> 这个文件记录个人精读进度，不是站点内容清单。站点当前有 "
        f"**{totals['content_files']}** 个内容文件；完整分层统计见 "
        "[`docs/progress.md`](docs/progress.md)。"
    )


def _render_docs_index(inventory: dict[str, Any]) -> str:
    return (
        _render_home_stats(inventory)
        + "\n\n<div class=\"iot-prose\" markdown>\n\n## 内容统计\n\n"
        + _markdown_table(inventory, compact=True)
        + "\n\n> 上表统计的是仓库中的内容文件，不代表来源和技术事实已经审核。"
        "显式导航、目录覆盖与扩展计划见[阅读进度](progress.md)。\n\n</div>"
    )


def _render_docs_progress(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    return (
        "## 仓库事实总览\n\n"
        + _markdown_table(inventory)
        + "\n\n"
        f"- **内容文件 {totals['content_files']}**：可被 MkDocs 构建，不等于已完成来源审计。\n"
        f"- **显式导航 {totals['explicit_nav_entries']}**：当前 `mkdocs.yml` 直接列出的内容文件。\n"
        f"- **层级首页入口 {totals['layer_index_entries']}**：八个概览页直接链接的内容文件。\n"
        f"- **Plan 条目 {totals['plan_topics']}**：包含已执行和未执行计划，不能与现有文件直接相加。\n"
        "- **来源审计**：尚无机器可读的全量记录，状态为 `NOT_TRACKED`。\n\n"
        "生成与校验：\n\n"
        "```bash\n"
        "python tools/content_inventory.py --write\n"
        "python tools/content_inventory.py --check\n"
        "```"
    )


def _render_docs_roadmap(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    return (
        "## 当前扩展基线\n\n"
        + _markdown_table(inventory)
        + "\n\n"
        f"当前仓库有 **{totals['content_files']}** 个内容文件和 **{totals['plan_topics']}** 条 plan 记录。"
        "Plan 同时包含已执行和未执行条目，因此不能把两者直接相加。\n\n"
        "### 扩展门禁\n\n"
        "Layer 3–8 暂不进行大批量生成。恢复扩展前必须先满足：\n\n"
        "1. 642 篇全部进入可发现目录，且不改变现有 URL；\n"
        "2. frontmatter schema、双模式内容 linter 和来源抽样通过；\n"
        "3. 生成流程具备幂等、失败恢复、去重、来源锁定和人工批准；\n"
        "4. 先做 4 篇 shadow pilot，再以每批最多 5 篇发布。"
    )


def _render_home_stats(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    return f'''<section class="iot-stats" aria-label="内容基线">
  <div class="iot-stats__item">
    <span class="iot-stats__num">8</span>
    <span class="iot-stats__label">技术层级</span>
  </div>
  <div class="iot-stats__item">
    <span class="iot-stats__num">{totals['content_files']}</span>
    <span class="iot-stats__label">内容文件</span>
  </div>
  <div class="iot-stats__item">
    <span class="iot-stats__num">{totals['explicit_nav_entries']}</span>
    <span class="iot-stats__label">显式导航</span>
  </div>
  <div class="iot-stats__item">
    <span class="iot-stats__num">{totals['plan_topics']}</span>
    <span class="iot-stats__label">Plan 条目</span>
  </div>
</section>'''


RENDERERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "README.md": _render_readme,
    "ROADMAP.md": _render_roadmap_root,
    "reading-progress.md": _render_reading_progress,
    "docs/index.md": _render_docs_index,
    "docs/progress.md": _render_docs_progress,
    "docs/roadmap.md": _render_docs_roadmap,
}


def _replace_block(text: str, replacement: str, path: str) -> str:
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.DOTALL,
    )
    rendered = f"{START_MARKER}\n{replacement.rstrip()}\n{END_MARKER}"
    updated, count = pattern.subn(rendered, text)
    if count != 1:
        raise ValueError(f"expected exactly one inventory block in {path}, found {count}")
    return updated


def _expected_surface(path: str, inventory: dict[str, Any]) -> str:
    current = (ROOT / path).read_text(encoding="utf-8")
    return _replace_block(current, RENDERERS[path](inventory), path)


def _json_bytes(inventory: dict[str, Any]) -> bytes:
    return (json.dumps(inventory, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_inventory(inventory: dict[str, Any]) -> None:
    output = ROOT / DATA_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_json_bytes(inventory))
    for path in RENDERERS:
        target = ROOT / path
        target.write_text(_expected_surface(path, inventory), encoding="utf-8")


def check_inventory(inventory: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    output = ROOT / DATA_PATH
    if not output.is_file():
        errors.append(f"missing generated inventory: {DATA_PATH}")
    elif output.read_bytes() != _json_bytes(inventory):
        errors.append(f"stale generated inventory: {DATA_PATH}")

    for path in RENDERERS:
        target = ROOT / path
        try:
            expected = _expected_surface(path, inventory)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if target.read_text(encoding="utf-8") != expected:
            errors.append(f"stale generated block: {path}")
    return errors


def _summary(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    return (
        f"content_files={totals['content_files']} "
        f"nav={totals['explicit_nav_entries']} "
        f"layer_index={totals['layer_index_entries']} "
        f"plan_topics={totals['plan_topics']} "
        f"planned_capacity={totals['planned_capacity']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail if inventory or generated blocks drift")
    mode.add_argument("--write", action="store_true", help="write inventory and generated blocks")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    args = parser.parse_args(argv)

    try:
        inventory = content_inventory()
        if args.write:
            write_inventory(inventory)
            print(f"CONTENT_INVENTORY_UPDATED {_summary(inventory)}")
            return 0
        if args.check:
            errors = check_inventory(inventory)
            if errors:
                print("CONTENT_INVENTORY_STALE", file=sys.stderr)
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"CONTENT_INVENTORY_OK {_summary(inventory)}")
            return 0
        if args.format == "json":
            sys.stdout.buffer.write(_json_bytes(inventory))
        else:
            print(_summary(inventory))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CONTENT_INVENTORY_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
