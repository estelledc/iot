"""Fail-closed single-record and repository trust-graph primitives.

Single-record callers retain schema, identity, and body-hash validation.  The
repository validator additionally consumes the graph functions here to resolve
supersession, linked evidence, authority-backed roles, and status projections.
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
from typing import Any, Iterable, Literal, Mapping, Sequence
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


@dataclass(frozen=True)
class TrustProjection:
    """Derived trust cache for one canonical content document."""

    content_id: str
    content_path: str
    body_sha256: str
    source_status: str
    review_status: str
    active_audit_ids: tuple[str, ...]
    active_review_ids: tuple[str, ...]


@dataclass(frozen=True)
class TrustGraphResult:
    """Fail-closed result of validating all records as one graph."""

    projections: Mapping[str, TrustProjection]
    issues: list[ValidationIssue]


@dataclass(frozen=True)
class ActorAuthority:
    """One actor identity and the roles granted by repository authority."""

    actor_id: str
    actor_type: Literal["HUMAN", "AGENT"]
    allowed_roles: frozenset[str]


@dataclass(frozen=True)
class _GraphRecord:
    kind: Literal["source", "review"]
    record_id: str
    path: Path
    display_path: str
    payload: Mapping[str, Any]
    timestamp: datetime

    @property
    def content_id(self) -> str:
        return str(self.payload.get("content_id", ""))

    @property
    def supersedes(self) -> str | None:
        value = self.payload.get("supersedes")
        return value if isinstance(value, str) else None


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


def _record_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not _is_rfc3339_datetime(value):
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def _graph_issue(
    record: _GraphRecord,
    code: str,
    message: str,
    location: str = "",
) -> ValidationIssue:
    return ValidationIssue(record.display_path, location, message, code)


def _actor_authority_issues(
    record: _GraphRecord,
    *,
    actor_id: object,
    declared_type: object | None,
    required_role: object,
    actor_authorities: Mapping[str, ActorAuthority] | None,
    location: str,
) -> list[ValidationIssue]:
    """Resolve one claimed actor against authority instead of trusting the record."""

    if not isinstance(actor_id, str):
        return [
            _graph_issue(
                record,
                "ACTOR_AUTHORITY_MISSING",
                "record actor does not resolve to repository authority",
                location,
            )
        ]
    authority = (
        actor_authorities.get(actor_id)
        if actor_authorities is not None
        else None
    )
    if authority is None:
        return [
            _graph_issue(
                record,
                "ACTOR_AUTHORITY_MISSING",
                "record actor does not resolve to repository authority",
                location,
            )
        ]

    issues: list[ValidationIssue] = []
    if not authority.actor_id.startswith(authority.actor_type.lower() + "-"):
        issues.append(
            _graph_issue(
                record,
                "ACTOR_AUTHORITY_ID_TYPE_MISMATCH",
                "authoritative actor id namespace does not match actor type",
                location,
            )
        )
    if isinstance(declared_type, str) and declared_type != authority.actor_type:
        issues.append(
            _graph_issue(
                record,
                "ACTOR_AUTHORITY_TYPE_MISMATCH",
                "record actor type does not match repository authority",
                location,
            )
        )
    if not isinstance(required_role, str) or required_role not in authority.allowed_roles:
        issues.append(
            _graph_issue(
                record,
                "ACTOR_ROLE_NOT_ALLOWED",
                "record actor is not authorized for the required role",
                location,
            )
        )
    return issues


def _author_actor_issues(
    record: _GraphRecord,
    *,
    author_ids: frozenset[str],
    actor_authorities: Mapping[str, ActorAuthority] | None,
    location: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for author_id in sorted(author_ids):
        issues.extend(
            _actor_authority_issues(
                record,
                actor_id=author_id,
                declared_type=None,
                required_role="CONTENT_AUTHOR",
                actor_authorities=actor_authorities,
                location=location,
            )
        )
    return issues


def _sorted_unique_issues(issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
    unique: dict[tuple[str, str, str, str], ValidationIssue] = {}
    for issue in issues:
        unique[(issue.path, issue.location, issue.code, issue.message)] = issue
    return list(
        sorted(
            unique.values(),
            key=lambda issue: (issue.path, issue.location, issue.code, issue.message),
        )
    )


def _collect_graph_records(
    entries: Sequence[tuple[Path, Mapping[str, Any]]],
    *,
    kind: Literal["source", "review"],
    documents_by_id: Mapping[str, ContentDocument],
    repo_root: Path,
    as_of: datetime | None,
) -> tuple[dict[str, _GraphRecord], list[ValidationIssue], set[str]]:
    id_key = "audit_id" if kind == "source" else "review_id"
    timestamp_key = "audited_at" if kind == "source" else "reviewed_at"
    duplicate_code = "DUPLICATE_AUDIT_ID" if kind == "source" else "DUPLICATE_REVIEW_ID"
    registry: dict[str, _GraphRecord] = {}
    issues: list[ValidationIssue] = []
    invalid_ids: set[str] = set()

    for path, payload in sorted(
        entries,
        key=lambda item: safe_display_path(item[0], repo_root=repo_root),
    ):
        display = safe_display_path(path, repo_root=repo_root)
        record_id = payload.get(id_key)
        if not isinstance(record_id, str) or not record_id:
            issues.append(
                ValidationIssue(
                    display,
                    id_key,
                    "record id is missing or invalid",
                    "RECORD_GRAPH_SHAPE_INVALID",
                )
            )
            continue
        timestamp = _record_datetime(payload.get(timestamp_key))
        if timestamp is None:
            issues.append(
                ValidationIssue(
                    display,
                    timestamp_key,
                    "record timestamp must be RFC3339 with an offset",
                    "INVALID_RECORD_TIMESTAMP",
                )
            )
            invalid_ids.add(record_id)
            continue
        record = _GraphRecord(kind, record_id, Path(path), display, payload, timestamp)
        if record_id in registry:
            issues.append(
                _graph_issue(
                    record,
                    duplicate_code,
                    f"{kind} record id must be globally unique",
                    id_key,
                )
            )
            invalid_ids.add(record_id)
            continue
        registry[record_id] = record

        document = documents_by_id.get(record.content_id)
        if document is None:
            issues.append(
                _graph_issue(
                    record,
                    "UNKNOWN_CONTENT_ID",
                    "record content_id does not resolve to canonical content",
                    "content_id",
                )
            )
            invalid_ids.add(record_id)
            continue
        if payload.get("content_path") != document.repo_relative_path:
            issues.append(
                _graph_issue(
                    record,
                    "CONTENT_PATH_MISMATCH",
                    "record content_path does not match canonical identity",
                    "content_path",
                )
            )
            invalid_ids.add(record_id)
        if (
            payload.get("body_sha256") != document.body_sha256
            and payload.get("revocation") is None
        ):
            issues.append(
                _graph_issue(
                    record,
                    "BODY_HASH_MISMATCH",
                    "record body hash does not match current canonical content",
                    "body_sha256",
                )
            )
            invalid_ids.add(record_id)
        if as_of is not None and timestamp > as_of:
            issues.append(
                _graph_issue(
                    record,
                    "RECORD_TIME_IN_FUTURE",
                    "record timestamp is later than the validation boundary",
                    timestamp_key,
                )
            )
            invalid_ids.add(record_id)

    return registry, issues, invalid_ids


def _source_semantic_issues(
    record: _GraphRecord,
    *,
    actor_authorities: Mapping[str, ActorAuthority] | None,
    author_ids_by_content: Mapping[str, frozenset[str]] | None,
    critical_claim_ids_by_content: Mapping[str, frozenset[str]] | None,
    as_of: datetime | None,
) -> list[ValidationIssue]:
    payload = record.payload
    issues: list[ValidationIssue] = []
    auditor_id = payload.get("auditor_id")
    auditor_type = payload.get("auditor_type")
    if isinstance(auditor_id, str) and isinstance(auditor_type, str):
        if not auditor_id.startswith(auditor_type.lower() + "-"):
            issues.append(
                _graph_issue(
                    record,
                    "AUDITOR_ID_TYPE_MISMATCH",
                    "auditor id namespace does not match auditor_type",
                    "auditor_id",
                )
            )

    reference_ids: list[str] = []
    for index, reference in enumerate(payload.get("source_references", [])):
        if not isinstance(reference, Mapping):
            continue
        reference_id = reference.get("reference_id")
        if isinstance(reference_id, str):
            reference_ids.append(reference_id)
        retrieved_at = _record_datetime(reference.get("retrieved_at"))
        if retrieved_at is not None and retrieved_at > record.timestamp:
            issues.append(
                _graph_issue(
                    record,
                    "SOURCE_REFERENCE_TIME_ORDER",
                    "source evidence was retrieved after the audit",
                    f"source_references.{index}.retrieved_at",
                )
            )
        if as_of is not None and retrieved_at is not None and retrieved_at > as_of:
            issues.append(
                _graph_issue(
                    record,
                    "RECORD_TIME_IN_FUTURE",
                    "source evidence is later than the validation boundary",
                    f"source_references.{index}.retrieved_at",
                )
            )
    if len(reference_ids) != len(set(reference_ids)):
        issues.append(
            _graph_issue(
                record,
                "DUPLICATE_SOURCE_REFERENCE_ID",
                "source reference ids must be unique within one audit",
                "source_references",
            )
        )

    revocation = payload.get("revocation")
    if isinstance(revocation, Mapping):
        issues.extend(
            _actor_authority_issues(
                record,
                actor_id=revocation.get("by_actor_id"),
                declared_type=revocation.get("by_actor_type"),
                required_role=revocation.get("by_role"),
                actor_authorities=actor_authorities,
                location="revocation.by_actor_id",
            )
        )
        revoked_at = _record_datetime(revocation.get("revoked_at"))
        if revoked_at is not None and revoked_at < record.timestamp:
            issues.append(
                _graph_issue(
                    record,
                    "REVOCATION_TIME_ORDER",
                    "audit revocation predates the audit",
                    "revocation.revoked_at",
                )
            )
        if as_of is not None and revoked_at is not None and revoked_at > as_of:
            issues.append(
                _graph_issue(
                    record,
                    "RECORD_TIME_IN_FUTURE",
                    "audit revocation is later than the validation boundary",
                    "revocation.revoked_at",
                )
            )

    coverage = payload.get("claim_coverage")
    covered_ids: list[str] = []
    uncovered_ids: set[str] = set()
    if isinstance(coverage, Mapping):
        claims = coverage.get("claims", [])
        for index, claim in enumerate(claims if isinstance(claims, list) else []):
            if not isinstance(claim, Mapping):
                continue
            claim_id = claim.get("claim_id")
            if isinstance(claim_id, str):
                covered_ids.append(claim_id)
            dangling = set(claim.get("reference_ids", [])) - set(reference_ids)
            if dangling:
                issues.append(
                    _graph_issue(
                        record,
                        "CLAIM_REFERENCE_NOT_FOUND",
                        "claim links an unknown source reference",
                        f"claim_coverage.claims.{index}.reference_ids",
                    )
                )
        uncovered = coverage.get("uncovered_claim_ids", [])
        if isinstance(uncovered, list):
            uncovered_ids = {item for item in uncovered if isinstance(item, str)}
        if len(covered_ids) != len(set(covered_ids)):
            issues.append(
                _graph_issue(
                    record,
                    "DUPLICATE_CLAIM_ID",
                    "claim ids must be unique within one audit",
                    "claim_coverage.claims",
                )
            )
        if set(covered_ids) & uncovered_ids:
            issues.append(
                _graph_issue(
                    record,
                    "CLAIM_SET_OVERLAP",
                    "covered and uncovered claim ids must be disjoint",
                    "claim_coverage",
                )
            )

    if revocation is not None:
        return issues

    issues.extend(
        _actor_authority_issues(
            record,
            actor_id=auditor_id,
            declared_type=auditor_type,
            required_role=payload.get("auditor_role"),
            actor_authorities=actor_authorities,
            location="auditor_id",
        )
    )

    transition = payload.get("status_transition")
    target = transition.get("to") if isinstance(transition, Mapping) else None
    promotes_source = (
        payload.get("audit_kind") == "CLAIM_VERIFICATION"
        and target in {"PARTIAL", "VERIFIED"}
    )
    if promotes_source:
        authors = (
            author_ids_by_content.get(record.content_id)
            if author_ids_by_content is not None
            else None
        )
        critical_claims = (
            critical_claim_ids_by_content.get(record.content_id)
            if critical_claim_ids_by_content is not None
            else None
        )
        if not authors:
            issues.append(
                _graph_issue(
                    record,
                    "AUTHOR_AUTHORITY_MISSING",
                    "source promotion requires an authoritative author mapping",
                    "auditor_id",
                )
            )
        else:
            issues.extend(
                _author_actor_issues(
                    record,
                    author_ids=authors,
                    actor_authorities=actor_authorities,
                    location="content_author_ids",
                )
            )
            if payload.get("auditor_role") == "FACT_AUDITOR" and auditor_id in authors:
                issues.append(
                    _graph_issue(
                        record,
                        "AUTHOR_AUDITOR_CONFLICT",
                        "content author and fact auditor must be independent",
                        "auditor_id",
                    )
                )
        if critical_claims is None:
            issues.append(
                _graph_issue(
                    record,
                    "CRITICAL_CLAIM_AUTHORITY_MISSING",
                    "source promotion requires a locked critical-claim inventory",
                    "claim_coverage",
                )
            )
        elif set(covered_ids) | uncovered_ids != set(critical_claims):
            issues.append(
                _graph_issue(
                    record,
                    "CRITICAL_CLAIM_SET_MISMATCH",
                    "audit claim coverage does not match the locked inventory",
                    "claim_coverage",
                )
            )
    return issues


def _review_basic_issues(
    record: _GraphRecord,
    *,
    actor_authorities: Mapping[str, ActorAuthority] | None,
    author_ids_by_content: Mapping[str, frozenset[str]] | None,
    as_of: datetime | None,
) -> list[ValidationIssue]:
    payload = record.payload
    issues: list[ValidationIssue] = []
    reviewer_id = payload.get("reviewer_id")
    reviewer_type = payload.get("reviewer_type")
    if isinstance(reviewer_id, str) and isinstance(reviewer_type, str):
        if not reviewer_id.startswith(reviewer_type.lower() + "-"):
            issues.append(
                _graph_issue(
                    record,
                    "REVIEWER_ID_TYPE_MISMATCH",
                    "reviewer id namespace does not match reviewer_type",
                    "reviewer_id",
                )
            )

    revocation = payload.get("revocation")
    if isinstance(revocation, Mapping):
        issues.extend(
            _actor_authority_issues(
                record,
                actor_id=revocation.get("by_actor_id"),
                declared_type=revocation.get("by_actor_type"),
                required_role=revocation.get("by_role"),
                actor_authorities=actor_authorities,
                location="revocation.by_actor_id",
            )
        )
        revoked_at = _record_datetime(revocation.get("revoked_at"))
        if revoked_at is not None and revoked_at < record.timestamp:
            issues.append(
                _graph_issue(
                    record,
                    "REVOCATION_TIME_ORDER",
                    "review revocation predates the review",
                    "revocation.revoked_at",
                )
            )
        if as_of is not None and revoked_at is not None and revoked_at > as_of:
            issues.append(
                _graph_issue(
                    record,
                    "RECORD_TIME_IN_FUTURE",
                    "review revocation is later than the validation boundary",
                    "revocation.revoked_at",
                )
            )
        return issues
    issues.extend(
        _actor_authority_issues(
            record,
            actor_id=reviewer_id,
            declared_type=reviewer_type,
            required_role=payload.get("reviewer_role"),
            actor_authorities=actor_authorities,
            location="reviewer_id",
        )
    )
    authors = (
        author_ids_by_content.get(record.content_id)
        if author_ids_by_content is not None
        else None
    )
    if not authors:
        issues.append(
            _graph_issue(
                record,
                "AUTHOR_AUTHORITY_MISSING",
                "review evidence requires an authoritative author mapping",
                "independence.author_ids",
            )
        )
        return issues
    issues.extend(
        _author_actor_issues(
            record,
            author_ids=authors,
            actor_authorities=actor_authorities,
            location="independence.author_ids",
        )
    )
    independence = payload.get("independence")
    declared_authors = (
        set(independence.get("author_ids", []))
        if isinstance(independence, Mapping)
        else set()
    )
    if declared_authors != set(authors):
        issues.append(
            _graph_issue(
                record,
                "AUTHOR_SET_MISMATCH",
                "declared authors do not match the authoritative mapping",
                "independence.author_ids",
            )
        )
    reviewer_is_author = reviewer_id in authors
    if reviewer_is_author:
        issues.append(
            _graph_issue(
                record,
                "REVIEWER_AUTHOR_CONFLICT",
                "reviewer must be independent from content authors",
                "reviewer_id",
            )
        )
    if (
        isinstance(independence, Mapping)
        and independence.get("reviewer_is_author") != reviewer_is_author
    ):
        issues.append(
            _graph_issue(
                record,
                "INDEPENDENCE_DECLARATION_MISMATCH",
                "reviewer_is_author does not match computed roles",
                "independence.reviewer_is_author",
            )
        )
    return issues


def _build_supersession_edges(
    registry: Mapping[str, _GraphRecord],
    *,
    invalid_ids: set[str],
) -> tuple[dict[str, str], list[ValidationIssue], set[str]]:
    edges: dict[str, str] = {}
    issues: list[ValidationIssue] = []
    invalid = set(invalid_ids)

    for record_id, record in sorted(registry.items()):
        predecessor_id = record.supersedes
        if predecessor_id is None:
            if (
                record.kind == "source"
                and record.payload.get("audit_kind") == "STRUCTURAL"
            ):
                continue
            transition = record.payload.get("status_transition")
            source = transition.get("from") if isinstance(transition, Mapping) else None
            allowed_roots = (
                {"UNKNOWN", "UNVERIFIED"}
                if record.kind == "source"
                else {"UNKNOWN", "UNREVIEWED"}
            )
            if source not in allowed_roots:
                issues.append(
                    _graph_issue(
                        record,
                        "SUPERSEDES_REQUIRED",
                        "non-initial transition requires a valid predecessor",
                        "supersedes",
                    )
                )
                invalid.add(record_id)
            continue
        predecessor = registry.get(predecessor_id)
        edge_issues: list[ValidationIssue] = []
        if predecessor_id == record_id:
            edge_issues.append(
                _graph_issue(
                    record,
                    "SUPERSEDES_CYCLE",
                    "record cannot supersede itself",
                    "supersedes",
                )
            )
        elif predecessor is None:
            edge_issues.append(
                _graph_issue(
                    record,
                    "SUPERSEDES_TARGET_NOT_FOUND",
                    "supersedes target does not resolve",
                    "supersedes",
                )
            )
        else:
            identity_fields = ("content_id", "content_path", "body_sha256")
            if any(record.payload.get(field) != predecessor.payload.get(field) for field in identity_fields):
                edge_issues.append(
                    _graph_issue(
                        record,
                        "SUPERSEDES_IDENTITY_MISMATCH",
                        "supersession must preserve canonical identity and body hash",
                        "supersedes",
                    )
                )
            if record.kind == "source" and record.payload.get("audit_kind") != predecessor.payload.get("audit_kind"):
                edge_issues.append(
                    _graph_issue(
                        record,
                        "SUPERSEDES_KIND_MISMATCH",
                        "source supersession must preserve audit_kind",
                        "supersedes",
                    )
                )
            if predecessor.timestamp > record.timestamp:
                edge_issues.append(
                    _graph_issue(
                        record,
                        "SUPERSEDES_TIME_ORDER",
                        "successor timestamp predates its predecessor",
                        "supersedes",
                    )
                )
            if (
                predecessor.payload.get("revocation") is not None
                and record.payload.get("revocation") is None
            ):
                edge_issues.append(
                    _graph_issue(
                        record,
                        "SUPERSEDES_PREDECESSOR_REVOKED",
                        "successor cannot depend on a revoked predecessor",
                        "supersedes",
                    )
                )
            predecessor_transition = predecessor.payload.get("status_transition")
            successor_transition = record.payload.get("status_transition")
            predecessor_target = (
                predecessor_transition.get("to")
                if isinstance(predecessor_transition, Mapping)
                else None
            )
            successor_source = (
                successor_transition.get("from")
                if isinstance(successor_transition, Mapping)
                else None
            )
            if predecessor_target != successor_source:
                edge_issues.append(
                    _graph_issue(
                        record,
                        "TRANSITION_PREDECESSOR_MISMATCH",
                        "successor transition must continue from predecessor target",
                        "status_transition.from",
                    )
                )
        if edge_issues:
            issues.extend(edge_issues)
            invalid.add(record_id)
            continue
        assert predecessor is not None
        edges[record_id] = predecessor_id

    successors_by_predecessor: dict[str, list[str]] = {}
    for successor_id, predecessor_id in edges.items():
        successors_by_predecessor.setdefault(predecessor_id, []).append(successor_id)
    for successor_ids in successors_by_predecessor.values():
        if len(successor_ids) <= 1:
            continue
        for successor_id in sorted(successor_ids):
            record = registry[successor_id]
            issues.append(
                _graph_issue(
                    record,
                    "SUPERSEDES_FORK",
                    "one predecessor cannot have multiple successors",
                    "supersedes",
                )
            )
            invalid.add(successor_id)

    cycle_ids: set[str] = set()
    for start in sorted(edges):
        chain: list[str] = []
        positions: dict[str, int] = {}
        current: str | None = start
        while current is not None and current in edges:
            if current in positions:
                cycle_ids.update(chain[positions[current] :])
                break
            positions[current] = len(chain)
            chain.append(current)
            current = edges.get(current)
    for record_id in sorted(cycle_ids):
        record = registry[record_id]
        issues.append(
            _graph_issue(
                record,
                "SUPERSEDES_CYCLE",
                "supersession graph must be acyclic",
                "supersedes",
            )
        )
    invalid.update(cycle_ids)
    valid_edges, dependency_issues, invalid = _prune_invalid_dependencies(
        registry,
        edges,
        invalid_ids=invalid,
    )
    issues.extend(dependency_issues)
    return valid_edges, issues, invalid


def _prune_invalid_dependencies(
    registry: Mapping[str, _GraphRecord],
    edges: Mapping[str, str],
    *,
    invalid_ids: set[str],
) -> tuple[dict[str, str], list[ValidationIssue], set[str]]:
    """Invalidate every successor whose transition depends on invalid history."""

    invalid = set(invalid_ids)
    issues: list[ValidationIssue] = []
    changed = True
    while changed:
        changed = False
        for successor_id, predecessor_id in sorted(edges.items()):
            if successor_id in invalid or predecessor_id not in invalid:
                continue
            record = registry[successor_id]
            issues.append(
                _graph_issue(
                    record,
                    "SUPERSEDES_PREDECESSOR_INVALID",
                    "successor depends on an invalid predecessor",
                    "supersedes",
                )
            )
            invalid.add(successor_id)
            changed = True
    valid_edges = {
        successor: predecessor
        for successor, predecessor in edges.items()
        if successor not in invalid and predecessor not in invalid
    }
    return valid_edges, issues, invalid


def _record_is_current(record: _GraphRecord, document: ContentDocument) -> bool:
    return (
        record.payload.get("revocation") is None
        and record.payload.get("body_sha256") == document.body_sha256
    )


def _active_current_records_by_content(
    registry: Mapping[str, _GraphRecord],
    edges: Mapping[str, str],
    *,
    invalid_ids: set[str],
    documents_by_id: Mapping[str, ContentDocument],
) -> dict[str, list[_GraphRecord]]:
    """Return current leaves after invalid dependency edges are pruned."""

    suppressed_ids = set(edges.values())
    active_by_content: dict[str, list[_GraphRecord]] = {}
    for record_id, record in sorted(registry.items()):
        document = documents_by_id.get(record.content_id)
        if (
            document is None
            or record_id in invalid_ids
            or record_id in suppressed_ids
            or not _record_is_current(record, document)
        ):
            continue
        active_by_content.setdefault(record.content_id, []).append(record)
    return active_by_content


def _record_was_effective_at(
    record: _GraphRecord,
    *,
    boundary: datetime,
    registry: Mapping[str, _GraphRecord],
    edges: Mapping[str, str],
    invalid_ids: set[str],
) -> bool:
    if record.record_id in invalid_ids or record.timestamp > boundary:
        return False
    revocation = record.payload.get("revocation")
    if isinstance(revocation, Mapping):
        revoked_at = _record_datetime(revocation.get("revoked_at"))
        if revoked_at is not None and revoked_at <= boundary:
            return False
    for successor_id, predecessor_id in edges.items():
        if predecessor_id != record.record_id:
            continue
        successor = registry[successor_id]
        if successor.timestamp <= boundary:
            return False
    return True


def validate_trust_graph(
    documents_by_id: Mapping[str, ContentDocument],
    source_record_entries: Sequence[tuple[Path, Mapping[str, Any]]],
    review_record_entries: Sequence[tuple[Path, Mapping[str, Any]]],
    *,
    actor_authorities: Mapping[str, ActorAuthority] | None = None,
    author_ids_by_content: Mapping[str, frozenset[str]] | None = None,
    critical_claim_ids_by_content: Mapping[str, frozenset[str]] | None = None,
    as_of: datetime,
    repo_root: Path = ROOT,
) -> TrustGraphResult:
    """Validate the repository-wide immutable record graph and project caches.

    The authority mappings are intentionally explicit inputs.  Actor identity,
    type, roles, authors, and all-claims scope cannot be self-authorized by a
    record payload.
    """

    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    root = Path(repo_root).absolute()
    source_records, source_issues, invalid_source = _collect_graph_records(
        source_record_entries,
        kind="source",
        documents_by_id=documents_by_id,
        repo_root=root,
        as_of=as_of,
    )
    review_records, review_issues, invalid_review = _collect_graph_records(
        review_record_entries,
        kind="review",
        documents_by_id=documents_by_id,
        repo_root=root,
        as_of=as_of,
    )
    issues: list[ValidationIssue] = [*source_issues, *review_issues]

    for record_id, record in sorted(source_records.items()):
        before = len(issues)
        issues.extend(
            _source_semantic_issues(
                record,
                actor_authorities=actor_authorities,
                author_ids_by_content=author_ids_by_content,
                critical_claim_ids_by_content=critical_claim_ids_by_content,
                as_of=as_of,
            )
        )
        if len(issues) != before:
            invalid_source.add(record_id)
    for record_id, record in sorted(review_records.items()):
        before = len(issues)
        issues.extend(
            _review_basic_issues(
                record,
                actor_authorities=actor_authorities,
                author_ids_by_content=author_ids_by_content,
                as_of=as_of,
            )
        )
        if len(issues) != before:
            invalid_review.add(record_id)

    source_edges, edge_issues, invalid_source = _build_supersession_edges(
        source_records,
        invalid_ids=invalid_source,
    )
    issues.extend(edge_issues)
    review_edges, edge_issues, invalid_review = _build_supersession_edges(
        review_records,
        invalid_ids=invalid_review,
    )
    issues.extend(edge_issues)

    suppressed_source = set(source_edges.values())
    active_source_by_content: dict[str, list[_GraphRecord]] = {}
    for record_id, record in sorted(source_records.items()):
        document = documents_by_id.get(record.content_id)
        if (
            document is None
            or record_id in invalid_source
            or record_id in suppressed_source
            or not _record_is_current(record, document)
        ):
            continue
        active_source_by_content.setdefault(record.content_id, []).append(record)

    projected_source: dict[str, str] = {}
    active_audit_ids: dict[str, tuple[str, ...]] = {}
    for content_id, document in sorted(
        documents_by_id.items(),
        key=lambda item: item[1].repo_relative_path,
    ):
        records = active_source_by_content.get(content_id, [])
        groups: dict[str, list[_GraphRecord]] = {}
        for record in records:
            groups.setdefault(str(record.payload.get("audit_kind", "")), []).append(record)
        ambiguous_ids: set[str] = set()
        for group in groups.values():
            if len(group) <= 1:
                continue
            ambiguous_ids.update(record.record_id for record in group)
            for record in group:
                issues.append(
                    _graph_issue(
                        record,
                        "DUPLICATE_ACTIVE_SOURCE_RECORD",
                        "one source chain cannot have multiple active leaves",
                    )
                )
        claim_records = [
            record
            for record in groups.get("CLAIM_VERIFICATION", [])
            if record.record_id not in ambiguous_ids
        ]
        source_status = "UNVERIFIED"
        if len(claim_records) == 1:
            transition = claim_records[0].payload.get("status_transition")
            target = transition.get("to") if isinstance(transition, Mapping) else None
            if target in {"PARTIAL", "VERIFIED"}:
                source_status = str(target)
        projected_source[content_id] = source_status
        active_audit_ids[content_id] = tuple(
            sorted(
                record.record_id
                for record in records
                if record.record_id not in ambiguous_ids
            )
        )

    # Review links and role separation depend on the validated source graph.
    initially_suppressed_reviews = set(review_edges.values())
    for record_id, record in sorted(review_records.items()):
        if record_id in invalid_review:
            continue
        is_approval = record.payload.get("decision") == "APPROVE"
        document = documents_by_id.get(record.content_id)
        approval_requires_current_evidence = (
            is_approval
            and document is not None
            and record_id not in initially_suppressed_reviews
            and _record_is_current(record, document)
        )
        approval_issues: list[ValidationIssue] = []
        linked_ids = record.payload.get("linked_audit_ids", [])
        effective_linked: list[_GraphRecord] = []
        for audit_id in linked_ids if isinstance(linked_ids, list) else []:
            audit = source_records.get(audit_id)
            if audit is None:
                approval_issues.append(
                    _graph_issue(
                        record,
                        "LINKED_AUDIT_NOT_FOUND",
                        "linked audit id does not resolve",
                        "linked_audit_ids",
                    )
                )
                continue
            link_is_valid = True
            if any(
                audit.payload.get(field) != record.payload.get(field)
                for field in ("content_id", "content_path", "body_sha256")
            ):
                approval_issues.append(
                    _graph_issue(
                        record,
                        "LINKED_AUDIT_IDENTITY_MISMATCH",
                        "linked audit targets different canonical content",
                        "linked_audit_ids",
                    )
                )
                link_is_valid = False
            if audit.timestamp > record.timestamp:
                approval_issues.append(
                    _graph_issue(
                        record,
                        "LINKED_AUDIT_TIME_ORDER",
                        "review predates linked audit evidence",
                        "linked_audit_ids",
                    )
                )
                link_is_valid = False
            if approval_requires_current_evidence:
                audit_is_effective = audit.record_id in active_audit_ids.get(
                    record.content_id,
                    (),
                )
            else:
                audit_is_effective = _record_was_effective_at(
                    audit,
                    boundary=record.timestamp,
                    registry=source_records,
                    edges=source_edges,
                    invalid_ids=invalid_source,
                )
            if not audit_is_effective:
                approval_issues.append(
                    _graph_issue(
                        record,
                        "LINKED_AUDIT_INACTIVE",
                        "linked audit is stale, revoked, superseded, or invalid",
                        "linked_audit_ids",
                    )
                )
                link_is_valid = False
            if link_is_valid:
                effective_linked.append(audit)
        linked_claim_records = [
            audit
            for audit in effective_linked
            if audit.payload.get("audit_kind") == "CLAIM_VERIFICATION"
        ]
        linked_source_status = "UNVERIFIED"
        if len(linked_claim_records) == 1:
            transition = linked_claim_records[0].payload.get("status_transition")
            target = transition.get("to") if isinstance(transition, Mapping) else None
            if target in {"PARTIAL", "VERIFIED"}:
                linked_source_status = str(target)
        if record.payload.get("source_status_at_review") != linked_source_status:
            approval_issues.append(
                _graph_issue(
                    record,
                    "SOURCE_STATUS_AT_REVIEW_MISMATCH",
                    "recorded source status does not match linked current evidence",
                    "source_status_at_review",
                )
            )
        if is_approval:
            if linked_source_status != "VERIFIED":
                approval_issues.append(
                    _graph_issue(
                        record,
                        "LINKED_AUDITS_NOT_VERIFIED",
                        "linked audits do not project VERIFIED",
                        "linked_audit_ids",
                    )
                )
        independence = record.payload.get("independence")
        declared_auditors = (
            set(independence.get("linked_auditor_ids", []))
            if isinstance(independence, Mapping)
            else set()
        )
        actual_auditors = {
            str(audit.payload.get("auditor_id"))
            for audit in effective_linked
        }
        actual_fact_auditors = {
            auditor_id
            for audit in effective_linked
            if audit.payload.get("auditor_role") == "FACT_AUDITOR"
            and (auditor_id := str(audit.payload.get("auditor_id")))
            and actor_authorities is not None
            and (authority := actor_authorities.get(auditor_id)) is not None
            and "FACT_AUDITOR" in authority.allowed_roles
        }
        if declared_auditors != actual_auditors:
            approval_issues.append(
                _graph_issue(
                    record,
                    "LINKED_AUDITOR_SET_MISMATCH",
                    "declared linked auditors do not match active audit records",
                    "independence.linked_auditor_ids",
                )
            )
        authors = (
            author_ids_by_content.get(record.content_id)
            if author_ids_by_content is not None
            else None
        )
        reviewer_id = record.payload.get("reviewer_id")
        if reviewer_id in actual_auditors:
            approval_issues.append(
                _graph_issue(
                    record,
                    "REVIEWER_AUDITOR_CONFLICT",
                    "reviewer must be independent from linked auditors",
                    "reviewer_id",
                )
            )
        if authors is not None and set(authors) & actual_fact_auditors:
            approval_issues.append(
                _graph_issue(
                    record,
                    "AUTHOR_AUDITOR_CONFLICT",
                    "content authors and linked fact auditors must be independent",
                    "independence",
                )
            )
        if isinstance(independence, Mapping):
            if independence.get("reviewer_is_linked_auditor") != (
                reviewer_id in actual_auditors
            ):
                approval_issues.append(
                    _graph_issue(
                        record,
                        "INDEPENDENCE_DECLARATION_MISMATCH",
                        "reviewer_is_linked_auditor does not match computed roles",
                        "independence.reviewer_is_linked_auditor",
                    )
                )
        if approval_issues:
            issues.extend(approval_issues)
            invalid_review.add(record_id)

    # An invalid successor cannot suppress an otherwise valid predecessor.
    review_edges, dependency_issues, invalid_review = _prune_invalid_dependencies(
        review_records,
        review_edges,
        invalid_ids=invalid_review,
    )
    issues.extend(dependency_issues)
    # Link validation can invalidate a successor that initially suppressed an
    # older approval.  Revalidate every approval exposed by the pruned graph
    # against current evidence, then prune again until the active leaves stop
    # changing.  Historical suppressed reviews keep their reviewed_at snapshot
    # semantics; only a final current approval must pass this gate.
    while True:
        active_review_by_content = _active_current_records_by_content(
            review_records,
            review_edges,
            invalid_ids=invalid_review,
            documents_by_id=documents_by_id,
        )
        newly_invalid: set[str] = set()
        current_approval_issues: list[ValidationIssue] = []
        for content_id, records in sorted(active_review_by_content.items()):
            current_audit_ids = set(active_audit_ids.get(content_id, ()))
            for record in records:
                if record.payload.get("decision") != "APPROVE":
                    continue
                linked_ids_value = record.payload.get("linked_audit_ids", [])
                linked_ids = (
                    linked_ids_value
                    if isinstance(linked_ids_value, list)
                    else []
                )
                linked_id_set = set(linked_ids)
                linked_audits_current = linked_id_set.issubset(
                    current_audit_ids
                )
                if not linked_audits_current:
                    current_approval_issues.append(
                        _graph_issue(
                            record,
                            "LINKED_AUDIT_INACTIVE",
                            "linked audit is stale, revoked, superseded, or invalid",
                            "linked_audit_ids",
                        )
                    )
                current_linked_claims = [
                    source_records[audit_id]
                    for audit_id in linked_ids
                    if audit_id in current_audit_ids
                    and audit_id in source_records
                    and source_records[audit_id].payload.get("audit_kind")
                    == "CLAIM_VERIFICATION"
                ]
                linked_source_status = "UNVERIFIED"
                if len(current_linked_claims) == 1:
                    transition = current_linked_claims[0].payload.get(
                        "status_transition"
                    )
                    target = (
                        transition.get("to")
                        if isinstance(transition, Mapping)
                        else None
                    )
                    if target in {"PARTIAL", "VERIFIED"}:
                        linked_source_status = str(target)
                approval_evidence_invalid = (
                    linked_source_status != "VERIFIED"
                    or projected_source.get(content_id) != "VERIFIED"
                )
                if approval_evidence_invalid:
                    current_approval_issues.append(
                        _graph_issue(
                            record,
                            "LINKED_AUDITS_NOT_VERIFIED",
                            "linked audits do not project VERIFIED",
                            "linked_audit_ids",
                        )
                    )
                if not linked_audits_current or approval_evidence_invalid:
                    newly_invalid.add(record.record_id)
        if not newly_invalid:
            break
        issues.extend(current_approval_issues)
        invalid_review.update(newly_invalid)
        review_edges, dependency_issues, invalid_review = (
            _prune_invalid_dependencies(
                review_records,
                review_edges,
                invalid_ids=invalid_review,
            )
        )
        issues.extend(dependency_issues)

    invalidated_review_history = {
        record.content_id
        for record in review_records.values()
        if (document := documents_by_id.get(record.content_id)) is not None
        and record.payload.get("content_path") == document.repo_relative_path
        and (
            record.payload.get("revocation") is not None
            or record.payload.get("body_sha256") != document.body_sha256
        )
    }

    projections: dict[str, TrustProjection] = {}
    for content_id, document in sorted(
        documents_by_id.items(),
        key=lambda item: item[1].repo_relative_path,
    ):
        active_reviews = active_review_by_content.get(content_id, [])
        if len(active_reviews) > 1:
            for record in active_reviews:
                issues.append(
                    _graph_issue(
                        record,
                        "DUPLICATE_ACTIVE_REVIEW_RECORD",
                        "one review chain cannot have multiple active leaves",
                    )
                )
            active_reviews = []
        review_status = (
            "IN_REVIEW" if content_id in invalidated_review_history else "UNREVIEWED"
        )
        active_review_ids: tuple[str, ...] = ()
        if len(active_reviews) == 1:
            transition = active_reviews[0].payload.get("status_transition")
            target = transition.get("to") if isinstance(transition, Mapping) else None
            if target in {"IN_REVIEW", "NEEDS_CHANGES", "HUMAN_APPROVED"}:
                review_status = str(target)
                active_review_ids = (active_reviews[0].record_id,)
        projections[content_id] = TrustProjection(
            content_id=content_id,
            content_path=document.repo_relative_path,
            body_sha256=document.body_sha256,
            source_status=projected_source.get(content_id, "UNVERIFIED"),
            review_status=review_status,
            active_audit_ids=active_audit_ids.get(content_id, ()),
            active_review_ids=active_review_ids,
        )

    return TrustGraphResult(projections, _sorted_unique_issues(issues))


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
