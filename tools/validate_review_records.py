#!/usr/bin/env python3
"""Validate review records against canonical content."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trust_records


def load_schema(path: Path | None = None) -> dict[str, Any]:
    selected = ROOT / "schemas/review-record.schema.json" if path is None else path
    return trust_records.load_schema(selected)


def validate_file(
    path: Path,
    schema: dict[str, Any],
) -> list[trust_records.ValidationIssue]:
    return trust_records.validate_record_file(
        path,
        schema,
        repo_root=ROOT,
        record_root=ROOT / "data/review-records",
    )


def main(argv: list[str] | None = None) -> int:
    record_root = ROOT / "data/review-records"
    return trust_records.run_validator_cli(
        argv,
        description=__doc__ or "Validate review records",
        repo_root=ROOT,
        schema_path=ROOT / "schemas/review-record.schema.json",
        record_root=record_root,
        all_help="validate all data/review-records/**/*.yml",
        schema_error_marker="REVIEW_RECORD_SCHEMA_ERROR",
        invalid_marker="REVIEW_RECORDS_INVALID",
        ok_marker="REVIEW_RECORDS_OK",
    )


if __name__ == "__main__":
    raise SystemExit(main())
