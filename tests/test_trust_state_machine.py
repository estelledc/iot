from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

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


if __name__ == "__main__":
    unittest.main()
