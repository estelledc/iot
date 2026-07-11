from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
OBSERVED_COMMIT = "a" * 40


class LegacyReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        from tools import reconcile_legacy_review_state

        self.module = reconcile_legacy_review_state
        # Git can briefly keep object directories busy on macOS after a commit.
        self.tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tempdir.name)
        self.documents = [
            self._write_document("alpha", "Alpha", body=b"# Alpha\nbody a\n"),
            self._write_document("beta", "Beta", body=b"# Beta\nbody b\n"),
        ]
        self._write_progress(
            [
                self._progress_entry("alpha"),
                self._progress_entry("beta"),
            ]
        )

    def tearDown(self) -> None:
        if hasattr(self, "tempdir"):
            self.tempdir.cleanup()

    def _write_document(self, content_id: str, title: str, *, body: bytes) -> Path:
        path = self.root / f"docs/network/papers/{content_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = (
            "---\n"
            "schema_version: '1.0'\n"
            f"id: {content_id}\n"
            f"title: {title}\n"
            "layer: 3\n"
            "source_status: UNVERIFIED\n"
            "review_status: IN_REVIEW\n"
            "---\n"
        ).encode("utf-8")
        path.write_bytes(frontmatter + body)
        return path

    @staticmethod
    def _progress_entry(content_id: str) -> dict[str, object]:
        return {
            "id": content_id,
            "layer": 3,
            "path": f"docs/network/papers/{content_id}.md",
            "batch": "L3-B01",
            "status": "in_review",
            "reviewed_at": "2026-07-10",
            "batch_done": "L3-B01",
        }

    def _write_progress(self, articles: list[dict[str, object]]) -> None:
        path = self.root / "data/deep-review-progress.yml"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "campaign": "full-deep-review",
            "task": "IOT-T034",
            "started": "2026-07-10",
            "order": "layer 8→1, filename asc, batch size 5",
            "counts": {
                "total": len(articles),
                "pending": 0,
                "in_review": len(articles),
            },
            "articles": articles,
        }
        path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def _build(self) -> dict[str, object]:
        return self.module.build_ledger(
            repo_root=self.root,
            observed_at_commit=OBSERVED_COMMIT,
        )

    def _init_git(self) -> str:
        commands = (
            ("init", "-q"),
            ("config", "user.name", "IoT Test"),
            ("config", "user.email", "iot-test@example.invalid"),
            ("add", "docs", "data/deep-review-progress.yml"),
            ("commit", "-q", "-m", "baseline"),
        )
        for command in commands:
            subprocess.run(
                ["git", "-C", str(self.root), *command],
                check=True,
                capture_output=True,
            )
        return subprocess.run(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_ledger_covers_every_canonical_identity_once(self) -> None:
        ledger = self._build()
        entries = ledger["entries"]
        self.assertEqual(2, len(entries))
        self.assertEqual(
            ["alpha", "beta"],
            [entry["content_id"] for entry in entries],
        )
        self.assertEqual(
            2,
            len({entry["content_path"] for entry in entries}),
        )

    def test_entries_bind_current_body_and_preserve_unbound_observation(self) -> None:
        ledger = self._build()
        alpha = ledger["entries"][0]
        self.assertEqual(
            hashlib.sha256(b"# Alpha\nbody a\n").hexdigest(),
            alpha["body_sha256"],
        )
        self.assertEqual("UNVERIFIED", alpha["observed_source_status"])
        self.assertEqual("IN_REVIEW", alpha["observed_review_status"])
        self.assertEqual("in_review", alpha["legacy_campaign_status"])
        self.assertEqual("LEGACY_UNBOUND", alpha["classification"])
        self.assertEqual(OBSERVED_COMMIT, alpha["observed_at_commit"])

    def test_statistics_separate_observation_from_evidence_binding(self) -> None:
        counts = self._build()["counts"]
        self.assertEqual(2, counts["canonical_content"])
        self.assertEqual(2, counts["observed_in_review"])
        self.assertEqual(2, counts["legacy_unbound"])
        self.assertEqual(0, counts["evidence_bound_review"])
        self.assertEqual(0, counts["bound"])

    def test_duplicate_progress_identity_is_rejected(self) -> None:
        duplicate = self._progress_entry("alpha")
        self._write_progress(
            [
                self._progress_entry("alpha"),
                self._progress_entry("beta"),
                duplicate,
            ]
        )
        with self.assertRaises(self.module.ReconciliationError) as caught:
            self._build()
        self.assertEqual("PROGRESS_DUPLICATE_CONTENT_ID", caught.exception.code)

    def test_missing_progress_identity_is_rejected(self) -> None:
        self._write_progress([self._progress_entry("alpha")])
        with self.assertRaises(self.module.ReconciliationError) as caught:
            self._build()
        self.assertEqual("PROGRESS_MISSING_CONTENT", caught.exception.code)

    def test_extra_progress_identity_is_rejected(self) -> None:
        self._write_progress(
            [
                self._progress_entry("alpha"),
                self._progress_entry("beta"),
                self._progress_entry("ghost"),
            ]
        )
        with self.assertRaises(self.module.ReconciliationError) as caught:
            self._build()
        self.assertEqual("PROGRESS_EXTRA_CONTENT", caught.exception.code)

    def test_non_in_review_progress_is_rejected_in_legacy_baseline(self) -> None:
        articles = [
            self._progress_entry("alpha"),
            self._progress_entry("beta"),
        ]
        articles[1]["status"] = "done"
        self._write_progress(articles)
        with self.assertRaises(self.module.ReconciliationError) as caught:
            self._build()
        self.assertEqual("PROGRESS_STATUS_MISMATCH", caught.exception.code)

    def test_existing_trust_records_fail_closed_until_t044(self) -> None:
        record = self.root / "data/review-records/review-alpha.yml"
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text("review_id: review-alpha\n", encoding="utf-8")
        with self.assertRaises(self.module.ReconciliationError) as caught:
            self._build()
        self.assertEqual("TRUST_RECORDS_REQUIRE_T044", caught.exception.code)

    def test_write_is_idempotent_and_never_rewrites_papers(self) -> None:
        before = {path: path.read_bytes() for path in self.documents}
        self.module.write_ledger(
            repo_root=self.root,
            observed_at_commit=OBSERVED_COMMIT,
        )
        output = self.root / self.module.LEDGER_PATH
        first = output.read_bytes()
        self.module.write_ledger(
            repo_root=self.root,
            observed_at_commit=OBSERVED_COMMIT,
        )
        self.assertEqual(first, output.read_bytes())
        self.assertEqual(before, {path: path.read_bytes() for path in self.documents})

    def test_check_rejects_a_tampered_body_hash(self) -> None:
        self.module.write_ledger(
            repo_root=self.root,
            observed_at_commit=OBSERVED_COMMIT,
        )
        output = self.root / self.module.LEDGER_PATH
        payload = self.module.load_ledger(output)
        payload["entries"][0]["body_sha256"] = "0" * 64
        output.write_bytes(self.module.render_ledger(payload))
        errors = self.module.check_ledger(
            repo_root=self.root,
            observed_at_commit=OBSERVED_COMMIT,
        )
        self.assertTrue(errors)
        self.assertIn("stale", " ".join(errors).lower())

    def test_invalid_observed_commit_is_rejected(self) -> None:
        with self.assertRaises(self.module.ReconciliationError) as caught:
            self.module.build_ledger(
                repo_root=self.root,
                observed_at_commit="not-a-commit",
            )
        self.assertEqual("INVALID_OBSERVED_COMMIT", caught.exception.code)

    def test_committing_the_ledger_does_not_change_observation_bytes(self) -> None:
        baseline = self._init_git()
        self.module.write_ledger(repo_root=self.root)
        output = self.root / self.module.LEDGER_PATH
        first = output.read_bytes()
        ledger = self.module.load_ledger(output)
        self.assertEqual(baseline, ledger["observed_at_commit"])
        subprocess.run(
            ["git", "-C", str(self.root), "add", self.module.LEDGER_PATH.as_posix()],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-q", "-m", "add ledger"],
            check=True,
            capture_output=True,
        )
        self.module.write_ledger(repo_root=self.root)
        self.assertEqual(first, output.read_bytes())
        self.assertEqual([], self.module.check_ledger(repo_root=self.root))

    def test_uncommitted_canonical_change_is_rejected(self) -> None:
        self._init_git()
        self.documents[0].write_bytes(self.documents[0].read_bytes() + b"changed\n")
        with self.assertRaises(self.module.ReconciliationError) as caught:
            self.module.write_ledger(repo_root=self.root)
        self.assertEqual("OBSERVATION_INPUT_UNCOMMITTED", caught.exception.code)

    def test_uncommitted_progress_change_is_rejected(self) -> None:
        self._init_git()
        progress = self.root / self.module.PROGRESS_PATH
        progress.write_bytes(progress.read_bytes() + b"# changed\n")
        with self.assertRaises(self.module.ReconciliationError) as caught:
            self.module.write_ledger(repo_root=self.root)
        self.assertEqual("OBSERVATION_INPUT_UNCOMMITTED", caught.exception.code)


class RepositoryLegacyLedgerTests(unittest.TestCase):
    def test_repository_ledger_is_current_and_covers_642_unbound_entries(self) -> None:
        from tools import reconcile_legacy_review_state

        path = ROOT / reconcile_legacy_review_state.LEDGER_PATH
        ledger = reconcile_legacy_review_state.load_ledger(path)
        self.assertEqual(642, ledger["counts"]["canonical_content"])
        self.assertEqual(642, ledger["counts"]["observed_in_review"])
        self.assertEqual(642, ledger["counts"]["legacy_unbound"])
        self.assertEqual(0, ledger["counts"]["evidence_bound_review"])
        self.assertEqual(
            {"LEGACY_UNBOUND"},
            {entry["classification"] for entry in ledger["entries"]},
        )
        self.assertEqual(
            [],
            reconcile_legacy_review_state.check_ledger(repo_root=ROOT),
        )


if __name__ == "__main__":
    unittest.main()
