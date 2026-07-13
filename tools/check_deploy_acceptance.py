#!/usr/bin/env python3
"""Validate deployed GitHub Pages acceptance evidence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trust_records


SCHEMA_PATH = ROOT / "schemas/deploy-acceptance.schema.json"
REQUIRED_CHECKS = {
    "homepage_http_status",
    "homepage_contains_brand",
    "homepage_has_eight_layer_nav",
    "foundation_catalog_http_status",
}


def _schema_location(error: Any) -> str:
    return ".".join(str(part) for part in error.absolute_path) or "<root>"


def _schema_errors(payload: Mapping[str, Any]) -> list[str]:
    schema = trust_records.load_schema(SCHEMA_PATH)
    return sorted(
        {
            f"SCHEMA:{_schema_location(error)}:{error.validator}"
            for error in Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
            ).iter_errors(payload)
        }
    )


def validate_payload(
    payload: Mapping[str, Any],
    target_sha: str,
) -> list[str]:
    errors = _schema_errors(payload)
    if errors:
        return errors

    if payload["target_sha"] != target_sha:
        errors.append("SEMANTIC:target_sha:mismatch")
    if payload["repository_quality"]["conclusion"] != "success":
        errors.append("SEMANTIC:repository_quality:conclusion-not-success")
    if payload["pages_deploy"]["conclusion"] != "success":
        errors.append("SEMANTIC:pages_deploy:conclusion-not-success")

    names = [check["name"] for check in payload["checks"]]
    if len(names) != len(set(names)):
        errors.append("SEMANTIC:checks:duplicate-name")
    if not REQUIRED_CHECKS <= set(names):
        errors.append("SEMANTIC:checks:missing-required")

    return sorted(set(errors))


def validate_record(path: Path, target_sha: str) -> list[str]:
    try:
        payload = trust_records.load_record(path)
    except trust_records.TrustRecordError as exc:
        return [f"DEPLOY_ACCEPTANCE_{exc.code}"]
    return validate_payload(payload, target_sha)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--target-sha", required=True)
    args = parser.parse_args(argv)

    errors = validate_record(args.file, args.target_sha)
    if errors:
        print("DEPLOY_ACCEPTANCE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"DEPLOY_ACCEPTANCE_OK target_sha={args.target_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
