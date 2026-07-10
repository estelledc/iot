#!/usr/bin/env python3
"""Validate IoT content frontmatter against the versioned JSON Schema."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/content-frontmatter.schema.json"
LAYER_BY_SLUG = {
    "foundation": 1,
    "connectivity": 2,
    "network": 3,
    "computing": 4,
    "intelligence": 5,
    "security": 6,
    "applications": 7,
    "frontier": 8,
}


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    location: str
    message: str

    def render(self) -> str:
        suffix = f"::{self.location}" if self.location else ""
        return f"{self.path}{suffix}: {self.message}"


def _normalize_yaml(value: Any) -> Any:
    """Convert YAML-native timestamps into JSON Schema-compatible strings."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _normalize_yaml(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_yaml(item) for item in value]
    return value


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(payload)
    return payload


def parse_frontmatter(path: Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    relative = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [ValidationIssue(relative, "line 1", "missing opening YAML frontmatter delimiter")]
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None, [ValidationIssue(relative, "line 1", "missing closing YAML frontmatter delimiter")]
    try:
        payload = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        return None, [ValidationIssue(relative, "frontmatter", f"invalid YAML: {exc}")]
    if not isinstance(payload, dict):
        return None, [ValidationIssue(relative, "frontmatter", "frontmatter must be a mapping")]
    return _normalize_yaml(payload), []


def _json_path(parts: list[Any]) -> str:
    return ".".join(str(part) for part in parts)


def validate_payload(
    payload: dict[str, Any],
    path: Path,
    schema: dict[str, Any],
    *,
    semantic_paths: bool,
) -> list[ValidationIssue]:
    relative = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues = [
        ValidationIssue(relative, _json_path(list(error.absolute_path)), error.message)
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    ]
    if not semantic_paths:
        return issues

    try:
        repo_relative = path.relative_to(ROOT)
    except ValueError:
        return issues
    parts = repo_relative.parts
    if len(parts) < 4 or parts[0] != "docs" or parts[2] != "papers":
        issues.append(ValidationIssue(relative, "path", "content file must live under docs/<layer>/papers"))
        return issues
    expected_layer = LAYER_BY_SLUG.get(parts[1])
    if expected_layer is None:
        issues.append(ValidationIssue(relative, "path", f"unknown layer slug: {parts[1]}"))
    elif payload.get("layer") != expected_layer:
        issues.append(
            ValidationIssue(relative, "layer", f"expected layer {expected_layer} from path, got {payload.get('layer')}")
        )
    if payload.get("id") != path.stem:
        issues.append(ValidationIssue(relative, "id", f"expected id {path.stem!r} from filename"))
    return issues


def validate_file(
    path: Path,
    schema: dict[str, Any],
    *,
    semantic_paths: bool = True,
) -> list[ValidationIssue]:
    payload, issues = parse_frontmatter(path)
    if payload is None:
        return issues
    return issues + validate_payload(payload, path, schema, semantic_paths=semantic_paths)


def validate_fixtures(directory: Path, schema: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    fixtures = sorted(directory.glob("*.md"))
    if not fixtures:
        return [ValidationIssue(directory.as_posix(), "", "no frontmatter fixtures found")]
    for fixture in fixtures:
        actual = validate_file(fixture, schema, semantic_paths=False)
        expects_valid = fixture.name.startswith("valid-")
        expects_invalid = fixture.name.startswith("invalid-")
        if not expects_valid and not expects_invalid:
            issues.append(ValidationIssue(fixture.as_posix(), "filename", "fixture must start with valid- or invalid-"))
        elif expects_valid and actual:
            issues.extend(actual)
        elif expects_invalid and not actual:
            issues.append(ValidationIssue(fixture.as_posix(), "fixture", "invalid fixture unexpectedly passed"))
    return issues


def _paper_paths() -> list[Path]:
    return sorted(ROOT.glob("docs/*/papers/*.md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-only", action="store_true", help="validate schema and optional fixtures")
    parser.add_argument(
        "--fixtures",
        nargs="?",
        const="tests/fixtures/frontmatter",
        help="validate valid-/invalid- Markdown fixtures (default: tests/fixtures/frontmatter)",
    )
    parser.add_argument("--all", action="store_true", help="validate all docs/*/papers/*.md")
    parser.add_argument("--path", action="append", default=[], help="validate one repository-relative Markdown file")
    args = parser.parse_args(argv)
    if not args.schema_only and not args.all and not args.path:
        parser.error("use --schema-only, --all, or --path")

    try:
        schema = load_schema()
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"FRONTMATTER_SCHEMA_ERROR: {exc}", file=sys.stderr)
        return 2

    issues: list[ValidationIssue] = []
    checked = 0
    if args.fixtures:
        fixture_dir = (ROOT / args.fixtures).resolve()
        issues.extend(validate_fixtures(fixture_dir, schema))
        checked += len(list(fixture_dir.glob("*.md")))
    paths = _paper_paths() if args.all else [(ROOT / item).resolve() for item in args.path]
    for path in paths:
        if not path.is_file():
            issues.append(ValidationIssue(path.as_posix(), "", "file not found"))
            continue
        issues.extend(validate_file(path, schema))
        checked += 1

    if issues:
        print("FRONTMATTER_INVALID", file=sys.stderr)
        for issue in issues:
            print(f"ERROR: {issue.render()}", file=sys.stderr)
        return 1
    print(f"FRONTMATTER_SCHEMA_OK checked={checked} schema_version={schema['properties']['schema_version']['const']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
