from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest import mock

import yaml

from tools import reconcile_legacy_review_state, validate_trust_state
from tools.iot_domain import parse_document


ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = Path(
    "docs/connectivity/papers/5g-mmtc-massive-iot-connection.md"
)
SOURCE_FIXTURE = Path(
    "tests/fixtures/source-audits/valid-claim-unverified-to-verified.yml"
)
STRUCTURAL_FIXTURE = Path(
    "tests/fixtures/source-audits/valid-structural-auditable-noop.yml"
)
START_FIXTURE = Path("tests/fixtures/review-records/valid-start-review.yml")
APPROVAL_FIXTURE = Path("tests/fixtures/review-records/valid-human-approved.yml")


class TrustAuthorityIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.repo_root = Path(self.tempdir.name)
        schema_root = self.repo_root / "schemas"
        schema_root.mkdir()
        for schema_name in (
            "source-audit.schema.json",
            "review-record.schema.json",
            "trust-authorities.schema.json",
        ):
            shutil.copyfile(ROOT / "schemas" / schema_name, schema_root / schema_name)

        document_path = self.repo_root / CONTENT_PATH
        document_path.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / CONTENT_PATH, document_path)
        progress_path = self.repo_root / "data/deep-review-progress.yml"
        progress_path.parent.mkdir(parents=True)
        progress_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "counts": {"total": 1, "pending": 0, "in_review": 1},
                    "articles": [
                        {
                            "id": CONTENT_PATH.stem,
                            "path": CONTENT_PATH.as_posix(),
                            "layer": 2,
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
                ["git", "-C", str(self.repo_root), *command],
                check=True,
                capture_output=True,
            )
        observed = subprocess.run(
            ["git", "-C", str(self.repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        ledger = reconcile_legacy_review_state.build_ledger(
            repo_root=self.repo_root,
            observed_at_commit=observed,
        )
        (self.repo_root / reconcile_legacy_review_state.LEDGER_PATH).write_bytes(
            reconcile_legacy_review_state.render_ledger(ledger)
        )
        self.as_of = datetime.fromisoformat("2026-07-11T10:00:00+00:00")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_authority(self, *, body_sha256: str | None = None) -> None:
        document = parse_document(
            self.repo_root / CONTENT_PATH,
            repo_root=self.repo_root,
        )
        source = yaml.safe_load((ROOT / SOURCE_FIXTURE).read_text(encoding="utf-8"))
        claims = [
            item["claim_id"] for item in source["claim_coverage"]["claims"]
        ]
        payload = {
            "schema_version": "1.0",
            "authority_kind": "TRUST_PROJECTION_AUTHORITY",
            "actors": [
                {
                    "actor_id": "human-content-author",
                    "actor_type": "HUMAN",
                    "allowed_roles": ["CONTENT_AUTHOR"],
                },
                {
                    "actor_id": "human-fact-auditor",
                    "actor_type": "HUMAN",
                    "allowed_roles": ["FACT_AUDITOR"],
                },
                {
                    "actor_id": "human-content-reviewer",
                    "actor_type": "HUMAN",
                    "allowed_roles": ["REVIEWER"],
                },
                {
                    "actor_id": "human-content-approver",
                    "actor_type": "HUMAN",
                    "allowed_roles": ["APPROVER"],
                },
                {
                    "actor_id": "human-governance-reviewer",
                    "actor_type": "HUMAN",
                    "allowed_roles": ["GOVERNANCE_REVIEWER"],
                },
            ],
            "entries": [
                {
                    "content_id": document.content_id,
                    "content_path": document.repo_relative_path,
                    "body_sha256": body_sha256 or document.body_sha256,
                    "author_ids": ["human-content-author"],
                    "critical_claim_ids": claims,
                }
            ],
        }
        (self.repo_root / validate_trust_state.AUTHORITY_PATH).write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

    def _install_verified_approval_chain(self) -> None:
        source_root = self.repo_root / "data/source-audits"
        review_root = self.repo_root / "data/review-records"
        source_root.mkdir(parents=True)
        review_root.mkdir(parents=True)
        shutil.copyfile(ROOT / SOURCE_FIXTURE, source_root / "verified.yml")
        shutil.copyfile(ROOT / START_FIXTURE, review_root / "start.yml")
        shutil.copyfile(ROOT / APPROVAL_FIXTURE, review_root / "approval.yml")
        document_path = self.repo_root / CONTENT_PATH
        text = document_path.read_text(encoding="utf-8")
        text = text.replace("source_status: UNVERIFIED", "source_status: VERIFIED")
        text = text.replace(
            "review_status: IN_REVIEW",
            "review_status: HUMAN_APPROVED",
        )
        document_path.write_text(text, encoding="utf-8")

    @staticmethod
    def _codes(result: validate_trust_state.RepositoryTrustResult) -> set[str]:
        return {issue.code for issue in result.issues}

    def test_empty_baseline_does_not_require_authority_file(self) -> None:
        result = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )

        self.assertEqual([], result.issues)
        self.assertEqual(0, result.summary.source_records)
        self.assertEqual(0, result.summary.review_records)

    def test_structural_only_authority_uses_actor_registry_without_entries(self) -> None:
        source_root = self.repo_root / "data/source-audits"
        source_root.mkdir(parents=True)
        shutil.copyfile(ROOT / STRUCTURAL_FIXTURE, source_root / "structural.yml")

        missing_authority = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )
        self.assertIn("ACTOR_AUTHORITY_MISSING", self._codes(missing_authority))

        payload = {
            "schema_version": "1.0",
            "authority_kind": "TRUST_PROJECTION_AUTHORITY",
            "actors": [
                {
                    "actor_id": "agent-structural-auditor",
                    "actor_type": "AGENT",
                    "allowed_roles": ["STRUCTURAL_AUDITOR"],
                }
            ],
            "entries": [],
        }
        (self.repo_root / validate_trust_state.AUTHORITY_PATH).write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        result = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )

        self.assertEqual([], result.issues)
        self.assertEqual(1, result.summary.source_records)
        self.assertEqual(0, result.summary.verified)

    def test_duplicate_and_type_mismatched_actor_authority_fail_closed(self) -> None:
        authority_path = self.repo_root / validate_trust_state.AUTHORITY_PATH
        self._write_authority()
        payload = yaml.safe_load(authority_path.read_text(encoding="utf-8"))
        duplicate = dict(payload["actors"][0])
        duplicate["allowed_roles"] = ["REVIEWER"]
        payload["actors"].append(duplicate)
        authority_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )

        duplicate_result = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )
        self.assertIn("DUPLICATE_ACTOR_AUTHORITY", self._codes(duplicate_result))

        payload["actors"] = payload["actors"][:-1]
        payload["actors"][0]["actor_type"] = "AGENT"
        authority_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )
        mismatch_result = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )
        self.assertIn(
            "ACTOR_AUTHORITY_ID_TYPE_MISMATCH",
            self._codes(mismatch_result),
        )
        for issue in [*duplicate_result.issues, *mismatch_result.issues]:
            self.assertEqual(validate_trust_state.AUTHORITY_PATH.as_posix(), issue.path)
            self.assertFalse(Path(issue.path).is_absolute())

    def test_fixed_authority_file_allows_real_cli_verified_approval(self) -> None:
        self._install_verified_approval_chain()
        self._write_authority()

        result = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )
        self.assertEqual([], result.issues)
        self.assertEqual(1, result.summary.verified)
        self.assertEqual(1, result.summary.approved)
        self.assertEqual(1, result.summary.evidence_bound_review)
        self.assertEqual(0, result.summary.legacy_unbound)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(validate_trust_state, "ROOT", self.repo_root),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            return_code = validate_trust_state.main(
                ["--all", "--baseline-mode", "--as-of", "2026-07-11T10:00:00Z"]
            )
        self.assertEqual(0, return_code, stderr.getvalue())
        self.assertIn("TRUST_STATE_OK", stdout.getvalue())
        self.assertNotIn(str(self.repo_root), stdout.getvalue() + stderr.getvalue())

    def test_source_only_verified_audit_does_not_require_review_binding(self) -> None:
        source_root = self.repo_root / "data/source-audits"
        source_root.mkdir(parents=True)
        shutil.copyfile(ROOT / SOURCE_FIXTURE, source_root / "verified.yml")
        document_path = self.repo_root / CONTENT_PATH
        document_path.write_text(
            document_path.read_text(encoding="utf-8").replace(
                "source_status: UNVERIFIED",
                "source_status: VERIFIED",
            ),
            encoding="utf-8",
        )
        self._write_authority()

        result = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )
        self.assertEqual([], result.issues)
        self.assertEqual(1, result.summary.verified)
        self.assertEqual(0, result.summary.approved)
        self.assertEqual(1, result.summary.legacy_unbound)
        self.assertEqual(0, result.summary.evidence_bound_review)

        with (
            mock.patch.object(validate_trust_state, "ROOT", self.repo_root),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            return_code = validate_trust_state.main(
                ["--all", "--baseline-mode", "--as-of", "2026-07-11T10:00:00Z"]
            )
        self.assertEqual(0, return_code)

    def test_missing_authority_file_blocks_every_current_promotion(self) -> None:
        self._install_verified_approval_chain()

        result = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )

        codes = self._codes(result)
        self.assertIn("AUTHOR_AUTHORITY_MISSING", codes)
        self.assertIn("CRITICAL_CLAIM_AUTHORITY_MISSING", codes)
        self.assertEqual(0, result.summary.verified)
        self.assertEqual(0, result.summary.approved)
        self.assertEqual(0, result.summary.evidence_bound_review)

    def test_authority_schema_identity_and_path_fail_closed(self) -> None:
        authority_path = self.repo_root / validate_trust_state.AUTHORITY_PATH
        authority_path.write_text(
            "schema_version: '1.0'\n"
            "authority_kind: TRUST_PROJECTION_AUTHORITY\n"
            "entries: []\n",
            encoding="utf-8",
        )
        empty = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )
        self.assertIn("AUTHORITY_SCHEMA_VALIDATION_FAILED", self._codes(empty))

        self._write_authority(body_sha256="f" * 64)
        stale = validate_trust_state.validate_repository_trust(
            repo_root=self.repo_root,
            baseline_mode=True,
            as_of=self.as_of,
        )
        self.assertIn("AUTHORITY_BODY_HASH_MISMATCH", self._codes(stale))

        authority_path.unlink()
        authority_path.symlink_to(ROOT / "data/trust-migration-ledger.yml")
        with self.assertRaises(validate_trust_state.TrustStateError) as raised:
            validate_trust_state.validate_repository_trust(
                repo_root=self.repo_root,
                baseline_mode=True,
                as_of=self.as_of,
            )
        self.assertEqual("UNSAFE_AUTHORITY_PATH", raised.exception.code)
        self.assertNotIn(str(self.repo_root), raised.exception.message)


if __name__ == "__main__":
    unittest.main()
