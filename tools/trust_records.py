"""Shared, fail-closed validation for immutable trust records.

This module deliberately validates one record at a time.  Cross-record graph
resolution (supersession, linked audits, role projection, and status
projection) belongs to IOT-T044 and is not inferred here.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping
from urllib.parse import urlsplit

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from yaml.constructor import ConstructorError
from yaml.resolver import BaseResolver

from tools.iot_domain import ContentDocument, ContentError, parse_document


ROOT = Path(__file__).resolve().parents[1]
DRAFT_2020_12_URI = "https://json-schema.org/draft/2020-12/schema"

RecordState = Literal["ACTIVE", "STALE", "REVOKED", "INVALID"]

_RFC3339_DATETIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?"
    r"(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
_DNS_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")


def _is_rfc3339_datetime(value: object) -> bool:
    if not isinstance(value, str) or _RFC3339_DATETIME_RE.fullmatch(value) is None:
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _is_https_uri(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if any(
        ord(character) >= 128
        or ord(character) < 0x21
        or ord(character) == 0x7F
        for character in value
    ):
        return False
    if _PERCENT_ESCAPE_RE.search(value):
        return False
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.netloc or hostname is None:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    if port is not None and not 1 <= port <= 65535:
        return False

    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    try:
        ascii_host = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    if len(ascii_host) > 253:
        return False
    if ascii_host.endswith("."):
        ascii_host = ascii_host[:-1]
    return bool(ascii_host) and all(
        _DNS_LABEL_RE.fullmatch(label) is not None
        for label in ascii_host.split(".")
    )


TRUST_FORMAT_CHECKER = FormatChecker()
TRUST_FORMAT_CHECKER.checks("date-time")(_is_rfc3339_datetime)
TRUST_FORMAT_CHECKER.checks("uri")(_is_https_uri)


@dataclass(frozen=True)
class RecordValidity:
    """Current-body validity of one otherwise schema-valid record."""

    state: RecordState
    code: str
    expected_body_sha256: str
    actual_body_sha256: str | None

    @property
    def is_current(self) -> bool:
        return self.state == "ACTIVE"

    @property
    def is_historical(self) -> bool:
        """Whether the record is retained history but excluded from evidence."""

        return self.state == "REVOKED"

    @property
    def lifecycle(self) -> RecordState:
        """Compatibility name used by callers that model record lifecycle."""

        return self.state

    @property
    def status(self) -> RecordState:
        return self.state


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    location: str
    message: str
    code: str

    def render(self) -> str:
        suffix = f"::{self.location}" if self.location else ""
        return f"{self.path}{suffix}: [{self.code}] {self.message}"


class TrustRecordError(ValueError):
    """Stable error boundary for schema and record I/O failures."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate or recursive mappings."""


def _construct_unique_mapping(
    loader: _UniqueKeySafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from None
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found a duplicate mapping key",
                key_node.start_mark,
            ) from None
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _construct_timestamp_as_string(
    loader: _UniqueKeySafeLoader,
    node: yaml.nodes.ScalarNode,
) -> str:
    """Preserve timestamp lexical form for strict RFC3339 validation."""

    return loader.construct_scalar(node)


_UniqueKeySafeLoader.add_constructor(
    "tag:yaml.org,2002:timestamp",
    _construct_timestamp_as_string,
)


def _normalize_yaml(value: Any, active: set[int] | None = None) -> Any:
    if active is None:
        active = set()
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        identity = id(value)
        if identity in active:
            raise ValueError("recursive YAML aliases are not supported")
        active.add(identity)
        try:
            return {key: _normalize_yaml(item, active) for key, item in value.items()}
        finally:
            active.remove(identity)
    if isinstance(value, list):
        identity = id(value)
        if identity in active:
            raise ValueError("recursive YAML aliases are not supported")
        active.add(identity)
        try:
            return [_normalize_yaml(item, active) for item in value]
        finally:
            active.remove(identity)
    return value


def safe_display_path(path: Path, *, repo_root: Path = ROOT) -> str:
    """Render a path without ever disclosing a host absolute path."""

    root = Path(os.path.abspath(repo_root))
    candidate = Path(path)
    if not candidate.is_absolute():
        display = candidate.as_posix()
    else:
        try:
            display = candidate.relative_to(root).as_posix()
        except ValueError:
            return "<outside-repository>"
    return "".join(
        character
        if character.isprintable()
        else f"\\u{ord(character):04x}"
        for character in display
    )


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError("duplicate JSON object key")
        payload[key] = value
    return payload


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON number")


def load_schema(path: Path) -> dict[str, Any]:
    """Load and meta-validate a Draft 2020-12 schema."""

    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise TrustRecordError("SCHEMA_READ_ERROR", "schema could not be read") from None
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise TrustRecordError("SCHEMA_PARSE_ERROR", "schema must be valid UTF-8 JSON") from None
    if not isinstance(payload, dict):
        raise TrustRecordError("SCHEMA_NOT_OBJECT", "schema must be a JSON object")
    if payload.get("$schema") != DRAFT_2020_12_URI:
        raise TrustRecordError(
            "SCHEMA_DIALECT_MISMATCH",
            "schema must explicitly declare JSON Schema Draft 2020-12",
        )
    try:
        Draft202012Validator.check_schema(payload)
    except SchemaError:
        raise TrustRecordError("SCHEMA_INVALID", "schema is not valid Draft 2020-12") from None
    return payload


def load_record(path: Path) -> dict[str, Any]:
    """Read one YAML record from bytes without path-bearing parser errors."""

    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise TrustRecordError("RECORD_READ_ERROR", "record could not be read") from None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise TrustRecordError("RECORD_INVALID_UTF8", "record must be valid UTF-8") from None
    try:
        payload = yaml.load(text, Loader=_UniqueKeySafeLoader)
        payload = _normalize_yaml(payload)
    except (yaml.YAMLError, ValueError):
        raise TrustRecordError("RECORD_INVALID_YAML", "record must be valid unambiguous YAML") from None
    if not isinstance(payload, dict):
        raise TrustRecordError("RECORD_NOT_MAPPING", "record must be a YAML mapping")
    return payload


def record_validity(
    record: Mapping[str, Any],
    document: ContentDocument,
) -> RecordValidity:
    """Classify one record against its canonical document.

    Identity is checked first because revocation cannot legitimize a record
    bound to the wrong content.  Revocation is then checked before body
    staleness: correctly bound revoked history stays revoked when the body later
    changes.  Schema validity is a caller responsibility.
    """

    expected = document.body_sha256
    declared = record.get("body_sha256")
    actual = declared if isinstance(declared, str) else None

    if record.get("content_id") != document.content_id:
        return RecordValidity("INVALID", "CONTENT_ID_MISMATCH", expected, actual)
    if record.get("content_path") != document.repo_relative_path:
        return RecordValidity("INVALID", "CONTENT_PATH_MISMATCH", expected, actual)
    if record.get("revocation") is not None:
        return RecordValidity("REVOKED", "REVOKED", expected, actual)
    if actual != expected:
        return RecordValidity("STALE", "BODY_HASH_MISMATCH", expected, actual)
    return RecordValidity("ACTIVE", "RECORD_CURRENT", expected, actual)


def _json_path(parts: Iterable[Any]) -> str:
    return ".".join(str(part) for part in parts)


def _schema_issues(
    payload: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    display: str,
) -> list[ValidationIssue]:
    validator = Draft202012Validator(schema, format_checker=TRUST_FORMAT_CHECKER)
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            str(error.validator),
        ),
    )
    return [
        ValidationIssue(
            display,
            _json_path(error.absolute_path),
            f"record does not satisfy schema rule {error.validator!r}",
            "SCHEMA_VALIDATION_FAILED",
        )
        for error in errors
    ]


def _safe_content_candidate(
    value: Any,
    *,
    repo_root: Path,
    display: str,
) -> tuple[Path | None, list[ValidationIssue]]:
    if not isinstance(value, str):
        return None, [
            ValidationIssue(
                display,
                "content_path",
                "content_path must be a repository-relative string",
                "INVALID_CONTENT_PATH",
            )
        ]
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or value != relative.as_posix():
        return None, [
            ValidationIssue(
                display,
                "content_path",
                "content_path must be a safe repository-relative canonical path",
                "INVALID_CONTENT_PATH",
            )
        ]
    root = Path(os.path.abspath(repo_root))
    candidate = Path(os.path.abspath(root / relative))
    try:
        lexical_relative = candidate.relative_to(root)
        resolved_root = root.resolve()
        resolved_candidate = candidate.resolve(strict=False)
        resolved_relative = resolved_candidate.relative_to(resolved_root)
    except (ValueError, OSError, RuntimeError):
        return None, [
            ValidationIssue(
                display,
                "content_path",
                "content_path cannot be resolved safely",
                "INVALID_CONTENT_PATH",
            )
        ]
    if lexical_relative != resolved_relative:
        return None, [
            ValidationIssue(
                display,
                "content_path",
                "content_path must not traverse symlinks",
                "INVALID_CONTENT_PATH",
            )
        ]
    return candidate, []


def validate_record_payload(
    payload: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    record_path: Path,
    repo_root: Path = ROOT,
) -> tuple[RecordValidity | None, list[ValidationIssue]]:
    """Validate schema, canonical identity, and current body binding."""

    display = safe_display_path(record_path, repo_root=repo_root)
    issues = _schema_issues(payload, schema, display=display)
    if issues:
        return None, issues

    content_path, path_issues = _safe_content_candidate(
        payload.get("content_path"),
        repo_root=repo_root,
        display=display,
    )
    if path_issues:
        return None, path_issues
    assert content_path is not None

    try:
        document = parse_document(content_path, repo_root=repo_root)
    except ContentError as exc:
        issue = exc.issue
        return None, [
            ValidationIssue(
                display,
                "content_path",
                "canonical content failed strict validation",
                issue.code,
            )
        ]
    except OSError:
        return None, [
            ValidationIssue(
                display,
                "content_path",
                "canonical content could not be read",
                "CONTENT_READ_ERROR",
            )
        ]

    validity = record_validity(payload, document)
    if validity.state == "ACTIVE" or validity.state == "REVOKED":
        return validity, []
    if validity.code == "BODY_HASH_MISMATCH":
        return validity, [
            ValidationIssue(
                display,
                "body_sha256",
                (
                    "body hash does not match current canonical content "
                    f"content_id={payload.get('content_id')} "
                    f"record_path={display} "
                    f"(expected={validity.expected_body_sha256} "
                    f"actual={validity.actual_body_sha256})"
                ),
                validity.code,
            )
        ]
    location = "content_id" if validity.code == "CONTENT_ID_MISMATCH" else "content_path"
    return validity, [
        ValidationIssue(
            display,
            location,
            "record identity does not match canonical content",
            validity.code,
        )
    ]


def validate_record_file(
    path: Path,
    schema: Mapping[str, Any],
    *,
    repo_root: Path = ROOT,
    record_root: Path | None = None,
) -> list[ValidationIssue]:
    display = safe_display_path(path, repo_root=repo_root)
    candidate, path_issue = _resolve_repository_candidate(
        path,
        repo_root=repo_root,
        allowed_root=record_root,
        display=display,
        code="UNSAFE_RECORD_PATH",
    )
    if path_issue is not None:
        return [path_issue]
    assert candidate is not None
    try:
        payload = load_record(candidate)
    except TrustRecordError as exc:
        return [ValidationIssue(display, "", exc.message, exc.code)]
    _, issues = validate_record_payload(
        payload,
        schema,
        record_path=candidate,
        repo_root=repo_root,
    )
    return issues


def _resolve_repository_candidate(
    path: Path,
    *,
    repo_root: Path,
    allowed_root: Path | None,
    display: str,
    code: str,
) -> tuple[Path | None, ValidationIssue | None]:
    root = Path(os.path.abspath(repo_root))
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = Path(os.path.abspath(candidate))
    try:
        lexical_relative = candidate.relative_to(root)
        resolved_root = root.resolve()
        resolved_candidate = candidate.resolve(strict=False)
        resolved_relative = resolved_candidate.relative_to(resolved_root)
    except (ValueError, OSError, RuntimeError):
        return None, ValidationIssue(
            display,
            "path",
            "record path cannot be resolved safely inside the repository",
            code,
        )
    if lexical_relative != resolved_relative:
        return None, ValidationIssue(
            display,
            "path",
            "record path must not traverse symlinks",
            code,
        )

    if allowed_root is not None:
        allowed = Path(allowed_root)
        if not allowed.is_absolute():
            allowed = root / allowed
        allowed = Path(os.path.abspath(allowed))
        try:
            candidate.relative_to(allowed)
            allowed_relative = allowed.relative_to(root)
            resolved_allowed = allowed.resolve(strict=False)
            resolved_allowed_relative = resolved_allowed.relative_to(resolved_root)
        except (ValueError, OSError, RuntimeError):
            allowed_display = safe_display_path(allowed, repo_root=root)
            return None, ValidationIssue(
                display,
                "path",
                f"record path must stay under {allowed_display}",
                code,
            )
        if allowed_relative != resolved_allowed_relative:
            return None, ValidationIssue(
                display,
                "path",
                "record root must not traverse symlinks",
                code,
            )
    return candidate, None


def resolve_cli_path(
    value: str,
    *,
    repo_root: Path = ROOT,
    record_root: Path | None = None,
) -> tuple[Path | None, ValidationIssue | None]:
    """Resolve one CLI path while rejecting absolute/traversal/symlink paths."""

    raw = Path(value)
    display = (
        safe_display_path(raw, repo_root=repo_root)
        if not raw.is_absolute()
        else "<absolute-path>"
    )
    if raw.is_absolute() or ".." in raw.parts:
        return None, ValidationIssue(
            display,
            "path",
            "--path must be repository-relative and must not contain '..'",
            "UNSAFE_RECORD_PATH",
        )
    return _resolve_repository_candidate(
        raw,
        repo_root=repo_root,
        allowed_root=record_root,
        display=display,
        code="UNSAFE_RECORD_PATH",
    )


def iter_record_paths(record_root: Path) -> list[Path]:
    if not record_root.is_dir():
        return []
    paths: list[Path] = []
    for path in record_root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("record directory contains a symlink")
        if path.is_file() and path.suffix == ".yml":
            paths.append(path)
    return sorted(paths, key=lambda path: path.as_posix())


def run_validator_cli(
    argv: list[str] | None,
    *,
    description: str,
    repo_root: Path,
    schema_path: Path,
    record_root: Path,
    all_help: str,
    schema_error_marker: str,
    invalid_marker: str,
    ok_marker: str,
) -> int:
    """Run the common source/review single-record validator CLI."""

    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).name,
        description=description,
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true", help=all_help)
    selection.add_argument(
        "--path",
        action="append",
        help="validate one safe repository-relative YAML file",
    )
    args = parser.parse_args(argv)

    safe_schema_path, schema_path_issue = _resolve_repository_candidate(
        schema_path,
        repo_root=repo_root,
        allowed_root=Path(repo_root) / "schemas",
        display="schemas/<trust-record-schema>.json",
        code="UNSAFE_SCHEMA_PATH",
    )
    if schema_path_issue is not None:
        print(
            f"{schema_error_marker} [{schema_path_issue.code}]: schema path is unsafe",
            file=sys.stderr,
        )
        return 2
    assert safe_schema_path is not None
    try:
        schema = load_schema(safe_schema_path)
    except TrustRecordError as exc:
        print(f"{schema_error_marker} [{exc.code}]: {exc.message}", file=sys.stderr)
        return 2

    issues: list[ValidationIssue] = []
    paths: list[Path] = []
    if args.all:
        _, root_issue = _resolve_repository_candidate(
            record_root,
            repo_root=repo_root,
            allowed_root=record_root,
            display=safe_display_path(record_root, repo_root=repo_root),
            code="UNSAFE_RECORD_ROOT",
        )
        if root_issue is not None:
            issues.append(root_issue)
        else:
            try:
                record_root_mode = os.stat(
                    record_root,
                    follow_symlinks=False,
                ).st_mode
            except FileNotFoundError:
                record_root_mode = None
            except (OSError, RuntimeError):
                print(
                    "RECORD_ENUMERATION_ERROR: record directory could not be enumerated",
                    file=sys.stderr,
                )
                return 2
            if record_root_mode is not None and not stat.S_ISDIR(record_root_mode):
                print(
                    "RECORD_ROOT_NOT_DIRECTORY: record root must be a directory",
                    file=sys.stderr,
                )
                return 2
            if record_root_mode is not None:
                try:
                    paths.extend(iter_record_paths(record_root))
                except (OSError, RuntimeError):
                    print(
                        "RECORD_ENUMERATION_ERROR: record directory could not be enumerated",
                        file=sys.stderr,
                    )
                    return 2

    for value in sorted(set(args.path or [])):
        path, issue = resolve_cli_path(
            value,
            repo_root=repo_root,
            record_root=record_root,
        )
        if issue is not None:
            issues.append(issue)
        else:
            assert path is not None
            paths.append(path)

    paths = sorted(
        set(paths),
        key=lambda path: safe_display_path(path, repo_root=repo_root),
    )
    checked = 0
    for path in paths:
        try:
            is_file = path.is_file()
        except (OSError, RuntimeError):
            is_file = False
        if not is_file:
            issues.append(
                ValidationIssue(
                    safe_display_path(path, repo_root=repo_root),
                    "",
                    "record file not found",
                    "RECORD_FILE_NOT_FOUND",
                )
            )
            continue
        issues.extend(
            validate_record_file(
                path,
                schema,
                repo_root=repo_root,
                record_root=record_root,
            )
        )
        checked += 1

    if issues:
        print(invalid_marker, file=sys.stderr)
        for issue in issues:
            print(f"ERROR: {issue.render()}", file=sys.stderr)
        return 1
    print(f"{ok_marker} checked={checked}")
    return 0
