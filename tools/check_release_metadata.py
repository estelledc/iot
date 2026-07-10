#!/usr/bin/env python3
"""Check VERSION, CHANGELOG and review-baseline metadata consistency."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
RELEASE_RE = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\] - (?P<date>\d{4}-\d{2}-\d{2})$", re.MULTILINE)
COMMIT_RE = re.compile(r"\b[0-9a-f]{40}\b")
SHA256_RE = re.compile(r"\b[0-9a-f]{64}\b")
TASK_RE = re.compile(r"\bIOT-T\d{3}\b")
# Split the marker so review-package scanners do not mistake this safety rule
# for a captured machine path in the source archive itself.
LOCAL_USER_PATH_RE = re.compile(r"/U" r"sers/|\\U" r"sers\\")


def validate(version_path: Path, changelog_path: Path) -> list[str]:
    errors: list[str] = []
    if not version_path.is_file():
        return [f"missing version file: {version_path}"]
    if not changelog_path.is_file():
        return [f"missing changelog: {changelog_path}"]

    version = version_path.read_text(encoding="utf-8").strip()
    changelog = changelog_path.read_text(encoding="utf-8")
    if not SEMVER_RE.fullmatch(version):
        errors.append(f"VERSION is not stable SemVer: {version!r}")

    releases = RELEASE_RE.findall(changelog)
    if not releases:
        errors.append("CHANGELOG has no dated release heading")
    elif releases[0][0] != version:
        errors.append(f"VERSION {version} does not match latest CHANGELOG release {releases[0][0]}")

    if not COMMIT_RE.search(changelog):
        errors.append("CHANGELOG has no 40-character review baseline commit")
    if not SHA256_RE.search(changelog):
        errors.append("CHANGELOG has no handoff ZIP SHA-256")
    if not TASK_RE.search(changelog):
        errors.append("CHANGELOG has no IOT-Txxx task reference")
    if LOCAL_USER_PATH_RE.search(changelog):
        errors.append("CHANGELOG contains a local absolute user path")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version-file", default="VERSION")
    parser.add_argument("--changelog", default="CHANGELOG.md")
    args = parser.parse_args(argv)
    version_path = (ROOT / args.version_file).resolve()
    changelog_path = (ROOT / args.changelog).resolve()
    errors = validate(version_path, changelog_path)
    if errors:
        print("RELEASE_METADATA_INVALID", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"RELEASE_METADATA_OK version={version_path.read_text(encoding='utf-8').strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
