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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trust_records, validate_trust_state
from tools.iot_domain import LAYERS, iter_content_documents

DATA_PATH = Path("data/content-inventory.json")
REVIEW_BASELINE_COMMIT = "2a18aec69793494156ffca67848ca0639c145fe4"
SOURCE_AUDIT_ROOT = Path("data/source-audits")
START_MARKER = "<!-- content-inventory:start -->"
END_MARKER = "<!-- content-inventory:end -->"


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


def _catalog_paths(slug: str) -> set[str]:
    path = ROOT / "docs" / slug / "catalog.md"
    if not path.is_file():
        return set()
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


def _source_audit_paths() -> list[Path]:
    root = ROOT / SOURCE_AUDIT_ROOT
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.suffix in {".yml", ".yaml"} and path.is_file()
    )


def _inventory_structural_paths() -> list[Path]:
    paths = [ROOT / "mkdocs.yml"]
    papers_by_layer = {layer.slug: [] for layer in LAYERS}
    for document in iter_content_documents(repo_root=ROOT):
        papers_by_layer[document.layer.slug].append(document.path)

    for _, slug, _, plan_name in LAYERS:
        plan_path = ROOT / "plans" / plan_name
        index_path = ROOT / "docs" / slug / "index.md"
        catalog_file = ROOT / "docs" / slug / "catalog.md"
        paths.extend(papers_by_layer[slug])
        paths.extend((plan_path, index_path))
        if catalog_file.is_file():
            paths.append(catalog_file)
    paths.extend(_source_audit_paths())
    return paths


def _load_source_audit_records_by_id() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in _source_audit_paths():
        record = trust_records.load_record(path)
        audit_id = record.get("audit_id")
        if not isinstance(audit_id, str) or not audit_id:
            raise ValueError(f"source audit missing audit_id: {path.relative_to(ROOT)}")
        if audit_id in records:
            raise ValueError(f"duplicate source audit id: {audit_id}")
        records[audit_id] = record
    return records


def _layer_slug_from_content_path(content_path: str) -> str:
    parts = Path(content_path).parts
    if len(parts) != 4 or parts[0] != "docs" or parts[2] != "papers":
        raise ValueError(f"invalid source audit content path: {content_path}")
    slugs = {layer.slug for layer in LAYERS}
    if parts[1] not in slugs:
        raise ValueError(f"unknown source audit layer slug: {parts[1]}")
    return parts[1]


def _source_audit_label(structural_files: int) -> str:
    if structural_files >= 3:
        return "SAMPLED_STRUCTURAL"
    if structural_files:
        return "PARTIAL_STRUCTURAL"
    return "NOT_TRACKED"


def _source_audit_projection(
    trust_result: Any,
    records_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    by_layer = {
        layer.slug: {
            "structural_records": 0,
            "structural_files": 0,
            "factual_source_audited_files": 0,
            "source_audit": "NOT_TRACKED",
        }
        for layer in LAYERS
    }
    source_status_counts = {"UNVERIFIED": 0, "PARTIAL": 0, "VERIFIED": 0}

    for projection in trust_result.projections.values():
        status = str(getattr(projection, "source_status"))
        source_status_counts.setdefault(status, 0)
        source_status_counts[status] += 1

        slug = _layer_slug_from_content_path(str(getattr(projection, "content_path")))
        if status in {"PARTIAL", "VERIFIED"}:
            by_layer[slug]["factual_source_audited_files"] += 1

        active_structural_ids = [
            audit_id
            for audit_id in getattr(projection, "active_audit_ids")
            if records_by_id.get(audit_id, {}).get("audit_kind") == "STRUCTURAL"
        ]
        if active_structural_ids:
            by_layer[slug]["structural_files"] += 1
            by_layer[slug]["structural_records"] += len(active_structural_ids)

    for layer_projection in by_layer.values():
        layer_projection["source_audit"] = _source_audit_label(
            layer_projection["structural_files"]
        )

    return {
        "by_layer": by_layer,
        "totals": {
            "source_status_counts": source_status_counts,
            "source_audited_files": (
                source_status_counts.get("PARTIAL", 0)
                + source_status_counts.get("VERIFIED", 0)
            ),
            "structural_source_audit_records": sum(
                layer["structural_records"] for layer in by_layer.values()
            ),
            "structural_source_audited_files": sum(
                layer["structural_files"] for layer in by_layer.values()
            ),
        },
    }


def _current_source_audit_projection() -> dict[str, Any]:
    trust_result = validate_trust_state.validate_repository_trust(
        repo_root=ROOT,
        baseline_mode=True,
    )
    if trust_result.issues:
        raise ValueError("trust state has validation issues; cannot project source audits")
    return _source_audit_projection(
        trust_result,
        _load_source_audit_records_by_id(),
    )


def content_inventory() -> dict[str, Any]:
    nav_paths = _nav_paper_paths()
    audit_projection = _current_source_audit_projection()
    layers: list[dict[str, Any]] = []
    papers_by_layer = {layer.slug: [] for layer in LAYERS}
    for document in iter_content_documents(repo_root=ROOT):
        papers_by_layer[document.layer.slug].append(document.path)

    for layer_id, slug, name, plan_name in LAYERS:
        paper_paths = papers_by_layer[slug]
        plan_path = ROOT / "plans" / plan_name
        index_path = ROOT / "docs" / slug / "index.md"
        catalog_file = ROOT / "docs" / slug / "catalog.md"
        plan_topics = len(_load_plan(plan_path))
        index_paths = _layer_index_paths(slug)
        catalog_paths = _catalog_paths(slug)
        content_files = len(paper_paths)
        seed_files = min(content_files, 25)
        planned_capacity = max(content_files, seed_files + plan_topics)
        layer_nav_paths = {path for path in nav_paths if path.startswith(f"{slug}/")}
        discoverable = layer_nav_paths | catalog_paths
        layer_audit = audit_projection["by_layer"][slug]

        layers.append(
            {
                "id": layer_id,
                "slug": slug,
                "name": name,
                "content_files": content_files,
                "explicit_nav_entries": len(layer_nav_paths),
                "layer_index_entries": len(index_paths),
                "catalog_entries": len(catalog_paths),
                "discoverable_entries": len(discoverable),
                "plan_topics": plan_topics,
                "planned_capacity": planned_capacity,
                "source_audit": layer_audit["source_audit"],
                "structural_source_audit_records": layer_audit["structural_records"],
                "structural_source_audited_files": layer_audit["structural_files"],
                "factual_source_audited_files": layer_audit[
                    "factual_source_audited_files"
                ],
            }
        )

    totals = {
        "content_files": sum(layer["content_files"] for layer in layers),
        "explicit_nav_entries": sum(layer["explicit_nav_entries"] for layer in layers),
        "layer_index_entries": sum(layer["layer_index_entries"] for layer in layers),
        "catalog_entries": sum(layer["catalog_entries"] for layer in layers),
        "discoverable_entries": sum(layer["discoverable_entries"] for layer in layers),
        "plan_topics": sum(layer["plan_topics"] for layer in layers),
        "planned_capacity": sum(layer["planned_capacity"] for layer in layers),
        **audit_projection["totals"],
    }

    return {
        "schema_version": 1,
        "review_baseline_commit": REVIEW_BASELINE_COMMIT,
        "generated_by": "python tools/content_inventory.py --write",
        "source_fingerprint_sha256": _source_fingerprint(_inventory_structural_paths()),
        "definitions": {
            "content_files": "docs/<layer>/papers 下存在的 Markdown 文件；不代表来源或事实已审核",
            "explicit_nav_entries": "mkdocs.yml 的 nav 中显式列出的内容文件",
            "layer_index_entries": "八个层级 index.md 直接链接的内容文件",
            "catalog_entries": "八个层级 catalog.md 直接链接的内容文件",
            "discoverable_entries": "显式导航 ∪ 层级 catalog 链接；不等于来源已审核",
            "plan_topics": "plans/*.json 中的条目；包含已完成扩展计划，不能与内容文件直接相加",
            "planned_capacity": "每层 max(现有文件数, 25 个种子文件 + plan 条目数) 的容量估计",
            "source_audited_files": "当前由 CLAIM_VERIFICATION 投影为 PARTIAL 或 VERIFIED 的内容文件数；STRUCTURAL 不计入",
            "structural_source_audit_records": "当前有效的 STRUCTURAL source audit 记录数，只证明结构可审计",
            "structural_source_audited_files": "至少有一条当前有效 STRUCTURAL source audit 的内容文件数",
            "source_status_counts": "仓库级 trust graph 当前投影出的 source_status 计数",
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
        "| 层级 | 方向 | 内容文件 | 显式导航 | 目录页入口 | 可发现 | 层级首页入口 | Plan 条目 | 目标容量 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for layer in inventory["layers"]:
        lines.append(
            f"| Layer {layer['id']} | {layer['name']} | {layer['content_files']} | "
            f"{layer['explicit_nav_entries']} | {layer['catalog_entries']} | "
            f"{layer['discoverable_entries']} | {layer['layer_index_entries']} | "
            f"{layer['plan_topics']} | {layer['planned_capacity']} |"
        )
    totals = inventory["totals"]
    lines.append(
        f"| **合计** | | **{totals['content_files']}** | "
        f"**{totals['explicit_nav_entries']}** | **{totals['catalog_entries']}** | "
        f"**{totals['discoverable_entries']}** | **{totals['layer_index_entries']}** | "
        f"**{totals['plan_topics']}** | **{totals['planned_capacity']}** |"
    )
    return "\n".join(lines)


def _render_readme(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    counts = "/".join(str(layer["content_files"]) for layer in inventory["layers"])
    return (
        "## 当前内容基线\n\n"
        f"- 内容文件：**{totals['content_files']}** 篇（八层依次为 {counts}）。\n"
        f"- 显式导航：**{totals['explicit_nav_entries']}** 篇；目录页入口："
        f"**{totals['catalog_entries']}** 篇；可发现："
        f"**{totals['discoverable_entries']}** 篇；层级首页直接入口："
        f"**{totals['layer_index_entries']}** 篇。\n"
        f"- 扩展计划：`plans/*.json` 共 **{totals['plan_topics']}** 条；按当前口径的目标容量为 "
        f"**{totals['planned_capacity']}** 篇。\n"
        f"- 来源审计：current valid `STRUCTURAL` 结构审计 **{totals['structural_source_audit_records']}** 条，"
        f"覆盖 **{totals['structural_source_audited_files']}** 个内容文件；事实核验："
        f"**{totals['source_audited_files']}** 篇（`PARTIAL`/`VERIFIED`）。"
        "`STRUCTURAL` 只证明结构可审计，不代表技术事实已验证。\n\n"
        "统计由 `python tools/content_inventory.py --write` 生成；"
        "`python tools/content_inventory.py --check` 用于检查漂移。\n\n"
        "配置的 Pages 地址：<https://estelledc.github.io/iot/>"
        "（运行状态必须针对目标 commit 单独验收）。"
    )


def _render_roadmap_root(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    return (
        "### 当前内容基线（自动派生）\n\n"
        + _markdown_table(inventory)
        + "\n\n> “内容文件”只表示 Markdown 存在；“可发现”= 显式导航 ∪ 层级 catalog。"
        f"当前有 **{totals['structural_source_audit_records']}** 条 current valid `STRUCTURAL` "
        f"结构审计记录；事实核验：**{totals['source_audited_files']}** 篇。"
        "`STRUCTURAL` 不提升 `PARTIAL`、`VERIFIED` 或 `HUMAN_APPROVED`。"
        "继续扩展 Layer 3–8 前，先完成事实核验、来源抽样和可重复生产门禁。"
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
        f"- **目录页入口 {totals['catalog_entries']}**：八个层级 `catalog.md` 直接链接的内容文件。\n"
        f"- **可发现 {totals['discoverable_entries']}**：显式导航 ∪ 目录页链接。\n"
        f"- **层级首页入口 {totals['layer_index_entries']}**：八个概览页直接链接的内容文件。\n"
        f"- **Plan 条目 {totals['plan_topics']}**：包含已执行和未执行计划，不能与现有文件直接相加。\n"
        f"- **来源审计**：current valid `STRUCTURAL` 结构审计 **{totals['structural_source_audit_records']}** 条，"
        f"覆盖 **{totals['structural_source_audited_files']}** 个内容文件；事实核验："
        f"**{totals['source_audited_files']}** 篇（`PARTIAL`/`VERIFIED`），"
        f"`VERIFIED` **{totals['source_status_counts']['VERIFIED']}** 篇。"
        "`STRUCTURAL` 只证明结构可审计，不代表技术事实已验证。\n\n"
        "生成与校验：\n\n"
        "```bash\n"
        "python tools/content_inventory.py --write\n"
        "python tools/content_inventory.py --check\n"
        "python tools/generate_layer_catalogs.py --check\n"
        "```"
    )


def _render_docs_roadmap(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    return (
        "## 当前扩展基线\n\n"
        + _markdown_table(inventory)
        + "\n\n"
        f"当前仓库有 **{totals['content_files']}** 个内容文件、"
        f"**{totals['discoverable_entries']}** 个可发现入口和 **{totals['plan_topics']}** 条 plan 记录。"
        "Plan 同时包含已执行和未执行条目，因此不能把两者直接相加。\n\n"
        "### 扩展门禁\n\n"
        "Layer 3–8 暂不进行大批量生成。恢复扩展前必须先满足：\n\n"
        "1. 内容文件全部可发现（显式导航 ∪ 层级 catalog），且不改变现有 URL；\n"
        "2. frontmatter schema、全量校验和来源抽样通过；\n"
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
        f"catalog={totals['catalog_entries']} "
        f"discoverable={totals['discoverable_entries']} "
        f"layer_index={totals['layer_index_entries']} "
        f"plan_topics={totals['plan_topics']} "
        f"planned_capacity={totals['planned_capacity']} "
        f"structural_source_audits={totals['structural_source_audit_records']} "
        f"source_audited_files={totals['source_audited_files']}"
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
