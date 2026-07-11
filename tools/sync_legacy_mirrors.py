#!/usr/bin/env python3
"""Check or atomically refresh declared legacy Markdown mirrors."""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_duplicates


@dataclass(frozen=True)
class PreparedMirror:
    pair: check_duplicates.LegacyMirrorPair
    canonical_bytes: bytes
    canonical_sha256: str
    mirror_bytes: bytes
    mirror_sha256: str


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _policy_inside_root(policy_path: Path, root: Path) -> Path:
    root = root.resolve()
    resolved = policy_path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("policy must be a safe repository-relative path")
    return resolved


def _prepare_policy(policy_path: Path, root: Path) -> list[PreparedMirror]:
    policy_path = _policy_inside_root(policy_path, root)
    policy = check_duplicates.load_policy(policy_path)
    pairs = check_duplicates.legacy_mirror_pairs(policy, root=root)
    prepared: list[PreparedMirror] = []

    for pair in pairs:
        if not pair.canonical.is_file():
            raise ValueError(f"missing canonical file: {pair.canonical_relative}")
        if not pair.mirror.is_file():
            raise ValueError(f"missing mirror file: {pair.mirror_relative}")

        canonical_bytes = pair.canonical.read_bytes()
        mirror_bytes = pair.mirror.read_bytes()
        prepared.append(
            PreparedMirror(
                pair=pair,
                canonical_bytes=canonical_bytes,
                canonical_sha256=_sha256(canonical_bytes),
                mirror_bytes=mirror_bytes,
                mirror_sha256=_sha256(mirror_bytes),
            )
        )
    return prepared


def _stage_updates(prepared: list[PreparedMirror]) -> list[tuple[PreparedMirror, Path]]:
    staged: list[tuple[PreparedMirror, Path]] = []
    try:
        for item in prepared:
            if item.canonical_bytes == item.mirror_bytes:
                continue
            mode = stat.S_IMODE(item.pair.mirror.stat().st_mode)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=item.pair.mirror.parent,
                prefix=f".{item.pair.mirror.name}.",
                suffix=".tmp",
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(item.canonical_bytes)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(temporary, mode)
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
            staged.append((item, temporary))
    except BaseException:
        for _item, temporary in staged:
            temporary.unlink(missing_ok=True)
        raise
    return staged


def sync_policy(
    policy_path: Path,
    *,
    root: Path = ROOT,
    write: bool,
) -> tuple[list[str], int]:
    """Check drift or copy canonical bytes to mirrors after a full preflight."""

    root = root.resolve()
    prepared = _prepare_policy(policy_path, root)
    stale = [item for item in prepared if item.canonical_bytes != item.mirror_bytes]
    if not write:
        return (
            [
                "legacy mirror drift: "
                f"{item.pair.canonical_relative} != {item.pair.mirror_relative}"
                for item in stale
            ],
            0,
        )
    if not stale:
        return [], 0

    staged = _stage_updates(prepared)
    try:
        for item, _temporary in staged:
            if item.pair.canonical.read_bytes() != item.canonical_bytes:
                raise RuntimeError(
                    f"canonical changed during sync: {item.pair.canonical_relative}"
                )
            if item.pair.mirror.read_bytes() != item.mirror_bytes:
                raise RuntimeError(
                    f"mirror changed during sync: {item.pair.mirror_relative}"
                )
        for _item, temporary in staged:
            os.replace(temporary, _item.pair.mirror)
    finally:
        for _item, temporary in staged:
            temporary.unlink(missing_ok=True)

    for item in stale:
        if item.pair.canonical.read_bytes() != item.canonical_bytes:
            raise RuntimeError(f"canonical changed during sync: {item.pair.canonical_relative}")
        if item.pair.mirror.read_bytes() != item.canonical_bytes:
            raise RuntimeError(f"mirror write failed: {item.pair.mirror_relative}")
    return [], len(stale)


def _print_pair_hashes(policy_path: Path, root: Path) -> None:
    for item in _prepare_policy(policy_path, root):
        print(
            "LEGACY_MIRROR_PAIR "
            f"canonical={item.pair.canonical_relative} "
            f"canonical_sha256={item.canonical_sha256} "
            f"mirror={item.pair.mirror_relative} "
            f"mirror_sha256={item.mirror_sha256}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", default="data/canonical-sources.yml")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="refresh stale mirrors")
    mode.add_argument("--check", action="store_true", help="fail if mirrors drift")
    args = parser.parse_args(argv)
    policy_path = ROOT / args.policy

    try:
        errors, updated = sync_policy(policy_path, root=ROOT, write=args.write)
        if errors:
            print("LEGACY_MIRRORS_STALE", file=sys.stderr)
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        _print_pair_hashes(policy_path, ROOT)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        print(f"LEGACY_MIRROR_SYNC_ERROR: {exc}", file=sys.stderr)
        return 2

    if args.write:
        print(f"LEGACY_MIRRORS_UPDATED count={updated}")
    else:
        print("LEGACY_MIRRORS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
