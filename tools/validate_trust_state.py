#!/usr/bin/env python3
"""Validate repository-wide trust records, projections, and legacy baseline."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import reconcile_legacy_review_state, trust_records
from tools.iot_domain import ContentDocument, ContentError, iter_content_documents


SOURCE_RECORD_ROOT = Path("data/source-audits")
REVIEW_RECORD_ROOT = Path("data/review-records")
LEDGER_PATH = Path("data/trust-migration-ledger.yml")
SOURCE_SCHEMA_PATH = Path("schemas/source-audit.schema.json")
REVIEW_SCHEMA_PATH = Path("schemas/review-record.schema.json")
AUTHORITY_PATH = Path("data/trust-authorities.yml")
AUTHORITY_SCHEMA_PATH = Path("schemas/trust-authorities.schema.json")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_AUTHORITY_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class TrustStateSummary:
    canonical_content: int
    source_records: int
    review_records: int
    legacy_unbound: int
    evidence_bound_review: int
    verified: int
    approved: int


@dataclass(frozen=True)
class RepositoryTrustResult:
    projections: Mapping[str, trust_records.TrustProjection]
    issues: list[trust_records.ValidationIssue]
    summary: TrustStateSummary


@dataclass(frozen=True)
class TrustAuthorityRegistry:
    actors_by_id: Mapping[str, trust_records.ActorAuthority]
    author_ids_by_content: Mapping[str, frozenset[str]]
    critical_claim_ids_by_content: Mapping[str, frozenset[str]]
    issues: list[trust_records.ValidationIssue]


class TrustStateError(ValueError):
    """Stable path-safe boundary for repository trust I/O failures."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def _issue(
    path: str,
    code: str,
    message: str,
    location: str = "",
) -> trust_records.ValidationIssue:
    return trust_records.ValidationIssue(path, location, message, code)


def _sorted_unique_issues(
    issues: list[trust_records.ValidationIssue],
) -> list[trust_records.ValidationIssue]:
    unique = {
        (issue.path, issue.location, issue.code, issue.message): issue
        for issue in issues
    }
    return sorted(
        unique.values(),
        key=lambda issue: (issue.path, issue.location, issue.code, issue.message),
    )


def _resolve_fixed_repository_path(
    repo_root: Path,
    relative_path: Path,
    *,
    code: str,
) -> Path:
    """Resolve one fixed repository path without following path redirections."""

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise TrustStateError(code, "repository path is not a safe relative path")
    root = Path(os.path.abspath(repo_root))
    candidate = Path(os.path.abspath(root / relative_path))
    try:
        lexical_relative = candidate.relative_to(root)
        resolved_root = root.resolve()
        resolved_candidate = candidate.resolve(strict=False)
        resolved_relative = resolved_candidate.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError):
        raise TrustStateError(code, "repository path could not be resolved safely") from None
    if lexical_relative != resolved_relative:
        raise TrustStateError(code, "repository path must not traverse symbolic links")
    return candidate


def _load_documents(repo_root: Path) -> dict[str, ContentDocument]:
    try:
        documents = list(iter_content_documents(repo_root=repo_root))
    except ContentError as exc:
        issue = exc.issue
        raise TrustStateError(issue.code, "canonical content failed strict validation") from None
    except OSError:
        raise TrustStateError(
            "CANONICAL_CONTENT_READ_ERROR",
            "canonical content could not be read",
        ) from None
    if not documents:
        raise TrustStateError(
            "CANONICAL_CONTENT_EMPTY",
            "no canonical content documents were found",
        )
    by_id: dict[str, ContentDocument] = {}
    paths: set[str] = set()
    for document in documents:
        if document.content_id in by_id:
            raise TrustStateError(
                "CANONICAL_DUPLICATE_CONTENT_ID",
                "canonical content ids must be unique",
            )
        if document.repo_relative_path in paths:
            raise TrustStateError(
                "CANONICAL_DUPLICATE_CONTENT_PATH",
                "canonical content paths must be unique",
            )
        by_id[document.content_id] = document
        paths.add(document.repo_relative_path)
    return by_id


def _load_record_entries(
    *,
    repo_root: Path,
    record_root: Path,
    schema_path: Path,
) -> tuple[
    list[tuple[Path, Mapping[str, Any]]],
    list[trust_records.ValidationIssue],
]:
    absolute_root = _resolve_fixed_repository_path(
        repo_root,
        record_root,
        code="UNSAFE_RECORD_ROOT",
    )
    absolute_schema = _resolve_fixed_repository_path(
        repo_root,
        schema_path,
        code="UNSAFE_SCHEMA_PATH",
    )
    display_root = record_root.as_posix()
    if absolute_root.is_symlink():
        return [], [
            _issue(
                display_root,
                "UNSAFE_RECORD_ROOT",
                "record root must not be a symbolic link",
            )
        ]
    if absolute_root.exists() and not absolute_root.is_dir():
        return [], [
            _issue(
                display_root,
                "RECORD_ROOT_NOT_DIRECTORY",
                "record root must be a directory",
            )
        ]
    try:
        schema = trust_records.load_schema(absolute_schema)
    except trust_records.TrustRecordError as exc:
        raise TrustStateError(exc.code, exc.message) from None
    try:
        paths = trust_records.iter_record_paths(absolute_root)
    except (OSError, RuntimeError):
        raise TrustStateError(
            "RECORD_ENUMERATION_ERROR",
            "record directory could not be enumerated safely",
        ) from None

    entries: list[tuple[Path, Mapping[str, Any]]] = []
    issues: list[trust_records.ValidationIssue] = []
    for path in paths:
        display = trust_records.safe_display_path(path, repo_root=repo_root)
        try:
            payload = trust_records.load_record(path)
        except trust_records.TrustRecordError as exc:
            issues.append(_issue(display, exc.code, exc.message))
            continue
        validity, record_issues = trust_records.validate_record_payload(
            payload,
            schema,
            record_path=path,
            repo_root=repo_root,
        )
        issues.extend(record_issues)
        if validity is not None and validity.state in {"ACTIVE", "STALE", "REVOKED"}:
            entries.append((path, payload))
    return entries, issues


def _load_trust_authorities(
    *,
    repo_root: Path,
    documents_by_id: Mapping[str, ContentDocument],
) -> TrustAuthorityRegistry:
    schema_path = _resolve_fixed_repository_path(
        repo_root,
        AUTHORITY_SCHEMA_PATH,
        code="UNSAFE_AUTHORITY_SCHEMA_PATH",
    )
    authority_path = _resolve_fixed_repository_path(
        repo_root,
        AUTHORITY_PATH,
        code="UNSAFE_AUTHORITY_PATH",
    )
    try:
        schema = trust_records.load_schema(schema_path)
    except trust_records.TrustRecordError as exc:
        raise TrustStateError(f"AUTHORITY_{exc.code}", exc.message) from None
    if not authority_path.exists():
        return TrustAuthorityRegistry({}, {}, {}, [])
    if authority_path.is_symlink() or not authority_path.is_file():
        raise TrustStateError(
            "UNSAFE_AUTHORITY_PATH",
            "trust authority path must be a regular repository file",
        )
    try:
        if authority_path.stat().st_size > MAX_AUTHORITY_BYTES:
            raise TrustStateError(
                "AUTHORITY_FILE_TOO_LARGE",
                "trust authority file exceeds the size limit",
            )
        payload = trust_records.load_record(authority_path)
    except OSError:
        raise TrustStateError(
            "AUTHORITY_READ_ERROR",
            "trust authority file could not be read",
        ) from None
    except trust_records.TrustRecordError as exc:
        raise TrustStateError(f"AUTHORITY_{exc.code}", exc.message) from None

    display = AUTHORITY_PATH.as_posix()
    validator = Draft202012Validator(schema)
    schema_errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if schema_errors:
        return TrustAuthorityRegistry(
            {},
            {},
            {},
            [
                _issue(
                    display,
                    "AUTHORITY_SCHEMA_VALIDATION_FAILED",
                    f"authority data does not satisfy schema rule {error.validator!r}",
                    ".".join(str(part) for part in error.absolute_path),
                )
                for error in schema_errors
            ],
        )

    actors_by_id: dict[str, trust_records.ActorAuthority] = {}
    ambiguous_actor_ids: set[str] = set()
    issues: list[trust_records.ValidationIssue] = []
    actors = payload.get("actors", [])
    for index, actor in enumerate(actors if isinstance(actors, list) else []):
        if not isinstance(actor, Mapping):
            continue
        location = f"actors.{index}"
        actor_id = str(actor.get("actor_id", ""))
        if actor_id in actors_by_id or actor_id in ambiguous_actor_ids:
            actors_by_id.pop(actor_id, None)
            ambiguous_actor_ids.add(actor_id)
            issues.append(
                _issue(
                    display,
                    "DUPLICATE_ACTOR_AUTHORITY",
                    "actor ids must be globally unique in repository authority",
                    f"{location}.actor_id",
                )
            )
            continue
        actor_type = str(actor.get("actor_type", ""))
        if not actor_id.startswith(actor_type.lower() + "-"):
            issues.append(
                _issue(
                    display,
                    "ACTOR_AUTHORITY_ID_TYPE_MISMATCH",
                    "authoritative actor id namespace does not match actor type",
                    f"{location}.actor_id",
                )
            )
            continue
        actors_by_id[actor_id] = trust_records.ActorAuthority(
            actor_id=actor_id,
            actor_type=actor_type,  # type: ignore[arg-type]
            allowed_roles=frozenset(actor.get("allowed_roles", [])),
        )

    author_ids: dict[str, frozenset[str]] = {}
    critical_claim_ids: dict[str, frozenset[str]] = {}
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    entries = payload.get("entries", [])
    for index, entry in enumerate(entries if isinstance(entries, list) else []):
        if not isinstance(entry, Mapping):
            continue
        location = f"entries.{index}"
        content_id = str(entry.get("content_id", ""))
        content_path = str(entry.get("content_path", ""))
        if content_id in seen_ids:
            issues.append(
                _issue(
                    display,
                    "DUPLICATE_AUTHORITY_CONTENT_ID",
                    "authority content ids must be unique",
                    f"{location}.content_id",
                )
            )
            continue
        seen_ids.add(content_id)
        if content_path in seen_paths:
            issues.append(
                _issue(
                    display,
                    "DUPLICATE_AUTHORITY_CONTENT_PATH",
                    "authority content paths must be unique",
                    f"{location}.content_path",
                )
            )
            continue
        seen_paths.add(content_path)
        document = documents_by_id.get(content_id)
        if document is None:
            issues.append(
                _issue(
                    display,
                    "UNKNOWN_AUTHORITY_CONTENT_ID",
                    "authority entry does not resolve to canonical content",
                    f"{location}.content_id",
                )
            )
            continue
        if content_path != document.repo_relative_path:
            issues.append(
                _issue(
                    display,
                    "AUTHORITY_CONTENT_PATH_MISMATCH",
                    "authority path does not match canonical content",
                    f"{location}.content_path",
                )
            )
            continue
        if entry.get("body_sha256") != document.body_sha256:
            issues.append(
                _issue(
                    display,
                    "AUTHORITY_BODY_HASH_MISMATCH",
                    "authority body hash does not match canonical content",
                    f"{location}.body_sha256",
                )
            )
            continue
        declared_authors = frozenset(entry.get("author_ids", []))
        authors_are_authorized = True
        for author_id in sorted(declared_authors):
            actor = actors_by_id.get(author_id)
            if actor is None:
                issues.append(
                    _issue(
                        display,
                        "AUTHOR_ACTOR_AUTHORITY_MISSING",
                        "content author does not resolve to repository actor authority",
                        f"{location}.author_ids",
                    )
                )
                authors_are_authorized = False
            elif "CONTENT_AUTHOR" not in actor.allowed_roles:
                issues.append(
                    _issue(
                        display,
                        "AUTHOR_ACTOR_ROLE_NOT_ALLOWED",
                        "content author actor lacks the CONTENT_AUTHOR role",
                        f"{location}.author_ids",
                    )
                )
                authors_are_authorized = False
        if authors_are_authorized:
            author_ids[content_id] = declared_authors
        claims = entry.get("critical_claim_ids")
        if isinstance(claims, list) and claims:
            critical_claim_ids[content_id] = frozenset(claims)

    return TrustAuthorityRegistry(
        actors_by_id,
        author_ids,
        critical_claim_ids,
        issues,
    )


def _load_and_validate_legacy_ledger(
    *,
    repo_root: Path,
    documents_by_id: Mapping[str, ContentDocument],
    required: bool,
) -> tuple[set[str], list[trust_records.ValidationIssue]]:
    """Validate immutable provenance, then derive current legacy bindings."""

    path = _resolve_fixed_repository_path(
        repo_root,
        LEDGER_PATH,
        code="UNSAFE_LEGACY_LEDGER_PATH",
    )
    display = LEDGER_PATH.as_posix()
    if path.is_symlink() or (path.exists() and not path.is_file()):
        return set(), [
            _issue(
                display,
                "LEGACY_LEDGER_INVALID",
                "migration ledger must be a regular repository file",
            )
        ]
    if not path.is_file():
        if required:
            return set(), [
                _issue(
                    display,
                    "LEGACY_LEDGER_MISSING",
                    "baseline mode requires the migration ledger",
                )
            ]
        return set(), []

    try:
        payload = reconcile_legacy_review_state.load_ledger(path)
    except reconcile_legacy_review_state.ReconciliationError as exc:
        return set(), [_issue(display, exc.code, exc.message)]

    observed_commit = payload.get("observed_at_commit")
    if (
        not isinstance(observed_commit, str)
        or FULL_COMMIT_RE.fullmatch(observed_commit) is None
    ):
        return set(), [
            _issue(
                display,
                "LEGACY_LEDGER_INVALID",
                "observed_at_commit must be a full lowercase commit SHA",
                "observed_at_commit",
            )
        ]

    try:
        expected = reconcile_legacy_review_state.build_ledger_at_commit(
            repo_root=repo_root,
            observed_at_commit=observed_commit,
        )
    except reconcile_legacy_review_state.ReconciliationError as exc:
        if exc.code in {
            "OBSERVED_COMMIT_NOT_FOUND",
            "OBSERVED_COMMIT_NOT_ANCESTOR",
        }:
            return set(), [_issue(display, exc.code, exc.message, "observed_at_commit")]
        raise TrustStateError(exc.code, exc.message) from None

    issues: list[trust_records.ValidationIssue] = []
    try:
        actual_bytes = path.read_bytes()
    except OSError:
        raise TrustStateError(
            "LEGACY_LEDGER_READ_ERROR",
            "migration ledger could not be read",
        ) from None
    expected_bytes = reconcile_legacy_review_state.render_ledger(expected)
    if actual_bytes != expected_bytes:
        issues.append(
            _issue(
                display,
                "LEGACY_LEDGER_PROVENANCE_MISMATCH",
                "migration ledger does not match its immutable observation commit",
            )
        )

    current_legacy_ids: set[str] = set()
    entries = expected.get("entries", [])
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, Mapping):
            continue
        content_id = entry.get("content_id")
        if not isinstance(content_id, str):
            continue
        document = documents_by_id.get(content_id)
        if document is None:
            continue
        if (
            entry.get("content_path") == document.repo_relative_path
            and entry.get("layer") == document.layer.id
            and entry.get("body_sha256") == document.body_sha256
        ):
            current_legacy_ids.add(content_id)
    return current_legacy_ids, issues


def validate_repository_trust(
    *,
    repo_root: Path = ROOT,
    baseline_mode: bool,
    actor_authorities: Mapping[str, trust_records.ActorAuthority] | None = None,
    author_ids_by_content: Mapping[str, frozenset[str]] | None = None,
    critical_claim_ids_by_content: Mapping[str, frozenset[str]] | None = None,
    as_of: datetime | None = None,
) -> RepositoryTrustResult:
    """Validate every canonical document, trust record, and derived cache."""

    root = Path(os.path.abspath(repo_root))
    boundary = as_of if as_of is not None else datetime.now(timezone.utc)
    if boundary.tzinfo is None or boundary.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    documents_by_id = _load_documents(root)
    authority_issues: list[trust_records.ValidationIssue] = []
    if (
        actor_authorities is None
        and author_ids_by_content is None
        and critical_claim_ids_by_content is None
    ):
        registry = _load_trust_authorities(
            repo_root=root,
            documents_by_id=documents_by_id,
        )
        actor_authorities = registry.actors_by_id
        author_ids_by_content = registry.author_ids_by_content
        critical_claim_ids_by_content = registry.critical_claim_ids_by_content
        authority_issues.extend(registry.issues)
    source_entries, source_issues = _load_record_entries(
        repo_root=root,
        record_root=SOURCE_RECORD_ROOT,
        schema_path=SOURCE_SCHEMA_PATH,
    )
    review_entries, review_issues = _load_record_entries(
        repo_root=root,
        record_root=REVIEW_RECORD_ROOT,
        schema_path=REVIEW_SCHEMA_PATH,
    )
    legacy_ids, ledger_issues = _load_and_validate_legacy_ledger(
        repo_root=root,
        documents_by_id=documents_by_id,
        required=baseline_mode,
    )
    issues = [
        *authority_issues,
        *source_issues,
        *review_issues,
        *ledger_issues,
    ]
    if legacy_ids and not baseline_mode:
        issues.append(
            _issue(
                LEDGER_PATH.as_posix(),
                "LEGACY_UNBOUND_REQUIRES_BASELINE",
                "LEGACY_UNBOUND observations require explicit baseline mode",
            )
        )

    graph = trust_records.validate_trust_graph(
        documents_by_id,
        source_entries,
        review_entries,
        actor_authorities=actor_authorities,
        author_ids_by_content=author_ids_by_content,
        critical_claim_ids_by_content=critical_claim_ids_by_content,
        as_of=boundary,
        repo_root=root,
    )
    issues.extend(graph.issues)

    projections: dict[str, trust_records.TrustProjection] = {}
    for content_id, document in sorted(
        documents_by_id.items(),
        key=lambda item: item[1].repo_relative_path,
    ):
        graph_projection = graph.projections[content_id]
        review_status = graph_projection.review_status
        if (
            baseline_mode
            and content_id in legacy_ids
            and not graph_projection.active_review_ids
            and review_status == "UNREVIEWED"
        ):
            review_status = "IN_REVIEW"
        projection = trust_records.TrustProjection(
            content_id=graph_projection.content_id,
            content_path=graph_projection.content_path,
            body_sha256=graph_projection.body_sha256,
            source_status=graph_projection.source_status,
            review_status=review_status,
            active_audit_ids=graph_projection.active_audit_ids,
            active_review_ids=graph_projection.active_review_ids,
        )
        projections[content_id] = projection

        actual_source = document.frontmatter.get("source_status")
        actual_review = document.frontmatter.get("review_status")
        if actual_source != projection.source_status:
            issues.append(
                _issue(
                    document.repo_relative_path,
                    "SOURCE_STATUS_PROJECTION_MISMATCH",
                    "frontmatter source_status does not match the valid record graph",
                    "source_status",
                )
            )
        if actual_review != projection.review_status:
            issues.append(
                _issue(
                    document.repo_relative_path,
                    "REVIEW_STATUS_PROJECTION_MISMATCH",
                    "frontmatter review_status does not match the valid record graph",
                    "review_status",
                )
            )
        if (
            content_id in legacy_ids
            and (
                (
                    actual_source in {"PARTIAL", "VERIFIED"}
                    and projection.source_status
                    not in {"PARTIAL", "VERIFIED"}
                )
                or (
                    actual_review == "HUMAN_APPROVED"
                    and projection.review_status != "HUMAN_APPROVED"
                )
            )
        ):
            issues.append(
                _issue(
                    document.repo_relative_path,
                    "LEGACY_UNBOUND_PROMOTION",
                    "legacy content cannot claim promoted trust without bound records",
                )
            )

    evidence_bound_review = sum(
        bool(projection.active_review_ids) for projection in projections.values()
    )
    legacy_unbound = sum(
        content_id in legacy_ids and not projection.active_review_ids
        for content_id, projection in projections.items()
    )
    summary = TrustStateSummary(
        canonical_content=len(documents_by_id),
        source_records=len(source_entries),
        review_records=len(review_entries),
        legacy_unbound=legacy_unbound,
        evidence_bound_review=evidence_bound_review,
        verified=sum(
            projection.source_status == "VERIFIED"
            for projection in projections.values()
        ),
        approved=sum(
            projection.review_status == "HUMAN_APPROVED"
            for projection in projections.values()
        ),
    )
    return RepositoryTrustResult(
        projections=projections,
        issues=_sorted_unique_issues(issues),
        summary=summary,
    )


def _parse_as_of(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise argparse.ArgumentTypeError("--as-of must be an RFC3339 datetime") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("--as-of must include a timezone offset")
    return parsed


def _summary_text(summary: TrustStateSummary, *, baseline_mode: bool) -> str:
    return (
        f"canonical_content={summary.canonical_content} "
        f"source_records={summary.source_records} "
        f"review_records={summary.review_records} "
        f"legacy_unbound={summary.legacy_unbound} "
        f"evidence_bound_review={summary.evidence_bound_review} "
        f"verified={summary.verified} "
        f"approved={summary.approved} "
        f"baseline_mode={str(baseline_mode).lower()}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", required=True)
    parser.add_argument(
        "--baseline-mode",
        action="store_true",
        help="allow ledger-bound legacy IN_REVIEW observations without treating them as review evidence",
    )
    parser.add_argument(
        "--as-of",
        help="optional RFC3339 replay boundary; records after it fail closed",
    )
    args = parser.parse_args(argv)
    try:
        as_of = _parse_as_of(args.as_of)
        result = validate_repository_trust(
            repo_root=ROOT,
            baseline_mode=args.baseline_mode,
            as_of=as_of,
        )
    except argparse.ArgumentTypeError as exc:
        print(f"TRUST_STATE_ERROR [INVALID_AS_OF]: {exc}", file=sys.stderr)
        return 2
    except TrustStateError as exc:
        print(f"TRUST_STATE_ERROR [{exc.code}]: {exc.message}", file=sys.stderr)
        return 2

    if result.issues:
        print(
            f"TRUST_STATE_INVALID {_summary_text(result.summary, baseline_mode=args.baseline_mode)}",
            file=sys.stderr,
        )
        for issue in result.issues:
            print(f"ERROR: {issue.render()}", file=sys.stderr)
        return 1
    print(f"TRUST_STATE_OK {_summary_text(result.summary, baseline_mode=args.baseline_mode)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
