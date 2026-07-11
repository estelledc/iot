#!/usr/bin/env python3
"""Reconcile legacy IN_REVIEW observations without manufacturing trust evidence."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml
from yaml.constructor import ConstructorError
from yaml.resolver import BaseResolver


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LEDGER_PATH = Path("data/trust-migration-ledger.yml")
PROGRESS_PATH = Path("data/deep-review-progress.yml")
TRUST_RECORD_ROOTS = (
    Path("data/source-audits"),
    Path("data/review-records"),
)
CANONICAL_PATHSPEC = ":(glob)docs/*/papers/*.md"
OBSERVATION_PATHS = (CANONICAL_PATHSPEC, PROGRESS_PATH.as_posix())
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class ReconciliationError(ValueError):
    """Stable, path-safe boundary for migration ledger failures."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


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


def _load_mapping(path: Path, *, kind: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise ReconciliationError(f"{kind}_MISSING", f"{kind.lower()} file is missing") from None
    except OSError:
        raise ReconciliationError(f"{kind}_READ_ERROR", f"{kind.lower()} file could not be read") from None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ReconciliationError(f"{kind}_INVALID_UTF8", f"{kind.lower()} must be UTF-8") from None
    try:
        payload = yaml.load(text, Loader=_UniqueKeySafeLoader)
    except yaml.YAMLError:
        raise ReconciliationError(f"{kind}_INVALID_YAML", f"{kind.lower()} must be unambiguous YAML") from None
    if not isinstance(payload, dict):
        raise ReconciliationError(f"{kind}_NOT_MAPPING", f"{kind.lower()} must be a mapping")
    return payload


def load_ledger(path: Path) -> dict[str, Any]:
    """Load one migration ledger without accepting ambiguous YAML."""

    return _load_mapping(Path(path), kind="LEDGER")


def _validate_observed_commit(value: object) -> str:
    if not isinstance(value, str) or FULL_COMMIT_RE.fullmatch(value) is None:
        raise ReconciliationError(
            "INVALID_OBSERVED_COMMIT",
            "observed_at_commit must be a full lowercase commit SHA",
        )
    return value


def _assert_no_trust_records(repo_root: Path) -> None:
    """Leave BOUND classification to the cross-record validator in T044."""

    for relative_root in TRUST_RECORD_ROOTS:
        root = repo_root / relative_root
        if root.is_symlink():
            raise ReconciliationError(
                "UNSAFE_TRUST_RECORD_ROOT",
                "trust record roots must not be symbolic links",
            )
        if not root.exists():
            continue
        if not root.is_dir():
            raise ReconciliationError(
                "UNSAFE_TRUST_RECORD_ROOT",
                "trust record roots must be directories",
            )
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ReconciliationError(
                    "UNSAFE_TRUST_RECORD_PATH",
                    "trust record trees must not contain symbolic links",
                )
            if path.is_file() and path.suffix in {".yml", ".yaml", ".json"}:
                raise ReconciliationError(
                    "TRUST_RECORDS_REQUIRE_T044",
                    "trust records exist; BOUND classification requires the T044 record graph",
                )


def _load_progress(repo_root: Path) -> tuple[dict[str, Mapping[str, Any]], int]:
    progress_path = repo_root / PROGRESS_PATH
    if progress_path.is_symlink():
        raise ReconciliationError(
            "UNSAFE_PROGRESS_PATH",
            "progress path must not be a symbolic link",
        )
    payload = _load_mapping(progress_path, kind="PROGRESS")
    if payload.get("schema_version") != "1.0":
        raise ReconciliationError("PROGRESS_SCHEMA_MISMATCH", "progress schema_version must be 1.0")
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise ReconciliationError("PROGRESS_ARTICLES_INVALID", "progress articles must be an array")

    by_id: dict[str, Mapping[str, Any]] = {}
    paths: set[str] = set()
    for article in articles:
        if not isinstance(article, dict):
            raise ReconciliationError("PROGRESS_ARTICLE_INVALID", "each progress article must be a mapping")
        content_id = article.get("id")
        content_path = article.get("path")
        if not isinstance(content_id, str) or not content_id:
            raise ReconciliationError("PROGRESS_CONTENT_ID_INVALID", "progress article id is invalid")
        if not isinstance(content_path, str) or not content_path:
            raise ReconciliationError("PROGRESS_CONTENT_PATH_INVALID", "progress article path is invalid")
        if content_id in by_id:
            raise ReconciliationError(
                "PROGRESS_DUPLICATE_CONTENT_ID",
                "progress contains a duplicate content id",
            )
        if content_path in paths:
            raise ReconciliationError(
                "PROGRESS_DUPLICATE_CONTENT_PATH",
                "progress contains a duplicate content path",
            )
        if article.get("status") != "in_review":
            raise ReconciliationError(
                "PROGRESS_STATUS_MISMATCH",
                "legacy reconciliation requires every progress article to remain in_review",
            )
        by_id[content_id] = article
        paths.add(content_path)

    counts = payload.get("counts")
    if not isinstance(counts, dict):
        raise ReconciliationError("PROGRESS_COUNTS_INVALID", "progress counts must be a mapping")
    expected_counts = {
        "total": len(articles),
        "pending": 0,
        "in_review": len(articles),
    }
    if any(counts.get(key) != value for key, value in expected_counts.items()):
        raise ReconciliationError(
            "PROGRESS_COUNT_MISMATCH",
            "progress counts do not match the legacy in_review article set",
        )
    return by_id, len(articles)


def build_ledger(*, repo_root: Path = ROOT, observed_at_commit: str) -> dict[str, Any]:
    """Build the deterministic LEGACY_UNBOUND observation ledger in memory."""

    from tools.iot_domain import ContentError, iter_content_documents

    root = Path(repo_root).absolute()
    observed_commit = _validate_observed_commit(observed_at_commit)
    _assert_no_trust_records(root)
    progress_by_id, progress_count = _load_progress(root)

    try:
        documents = list(iter_content_documents(repo_root=root))
    except ContentError as exc:
        issue = exc.issue
        raise ReconciliationError(issue.code, f"canonical content is invalid: {issue.path}") from None
    except OSError:
        raise ReconciliationError("CANONICAL_CONTENT_READ_ERROR", "canonical content could not be read") from None
    if not documents:
        raise ReconciliationError("CANONICAL_CONTENT_EMPTY", "no canonical content documents were found")

    document_ids = [document.content_id for document in documents]
    document_paths = [document.repo_relative_path for document in documents]
    if len(document_ids) != len(set(document_ids)):
        raise ReconciliationError(
            "CANONICAL_DUPLICATE_CONTENT_ID",
            "canonical content contains a duplicate content id",
        )
    if len(document_paths) != len(set(document_paths)):
        raise ReconciliationError(
            "CANONICAL_DUPLICATE_CONTENT_PATH",
            "canonical content contains a duplicate content path",
        )

    canonical_ids = set(document_ids)
    progress_ids = set(progress_by_id)
    if canonical_ids - progress_ids:
        raise ReconciliationError(
            "PROGRESS_MISSING_CONTENT",
            "progress is missing one or more canonical content identities",
        )
    if progress_ids - canonical_ids:
        raise ReconciliationError(
            "PROGRESS_EXTRA_CONTENT",
            "progress contains one or more non-canonical content identities",
        )
    if progress_count != len(documents):
        raise ReconciliationError(
            "PROGRESS_COUNT_MISMATCH",
            "progress and canonical content counts differ",
        )

    entries: list[dict[str, Any]] = []
    for document in sorted(documents, key=lambda item: item.repo_relative_path):
        progress = progress_by_id[document.content_id]
        if progress.get("path") != document.repo_relative_path:
            raise ReconciliationError(
                "PROGRESS_PATH_MISMATCH",
                "progress path does not match canonical content identity",
            )
        if progress.get("layer") != document.layer.id:
            raise ReconciliationError(
                "PROGRESS_LAYER_MISMATCH",
                "progress layer does not match canonical content identity",
            )
        source_status = document.frontmatter.get("source_status")
        review_status = document.frontmatter.get("review_status")
        if source_status != "UNVERIFIED":
            raise ReconciliationError(
                "FRONTMATTER_SOURCE_STATUS_MISMATCH",
                "legacy baseline requires source_status UNVERIFIED",
            )
        if review_status != "IN_REVIEW":
            raise ReconciliationError(
                "FRONTMATTER_REVIEW_STATUS_MISMATCH",
                "legacy baseline requires review_status IN_REVIEW",
            )
        entries.append(
            {
                "content_id": document.content_id,
                "content_path": document.repo_relative_path,
                "layer": document.layer.id,
                "body_sha256": document.body_sha256,
                "observed_source_status": source_status,
                "observed_review_status": review_status,
                "legacy_campaign_status": "in_review",
                "classification": "LEGACY_UNBOUND",
                "observed_at_commit": observed_commit,
            }
        )

    total = len(entries)
    return {
        "schema_version": "1.0",
        "ledger_kind": "TRUST_MIGRATION",
        "generated_by": "python tools/reconcile_legacy_review_state.py --write",
        "observed_at_commit": observed_commit,
        "source": {
            "legacy_campaign": PROGRESS_PATH.as_posix(),
            "canonical_glob": "docs/*/papers/*.md",
            "binding_transition_owner": "IOT-T044",
        },
        "counts": {
            "canonical_content": total,
            "observed_in_review": total,
            "legacy_unbound": total,
            "evidence_bound_review": 0,
            "bound": 0,
        },
        "definitions": {
            "observed_in_review": (
                "Historical repository state only; it is not evidence that independent review occurred."
            ),
            "LEGACY_UNBOUND": (
                "The observed status has no independently verifiable review record bound to this body hash."
            ),
            "BOUND": (
                "Reserved for IOT-T044 after current audit/review records and role separation validate."
            ),
        },
        "entries": entries,
    }


def render_ledger(payload: Mapping[str, Any]) -> bytes:
    """Render one ledger with stable key and entry order."""

    return yaml.safe_dump(
        dict(payload),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    ).encode("utf-8")


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
    )


def _head_commit(repo_root: Path) -> str:
    result = _git(repo_root, "rev-parse", "--verify", "HEAD^{commit}")
    if result.returncode != 0:
        raise ReconciliationError("GIT_HEAD_UNAVAILABLE", "repository HEAD could not be resolved")
    try:
        value = result.stdout.decode("ascii").strip().lower()
    except UnicodeDecodeError:
        raise ReconciliationError("GIT_HEAD_UNAVAILABLE", "repository HEAD is invalid") from None
    return _validate_observed_commit(value)


def _assert_observation_worktree_clean(repo_root: Path) -> None:
    result = _git(
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        *OBSERVATION_PATHS,
    )
    if result.returncode != 0:
        raise ReconciliationError("GIT_STATUS_FAILED", "canonical worktree status could not be checked")
    if result.stdout:
        raise ReconciliationError(
            "OBSERVATION_INPUT_UNCOMMITTED",
            "canonical content and legacy progress must match an immutable commit before reconciliation",
        )


def _existing_observed_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ReconciliationError("UNSAFE_LEDGER_PATH", "migration ledger path must be a regular file")
    payload = load_ledger(path)
    return _validate_observed_commit(payload.get("observed_at_commit"))


def _commit_is_unchanged_ancestor(repo_root: Path, previous: str, head: str) -> bool:
    exists = _git(repo_root, "cat-file", "-e", f"{previous}^{{commit}}")
    if exists.returncode != 0:
        return False
    ancestor = _git(repo_root, "merge-base", "--is-ancestor", previous, head)
    if ancestor.returncode == 1:
        return False
    if ancestor.returncode != 0:
        raise ReconciliationError("GIT_ANCESTRY_FAILED", "observation commit ancestry could not be checked")
    diff = _git(repo_root, "diff", "--quiet", previous, head, "--", *OBSERVATION_PATHS)
    if diff.returncode == 0:
        return True
    if diff.returncode == 1:
        return False
    raise ReconciliationError("GIT_DIFF_FAILED", "canonical commit difference could not be checked")


def observation_commit(*, repo_root: Path, ledger_path: Path) -> str:
    """Reuse the first observation commit while canonical content stays identical."""

    _assert_observation_worktree_clean(repo_root)
    head = _head_commit(repo_root)
    previous = _existing_observed_commit(ledger_path)
    if previous is None or previous == head:
        return head
    if _commit_is_unchanged_ancestor(repo_root, previous, head):
        return previous
    return head


def write_ledger(
    *,
    repo_root: Path = ROOT,
    observed_at_commit: str | None = None,
) -> dict[str, Any]:
    """Write the ledger only; canonical Markdown is always read-only."""

    root = Path(repo_root).absolute()
    output = root / LEDGER_PATH
    if output.is_symlink() or (output.exists() and not output.is_file()):
        raise ReconciliationError("UNSAFE_LEDGER_PATH", "migration ledger path must be a regular file")
    observed = (
        observation_commit(repo_root=root, ledger_path=output)
        if observed_at_commit is None
        else _validate_observed_commit(observed_at_commit)
    )
    payload = build_ledger(repo_root=root, observed_at_commit=observed)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(render_ledger(payload))
    return payload


def check_ledger(
    *,
    repo_root: Path = ROOT,
    observed_at_commit: str | None = None,
) -> list[str]:
    """Return deterministic drift messages without modifying repository files."""

    root = Path(repo_root).absolute()
    output = root / LEDGER_PATH
    if output.is_symlink() or (output.exists() and not output.is_file()):
        raise ReconciliationError("UNSAFE_LEDGER_PATH", "migration ledger path must be a regular file")
    if not output.is_file():
        return [f"missing generated ledger: {LEDGER_PATH.as_posix()}"]
    observed = (
        observation_commit(repo_root=root, ledger_path=output)
        if observed_at_commit is None
        else _validate_observed_commit(observed_at_commit)
    )
    expected = render_ledger(build_ledger(repo_root=root, observed_at_commit=observed))
    try:
        actual = output.read_bytes()
    except OSError:
        raise ReconciliationError("LEDGER_READ_ERROR", "ledger could not be read") from None
    if actual != expected:
        return [f"stale generated ledger: {LEDGER_PATH.as_posix()}"]
    return []


def _summary(payload: Mapping[str, Any]) -> str:
    counts = payload["counts"]
    return (
        f"entries={counts['canonical_content']} "
        f"legacy_unbound={counts['legacy_unbound']} "
        f"evidence_bound_review={counts['evidence_bound_review']} "
        f"observed_at_commit={payload['observed_at_commit']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the deterministic migration ledger")
    mode.add_argument("--check", action="store_true", help="fail when the migration ledger drifts")
    args = parser.parse_args(argv)

    try:
        if args.write:
            payload = write_ledger(repo_root=ROOT)
            print(f"TRUST_MIGRATION_LEDGER_UPDATED {_summary(payload)}")
            return 0
        errors = check_ledger(repo_root=ROOT)
        if errors:
            print("TRUST_MIGRATION_LEDGER_STALE", file=sys.stderr)
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        payload = load_ledger(ROOT / LEDGER_PATH)
        print(f"TRUST_MIGRATION_LEDGER_OK {_summary(payload)}")
        return 0
    except ReconciliationError as exc:
        print(f"TRUST_MIGRATION_LEDGER_ERROR [{exc.code}]: {exc.message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
