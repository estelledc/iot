from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tools import check_deploy_acceptance


TARGET_SHA = "b375fd8bb32b35be9ab03e08ecedd4287dec87a1"


def _valid_record() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "accepted_at": "2026-07-13T04:34:11Z",
        "target_sha": TARGET_SHA,
        "site_url": "https://estelledc.github.io/iot/",
        "repository_quality": {
            "workflow_name": "Repository quality",
            "run_id": 29224133596,
            "run_url": "https://github.com/estelledc/iot/actions/runs/29224133596",
            "conclusion": "success",
        },
        "pages_deploy": {
            "workflow_name": "Deploy MkDocs to GitHub Pages",
            "run_id": 29224133597,
            "run_url": "https://github.com/estelledc/iot/actions/runs/29224133597",
            "conclusion": "success",
        },
        "checks": [
            {
                "name": "homepage_http_status",
                "ok": True,
                "url": "https://estelledc.github.io/iot/",
                "detail": "HTTP 200",
            },
            {
                "name": "homepage_contains_brand",
                "ok": True,
                "url": "https://estelledc.github.io/iot/",
                "detail": "物联网全栈技术学习站",
            },
            {
                "name": "homepage_has_eight_layer_nav",
                "ok": True,
                "url": "https://estelledc.github.io/iot/",
                "detail": "All eight layer labels are present.",
            },
            {
                "name": "foundation_catalog_http_status",
                "ok": True,
                "url": "https://estelledc.github.io/iot/foundation/catalog/",
                "detail": "HTTP 200",
            },
        ],
        "inventory_summary": {
            "content_files": 642,
            "structural_source_audit_records": 29,
            "source_audited_files": 0,
            "source_status_counts": {
                "UNVERIFIED": 642,
                "PARTIAL": 0,
                "VERIFIED": 0,
            },
        },
        "trust_summary": {
            "source_records": 29,
            "review_records": 0,
            "legacy_unbound": 642,
            "evidence_bound_review": 0,
            "verified": 0,
            "approved": 0,
        },
        "notes": "Acceptance against the deployed Pages artifact for the recorded commit.",
    }


class DeployAcceptanceTests(unittest.TestCase):
    def _write_record(self, payload: dict[str, object]) -> Path:
        path = Path(self.tempdir.name) / "deploy-acceptance.yml"
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_valid_record_passes(self) -> None:
        path = self._write_record(_valid_record())
        self.assertEqual([], check_deploy_acceptance.validate_record(path, TARGET_SHA))

    def test_inventory_and_trust_counts_are_release_specific(self) -> None:
        payload = _valid_record()
        payload["inventory_summary"] = {
            "content_files": 647,
            "structural_source_audit_records": 642,
            "source_audited_files": 642,
            "source_status_counts": {
                "UNVERIFIED": 5,
                "PARTIAL": 0,
                "VERIFIED": 642,
            },
        }
        payload["trust_summary"] = {
            "source_records": 1284,
            "review_records": 1284,
            "legacy_unbound": 0,
            "evidence_bound_review": 642,
            "verified": 642,
            "approved": 642,
        }
        path = self._write_record(payload)

        self.assertEqual([], check_deploy_acceptance.validate_record(path, TARGET_SHA))

    def test_target_sha_must_match_requested_sha(self) -> None:
        payload = _valid_record()
        payload["target_sha"] = "0" * 40
        path = self._write_record(payload)

        self.assertIn(
            "SEMANTIC:target_sha:mismatch",
            check_deploy_acceptance.validate_record(path, TARGET_SHA),
        )

    def test_successful_workflows_are_required(self) -> None:
        payload = _valid_record()
        payload["pages_deploy"]["conclusion"] = "failure"
        path = self._write_record(payload)

        self.assertIn(
            "SEMANTIC:pages_deploy:conclusion-not-success",
            check_deploy_acceptance.validate_record(path, TARGET_SHA),
        )

    def test_required_public_checks_must_be_present(self) -> None:
        payload = _valid_record()
        payload["checks"] = payload["checks"][:-1]
        path = self._write_record(payload)

        self.assertIn(
            "SEMANTIC:checks:missing-required",
            check_deploy_acceptance.validate_record(path, TARGET_SHA),
        )
