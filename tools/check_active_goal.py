#!/usr/bin/env python3
"""Validate the bounded agent goal contract and its lifecycle invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import content_inventory, trust_records, validate_trust_state


GOAL_PATH = ROOT / "ops/active-goal.yml"
LOCK_PATH = ROOT / "ops/active-goal.lock.json"
SCHEMA_PATH = ROOT / "schemas/active-goal.schema.json"
PAUSE_AFTER_NO_EXTERNAL_DELTA = 3
ARTICLE_SELECTION_MODES = {"STRUCTURAL_SHADOW_AUDIT"}
IMMUTABLE_FIELDS = (
    "schema_version",
    "goal_id",
    "objective",
    "scope",
    "budget",
    "stop_conditions",
    "baseline",
    "acceptance_checks",
    "allowed_mutations",
    "forbidden_mutations",
    "external_action_grant",
)


def immutable_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the goal fields an active worker may never expand in place."""

    projection = {field: payload[field] for field in IMMUTABLE_FIELDS}
    projection["external_outcome"] = {
        "definition": payload["external_outcome"]["definition"],
        "satisfies_when": payload["external_outcome"]["satisfies_when"],
    }
    projection["external_action_authority"] = payload["external_action_authority"]
    return projection


def immutable_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        immutable_projection(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError("duplicate JSON object key")
        payload[key] = value
    return payload


def load_lock(path: Path = LOCK_PATH) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        raw = path.read_bytes()
    except OSError:
        return None, ["GOAL_LOCK_READ_ERROR"]
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, ["GOAL_LOCK_INVALID_JSON"]
    if not isinstance(payload, dict):
        return None, ["GOAL_LOCK_NOT_OBJECT"]
    return payload, []


def validate_lock(
    payload: Mapping[str, Any],
    lock: Mapping[str, Any],
) -> list[str]:
    expected_keys = {"schema_version", "goal_id", "immutable_sha256"}
    if set(lock) != expected_keys:
        return ["GOAL_LOCK_FIELDS_MISMATCH"]
    errors: list[str] = []
    if lock["schema_version"] != "1.0":
        errors.append("GOAL_LOCK_SCHEMA_VERSION_MISMATCH")
    if lock["goal_id"] != payload["goal_id"]:
        errors.append("GOAL_LOCK_GOAL_ID_MISMATCH")
    if lock["immutable_sha256"] != immutable_sha256(payload):
        errors.append("GOAL_LOCK_IMMUTABLE_CONTRACT_MISMATCH")
    return errors


def _normalize_rule_path(raw: str) -> str | None:
    if raw.startswith(("/", "~")) or "\\" in raw or ":" in raw:
        return None
    candidate = raw.rstrip("/")
    lexical_parts = candidate.split("/")
    if not lexical_parts or any(part in {"", ".", ".."} for part in lexical_parts):
        return None
    parts = PurePosixPath(candidate).parts
    return "/".join(parts)


def _path_rules_overlap(first: str, second: str) -> bool:
    return (
        first == second
        or first.startswith(f"{second}/")
        or second.startswith(f"{first}/")
    )


def _record_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if not root.is_dir() or root.is_symlink():
        return [root]
    return sorted(
        path
        for path in root.rglob("*")
        if path.suffix in {".yml", ".yaml"} and path.is_file()
    )


def _git_output(root: Path, *args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return result.returncode, result.stdout


def _path_is_allowed(path: str, rules: list[str]) -> bool:
    normalized = _normalize_rule_path(path)
    if normalized is None:
        return False
    return any(
        normalized == rule or normalized.startswith(f"{rule}/")
        for rule in rules
    )


def _uses_article_selection(payload: Mapping[str, Any]) -> bool:
    return (
        payload["scope"]["mode"] in ARTICLE_SELECTION_MODES
        or payload["scope"]["max_articles"] > 0
    )


def _validate_structural_shadow_audit_state(
    payload: Mapping[str, Any],
    *,
    root: Path,
    source_records: list[Mapping[str, Any]],
    review_files: list[Path],
) -> list[str]:
    """Validate the legacy IOT-T046 structural audit repository policy."""

    errors: list[str] = []
    selected = payload["selection"]["selected_articles"]
    for relative in selected:
        candidate = root / relative
        if not candidate.is_file() or candidate.is_symlink():
            errors.append("REPOSITORY:selection:canonical-file-missing-or-unsafe")

    if review_files:
        errors.append("REPOSITORY:review-records:must-remain-empty")

    selected_set = set(selected)
    record_content_paths: list[str] = []
    is_prepared = payload["status"] == "PREPARED"
    for record in source_records:
        content_path = record.get("content_path")
        if isinstance(content_path, str):
            record_content_paths.append(content_path)
        if not is_prepared and content_path not in selected_set:
            errors.append("REPOSITORY:source-audits:record-outside-selection")
        if (
            record.get("audit_kind") != "STRUCTURAL"
            or record.get("auditor_type") != "AGENT"
            or record.get("auditor_role") != "STRUCTURAL_AUDITOR"
        ):
            errors.append("REPOSITORY:source-audits:non-structural-record")
        transition = record.get("status_transition")
        if (
            not isinstance(transition, Mapping)
            or transition.get("from") != transition.get("to")
        ):
            errors.append("REPOSITORY:source-audits:status-transition-not-noop")
        if record.get("supersedes") is not None:
            errors.append("REPOSITORY:source-audits:supersession-outside-pilot")

    if not is_prepared and len(source_records) > len(selected):
        errors.append("REPOSITORY:source-audits:records-exceed-selection")
    if len(record_content_paths) != len(set(record_content_paths)):
        errors.append("REPOSITORY:source-audits:duplicate-content-record")
    completed_articles = payload["progress"]["completed_articles"]
    if len(source_records) < completed_articles:
        errors.append("REPOSITORY:source-audits:records-below-completed-count")
    if (
        payload["status"] in {"CLOSING", "PAUSED", "COMPLETE", "SUPERSEDED"}
        and len(source_records) != completed_articles
    ):
        errors.append("REPOSITORY:source-audits:settled-count-mismatch")
    if completed_articles and any(
        record.get("revocation") is not None or record.get("outcome") == "ERROR"
        for record in source_records
    ):
        errors.append("REPOSITORY:source-audits:completed-record-not-current")

    authority_path = root / "data/trust-authorities.yml"
    if authority_path.exists():
        try:
            authority = trust_records.load_record(authority_path)
        except trust_records.TrustRecordError:
            errors.append("REPOSITORY:trust-authorities:invalid-yaml")
        else:
            actors = authority.get("actors")
            entries = authority.get("entries")
            if not isinstance(actors, list) or not actors:
                errors.append("REPOSITORY:trust-authorities:actors-required")
            else:
                for actor in actors:
                    if (
                        not isinstance(actor, Mapping)
                        or actor.get("actor_type") != "AGENT"
                        or actor.get("allowed_roles") != ["STRUCTURAL_AUDITOR"]
                    ):
                        errors.append(
                            "REPOSITORY:trust-authorities:structural-agent-only"
                        )
            if entries != []:
                errors.append("REPOSITORY:trust-authorities:entries-must-be-empty")
    elif source_records:
        errors.append("REPOSITORY:trust-authorities:required-for-source-records")

    return errors


def validate_git_scope(
    payload: Mapping[str, Any],
    *,
    root: Path = ROOT,
) -> list[str]:
    """Verify activation ref and all post-activation paths fail closed."""

    activation_ref = payload["activation"]["ref"]
    if activation_ref is None:
        return []
    code, _ = _git_output(root, "cat-file", "-e", f"{activation_ref}^{{commit}}")
    if code != 0:
        return ["GIT:activation-ref:not-a-local-commit"]
    code, _ = _git_output(root, "merge-base", "--is-ancestor", activation_ref, "HEAD")
    if code != 0:
        return ["GIT:activation-ref:not-an-ancestor-of-head"]

    code, tracked = _git_output(
        root,
        "diff",
        "--name-only",
        "--no-renames",
        activation_ref,
        "--",
    )
    if code != 0:
        return ["GIT:worktree:diff-enumeration-failed"]
    code, untracked = _git_output(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
    )
    if code != 0:
        return ["GIT:worktree:untracked-enumeration-failed"]

    allowed_rules = [
        normalized
        for raw in payload["allowed_mutations"]
        if (normalized := _normalize_rule_path(raw)) is not None
    ]
    changed = {
        line.strip()
        for line in f"{tracked}\n{untracked}".splitlines()
        if line.strip()
    }
    if any(not _path_is_allowed(path, allowed_rules) for path in changed):
        return ["GIT:worktree:change-outside-allowed-mutations"]
    return []


def validate_repository_state(
    payload: Mapping[str, Any],
    *,
    root: Path = ROOT,
) -> list[str]:
    """Bind contract counters and mode-specific invariants to the repository."""

    errors: list[str] = []
    source_files = _record_files(root / "data/source-audits")
    review_files = _record_files(root / "data/review-records")
    source_records: list[Mapping[str, Any]] = []
    for path in source_files:
        try:
            source_records.append(trust_records.load_record(path))
        except trust_records.TrustRecordError:
            errors.append("REPOSITORY:source-audits:invalid-yaml-record")

    if payload["scope"]["mode"] == "STRUCTURAL_SHADOW_AUDIT":
        errors.extend(
            _validate_structural_shadow_audit_state(
                payload,
                root=root,
                source_records=source_records,
                review_files=review_files,
            )
        )

    if root == ROOT:
        expected_trust = payload["baseline"]["expected_trust"]
        if len(source_records) != expected_trust["source_records"]:
            errors.append("REPOSITORY:source-audits:count-drift")
        if len(review_files) != expected_trust["review_records"]:
            errors.append("REPOSITORY:review-records:count-drift")

        inventory = content_inventory.content_inventory()
        totals = inventory["totals"]
        expected_inventory = payload["baseline"]["expected_inventory"]
        if totals["content_files"] != expected_inventory["canonical_content"]:
            errors.append("REPOSITORY:baseline:canonical-content-drift")
        if totals["plan_topics"] != expected_inventory["plan_topics"]:
            errors.append("REPOSITORY:baseline:plan-topics-drift")

        try:
            trust = validate_trust_state.validate_repository_trust(
                repo_root=root,
                baseline_mode=True,
            )
        except (OSError, RuntimeError, ValueError):
            errors.append("REPOSITORY:trust-state:validation-error")
        else:
            if trust.issues:
                errors.append("REPOSITORY:trust-state:issues-present")
            summary = trust.summary
            for field in (
                "source_records",
                "review_records",
                "legacy_unbound",
                "evidence_bound_review",
                "verified",
                "approved",
            ):
                if getattr(summary, field) != expected_trust[field]:
                    errors.append(f"REPOSITORY:trust-state:{field}-drift")

    return sorted(set(errors))


def _schema_location(error: Any) -> str:
    return ".".join(str(part) for part in error.absolute_path) or "<root>"


def validate_payload(
    payload: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> list[str]:
    """Return stable schema and lifecycle errors for one decoded contract."""

    errors = [
        f"SCHEMA:{_schema_location(error)}:{error.validator}"
        for error in Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        ).iter_errors(payload)
    ]
    if errors:
        return sorted(set(errors))

    status = payload["status"]
    scope = payload["scope"]
    budget = payload["budget"]
    authority = payload["external_action_authority"]
    authority_grant = payload["external_action_grant"]
    selection = payload["selection"]["selected_articles"]
    selection_rationale = payload["selection"]["rationale"]
    progress = payload["progress"]
    activation = payload["activation"]
    next_action = payload["next_action"]
    uses_article_selection = _uses_article_selection(payload)

    if payload["goal_id"] != scope["task_id"]:
        errors.append("SEMANTIC:scope.task_id:must-match-goal-id")
    if scope["first_batch_articles"] > scope["max_articles"]:
        errors.append("SEMANTIC:scope:first-batch-exceeds-goal-maximum")
    if budget["max_articles"] != scope["max_articles"]:
        errors.append("SEMANTIC:budget.max_articles:must-match-scope-maximum")
    if budget["max_parallel_writers"] != 1:
        errors.append("SEMANTIC:budget.max_parallel_writers:must-be-one")
    if budget["max_parallel_agents"] < budget["max_parallel_writers"]:
        errors.append("SEMANTIC:budget:max-agents-below-writers")

    limits = (
        ("completed_batches", "max_batches"),
        ("completed_articles", "max_articles"),
        ("completed_commits", "max_commits"),
    )
    for progress_key, budget_key in limits:
        if progress[progress_key] > budget[budget_key]:
            errors.append(f"SEMANTIC:progress.{progress_key}:budget-exceeded")
    if len(selection) > scope["max_articles"]:
        errors.append("SEMANTIC:selection.selected_articles:goal-maximum-exceeded")
    if progress["completed_articles"] > len(selection):
        errors.append("SEMANTIC:progress.completed_articles:exceeds-selection")
    if progress["no_external_delta_batches"] > progress["completed_batches"]:
        errors.append("SEMANTIC:progress.no-external-delta:exceeds-completed-batches")
    if (
        uses_article_selection
        and progress["completed_batches"] > progress["completed_articles"]
    ):
        errors.append("SEMANTIC:progress.completed_batches:exceeds-completed-articles")

    check_ids = [check["id"] for check in payload["acceptance_checks"]]
    if len(check_ids) != len(set(check_ids)):
        errors.append("SEMANTIC:acceptance_checks:id-must-be-unique")

    if any(authority.values()) and authority_grant is None:
        errors.append("SEMANTIC:external_action_grant:required-for-authority")
    if not any(authority.values()) and authority_grant is not None:
        errors.append("SEMANTIC:external_action_grant:authority-required-for-grant")

    normalized_rules: dict[str, list[str]] = {}
    for key in ("allowed_mutations", "forbidden_mutations"):
        normalized_rules[key] = []
        for raw in payload[key]:
            normalized = _normalize_rule_path(raw)
            if normalized is None:
                errors.append(f"SEMANTIC:{key}:unsafe-repository-path")
                continue
            normalized_rules[key].append(normalized)
    if any(
        _path_rules_overlap(allowed, forbidden)
        for allowed in normalized_rules["allowed_mutations"]
        for forbidden in normalized_rules["forbidden_mutations"]
    ):
        errors.append("SEMANTIC:mutation-paths:allowed-forbidden-overlap")

    superseded_by = payload["superseded_by"]
    if status == "SUPERSEDED":
        if superseded_by is None or superseded_by == payload["goal_id"]:
            errors.append("SEMANTIC:superseded_by:terminal-successor-required")
    elif superseded_by is not None:
        errors.append("SEMANTIC:superseded_by:only-valid-for-superseded-status")

    if status == "PREPARED":
        if activation["ref"] is not None or activation["activated_at"] is not None:
            errors.append("SEMANTIC:activation:prepared-must-be-empty")
        if selection:
            errors.append("SEMANTIC:selection:prepared-must-be-empty")
        if selection_rationale is not None:
            errors.append("SEMANTIC:selection:prepared-rationale-must-be-empty")
        if any(
            progress[key] != 0
            for key in (
                "completed_batches",
                "completed_articles",
                "completed_commits",
                "no_external_delta_batches",
            )
        ):
            errors.append("SEMANTIC:progress:prepared-counters-must-be-zero")
        if next_action["kind"] != "ACTIVATE_AND_RUN_FIRST_SLICE":
            errors.append("SEMANTIC:next_action:prepared-kind-mismatch")
        if next_action["requires_activation"] is not True:
            errors.append("SEMANTIC:next_action:prepared-must-require-activation")

    if status == "ACTIVE":
        if activation["ref"] is None or activation["activated_at"] is None:
            errors.append("SEMANTIC:activation:active-requires-snapshot")
        if payload["activated_by"].startswith("PENDING"):
            errors.append("SEMANTIC:activated_by:active-cannot-be-pending")
        if uses_article_selection and not selection:
            errors.append("SEMANTIC:selection:active-requires-article")
        if selection_rationale is None:
            errors.append("SEMANTIC:selection:active-requires-rationale")
        if (
            uses_article_selection
            and progress["completed_batches"] == 0
            and len(selection) != scope["first_batch_articles"]
        ):
            errors.append("SEMANTIC:selection:active-first-batch-size-mismatch")
        if (
            progress["completed_batches"] == 0
            and not uses_article_selection
            and selection
        ):
            errors.append("SEMANTIC:selection:non-article-goal-must-stay-empty")
        if next_action["kind"].startswith("ACTIVATE"):
            errors.append("SEMANTIC:next_action:active-kind-cannot-be-activate")
        if next_action["requires_activation"] is not False:
            errors.append("SEMANTIC:next_action:active-cannot-require-activation")
        if progress["no_external_delta_batches"] >= PAUSE_AFTER_NO_EXTERNAL_DELTA:
            errors.append("SEMANTIC:status:active-must-pause-after-three-no-delta-batches")
        if (
            progress["completed_batches"] >= budget["max_batches"]
            or (
                uses_article_selection
                and progress["completed_articles"] >= budget["max_articles"]
            )
            or progress["completed_commits"] >= budget["max_commits"]
        ):
            errors.append("SEMANTIC:status:active-cannot-have-exhausted-budget")

    if status == "CLOSING":
        if activation["ref"] is None or activation["activated_at"] is None:
            errors.append("SEMANTIC:activation:closing-requires-prior-activation")
        if progress["completed_batches"] < 1:
            errors.append("SEMANTIC:progress:closing-requires-finished-slice")
        if uses_article_selection and progress["completed_articles"] < 1:
            errors.append("SEMANTIC:progress:closing-requires-finished-article")
        if uses_article_selection and progress["completed_articles"] != len(selection):
            errors.append("SEMANTIC:progress:closing-must-cover-selection")
        if (
            next_action["kind"] != "RUN_GOAL_CLOSE_CHECKS"
            or next_action["requires_activation"]
        ):
            errors.append("SEMANTIC:next_action:closing-kind-mismatch")

    if status == "PAUSED":
        if activation["ref"] is None or activation["activated_at"] is None:
            errors.append("SEMANTIC:activation:paused-requires-prior-activation")
        if uses_article_selection and not selection:
            errors.append("SEMANTIC:selection:paused-requires-article")
        if next_action["requires_activation"] is not False:
            errors.append("SEMANTIC:next_action:paused-cannot-require-activation")

    if status == "BLOCKED":
        if next_action["kind"] != "WAIT_FOR_USER_OR_EXTERNAL_CHANGE":
            errors.append("SEMANTIC:next_action:blocked-kind-mismatch")
        if next_action["requires_activation"] is not False:
            errors.append("SEMANTIC:next_action:blocked-cannot-require-activation")

    if status == "COMPLETE":
        if activation["ref"] is None or activation["activated_at"] is None:
            errors.append("SEMANTIC:activation:complete-requires-prior-activation")
        if progress["completed_batches"] < 1:
            errors.append("SEMANTIC:progress:complete-requires-finished-slice")
        if uses_article_selection and progress["completed_articles"] < 1:
            errors.append("SEMANTIC:progress:complete-requires-finished-article")
        if uses_article_selection and progress["completed_articles"] != len(selection):
            errors.append("SEMANTIC:progress:complete-must-cover-selection")
        if next_action["kind"] != "NONE" or next_action["requires_activation"]:
            errors.append("SEMANTIC:next_action:complete-must-be-none")

    if status == "SUPERSEDED":
        if next_action["kind"] != "NONE" or next_action["requires_activation"]:
            errors.append("SEMANTIC:next_action:superseded-must-be-none")

    return sorted(set(errors))


def load_and_validate(
    goal_path: Path = GOAL_PATH,
    schema_path: Path = SCHEMA_PATH,
    lock_path: Path = LOCK_PATH,
    *,
    check_repository: bool = True,
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        schema = trust_records.load_schema(schema_path)
    except trust_records.TrustRecordError as exc:
        return None, [f"GOAL_{exc.code}"]
    try:
        payload = trust_records.load_record(goal_path)
    except trust_records.TrustRecordError as exc:
        return None, [f"GOAL_{exc.code}"]
    errors = validate_payload(payload, schema)
    if errors:
        return payload, errors
    lock, lock_errors = load_lock(lock_path)
    if lock_errors:
        return payload, lock_errors
    assert lock is not None
    errors.extend(validate_lock(payload, lock))
    if check_repository and not errors:
        errors.extend(validate_repository_state(payload))
        errors.extend(validate_git_scope(payload))
    return payload, sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal", type=Path, default=GOAL_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--lock", type=Path, default=LOCK_PATH)
    parser.add_argument(
        "--print-immutable-hash",
        action="store_true",
        help="print the current immutable contract hash without accepting it",
    )
    args = parser.parse_args()

    if args.print_immutable_hash:
        try:
            schema = trust_records.load_schema(args.schema)
            payload = trust_records.load_record(args.goal)
        except trust_records.TrustRecordError as exc:
            print(f"ACTIVE_GOAL_INVALID GOAL_{exc.code}", file=sys.stderr)
            return 1
        errors = validate_payload(payload, schema)
        if errors:
            for error in errors:
                print(f"ACTIVE_GOAL_INVALID {error}", file=sys.stderr)
            return 1
        print(immutable_sha256(payload))
        return 0

    payload, errors = load_and_validate(args.goal, args.schema, args.lock)
    if errors:
        for error in errors:
            print(f"ACTIVE_GOAL_INVALID {error}", file=sys.stderr)
        return 1

    assert payload is not None
    print(
        "ACTIVE_GOAL_OK"
        f" goal_id={payload['goal_id']}"
        f" status={payload['status']}"
        f" selected={len(payload['selection']['selected_articles'])}"
        f" completed_batches={payload['progress']['completed_batches']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
