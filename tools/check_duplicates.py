#!/usr/bin/env python3
"""Enforce canonical CSS sources and declared read-only Markdown mirrors."""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class LegacyMirrorPair:
    """A validated canonical Markdown source and its generated mirror."""

    canonical_relative: str
    mirror_relative: str
    canonical: Path
    mirror: Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_policy(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("canonical source policy must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported canonical source policy schema_version")
    return payload


def _safe_repository_path(
    root: Path,
    raw_path: Any,
    *,
    role: str,
    required_directory: str,
) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"{role} must be a safe repository-relative path")

    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{role} must be a safe repository-relative path: {raw_path}")
    if not relative.parts or relative.parts[0] != required_directory:
        raise ValueError(f"{role} must be under {required_directory}/: {raw_path}")

    root = root.resolve()
    candidate = root / relative
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ValueError(f"{role} must be a safe repository-relative path: {raw_path}")
    if resolved != candidate.absolute():
        raise ValueError(f"{role} must not traverse symlinks: {raw_path}")
    return relative.as_posix(), candidate


def legacy_mirror_pairs(
    policy: dict[str, Any],
    *,
    root: Path = ROOT,
) -> list[LegacyMirrorPair]:
    raw_pairs = policy.get("legacy_markdown_mirrors", [])
    if not isinstance(raw_pairs, list):
        raise ValueError("legacy_markdown_mirrors must be a list")

    pairs: list[LegacyMirrorPair] = []
    mirror_targets: set[Path] = set()
    for index, item in enumerate(raw_pairs):
        if not isinstance(item, dict):
            raise ValueError(f"legacy mirror entry {index} must be a mapping")
        if item.get("policy") != "READ_ONLY_MIRROR":
            raise ValueError(f"legacy mirror has unsupported policy: {item.get('policy')}")

        canonical_relative, canonical = _safe_repository_path(
            root,
            item.get("canonical"),
            role="canonical",
            required_directory="docs",
        )
        mirror_relative, mirror = _safe_repository_path(
            root,
            item.get("mirror"),
            role="mirror",
            required_directory="papers",
        )
        if canonical == mirror:
            raise ValueError(f"canonical and mirror must be different: {canonical_relative}")
        if mirror in mirror_targets:
            raise ValueError(f"duplicate mirror target: {mirror_relative}")
        mirror_targets.add(mirror)
        pairs.append(
            LegacyMirrorPair(
                canonical_relative=canonical_relative,
                mirror_relative=mirror_relative,
                canonical=canonical,
                mirror=mirror,
            )
        )
    return pairs


def validate_policy(
    policy_path: Path,
    *,
    root: Path = ROOT,
) -> tuple[list[str], dict[str, int]]:
    policy = load_policy(policy_path)
    errors: list[str] = []
    counts = {"canonical_css": 0, "legacy_markdown_mirrors": 0}

    for item in policy.get("canonical_css", []):
        canonical = root / item["path"]
        duplicate = root / item["removed_duplicate"]
        counts["canonical_css"] += 1
        if not canonical.is_file():
            errors.append(f"missing canonical CSS: {item['path']}")
        if duplicate.exists():
            errors.append(f"removed CSS duplicate exists again: {item['removed_duplicate']}")

    for pair in legacy_mirror_pairs(policy, root=root):
        counts["legacy_markdown_mirrors"] += 1
        if not pair.canonical.is_file() or not pair.mirror.is_file():
            errors.append(
                "legacy mirror pair is incomplete: "
                f"{pair.canonical_relative} <-> {pair.mirror_relative}"
            )
            continue
        if _sha256(pair.canonical) != _sha256(pair.mirror):
            errors.append(
                f"legacy mirror drift: {pair.canonical_relative} != {pair.mirror_relative}"
            )
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
