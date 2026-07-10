#!/usr/bin/env python3
"""Enforce canonical CSS sources and declared read-only Markdown mirrors."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_policy(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("canonical source policy must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported canonical source policy schema_version")
    return payload


def validate_policy(policy_path: Path) -> tuple[list[str], dict[str, int]]:
    policy = _load_policy(policy_path)
    errors: list[str] = []
    counts = {"canonical_css": 0, "legacy_markdown_mirrors": 0}

    for item in policy.get("canonical_css", []):
        canonical = ROOT / item["path"]
        duplicate = ROOT / item["removed_duplicate"]
        counts["canonical_css"] += 1
        if not canonical.is_file():
            errors.append(f"missing canonical CSS: {item['path']}")
        if duplicate.exists():
            errors.append(f"removed CSS duplicate exists again: {item['removed_duplicate']}")

    for item in policy.get("legacy_markdown_mirrors", []):
        canonical = ROOT / item["canonical"]
        mirror = ROOT / item["mirror"]
        counts["legacy_markdown_mirrors"] += 1
        if item.get("policy") != "READ_ONLY_MIRROR":
            errors.append(f"legacy mirror has unsupported policy: {item.get('policy')}")
            continue
        if not canonical.is_file() or not mirror.is_file():
            errors.append(f"legacy mirror pair is incomplete: {item['canonical']} <-> {item['mirror']}")
            continue
        if _sha256(canonical) != _sha256(mirror):
            errors.append(f"legacy mirror drift: {item['canonical']} != {item['mirror']}")
    return errors, counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", default="data/canonical-sources.yml")
    args = parser.parse_args(argv)
    policy_path = (ROOT / args.policy).resolve()
    try:
        errors, counts = validate_policy(policy_path)
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"DUPLICATE_POLICY_ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("DUPLICATE_POLICY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "DUPLICATE_POLICY_OK "
        f"canonical_css={counts['canonical_css']} "
        f"legacy_markdown_mirrors={counts['legacy_markdown_mirrors']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
