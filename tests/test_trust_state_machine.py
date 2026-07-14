from __future__ import annotations

import copy
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any
from unittest import mock

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from tools import trust_records
from tools.iot_domain import LAYERS, parse_document


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATHS = {
    "source": ROOT / "schemas/source-audit.schema.json",
    "review": ROOT / "schemas/review-record.schema.json",
    "frontmatter": ROOT / "schemas/content-frontmatter.schema.json",
}
FIXTURE_ROOTS = {
    "source": ROOT / "tests/fixtures/source-audits",
    "review": ROOT / "tests/fixtures/review-records",
}

SOURCE_STATUSES = ("UNKNOWN", "UNVERIFIED", "PARTIAL", "VERIFIED")
REVIEW_STATUSES = (
    "UNKNOWN",
    "UNREVIEWED",
    "IN_REVIEW",
    "HUMAN_APPROVED",
    "NEEDS_CHANGES",
)
LEGAL_SOURCE_TRANSITIONS = {
    ("UNKNOWN", "UNKNOWN"),
    ("UNKNOWN", "PARTIAL"),
    ("UNKNOWN", "VERIFIED"),
    ("UNVERIFIED", "UNVERIFIED"),
    ("UNVERIFIED", "PARTIAL"),
    ("UNVERIFIED", "VERIFIED"),
    ("PARTIAL", "PARTIAL"),
    ("PARTIAL", "VERIFIED"),
    ("VERIFIED", "VERIFIED"),
}
LEGAL_REVIEW_TRANSITIONS = {
    ("UNKNOWN", "IN_REVIEW"): "START_REVIEW",
    ("UNREVIEWED", "IN_REVIEW"): "START_REVIEW",
    ("NEEDS_CHANGES", "IN_REVIEW"): "START_REVIEW",
    ("HUMAN_APPROVED", "IN_REVIEW"): "START_REVIEW",
    ("IN_REVIEW", "NEEDS_CHANGES"): "REQUEST_CHANGES",
    ("IN_REVIEW", "HUMAN_APPROVED"): "APPROVE",
}
CANONICAL_LAYER_SLUGS = tuple(layer.slug for layer in LAYERS)
EXPECTED_SEMANTIC_ERRORS = {
    "source": {
        "semantic-invalid-body-hash-mismatch.yml": "body hash does not match current content",
        "semantic-invalid-dangling-reference.yml": "claim links unknown source reference",
        "semantic-invalid-overlapping-claim.yml": "covered and uncovered claim ids overlap",
        "semantic-invalid-time-order.yml": "source evidence was retrieved after the audit",
    },
    "review": {
        "semantic-invalid-body-hash-mismatch.yml": "body hash does not match current content",
        "semantic-invalid-dangling-audit.yml": "linked audit id does not resolve",
        "semantic-invalid-dangling-review.yml": "superseded review id does not resolve",
        "semantic-invalid-author-auditor-overlap.yml": "author is also a fact auditor",
        "semantic-invalid-linked-auditor-approval.yml": "approver is also a fact auditor",
        "semantic-invalid-linked-auditor-set-mismatch.yml": "declared linked auditors do not match audit records",
        "semantic-invalid-self-approval.yml": "approver is also an author",
        "semantic-invalid-time-order.yml": "review revocation predates the review",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path}: expected a JSON object")
    return payload


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path}: expected a YAML mapping")
    return payload


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _source_transition_is_legal(before: str, after: str) -> bool:
    return (before, after) in LEGAL_SOURCE_TRANSITIONS


def _review_transition_decision(before: str, after: str) -> str | None:
    return LEGAL_REVIEW_TRANSITIONS.get((before, after))


def _content_path_matches_id(record: dict[str, Any]) -> bool:
    return Path(str(record.get("content_path", ""))).stem == record.get("content_id")


def _source_semantic_errors(
    record: dict[str, Any],
    *,
    current_body_sha256: str,
) -> list[str]:
    errors: list[str] = []
    transition = record["status_transition"]
    if not _source_transition_is_legal(transition["from"], transition["to"]):
        errors.append("illegal source transition")
    if not _content_path_matches_id(record):
        errors.append("content_path does not match content_id")
    if record.get("supersedes") == record.get("audit_id"):
        errors.append("audit cannot supersede itself")

    audited_at = _timestamp(record["audited_at"])
    if any(
        _timestamp(reference["retrieved_at"]) > audited_at
        for reference in record["source_references"]
    ):
        errors.append("source evidence was retrieved after the audit")
    revocation = record.get("revocation")
    if revocation is not None and _timestamp(revocation["revoked_at"]) < audited_at:
        errors.append("audit revocation predates the audit")
    if not str(record["auditor_id"]).startswith(record["auditor_type"].lower() + "-"):
        errors.append("auditor id/type mismatch")

    # Revoked records remain valid history, but are intentionally not current
    # evidence. A stale hash on such a record is therefore not a malformed
    # historical record.
    if record.get("revocation") is None and record["body_sha256"] != current_body_sha256:
        errors.append("body hash does not match current content")

    reference_ids = [item["reference_id"] for item in record["source_references"]]
    if len(reference_ids) != len(set(reference_ids)):
        errors.append("duplicate source reference id")
    coverage = record.get("claim_coverage")
    if coverage is not None:
        claim_ids = [claim["claim_id"] for claim in coverage["claims"]]
        if len(claim_ids) != len(set(claim_ids)):
            errors.append("duplicate claim id")
        if set(claim_ids) & set(coverage["uncovered_claim_ids"]):
            errors.append("covered and uncovered claim ids overlap")
        for claim in coverage["claims"]:
            dangling = set(claim["reference_ids"]) - set(reference_ids)
            if dangling:
                errors.append("claim links unknown source reference")
    return errors


def _effective_source_records(
    records: list[dict[str, Any]],
    *,
    current_body_sha256: str,
) -> list[dict[str, Any]]:
    current = [
        record
        for record in records
        if record.get("revocation") is None
        and record.get("body_sha256") == current_body_sha256
    ]
    superseded_ids = {
        record["supersedes"]
        for record in records
        if record.get("supersedes") is not None
    }
    return [record for record in current if record["audit_id"] not in superseded_ids]


def _project_source_status(
    records: list[dict[str, Any]],
    *,
    current_body_sha256: str,
    default: str = "UNVERIFIED",
) -> str:
    effective = _effective_source_records(
        records,
        current_body_sha256=current_body_sha256,
    )
    claim_targets = {
        record["status_transition"]["to"]
        for record in effective
        if record["audit_kind"] == "CLAIM_VERIFICATION"
        and not _source_semantic_errors(
            record,
            current_body_sha256=current_body_sha256,
        )
    }
    if "VERIFIED" in claim_targets:
        return "VERIFIED"
    if "PARTIAL" in claim_targets:
        return "PARTIAL"
    return default


def _review_semantic_errors(
    record: dict[str, Any],
    *,
    source_records_by_id: dict[str, dict[str, Any]],
    review_records_by_id: dict[str, dict[str, Any]],
    current_body_sha256: str,
) -> list[str]:
    errors: list[str] = []
    transition = record["status_transition"]
    expected_decision = _review_transition_decision(
        transition["from"], transition["to"]
    )
    if expected_decision != record["decision"]:
        errors.append("illegal review transition or decision")
    if not _content_path_matches_id(record):
        errors.append("content_path does not match content_id")
    if record.get("supersedes") == record.get("review_id"):
        errors.append("review cannot supersede itself")
    if not str(record["reviewer_id"]).startswith(record["reviewer_type"].lower() + "-"):
        errors.append("reviewer id/type mismatch")

    reviewed_at = _timestamp(record["reviewed_at"])
    revocation = record.get("revocation")
    if revocation is not None and _timestamp(revocation["revoked_at"]) < reviewed_at:
        errors.append("review revocation predates the review")
    if revocation is None and record["body_sha256"] != current_body_sha256:
        errors.append("body hash does not match current content")
    evidence_body_sha256 = (
        record["body_sha256"] if revocation is not None else current_body_sha256
    )

    if record["decision"] != "APPROVE":
        return errors

    predecessor = review_records_by_id.get(record["supersedes"])
    if predecessor is None:
        errors.append("superseded review id does not resolve")
    elif (
        predecessor["content_id"] != record["content_id"]
        or predecessor["content_path"] != record["content_path"]
        or predecessor["body_sha256"] != record["body_sha256"]
        or predecessor["status_transition"]["to"] != "IN_REVIEW"
        or predecessor.get("revocation") is not None
    ):
        errors.append("approval predecessor is not an active matching IN_REVIEW record")
    elif _timestamp(predecessor["reviewed_at"]) > reviewed_at:
        errors.append("approval predates its IN_REVIEW predecessor")

    linked_ids = record["linked_audit_ids"]
    linked_records: list[dict[str, Any]] = []
    for audit_id in linked_ids:
        audit = source_records_by_id.get(audit_id)
        if audit is None:
            errors.append("linked audit id does not resolve")
            continue
        linked_records.append(audit)
        if _timestamp(audit["audited_at"]) > reviewed_at:
            errors.append("approval predates linked audit evidence")
        if (
            audit["content_id"] != record["content_id"]
            or audit["content_path"] != record["content_path"]
            or audit["body_sha256"] != record["body_sha256"]
        ):
            errors.append("linked audit targets different content identity")

    globally_effective = _effective_source_records(
        list(source_records_by_id.values()),
        current_body_sha256=evidence_body_sha256,
    )
    globally_effective_by_id = {
        item["audit_id"]: item for item in globally_effective
    }
    effective_ids = set(globally_effective_by_id) & set(linked_ids)
    effective_linked = [
        globally_effective_by_id[audit_id]
        for audit_id in linked_ids
        if audit_id in effective_ids
    ]
    if set(linked_ids) != effective_ids:
        errors.append("linked audit is stale, revoked, or superseded")
    if (
        _project_source_status(
            linked_records,
            current_body_sha256=evidence_body_sha256,
        )
        != "VERIFIED"
    ):
        errors.append("linked audits do not project VERIFIED")

    independence = record["independence"]
    linked_auditor_ids = {item["auditor_id"] for item in effective_linked}
    declared_auditor_ids = set(independence["linked_auditor_ids"])
    author_ids = set(independence["author_ids"])
    reviewer_id = record["reviewer_id"]
    if declared_auditor_ids != linked_auditor_ids:
        errors.append("declared linked auditors do not match audit records")
    if reviewer_id in author_ids:
        errors.append("approver is also an author")
    if reviewer_id in linked_auditor_ids:
        errors.append("approver is also a fact auditor")
    if author_ids & linked_auditor_ids:
        errors.append("author is also a fact auditor")
    if independence["reviewer_is_author"] != (reviewer_id in author_ids):
        errors.append("reviewer_is_author declaration is false")
    if independence["reviewer_is_linked_auditor"] != (
        reviewer_id in linked_auditor_ids
    ):
        errors.append("reviewer_is_linked_auditor declaration is false")
    return errors


def _effective_review_records(
    records: list[dict[str, Any]],
    *,
    current_body_sha256: str,
) -> list[dict[str, Any]]:
    current = [
        record
        for record in records
        if record.get("revocation") is None
        and record.get("body_sha256") == current_body_sha256
    ]
    superseded_ids = {
        record["supersedes"]
        for record in records
        if record.get("supersedes") is not None
    }
    return [record for record in current if record["review_id"] not in superseded_ids]


class TrustSchemaFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {name: _load_json(path) for name, path in SCHEMA_PATHS.items()}
        cls.validators = {
            name: Draft202012Validator(schema, format_checker=FormatChecker())
            for name, schema in cls.schemas.items()
        }
        cls.source_fixtures = {
            path.name: _load_yaml(path)
            for path in sorted(FIXTURE_ROOTS["source"].glob("*.yml"))
        }
        cls.review_fixtures = {
            path.name: _load_yaml(path)
            for path in sorted(FIXTURE_ROOTS["review"].glob("*.yml"))
        }
        fixture_content_path = cls.source_fixtures[
            "valid-claim-unverified-to-verified.yml"
        ]["content_path"]
        cls.current_hash = parse_document(
            ROOT / fixture_content_path,
            repo_root=ROOT,
        ).body_sha256
        cls.source_records_by_id = {
            record["audit_id"]: record
            for name, record in cls.source_fixtures.items()
            if name.startswith("valid-")
        }
        cls.review_records_by_id = {
            record["review_id"]: record
            for name, record in cls.review_fixtures.items()
            if name.startswith("valid-")
        }

    def test_schemas_are_valid_draft_2020_12_contracts(self) -> None:
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                self.assertEqual(
                    "https://json-schema.org/draft/2020-12/schema",
                    schema.get("$schema"),
                )
                Draft202012Validator.check_schema(schema)

    def test_fixture_prefixes_encode_schema_and_semantic_expectations(self) -> None:
        for kind, fixture_root in FIXTURE_ROOTS.items():
            validator = self.validators[kind]
            fixture_paths = sorted(fixture_root.glob("*.yml"))
            self.assertTrue(fixture_paths, f"no {kind} fixtures found")
            prefixes = {path.name.split("-", 1)[0] for path in fixture_paths}
            self.assertIn("valid", prefixes)
            self.assertTrue(
                any(path.name.startswith("invalid-schema-") for path in fixture_paths),
                f"no invalid-schema {kind} fixture found",
            )
            self.assertTrue(
                any(path.name.startswith("semantic-invalid-") for path in fixture_paths),
                f"no semantic-invalid {kind} fixture found",
            )

            for path in fixture_paths:
                with self.subTest(kind=kind, fixture=path.name):
                    payload = _load_yaml(path)
                    errors = sorted(
                        validator.iter_errors(payload),
                        key=lambda error: tuple(str(part) for part in error.absolute_path),
                    )
                    if path.name.startswith("invalid-schema-"):
                        self.assertTrue(errors, f"{path.name} unexpectedly passed schema")
                    elif path.name.startswith(("valid-", "semantic-invalid-")):
                        self.assertEqual([], errors, f"{path.name} failed schema")
                    else:
                        self.fail(f"unrecognized fixture contract prefix: {path.name}")

    def test_fixture_semantics_are_caught_by_reference_oracle(self) -> None:
        for name, record in self.source_fixtures.items():
            if name.startswith(("valid-", "semantic-invalid-")):
                errors = _source_semantic_errors(
                    record,
                    current_body_sha256=self.current_hash,
                )
                with self.subTest(kind="source", fixture=name):
                    if name.startswith("valid-"):
                        self.assertEqual([], errors)
                    else:
                        self.assertTrue(errors)
                        self.assertIn(EXPECTED_SEMANTIC_ERRORS["source"][name], errors)
        for name, record in self.review_fixtures.items():
            if name.startswith(("valid-", "semantic-invalid-")):
                errors = _review_semantic_errors(
                    record,
                    source_records_by_id=self.source_records_by_id,
                    review_records_by_id=self.review_records_by_id,
                    current_body_sha256=self.current_hash,
                )
                with self.subTest(kind="review", fixture=name):
                    if name.startswith("valid-"):
                        self.assertEqual([], errors)
                    else:
                        self.assertTrue(errors)
                        self.assertIn(EXPECTED_SEMANTIC_ERRORS["review"][name], errors)

    def test_complete_source_transition_matrix_and_schema_templates(self) -> None:
        observed: set[tuple[str, str]] = set()
        for before, after in product(SOURCE_STATUSES, repeat=2):
            if before == after:
                record = copy.deepcopy(
                    self.source_fixtures["valid-structural-auditable-noop.yml"]
                )
            elif after == "PARTIAL":
                record = copy.deepcopy(
                    self.source_fixtures["valid-claim-unverified-to-partial.yml"]
                )
            else:
                record = copy.deepcopy(
                    self.source_fixtures["valid-claim-unverified-to-verified.yml"]
                )
            record["status_transition"] = {"from": before, "to": after}
            errors = list(self.validators["source"].iter_errors(record))
            with self.subTest(before=before, after=after):
                if _source_transition_is_legal(before, after):
                    self.assertEqual([], errors)
                    observed.add((before, after))
                else:
                    self.assertTrue(errors, "illegal source transition passed schema")
        self.assertEqual(LEGAL_SOURCE_TRANSITIONS, observed)

    def test_complete_review_transition_matrix_and_schema_templates(self) -> None:
        fixture_for_decision = {
            "START_REVIEW": "valid-start-review.yml",
            "REQUEST_CHANGES": "valid-request-changes.yml",
            "APPROVE": "valid-human-approved.yml",
        }
        observed: dict[tuple[str, str], str] = {}
        for before, after in product(REVIEW_STATUSES, repeat=2):
            expected = _review_transition_decision(before, after)
            decision = expected
            if decision is None:
                decision = (
                    "APPROVE"
                    if after == "HUMAN_APPROVED"
                    else "REQUEST_CHANGES"
                    if after == "NEEDS_CHANGES"
                    else "START_REVIEW"
                )
            record = copy.deepcopy(self.review_fixtures[fixture_for_decision[decision]])
            record["status_transition"] = {"from": before, "to": after}
            errors = list(self.validators["review"].iter_errors(record))
            with self.subTest(before=before, after=after):
                if expected is not None:
                    self.assertEqual([], errors)
                    observed[(before, after)] = expected
                else:
                    self.assertTrue(errors, "illegal review transition passed schema")
        self.assertEqual(LEGAL_REVIEW_TRANSITIONS, observed)

    def test_structural_check_result_never_elevates_source_status(self) -> None:
        template = self.source_fixtures["valid-structural-auditable-noop.yml"]
        outcomes = {"PASS": "AUDITABLE", "FAIL": "NEEDS_CHANGES", "ERROR": "ERROR"}
        for status, (result, outcome) in product(SOURCE_STATUSES, outcomes.items()):
            record = copy.deepcopy(template)
            record["outcome"] = outcome
            record["status_transition"] = {"from": status, "to": status}
            record["structural_checks"][0]["result"] = result
            with self.subTest(status=status, checklist_result=result):
                self.assertEqual([], list(self.validators["source"].iter_errors(record)))
                self.assertEqual(
                    status,
                    _project_source_status(
                        [record],
                        current_body_sha256=self.current_hash,
                        default=status,
                    ),
                )

    def test_claim_promotions_are_fail_closed(self) -> None:
        partial = self.source_fixtures["valid-claim-unverified-to-partial.yml"]
        verified = self.source_fixtures["valid-claim-unverified-to-verified.yml"]
        self.assertEqual([], list(self.validators["source"].iter_errors(partial)))
        self.assertEqual([], list(self.validators["source"].iter_errors(verified)))

        partial_mutations = (
            lambda record: record["claim_coverage"].update(uncovered_claim_ids=[]),
            lambda record: record["claim_coverage"].update(blocking_issue_ids=["issue-blocked"]),
            lambda record: record["claim_coverage"]["claims"][0].update(result="UNVERIFIED"),
            lambda record: record["claim_coverage"]["claims"][0].update(result="BLOCKED"),
        )
        for mutate in partial_mutations:
            record = copy.deepcopy(partial)
            mutate(record)
            self.assertTrue(list(self.validators["source"].iter_errors(record)))

        verified_mutations = (
            lambda record: record["claim_coverage"].update(uncovered_claim_ids=["claim-gap"]),
            lambda record: record["claim_coverage"].update(blocking_issue_ids=["issue-blocked"]),
            lambda record: record["claim_coverage"]["claims"][0].update(result="UNVERIFIED"),
            lambda record: record["claim_coverage"]["claims"][0].update(reference_ids=[]),
        )
        for mutate in verified_mutations:
            record = copy.deepcopy(verified)
            mutate(record)
            self.assertTrue(list(self.validators["source"].iter_errors(record)))

        agent_verified = copy.deepcopy(verified)
        agent_verified["auditor_id"] = "agent-content-author"
        agent_verified["auditor_type"] = "AGENT"
        self.assertTrue(list(self.validators["source"].iter_errors(agent_verified)))

    def test_hash_revocation_and_supersession_exclude_evidence_but_keep_history(self) -> None:
        old = copy.deepcopy(
            self.source_fixtures["valid-claim-unverified-to-verified.yml"]
        )
        old["audit_id"] = "audit-20260711-history-old"
        new = copy.deepcopy(old)
        new["audit_id"] = "audit-20260711-history-new"
        new["supersedes"] = old["audit_id"]
        history = [old, new]
        self.assertEqual([new["audit_id"]], [r["audit_id"] for r in _effective_source_records(history, current_body_sha256=self.current_hash)])
        new["revocation"] = copy.deepcopy(self.source_fixtures["valid-revoked.yml"]["revocation"])
        self.assertEqual([], _effective_source_records(history, current_body_sha256=self.current_hash))
        self.assertEqual(2, len(history))
        stale = copy.deepcopy(old)
        stale["body_sha256"] = "f" * 64
        self.assertEqual("UNVERIFIED", _project_source_status([stale], current_body_sha256=self.current_hash))

        stale_revoked_source = copy.deepcopy(self.source_fixtures["valid-revoked.yml"])
        stale_revoked_source["body_sha256"] = "f" * 64
        self.assertEqual(
            [],
            _source_semantic_errors(
                stale_revoked_source,
                current_body_sha256=self.current_hash,
            ),
        )
        self.assertEqual(
            [],
            _effective_source_records(
                [stale_revoked_source],
                current_body_sha256=self.current_hash,
            ),
        )

        old_review = copy.deepcopy(self.review_fixtures["valid-human-approved.yml"])
        old_review["review_id"] = "review-20260711-history-old"
        new_review = copy.deepcopy(old_review)
        new_review["review_id"] = "review-20260711-history-new"
        new_review["supersedes"] = old_review["review_id"]
        review_history = [old_review, new_review]
        self.assertEqual([new_review["review_id"]], [r["review_id"] for r in _effective_review_records(review_history, current_body_sha256=self.current_hash)])
        new_review["revocation"] = copy.deepcopy(self.review_fixtures["valid-revoked.yml"]["revocation"])
        self.assertEqual([], _effective_review_records(review_history, current_body_sha256=self.current_hash))
        self.assertEqual(2, len(review_history))

        stale_revoked_review = copy.deepcopy(self.review_fixtures["valid-revoked.yml"])
        stale_revoked_review["body_sha256"] = "f" * 64
        historical_sources = copy.deepcopy(self.source_records_by_id)
        linked_audit_id = stale_revoked_review["linked_audit_ids"][0]
        historical_sources[linked_audit_id]["body_sha256"] = "f" * 64
        historical_reviews = copy.deepcopy(self.review_records_by_id)
        predecessor_id = stale_revoked_review["supersedes"]
        historical_reviews[predecessor_id]["body_sha256"] = "f" * 64
        self.assertEqual(
            [],
            _review_semantic_errors(
                stale_revoked_review,
                source_records_by_id=historical_sources,
                review_records_by_id=historical_reviews,
                current_body_sha256=self.current_hash,
            ),
        )
        self.assertEqual(
            [],
            _effective_review_records(
                [stale_revoked_review],
                current_body_sha256=self.current_hash,
            ),
        )

    def test_approval_rejects_a_globally_superseded_audit(self) -> None:
        old = copy.deepcopy(
            self.source_fixtures["valid-claim-unverified-to-verified.yml"]
        )
        successor = copy.deepcopy(old)
        successor["audit_id"] = "audit-20260711-claim-verified-successor"
        successor["status_transition"] = {"from": "VERIFIED", "to": "VERIFIED"}
        successor["supersedes"] = old["audit_id"]
        approval = copy.deepcopy(self.review_fixtures["valid-human-approved.yml"])
        approval["linked_audit_ids"] = [old["audit_id"]]
        errors = _review_semantic_errors(
            approval,
            source_records_by_id={old["audit_id"]: old, successor["audit_id"]: successor},
            review_records_by_id=self.review_records_by_id,
            current_body_sha256=self.current_hash,
        )
        self.assertIn("linked audit is stale, revoked, or superseded", errors)

    def test_enums_frontmatter_and_record_schemas_share_one_contract(self) -> None:
        enums = _load_yaml(ROOT / "data/content-enums.yml")
        source = set(enums["source_status"])
        review = set(enums["review_status"])
        self.assertEqual(source, set(self.schemas["frontmatter"]["properties"]["source_status"]["enum"]))
        self.assertEqual(source, set(self.schemas["source"]["$defs"]["source_status"]["enum"]))
        self.assertEqual(source, set(self.schemas["review"]["$defs"]["source_status"]["enum"]))
        self.assertEqual(review, set(self.schemas["frontmatter"]["properties"]["review_status"]["enum"]))
        self.assertEqual(review, set(self.schemas["review"]["$defs"]["review_status"]["enum"]))
        for schema in self.schemas.values():
            self.assertEqual(enums["schema_version"], schema["properties"]["schema_version"]["const"])
        source_transitions = {
            (before, after)
            for before, targets in enums["trust_state_machine"]["active_record_transitions"]["source_status"].items()
            for after in targets
        }
        review_transitions = {
            (before, after)
            for before, targets in enums["trust_state_machine"]["active_record_transitions"]["review_status"].items()
            for after in targets
        }
        self.assertEqual(LEGAL_SOURCE_TRANSITIONS, source_transitions)
        self.assertEqual(set(LEGAL_REVIEW_TRANSITIONS), review_transitions)

    def test_promotion_and_invalidation_contract_is_fail_closed(self) -> None:
        machine = _load_yaml(ROOT / "data/content-enums.yml")["trust_state_machine"]
        self.assertEqual(
            {
                "audit_kind": "CLAIM_VERIFICATION",
                "coverage_scope": "PARTIAL",
                "minimum_verified_claims": 1,
                "minimum_uncovered_claims": 1,
                "maximum_blocking_issues": 0,
            },
            machine["promotion_requirements"]["source_status"]["PARTIAL"],
        )
        self.assertEqual(
            {
                "audit_kind": "CLAIM_VERIFICATION",
                "auditor_type": "HUMAN",
                "coverage_scope": "ALL_CRITICAL_CLAIMS",
                "all_claims_verified": True,
                "minimum_references_per_claim": 1,
                "maximum_uncovered_claims": 0,
                "maximum_blocking_issues": 0,
            },
            machine["promotion_requirements"]["source_status"]["VERIFIED"],
        )
        self.assertEqual(
            {"maximum_source_status_effect": "NO_CHANGE"},
            machine["promotion_requirements"]["source_status"]["STRUCTURAL"],
        )
        self.assertEqual(
            {
                "decision": "APPROVE",
                "source_status_at_review": "VERIFIED",
                "reviewer_type": "HUMAN",
                "reviewer_role": "APPROVER",
                "reviewer_must_be_independent": True,
                "minimum_linked_audits": 1,
                "all_review_checks_pass": True,
                "body_hash_must_match": True,
            },
            machine["promotion_requirements"]["review_status"]["HUMAN_APPROVED"],
        )
        self.assertEqual(
            {
                "active": "ACTIVE",
                "superseded": "SUPERSEDED",
                "revoked": "REVOKED",
                "body_hash_mismatch": "STALE",
            },
            machine["record_lifecycle"],
        )
        self.assertEqual(
            {
                "BODY_HASH_MISMATCH": {
                    "source_record_effect": "STALE",
                    "review_record_effect": "STALE",
                    "source_status_projection": "RECOMPUTE_FROM_ACTIVE_EVIDENCE",
                    "default_source_status_projection": "UNVERIFIED",
                    "review_status_projection": "RECOMPUTE_FROM_ACTIVE_EVIDENCE",
                    "default_review_status_projection": "IN_REVIEW",
                    "preserve_history": True,
                },
                "SOURCE_REFERENCE_INVALIDATED": {
                    "source_record_effect": "RECOMPUTE",
                    "review_record_effect": "STALE_IF_LINKED",
                    "source_status_projection": "RECOMPUTE_FROM_ACTIVE_EVIDENCE",
                    "maximum_source_status_projection": "PARTIAL",
                    "review_status_projection": "IN_REVIEW",
                    "preserve_history": True,
                },
                "AUDIT_REVOKED": {
                    "source_record_effect": "REVOKED",
                    "review_record_effect": "STALE_IF_LINKED",
                    "source_status_projection": "RECOMPUTE_FROM_ACTIVE_EVIDENCE",
                    "review_status_projection": "IN_REVIEW",
                    "preserve_history": True,
                },
                "REVIEW_REVOKED": {
                    "source_record_effect": "NO_CHANGE",
                    "review_record_effect": "REVOKED",
                    "source_status_projection": "NO_CHANGE",
                    "review_status_projection": "IN_REVIEW",
                    "preserve_history": True,
                },
                "RECORD_SUPERSEDED": {
                    "source_record_effect": "SUPERSEDED_IF_SOURCE_RECORD",
                    "review_record_effect": "SUPERSEDED_IF_REVIEW_RECORD",
                    "projection_rule": "EXCLUDE_SUPERSEDED_RECORD",
                    "preserve_history": True,
                },
            },
            machine["derived_invalidation"],
        )
        self.assertEqual(
            {
                "source_evidence": "RETRIEVED_AT_LTE_AUDITED_AT",
                "source_revocation": "AUDITED_AT_LTE_REVOKED_AT",
                "review_predecessor": "PREDECESSOR_REVIEWED_AT_LTE_REVIEWED_AT",
                "linked_audit": "AUDITED_AT_LTE_REVIEWED_AT",
                "review_revocation": "REVIEWED_AT_LTE_REVOKED_AT",
            },
            machine["temporal_ordering"],
        )
        self.assertEqual(
            {
                "enabled": True,
                "mode": "FAIL_CLOSED",
                "on_missing_authority": "KEEP_DEFAULT",
                "default_source_status": "UNVERIFIED",
                "default_review_status": "IN_REVIEW",
                "required_authorities": [
                    "CURRENT_BODY_HASH",
                    "AUTHORITATIVE_AUTHOR_ACTOR_MAPPING",
                    "LOCKED_CRITICAL_CLAIM_INVENTORY",
                    "CROSS_RECORD_REFERENCE_VALIDATION",
                ],
            },
            machine["production_projection_gate"],
        )

    def test_temporal_rules_are_independently_enforced(self) -> None:
        source = copy.deepcopy(self.source_fixtures["valid-claim-unverified-to-verified.yml"])
        source["source_references"][0]["retrieved_at"] = "2026-07-11T08:30:00Z"
        self.assertEqual(
            ["source evidence was retrieved after the audit"],
            _source_semantic_errors(source, current_body_sha256=self.current_hash),
        )

        revoked_source = copy.deepcopy(self.source_fixtures["valid-revoked.yml"])
        revoked_source["revocation"]["revoked_at"] = "2026-07-11T08:00:00Z"
        self.assertEqual(
            ["audit revocation predates the audit"],
            _source_semantic_errors(revoked_source, current_body_sha256=self.current_hash),
        )

        approval = self.review_fixtures["valid-human-approved.yml"]
        future_predecessor = copy.deepcopy(self.review_records_by_id)
        future_predecessor[approval["supersedes"]] = copy.deepcopy(
            future_predecessor[approval["supersedes"]]
        )
        future_predecessor[approval["supersedes"]]["reviewed_at"] = "2026-07-11T10:00:00Z"
        self.assertIn(
            "approval predates its IN_REVIEW predecessor",
            _review_semantic_errors(
                approval,
                source_records_by_id=self.source_records_by_id,
                review_records_by_id=future_predecessor,
                current_body_sha256=self.current_hash,
            ),
        )

        future_audit = copy.deepcopy(self.source_records_by_id)
        linked_id = approval["linked_audit_ids"][0]
        future_audit[linked_id]["audited_at"] = "2026-07-11T10:00:00Z"
        self.assertIn(
            "approval predates linked audit evidence",
            _review_semantic_errors(
                approval,
                source_records_by_id=future_audit,
                review_records_by_id=self.review_records_by_id,
                current_body_sha256=self.current_hash,
            ),
        )

        revoked_review = copy.deepcopy(self.review_fixtures["valid-revoked.yml"])
        revoked_review["revocation"]["revoked_at"] = "2026-07-11T09:00:00Z"
        self.assertIn(
            "review revocation predates the review",
            _review_semantic_errors(
                revoked_review,
                source_records_by_id=self.source_records_by_id,
                review_records_by_id=self.review_records_by_id,
                current_body_sha256=self.current_hash,
            ),
        )

    def test_valid_fixture_hashes_match_current_canonical_body(self) -> None:
        for fixtures in (self.source_fixtures, self.review_fixtures):
            for name, record in fixtures.items():
                if not name.startswith("valid-"):
                    continue
                document = parse_document(ROOT / record["content_path"], repo_root=ROOT)
                with self.subTest(fixture=name):
                    self.assertEqual(document.body_sha256, record["body_sha256"])

    def test_human_approval_threshold_lives_in_external_record_contract(self) -> None:
        raw = (ROOT / "tests/fixtures/frontmatter/valid-technical-analysis.md").read_text(encoding="utf-8")
        payload = yaml.safe_load(raw.split("---", 2)[1])
        payload.update(review_status="HUMAN_APPROVED", last_reviewed="2026-07-11")
        payload["source_status"] = "PARTIAL"
        # Frontmatter v1 remains backward-compatible; it is a cache, not the
        # approval authority. The external review record is fail-closed.
        self.assertEqual([], list(self.validators["frontmatter"].iter_errors(payload)))
        review = copy.deepcopy(self.review_fixtures["valid-human-approved.yml"])
        review["source_status_at_review"] = "PARTIAL"
        self.assertTrue(list(self.validators["review"].iter_errors(review)))
        review["source_status_at_review"] = "VERIFIED"
        self.assertEqual([], list(self.validators["review"].iter_errors(review)))

    def test_nonhuman_actor_cannot_drive_human_review_status(self) -> None:
        for name in (
            "valid-start-review.yml",
            "valid-request-changes.yml",
            "valid-human-approved.yml",
        ):
            review = copy.deepcopy(self.review_fixtures[name])
            review["reviewer_id"] = "agent-content-reviewer"
            review["reviewer_type"] = "AGENT"
            with self.subTest(fixture=name):
                self.assertTrue(list(self.validators["review"].iter_errors(review)))

        disguised_agent = copy.deepcopy(self.review_fixtures["valid-start-review.yml"])
        disguised_agent["reviewer_id"] = "agent-content-reviewer"
        disguised_agent["reviewer_type"] = "HUMAN"
        self.assertTrue(list(self.validators["review"].iter_errors(disguised_agent)))

    def test_human_approval_evidence_cannot_be_empty(self) -> None:
        approved = self.review_fixtures["valid-human-approved.yml"]
        mutations = (
            lambda record: record.update(review_checks=[]),
            lambda record: record["independence"].update(author_ids=[]),
            lambda record: record["independence"].update(linked_auditor_ids=[]),
        )
        for mutate in mutations:
            record = copy.deepcopy(approved)
            mutate(record)
            self.assertTrue(list(self.validators["review"].iter_errors(record)))

    def test_canonical_paths_and_stable_identifier_namespaces(self) -> None:
        source_schema = self.schemas["source"]
        review_schema = self.schemas["review"]
        self.assertEqual("^audit-[0-9]{8}-[a-z0-9]+(?:-[a-z0-9]+)*$", source_schema["properties"]["audit_id"]["pattern"])
        self.assertEqual("^review-[0-9]{8}-[a-z0-9]+(?:-[a-z0-9]+)*$", review_schema["properties"]["review_id"]["pattern"])
        self.assertEqual("^(human|agent)-[a-z0-9]+(?:-[a-z0-9]+)*$", source_schema["properties"]["auditor_id"]["pattern"])
        self.assertEqual("^human-[a-z0-9]+(?:-[a-z0-9]+)*$", review_schema["properties"]["reviewer_id"]["pattern"])
        self.assertEqual("^src-[a-z0-9]+(?:-[a-z0-9]+)*$", source_schema["$defs"]["source_reference"]["properties"]["reference_id"]["pattern"])
        self.assertEqual("^https://", source_schema["$defs"]["source_reference"]["properties"]["uri"]["pattern"])
        self.assertEqual("^claim-[a-z0-9]+(?:-[a-z0-9]+)*$", source_schema["$defs"]["claim_result"]["properties"]["claim_id"]["pattern"])
        self.assertEqual("^issue-[a-z0-9]+(?:-[a-z0-9]+)*$", source_schema["$defs"]["claim_coverage"]["properties"]["blocking_issue_ids"]["items"]["pattern"])
        path_contract = source_schema["$defs"]["content_path"]
        self.assertEqual(path_contract, review_schema["$defs"]["content_path"])
        validator = Draft202012Validator(path_contract)
        for slug in CANONICAL_LAYER_SLUGS:
            self.assertEqual([], list(validator.iter_errors(f"docs/{slug}/papers/demo.md")))
        for noncanonical in ("platform", "edge-computing"):
            self.assertTrue(list(validator.iter_errors(f"docs/{noncanonical}/papers/demo.md")))


class RepositoryTrustGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content_path = (
            "docs/connectivity/papers/5g-mmtc-massive-iot-connection.md"
        )
        cls.document = parse_document(ROOT / cls.content_path, repo_root=ROOT)
        cls.content_id = cls.document.content_id
        cls.documents_by_id = {cls.content_id: cls.document}
        cls.verified_audit = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-unverified-to-verified.yml"
        )
        cls.start_review = _load_yaml(
            FIXTURE_ROOTS["review"] / "valid-start-review.yml"
        )
        cls.approval = _load_yaml(
            FIXTURE_ROOTS["review"] / "valid-human-approved.yml"
        )
        cls.authorities = {
            cls.content_id: frozenset({"human-content-author"}),
        }
        cls.actor_authorities = {
            "human-content-author": trust_records.ActorAuthority(
                "human-content-author",
                "HUMAN",
                frozenset({"CONTENT_AUTHOR"}),
            ),
            "human-fact-auditor": trust_records.ActorAuthority(
                "human-fact-auditor",
                "HUMAN",
                frozenset({"FACT_AUDITOR"}),
            ),
            "agent-structural-auditor": trust_records.ActorAuthority(
                "agent-structural-auditor",
                "AGENT",
                frozenset({"STRUCTURAL_AUDITOR"}),
            ),
            "human-content-reviewer": trust_records.ActorAuthority(
                "human-content-reviewer",
                "HUMAN",
                frozenset({"REVIEWER"}),
            ),
            "human-content-approver": trust_records.ActorAuthority(
                "human-content-approver",
                "HUMAN",
                frozenset({"APPROVER"}),
            ),
            "human-governance-reviewer": trust_records.ActorAuthority(
                "human-governance-reviewer",
                "HUMAN",
                frozenset({"GOVERNANCE_REVIEWER"}),
            ),
        }
        cls.critical_claims = {
            cls.content_id: frozenset(
                claim["claim_id"]
                for claim in cls.verified_audit["claim_coverage"]["claims"]
            ),
        }
        cls.as_of = datetime.fromisoformat("2026-07-11T10:00:00+00:00")

    @staticmethod
    def _source_entry(name: str, payload: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
        return Path(f"data/source-audits/{name}.yml"), payload

    @staticmethod
    def _review_entry(name: str, payload: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
        return Path(f"data/review-records/{name}.yml"), payload

    @staticmethod
    def _issue_codes(result: Any) -> set[str]:
        return {issue.code for issue in result.issues}

    def _invalid_reopen_after_approval(self) -> dict[str, Any]:
        reopen = _load_yaml(
            FIXTURE_ROOTS["review"] / "valid-reopen-review.yml"
        )
        reopen["review_id"] = "review-20260711-invalid-reopen"
        reopen["reviewed_at"] = "2026-07-11T09:40:00Z"
        reopen["supersedes"] = self.approval["review_id"]
        reopen["source_status_at_review"] = "UNVERIFIED"
        reopen["linked_audit_ids"] = ["audit-20260711-does-not-exist"]
        reopen["independence"]["linked_auditor_ids"] = []
        return reopen

    def _validate_graph(
        self,
        *,
        source_records: list[tuple[Path, dict[str, Any]]] | None = None,
        review_records: list[tuple[Path, dict[str, Any]]] | None = None,
        actor_authorities: dict[str, trust_records.ActorAuthority] | None = None,
        author_ids_by_content: dict[str, frozenset[str]] | None = None,
        critical_claim_ids_by_content: dict[str, frozenset[str]] | None = None,
    ) -> Any:
        return trust_records.validate_trust_graph(
            self.documents_by_id,
            source_records
            if source_records is not None
            else [self._source_entry("verified", copy.deepcopy(self.verified_audit))],
            review_records
            if review_records is not None
            else [
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", copy.deepcopy(self.approval)),
            ],
            actor_authorities=(
                self.actor_authorities
                if actor_authorities is None
                else actor_authorities
            ),
            author_ids_by_content=(
                self.authorities
                if author_ids_by_content is None
                else author_ids_by_content
            ),
            critical_claim_ids_by_content=(
                self.critical_claims
                if critical_claim_ids_by_content is None
                else critical_claim_ids_by_content
            ),
            as_of=self.as_of,
        )

    def test_repository_baseline_reflects_current_bound_evidence(self) -> None:
        from tools import validate_trust_state

        result = validate_trust_state.validate_repository_trust(
            repo_root=ROOT,
            baseline_mode=True,
            author_ids_by_content=None,
            critical_claim_ids_by_content=None,
        )

        self.assertEqual([], result.issues)
        self.assertEqual(652, result.summary.canonical_content)
        self.assertEqual(0, result.summary.legacy_unbound)
        self.assertEqual(642, result.summary.evidence_bound_review)
        self.assertEqual(642, result.summary.verified)
        self.assertEqual(642, result.summary.approved)
        expected_source_records = len(
            list((ROOT / "data/source-audits").rglob("*.yml"))
        )
        self.assertEqual(expected_source_records, result.summary.source_records)
        expected_review_records = len(
            list((ROOT / "data/review-records").rglob("*.yml"))
        )
        self.assertEqual(expected_review_records, result.summary.review_records)

    def test_valid_verified_and_human_approved_chain_projects_both_axes(self) -> None:
        result = self._validate_graph()

        self.assertEqual([], result.issues)
        projection = result.projections[self.content_id]
        self.assertEqual("VERIFIED", projection.source_status)
        self.assertEqual("HUMAN_APPROVED", projection.review_status)

    def test_self_reported_human_actors_cannot_create_authority(self) -> None:
        audit = copy.deepcopy(self.verified_audit)
        audit["auditor_id"] = "human-forged-auditor"
        audit["auditor_type"] = "HUMAN"
        audit["auditor_role"] = "FACT_AUDITOR"
        source_result = self._validate_graph(
            source_records=[self._source_entry("forged-auditor", audit)],
            review_records=[],
        )
        self.assertIn("ACTOR_AUTHORITY_MISSING", self._issue_codes(source_result))
        self.assertEqual(
            "UNVERIFIED",
            source_result.projections[self.content_id].source_status,
        )

        review = copy.deepcopy(self.start_review)
        review["reviewer_id"] = "human-forged-reviewer"
        review["reviewer_type"] = "HUMAN"
        review["reviewer_role"] = "REVIEWER"
        review_result = self._validate_graph(
            source_records=[],
            review_records=[self._review_entry("forged-reviewer", review)],
        )
        self.assertIn("ACTOR_AUTHORITY_MISSING", self._issue_codes(review_result))
        self.assertEqual(
            "UNREVIEWED",
            review_result.projections[self.content_id].review_status,
        )

        approval = copy.deepcopy(self.approval)
        approval["reviewer_id"] = "human-forged-approver"
        approval_result = self._validate_graph(
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("forged-approval", approval),
            ],
        )
        self.assertIn(
            "ACTOR_AUTHORITY_MISSING",
            self._issue_codes(approval_result),
        )
        self.assertEqual(
            "IN_REVIEW",
            approval_result.projections[self.content_id].review_status,
        )

    def test_authoritative_actor_type_and_role_are_enforced(self) -> None:
        wrong_type = dict(self.actor_authorities)
        wrong_type["human-fact-auditor"] = trust_records.ActorAuthority(
            "human-fact-auditor",
            "AGENT",
            frozenset({"FACT_AUDITOR"}),
        )
        type_result = self._validate_graph(
            source_records=[
                self._source_entry("wrong-actor-type", copy.deepcopy(self.verified_audit))
            ],
            review_records=[],
            actor_authorities=wrong_type,
        )
        self.assertIn(
            "ACTOR_AUTHORITY_TYPE_MISMATCH",
            self._issue_codes(type_result),
        )

        wrong_role = dict(self.actor_authorities)
        wrong_role["human-fact-auditor"] = trust_records.ActorAuthority(
            "human-fact-auditor",
            "HUMAN",
            frozenset({"STRUCTURAL_AUDITOR"}),
        )
        role_result = self._validate_graph(
            source_records=[
                self._source_entry("wrong-actor-role", copy.deepcopy(self.verified_audit))
            ],
            review_records=[],
            actor_authorities=wrong_role,
        )
        self.assertIn("ACTOR_ROLE_NOT_ALLOWED", self._issue_codes(role_result))
        self.assertEqual(
            "UNVERIFIED",
            role_result.projections[self.content_id].source_status,
        )

        wrong_approver_role = dict(self.actor_authorities)
        wrong_approver_role["human-content-approver"] = (
            trust_records.ActorAuthority(
                "human-content-approver",
                "HUMAN",
                frozenset({"REVIEWER"}),
            )
        )
        approval_result = self._validate_graph(
            actor_authorities=wrong_approver_role,
        )
        self.assertIn(
            "ACTOR_ROLE_NOT_ALLOWED",
            self._issue_codes(approval_result),
        )
        self.assertEqual(
            "IN_REVIEW",
            approval_result.projections[self.content_id].review_status,
        )

    def test_content_authors_require_authoritative_author_role(self) -> None:
        authors = {
            self.content_id: frozenset({"human-untrusted-author"}),
        }
        missing_result = self._validate_graph(
            source_records=[
                self._source_entry("missing-author", copy.deepcopy(self.verified_audit))
            ],
            review_records=[],
            author_ids_by_content=authors,
        )
        self.assertIn("ACTOR_AUTHORITY_MISSING", self._issue_codes(missing_result))

        actors = dict(self.actor_authorities)
        actors["human-untrusted-author"] = trust_records.ActorAuthority(
            "human-untrusted-author",
            "HUMAN",
            frozenset({"REVIEWER"}),
        )
        role_result = self._validate_graph(
            source_records=[
                self._source_entry("wrong-author-role", copy.deepcopy(self.verified_audit))
            ],
            review_records=[],
            actor_authorities=actors,
            author_ids_by_content=authors,
        )
        self.assertIn("ACTOR_ROLE_NOT_ALLOWED", self._issue_codes(role_result))

    def test_author_may_supply_structural_noop_but_not_fact_evidence(self) -> None:
        structural = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-structural-auditable-noop.yml"
        )
        structural["auditor_id"] = "human-content-author"
        structural["auditor_type"] = "HUMAN"
        approval = copy.deepcopy(self.approval)
        approval["linked_audit_ids"].append(structural["audit_id"])
        approval["independence"]["linked_auditor_ids"].append(
            "human-content-author"
        )
        actors = dict(self.actor_authorities)
        actors["human-content-author"] = trust_records.ActorAuthority(
            "human-content-author",
            "HUMAN",
            frozenset({"CONTENT_AUTHOR", "STRUCTURAL_AUDITOR"}),
        )

        result = self._validate_graph(
            source_records=[
                self._source_entry("verified", copy.deepcopy(self.verified_audit)),
                self._source_entry("structural-by-author", structural),
            ],
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", approval),
            ],
            actor_authorities=actors,
        )

        self.assertEqual([], result.issues)
        self.assertEqual(
            "HUMAN_APPROVED",
            result.projections[self.content_id].review_status,
        )

    def test_revocation_requires_authoritative_governance_actor(self) -> None:
        revoked = copy.deepcopy(
            _load_yaml(FIXTURE_ROOTS["source"] / "valid-revoked.yml")
        )
        result = self._validate_graph(
            source_records=[self._source_entry("unauthorized-revocation", revoked)],
            review_records=[],
            actor_authorities={},
            author_ids_by_content={},
            critical_claim_ids_by_content={},
        )

        self.assertIn("ACTOR_AUTHORITY_MISSING", self._issue_codes(result))
        self.assertEqual(
            "UNVERIFIED",
            result.projections[self.content_id].source_status,
        )

    def test_valid_partial_audit_requires_locked_claim_inventory(self) -> None:
        audit = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-unverified-to-partial.yml"
        )

        result = self._validate_graph(
            source_records=[self._source_entry("partial", audit)],
            review_records=[],
        )

        self.assertEqual([], result.issues)
        projection = result.projections[self.content_id]
        self.assertEqual("PARTIAL", projection.source_status)
        self.assertEqual((audit["audit_id"],), projection.active_audit_ids)

    def test_structural_noop_root_does_not_require_claim_predecessor(self) -> None:
        structural = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-structural-auditable-noop.yml"
        )
        structural["status_transition"] = {"from": "VERIFIED", "to": "VERIFIED"}

        result = self._validate_graph(
            source_records=[
                self._source_entry("verified", copy.deepcopy(self.verified_audit)),
                self._source_entry("structural", structural),
            ],
            review_records=[],
        )

        self.assertEqual([], result.issues)
        self.assertEqual(
            "VERIFIED",
            result.projections[self.content_id].source_status,
        )

    def test_duplicate_audit_id_fails_closed(self) -> None:
        first = copy.deepcopy(self.verified_audit)
        second = copy.deepcopy(self.verified_audit)
        result = self._validate_graph(
            source_records=[
                self._source_entry("duplicate-a", first),
                self._source_entry("duplicate-b", second),
            ],
            review_records=[],
        )

        self.assertIn("DUPLICATE_AUDIT_ID", self._issue_codes(result))

    def test_two_node_audit_supersedes_cycle_fails_closed(self) -> None:
        first = copy.deepcopy(self.verified_audit)
        second = copy.deepcopy(self.verified_audit)
        first["audit_id"] = "audit-20260711-cycle-a"
        second["audit_id"] = "audit-20260711-cycle-b"
        first["status_transition"] = {"from": "VERIFIED", "to": "VERIFIED"}
        second["status_transition"] = {"from": "VERIFIED", "to": "VERIFIED"}
        first["supersedes"] = second["audit_id"]
        second["supersedes"] = first["audit_id"]

        result = self._validate_graph(
            source_records=[
                self._source_entry("cycle-a", first),
                self._source_entry("cycle-b", second),
            ],
            review_records=[],
        )

        self.assertIn("SUPERSEDES_CYCLE", self._issue_codes(result))

    def test_approver_cannot_be_an_author(self) -> None:
        approval = copy.deepcopy(self.approval)
        approval["reviewer_id"] = "human-content-author"
        result = self._validate_graph(
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", approval),
            ],
        )

        self.assertIn("REVIEWER_AUTHOR_CONFLICT", self._issue_codes(result))

    def test_author_cannot_bind_start_review(self) -> None:
        start = copy.deepcopy(self.start_review)
        start["reviewer_id"] = "human-content-author"

        result = self._validate_graph(
            source_records=[],
            review_records=[self._review_entry("self-review", start)],
        )

        self.assertIn("REVIEWER_AUTHOR_CONFLICT", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("UNREVIEWED", projection.review_status)
        self.assertEqual((), projection.active_review_ids)

    def test_start_review_cannot_bind_with_dangling_audit_link(self) -> None:
        start = copy.deepcopy(self.start_review)
        start["linked_audit_ids"] = ["audit-20260711-missing"]

        result = self._validate_graph(
            source_records=[],
            review_records=[self._review_entry("dangling-start", start)],
        )

        self.assertIn("LINKED_AUDIT_NOT_FOUND", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("UNREVIEWED", projection.review_status)
        self.assertEqual((), projection.active_review_ids)

    def test_start_review_source_snapshot_cannot_be_self_declared(self) -> None:
        start = copy.deepcopy(self.start_review)
        start["source_status_at_review"] = "VERIFIED"

        result = self._validate_graph(
            source_records=[],
            review_records=[self._review_entry("false-source-snapshot", start)],
        )

        self.assertIn("SOURCE_STATUS_AT_REVIEW_MISMATCH", self._issue_codes(result))
        self.assertEqual(
            "UNREVIEWED",
            result.projections[self.content_id].review_status,
        )

    def test_future_review_record_is_never_active(self) -> None:
        start = copy.deepcopy(self.start_review)
        start["reviewed_at"] = "2099-01-01T00:00:00Z"

        result = self._validate_graph(
            source_records=[],
            review_records=[self._review_entry("future-start", start)],
        )

        self.assertIn("RECORD_TIME_IN_FUTURE", self._issue_codes(result))
        self.assertEqual(
            "UNREVIEWED",
            result.projections[self.content_id].review_status,
        )

    def test_valid_partial_request_changes_chain_uses_linked_snapshot(self) -> None:
        partial = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-unverified-to-partial.yml"
        )
        request_changes = _load_yaml(
            FIXTURE_ROOTS["review"] / "valid-request-changes.yml"
        )

        result = self._validate_graph(
            source_records=[self._source_entry("partial", partial)],
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("request-changes", request_changes),
            ],
        )

        self.assertEqual([], result.issues)
        projection = result.projections[self.content_id]
        self.assertEqual("PARTIAL", projection.source_status)
        self.assertEqual("NEEDS_CHANGES", projection.review_status)

    def test_review_snapshot_survives_later_audit_supersession(self) -> None:
        partial = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-unverified-to-partial.yml"
        )
        verified = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-partial-to-verified.yml"
        )
        verified["audited_at"] = "2026-07-11T09:16:00Z"
        request_changes = _load_yaml(
            FIXTURE_ROOTS["review"] / "valid-request-changes.yml"
        )

        result = self._validate_graph(
            source_records=[
                self._source_entry("partial", partial),
                self._source_entry("verified-later", verified),
            ],
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("request-changes", request_changes),
            ],
        )

        self.assertEqual([], result.issues)
        projection = result.projections[self.content_id]
        self.assertEqual("VERIFIED", projection.source_status)
        self.assertEqual("NEEDS_CHANGES", projection.review_status)

    def test_invalid_successor_cannot_resurface_approval_with_revoked_audit(
        self,
    ) -> None:
        audit = copy.deepcopy(self.verified_audit)
        revocation = copy.deepcopy(
            _load_yaml(FIXTURE_ROOTS["source"] / "valid-revoked.yml")[
                "revocation"
            ]
        )
        revocation["revoked_at"] = "2026-07-11T09:30:00Z"
        audit["revocation"] = revocation

        source_records = [self._source_entry("revoked-after-approval", audit)]
        review_records = [
            self._review_entry("start", copy.deepcopy(self.start_review)),
            self._review_entry("approval", copy.deepcopy(self.approval)),
            self._review_entry(
                "invalid-reopen",
                self._invalid_reopen_after_approval(),
            ),
        ]
        result = self._validate_graph(
            source_records=source_records,
            review_records=review_records,
        )

        codes = self._issue_codes(result)
        self.assertIn("LINKED_AUDIT_NOT_FOUND", codes)
        self.assertIn("LINKED_AUDIT_INACTIVE", codes)
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual("IN_REVIEW", projection.review_status)
        self.assertEqual(
            (self.start_review["review_id"],),
            projection.active_review_ids,
        )

        from tools import validate_trust_state

        with (
            mock.patch.object(
                validate_trust_state,
                "_load_documents",
                return_value=self.documents_by_id,
            ),
            mock.patch.object(
                validate_trust_state,
                "_load_record_entries",
                side_effect=[
                    (source_records, []),
                    (review_records, []),
                ],
            ),
            mock.patch.object(
                validate_trust_state,
                "_load_and_validate_legacy_ledger",
                return_value=(set(), []),
            ),
        ):
            repository_result = validate_trust_state.validate_repository_trust(
                repo_root=ROOT,
                baseline_mode=False,
                actor_authorities=self.actor_authorities,
                author_ids_by_content=self.authorities,
                critical_claim_ids_by_content=self.critical_claims,
                as_of=self.as_of,
            )

        self.assertEqual(0, repository_result.summary.approved)
        self.assertEqual(
            "IN_REVIEW",
            repository_result.projections[self.content_id].review_status,
        )

    def test_invalid_successor_can_resurface_approval_with_active_audit(
        self,
    ) -> None:
        result = self._validate_graph(
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", copy.deepcopy(self.approval)),
                self._review_entry(
                    "invalid-reopen",
                    self._invalid_reopen_after_approval(),
                ),
            ],
        )

        codes = self._issue_codes(result)
        self.assertIn("LINKED_AUDIT_NOT_FOUND", codes)
        self.assertNotIn("LINKED_AUDIT_INACTIVE", codes)
        projection = result.projections[self.content_id]
        self.assertEqual("VERIFIED", projection.source_status)
        self.assertEqual("HUMAN_APPROVED", projection.review_status)
        self.assertEqual(
            (self.approval["review_id"],),
            projection.active_review_ids,
        )

    def test_valid_reopen_preserves_suppressed_approval_history(self) -> None:
        audit = copy.deepcopy(self.verified_audit)
        revocation = copy.deepcopy(
            _load_yaml(FIXTURE_ROOTS["source"] / "valid-revoked.yml")[
                "revocation"
            ]
        )
        revocation["revoked_at"] = "2026-07-11T09:30:00Z"
        audit["revocation"] = revocation
        reopen = _load_yaml(
            FIXTURE_ROOTS["review"] / "valid-reopen-review.yml"
        )
        reopen["review_id"] = "review-20260711-valid-reopen"
        reopen["reviewed_at"] = "2026-07-11T09:25:00Z"
        reopen["supersedes"] = self.approval["review_id"]

        result = self._validate_graph(
            source_records=[self._source_entry("revoked-after-reopen", audit)],
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", copy.deepcopy(self.approval)),
                self._review_entry("valid-reopen", reopen),
            ],
        )

        self.assertEqual([], result.issues)
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual("IN_REVIEW", projection.review_status)
        self.assertEqual(
            (reopen["review_id"],),
            projection.active_review_ids,
        )

    def test_resurfaced_approval_cannot_borrow_superseding_verified_audit(
        self,
    ) -> None:
        original = copy.deepcopy(self.verified_audit)
        successor = copy.deepcopy(self.verified_audit)
        successor["audit_id"] = "audit-20260711-claim-verified-refresh"
        successor["audited_at"] = "2026-07-11T09:30:00Z"
        successor["status_transition"] = {
            "from": "VERIFIED",
            "to": "VERIFIED",
        }
        successor["supersedes"] = original["audit_id"]

        result = self._validate_graph(
            source_records=[
                self._source_entry("verified-original", original),
                self._source_entry("verified-successor", successor),
            ],
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", copy.deepcopy(self.approval)),
                self._review_entry(
                    "invalid-reopen",
                    self._invalid_reopen_after_approval(),
                ),
            ],
        )

        codes = self._issue_codes(result)
        self.assertIn("LINKED_AUDIT_NOT_FOUND", codes)
        self.assertIn("LINKED_AUDIT_INACTIVE", codes)
        projection = result.projections[self.content_id]
        self.assertEqual("VERIFIED", projection.source_status)
        self.assertEqual((successor["audit_id"],), projection.active_audit_ids)
        self.assertEqual("IN_REVIEW", projection.review_status)
        self.assertEqual(
            (self.start_review["review_id"],),
            projection.active_review_ids,
        )

    def test_author_cannot_be_the_linked_fact_auditor(self) -> None:
        approval = copy.deepcopy(self.approval)
        approval["independence"]["author_ids"] = ["human-fact-auditor"]
        result = self._validate_graph(
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", approval),
            ],
            author_ids_by_content={
                self.content_id: frozenset({"human-fact-auditor"}),
            },
        )

        self.assertIn("AUTHOR_AUDITOR_CONFLICT", self._issue_codes(result))

    def test_missing_authorities_cannot_project_verified_or_approved(self) -> None:
        result = trust_records.validate_trust_graph(
            self.documents_by_id,
            [self._source_entry("verified", copy.deepcopy(self.verified_audit))],
            [
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", copy.deepcopy(self.approval)),
            ],
            author_ids_by_content=None,
            critical_claim_ids_by_content=None,
            as_of=self.as_of,
        )

        codes = self._issue_codes(result)
        self.assertIn("AUTHOR_AUTHORITY_MISSING", codes)
        self.assertIn("CRITICAL_CLAIM_AUTHORITY_MISSING", codes)
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual("UNREVIEWED", projection.review_status)
        self.assertEqual((), projection.active_review_ids)

    def test_unknown_content_id_reports_stable_code_and_relative_path(self) -> None:
        audit = copy.deepcopy(self.verified_audit)
        audit["content_id"] = "missing-content"
        result = self._validate_graph(
            source_records=[self._source_entry("unknown-content", audit)],
            review_records=[],
        )

        matching = [
            issue for issue in result.issues if issue.code == "UNKNOWN_CONTENT_ID"
        ]
        self.assertEqual(1, len(matching))
        self.assertEqual("data/source-audits/unknown-content.yml", matching[0].path)
        self.assertFalse(Path(matching[0].path).is_absolute())

    def test_body_hash_mismatch_excludes_source_from_projection(self) -> None:
        audit = copy.deepcopy(self.verified_audit)
        audit["body_sha256"] = "f" * 64
        result = self._validate_graph(
            source_records=[self._source_entry("stale-body", audit)],
            review_records=[],
        )

        self.assertIn("BODY_HASH_MISMATCH", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual((), projection.active_audit_ids)

    def test_dangling_source_supersedes_target_fails_closed(self) -> None:
        audit = copy.deepcopy(self.verified_audit)
        audit["supersedes"] = "audit-20260711-does-not-exist"
        result = self._validate_graph(
            source_records=[self._source_entry("dangling-supersedes", audit)],
            review_records=[],
        )

        self.assertIn("SUPERSEDES_TARGET_NOT_FOUND", self._issue_codes(result))
        self.assertEqual(
            "UNVERIFIED",
            result.projections[self.content_id].source_status,
        )

    def test_duplicate_active_source_leaves_are_ambiguous(self) -> None:
        first = copy.deepcopy(self.verified_audit)
        second = copy.deepcopy(self.verified_audit)
        second["audit_id"] = "audit-20260711-second-active-root"
        result = self._validate_graph(
            source_records=[
                self._source_entry("active-a", first),
                self._source_entry("active-b", second),
            ],
            review_records=[],
        )

        matching = [
            issue
            for issue in result.issues
            if issue.code == "DUPLICATE_ACTIVE_SOURCE_RECORD"
        ]
        self.assertEqual(2, len(matching))
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual((), projection.active_audit_ids)

    def test_duplicate_active_review_leaves_are_ambiguous(self) -> None:
        first = copy.deepcopy(self.start_review)
        second = copy.deepcopy(self.start_review)
        second["review_id"] = "review-20260711-second-active-root"
        result = self._validate_graph(
            source_records=[],
            review_records=[
                self._review_entry("active-a", first),
                self._review_entry("active-b", second),
            ],
        )

        matching = [
            issue
            for issue in result.issues
            if issue.code == "DUPLICATE_ACTIVE_REVIEW_RECORD"
        ]
        self.assertEqual(2, len(matching))
        projection = result.projections[self.content_id]
        self.assertEqual("UNREVIEWED", projection.review_status)
        self.assertEqual((), projection.active_review_ids)

    def test_approval_linking_missing_audit_stays_in_review(self) -> None:
        approval = copy.deepcopy(self.approval)
        approval["linked_audit_ids"] = ["audit-20260711-missing"]
        result = self._validate_graph(
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", approval),
            ],
        )

        self.assertIn("LINKED_AUDIT_NOT_FOUND", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("VERIFIED", projection.source_status)
        self.assertEqual("IN_REVIEW", projection.review_status)

    def test_approval_linking_revoked_audit_stays_in_review(self) -> None:
        audit = copy.deepcopy(self.verified_audit)
        revoked = _load_yaml(FIXTURE_ROOTS["source"] / "valid-revoked.yml")
        audit["revocation"] = copy.deepcopy(revoked["revocation"])
        result = self._validate_graph(
            source_records=[self._source_entry("revoked-audit", audit)],
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", copy.deepcopy(self.approval)),
            ],
        )

        self.assertIn("LINKED_AUDIT_INACTIVE", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual("IN_REVIEW", projection.review_status)

    def test_approval_linked_evidence_must_itself_project_verified(self) -> None:
        structural = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-structural-auditable-noop.yml"
        )
        approval = copy.deepcopy(self.approval)
        approval["linked_audit_ids"] = [structural["audit_id"]]
        approval["independence"]["linked_auditor_ids"] = [
            structural["auditor_id"]
        ]

        result = self._validate_graph(
            source_records=[
                self._source_entry("verified", copy.deepcopy(self.verified_audit)),
                self._source_entry("structural", structural),
            ],
            review_records=[
                self._review_entry("start", copy.deepcopy(self.start_review)),
                self._review_entry("approval", approval),
            ],
        )

        self.assertIn("LINKED_AUDITS_NOT_VERIFIED", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("VERIFIED", projection.source_status)
        self.assertEqual("IN_REVIEW", projection.review_status)

    def test_approval_cannot_depend_on_revoked_predecessor(self) -> None:
        start = copy.deepcopy(self.start_review)
        revoked = _load_yaml(FIXTURE_ROOTS["review"] / "valid-revoked.yml")
        start["revocation"] = copy.deepcopy(revoked["revocation"])

        result = self._validate_graph(
            review_records=[
                self._review_entry("revoked-start", start),
                self._review_entry("approval", copy.deepcopy(self.approval)),
            ],
        )

        self.assertIn("SUPERSEDES_PREDECESSOR_REVOKED", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("VERIFIED", projection.source_status)
        self.assertEqual("IN_REVIEW", projection.review_status)
        self.assertEqual((), projection.active_review_ids)

    def test_fully_revoked_stale_chain_is_retained_as_history(self) -> None:
        source = copy.deepcopy(self.verified_audit)
        source_revocation = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-revoked.yml"
        )["revocation"]
        source_revocation["revoked_at"] = "2026-07-11T09:30:00Z"
        source["body_sha256"] = "f" * 64
        source["revocation"] = copy.deepcopy(source_revocation)

        review_revocation = _load_yaml(
            FIXTURE_ROOTS["review"] / "valid-revoked.yml"
        )["revocation"]
        start = copy.deepcopy(self.start_review)
        start["body_sha256"] = "f" * 64
        start["revocation"] = copy.deepcopy(review_revocation)
        approval = copy.deepcopy(self.approval)
        approval["body_sha256"] = "f" * 64
        approval["revocation"] = copy.deepcopy(review_revocation)

        result = self._validate_graph(
            source_records=[self._source_entry("revoked-source-history", source)],
            review_records=[
                self._review_entry("revoked-start-history", start),
                self._review_entry("revoked-approval-history", approval),
            ],
            actor_authorities={
                "human-governance-reviewer": trust_records.ActorAuthority(
                    "human-governance-reviewer",
                    "HUMAN",
                    frozenset({"GOVERNANCE_REVIEWER"}),
                )
            },
            author_ids_by_content={},
            critical_claim_ids_by_content={},
        )

        self.assertEqual([], result.issues)
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual("IN_REVIEW", projection.review_status)
        self.assertEqual((), projection.active_audit_ids)
        self.assertEqual((), projection.active_review_ids)

    def test_stale_review_history_keeps_in_review_floor(self) -> None:
        start = copy.deepcopy(self.start_review)
        start["body_sha256"] = "f" * 64

        result = self._validate_graph(
            source_records=[],
            review_records=[self._review_entry("stale-start", start)],
        )

        self.assertIn("BODY_HASH_MISMATCH", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("IN_REVIEW", projection.review_status)
        self.assertEqual((), projection.active_review_ids)

    def test_noninitial_source_transition_requires_predecessor(self) -> None:
        successor = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-partial-to-verified.yml"
        )
        successor["supersedes"] = None

        result = self._validate_graph(
            source_records=[self._source_entry("orphan-successor", successor)],
            review_records=[],
        )

        self.assertIn("SUPERSEDES_REQUIRED", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual((), projection.active_audit_ids)

    def test_noninitial_review_transition_requires_predecessor(self) -> None:
        request_changes = _load_yaml(
            FIXTURE_ROOTS["review"] / "valid-request-changes.yml"
        )
        request_changes["supersedes"] = None

        result = self._validate_graph(
            source_records=[],
            review_records=[self._review_entry("orphan-review", request_changes)],
        )

        self.assertIn("SUPERSEDES_REQUIRED", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("UNREVIEWED", projection.review_status)
        self.assertEqual((), projection.active_review_ids)

    def test_invalid_predecessor_cannot_promote_valid_successor(self) -> None:
        predecessor = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-unverified-to-partial.yml"
        )
        predecessor["auditor_id"] = "human-content-author"
        successor = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-partial-to-verified.yml"
        )

        result = self._validate_graph(
            source_records=[
                self._source_entry("invalid-predecessor", predecessor),
                self._source_entry("dependent-successor", successor),
            ],
            review_records=[],
        )

        codes = self._issue_codes(result)
        self.assertIn("AUTHOR_AUDITOR_CONFLICT", codes)
        self.assertIn("SUPERSEDES_PREDECESSOR_INVALID", codes)
        projection = result.projections[self.content_id]
        self.assertEqual("UNVERIFIED", projection.source_status)
        self.assertEqual((), projection.active_audit_ids)

    def test_supersession_fork_keeps_predecessor_as_only_effective_leaf(self) -> None:
        predecessor = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-unverified-to-partial.yml"
        )
        first = _load_yaml(
            FIXTURE_ROOTS["source"] / "valid-claim-partial-to-verified.yml"
        )
        second = copy.deepcopy(first)
        second["audit_id"] = "audit-20260711-claim-partial-verified-fork"

        result = self._validate_graph(
            source_records=[
                self._source_entry("fork-root", predecessor),
                self._source_entry("fork-a", first),
                self._source_entry("fork-b", second),
            ],
            review_records=[],
        )

        self.assertIn("SUPERSEDES_FORK", self._issue_codes(result))
        projection = result.projections[self.content_id]
        self.assertEqual("PARTIAL", projection.source_status)
        self.assertEqual((predecessor["audit_id"],), projection.active_audit_ids)

    def test_repository_validator_rejects_symlinked_schema_path(self) -> None:
        from tools import validate_trust_state

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo_root = base / "repo"
            outside_schema_root = base / "outside-schemas"
            outside_schema_root.mkdir(parents=True)
            for schema_name in (
                "source-audit.schema.json",
                "review-record.schema.json",
            ):
                shutil.copyfile(
                    ROOT / "schemas" / schema_name,
                    outside_schema_root / schema_name,
                )
            repo_root.mkdir()
            (repo_root / "schemas").symlink_to(
                outside_schema_root,
                target_is_directory=True,
            )
            document_path = repo_root / "docs/network/papers/alpha.md"
            document_path.parent.mkdir(parents=True)
            document_path.write_text(
                "---\n"
                "schema_version: '1.0'\n"
                "id: alpha\n"
                "title: Alpha\n"
                "layer: 3\n"
                "source_status: UNVERIFIED\n"
                "review_status: UNREVIEWED\n"
                "last_reviewed: UNKNOWN\n"
                "---\n"
                "# Alpha\n"
                "body\n",
                encoding="utf-8",
            )

            with self.assertRaises(validate_trust_state.TrustStateError) as raised:
                validate_trust_state.validate_repository_trust(
                    repo_root=repo_root,
                    baseline_mode=False,
                    as_of=self.as_of,
                )

        self.assertEqual("UNSAFE_AUTHORITY_SCHEMA_PATH", raised.exception.code)
        self.assertNotIn(directory, raised.exception.message)

    def test_legacy_unbound_promotion_is_rejected_with_relative_path(self) -> None:
        from tools import validate_trust_state

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            repo_root = Path(directory)
            schema_root = repo_root / "schemas"
            schema_root.mkdir()
            for schema_name in (
                "source-audit.schema.json",
                "review-record.schema.json",
                "trust-authorities.schema.json",
            ):
                shutil.copyfile(ROOT / "schemas" / schema_name, schema_root / schema_name)

            document_path = repo_root / "docs/network/papers/alpha.md"
            document_path.parent.mkdir(parents=True)
            document_path.write_text(
                "---\n"
                "schema_version: '1.0'\n"
                "id: alpha\n"
                "title: Alpha\n"
                "layer: 3\n"
                "source_status: UNVERIFIED\n"
                "review_status: IN_REVIEW\n"
                "last_reviewed: '2026-07-10'\n"
                "---\n"
                "# Alpha\n"
                "body\n",
                encoding="utf-8",
            )
            progress_path = repo_root / "data/deep-review-progress.yml"
            progress_path.parent.mkdir(parents=True)
            progress_path.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "1.0",
                        "counts": {"total": 1, "pending": 0, "in_review": 1},
                        "articles": [
                            {
                                "id": "alpha",
                                "path": "docs/network/papers/alpha.md",
                                "layer": 3,
                                "status": "in_review",
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            for command in (
                ("init", "-q"),
                ("config", "user.name", "IoT Test"),
                ("config", "user.email", "iot-test@example.invalid"),
                ("add", "docs", "data/deep-review-progress.yml"),
                ("commit", "-q", "-m", "legacy observation"),
            ):
                subprocess.run(
                    ["git", "-C", str(repo_root), *command],
                    check=True,
                    capture_output=True,
                )
            observed_commit = subprocess.run(
                ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            from tools import reconcile_legacy_review_state

            ledger = reconcile_legacy_review_state.build_ledger(
                repo_root=repo_root,
                observed_at_commit=observed_commit,
            )
            ledger_path = repo_root / reconcile_legacy_review_state.LEDGER_PATH
            ledger_bytes = reconcile_legacy_review_state.render_ledger(ledger)
            ledger_path.write_bytes(ledger_bytes)
            document_path.write_text(
                document_path.read_text(encoding="utf-8").replace(
                    "source_status: UNVERIFIED",
                    "source_status: VERIFIED",
                ),
                encoding="utf-8",
            )

            result = validate_trust_state.validate_repository_trust(
                repo_root=repo_root,
                baseline_mode=True,
                author_ids_by_content=None,
                critical_claim_ids_by_content=None,
                as_of=self.as_of,
            )
            stderr = io.StringIO()
            with (
                mock.patch.object(validate_trust_state, "ROOT", repo_root),
                redirect_stderr(stderr),
            ):
                return_code = validate_trust_state.main(
                    ["--all", "--baseline-mode", "--as-of", "2026-07-11T10:00:00Z"]
                )
            cli_error = stderr.getvalue()

            document_path.write_text(
                document_path.read_text(encoding="utf-8") + "changed body\n",
                encoding="utf-8",
            )
            stale_binding_result = validate_trust_state.validate_repository_trust(
                repo_root=repo_root,
                baseline_mode=True,
                as_of=self.as_of,
            )

            tampered = copy.deepcopy(ledger)
            tampered["generated_by"] = "forged-generator"
            ledger_path.write_bytes(
                reconcile_legacy_review_state.render_ledger(tampered)
            )
            tampered_result = validate_trust_state.validate_repository_trust(
                repo_root=repo_root,
                baseline_mode=True,
                as_of=self.as_of,
            )

            missing_commit = copy.deepcopy(ledger)
            missing_commit["observed_at_commit"] = "f" * 40
            for entry in missing_commit["entries"]:
                entry["observed_at_commit"] = "f" * 40
            ledger_path.write_bytes(
                reconcile_legacy_review_state.render_ledger(missing_commit)
            )
            missing_commit_result = validate_trust_state.validate_repository_trust(
                repo_root=repo_root,
                baseline_mode=True,
                as_of=self.as_of,
            )

        codes = self._issue_codes(result)
        self.assertIn("SOURCE_STATUS_PROJECTION_MISMATCH", codes)
        self.assertIn("LEGACY_UNBOUND_PROMOTION", codes)
        self.assertEqual(0, result.summary.verified)
        self.assertEqual(0, result.summary.approved)
        for issue in result.issues:
            self.assertFalse(Path(issue.path).is_absolute())
            self.assertNotIn(directory, issue.render())
        self.assertEqual(1, return_code)
        self.assertIn("TRUST_STATE_INVALID", cli_error)
        self.assertIn("SOURCE_STATUS_PROJECTION_MISMATCH", cli_error)
        self.assertNotIn(directory, cli_error)
        self.assertNotIn(
            "LEGACY_LEDGER_PROVENANCE_MISMATCH",
            self._issue_codes(stale_binding_result),
        )
        self.assertIn(
            "REVIEW_STATUS_PROJECTION_MISMATCH",
            self._issue_codes(stale_binding_result),
        )
        self.assertEqual(0, stale_binding_result.summary.legacy_unbound)
        self.assertIn(
            "LEGACY_LEDGER_PROVENANCE_MISMATCH",
            self._issue_codes(tampered_result),
        )
        self.assertIn(
            "OBSERVED_COMMIT_NOT_FOUND",
            self._issue_codes(missing_commit_result),
        )


if __name__ == "__main__":
    unittest.main()
