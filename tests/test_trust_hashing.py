from __future__ import annotations

import hashlib
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import yaml

from tools.iot_domain import ContentError, parse_document


ROOT = Path(__file__).resolve().parents[1]


class TrustHashingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_document(
        self,
        *,
        frontmatter_extra: str = "source_status: UNVERIFIED\n",
        body: bytes = b"# Demo\nbody\n",
    ):
        path = self.root / "docs/network/papers/demo.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        prefix = (
            "---\n"
            "schema_version: '1.0'\n"
            "id: demo\n"
            "title: Demo\n"
            "layer: 3\n"
            f"{frontmatter_extra}"
            "---\n"
        ).encode("utf-8")
        path.write_bytes(prefix + body)
        return parse_document(path, repo_root=self.root)

    def test_frontmatter_only_change_keeps_body_hash_stable(self) -> None:
        before = self._write_document(frontmatter_extra="source_status: UNVERIFIED\n")
        after = self._write_document(frontmatter_extra="source_status: VERIFIED\n")
        self.assertEqual(before.body_sha256, after.body_sha256)
        self.assertEqual(
            hashlib.sha256(b"# Demo\nbody\n").hexdigest(),
            after.body_sha256,
        )

    def test_each_body_byte_policy_change_changes_hash(self) -> None:
        baseline = self._write_document(body=b"# Demo\nbody\n")
        old_hash = baseline.body_sha256
        variants = {
            "single character": b"# Demo\nBody\n",
            "LF to CRLF": b"# Demo\r\nbody\r\n",
            "trailing newline": b"# Demo\nbody",
        }
        for label, body in variants.items():
            with self.subTest(label=label):
                changed = self._write_document(body=body)
                self.assertNotEqual(baseline.body_sha256, changed.body_sha256)

                from tools.trust_records import record_validity

                for record_id_key in ("audit_id", "review_id"):
                    with self.subTest(record_kind=record_id_key):
                        record = self._minimal_record(record_id_key, old_hash)
                        validity = record_validity(record, changed)
                        self.assertFalse(validity.is_current)
                        self.assertEqual("BODY_HASH_MISMATCH", validity.code)
                        # `expected` is the current canonical body; `actual` is
                        # the hash declared by the immutable record.
                        self.assertEqual(
                            changed.body_sha256,
                            validity.expected_body_sha256,
                        )
                        self.assertEqual(old_hash, validity.actual_body_sha256)

    def test_malformed_frontmatter_and_empty_body_fail_strict_parser(self) -> None:
        path = self.root / "docs/network/papers/demo.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        cases = {
            "malformed": (
                b"---\nid: demo\ntitle: [\n---\n# Demo\n",
                "INVALID_FRONTMATTER_YAML",
            ),
            "empty": (
                b"---\nid: demo\ntitle: Demo\nlayer: 3\n---\n",
                "MISSING_BODY_H1",
            ),
        }
        for label, (raw, code) in cases.items():
            with self.subTest(label=label):
                path.write_bytes(raw)
                with self.assertRaises(ContentError) as caught:
                    parse_document(path, repo_root=self.root)
                self.assertEqual(code, caught.exception.issue.code)

    @staticmethod
    def _minimal_record(record_id_key: str, body_hash: str) -> dict[str, object]:
        return {
            record_id_key: f"{record_id_key.removesuffix('_id')}-20260711-demo",
            "content_id": "demo",
            "content_path": "docs/network/papers/demo.md",
            "body_sha256": body_hash,
            "revocation": None,
        }

    def test_revoked_stale_record_remains_history_not_current_evidence(self) -> None:
        from tools.trust_records import record_validity

        current = self._write_document(body=b"# Demo\nbody changed\n")
        old_hash = hashlib.sha256(b"# Demo\nbody\n").hexdigest()
        for record_id_key in ("audit_id", "review_id"):
            with self.subTest(record_kind=record_id_key):
                record = self._minimal_record(record_id_key, old_hash)
                record["revocation"] = {
                    "revoked_at": "2026-07-11T09:30:00Z",
                    "reason_code": "BODY_CHANGED",
                }
                validity = record_validity(record, current)
                self.assertFalse(validity.is_current)
                self.assertTrue(validity.is_historical)
                self.assertEqual("REVOKED", validity.code)
                self.assertEqual(current.body_sha256, validity.expected_body_sha256)
                self.assertEqual(old_hash, validity.actual_body_sha256)

    def test_revocation_cannot_mask_wrong_content_identity(self) -> None:
        from tools.trust_records import record_validity

        current = self._write_document()
        revocation = {
            "revoked_at": "2026-07-11T09:30:00Z",
            "reason_code": "BODY_CHANGED",
        }
        mutations = (
            ("content_id", "other", "CONTENT_ID_MISMATCH"),
            ("content_path", "docs/network/papers/other.md", "CONTENT_PATH_MISMATCH"),
        )
        for field, value, expected_code in mutations:
            with self.subTest(field=field):
                record = self._minimal_record("audit_id", current.body_sha256)
                record["revocation"] = revocation
                record[field] = value
                validity = record_validity(record, current)
                self.assertEqual("INVALID", validity.state)
                self.assertEqual(expected_code, validity.code)
                self.assertFalse(validity.is_historical)

    def test_mirror_path_cannot_become_an_independent_trust_identity(self) -> None:
        from tools.trust_records import record_validity

        document = self._write_document()
        mirror = self.root / "papers/demo/index.md"
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_bytes(document.path.read_bytes())
        with self.assertRaises(ContentError) as caught:
            parse_document(mirror, repo_root=self.root)
        self.assertEqual("INVALID_CONTENT_PATH", caught.exception.issue.code)

        record = self._minimal_record("audit_id", document.body_sha256)
        record["content_path"] = "papers/demo/index.md"
        validity = record_validity(record, document)
        self.assertFalse(validity.is_current)
        self.assertEqual("CONTENT_PATH_MISMATCH", validity.code)


class TrustValidatorCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "data/source-audits").mkdir(parents=True)
        (self.root / "data/review-records").mkdir(parents=True)
        (self.root / "schemas").mkdir(parents=True)
        for name in ("source-audit.schema.json", "review-record.schema.json"):
            shutil.copyfile(ROOT / "schemas" / name, self.root / "schemas" / name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_document(self) -> object:
        path = self.root / "docs/network/papers/demo.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            b"---\n"
            b"schema_version: '1.0'\n"
            b"id: demo\n"
            b"title: Demo\n"
            b"layer: 3\n"
            b"---\n"
            b"# Demo\nbody changed\n"
        )
        return parse_document(path, repo_root=self.root)

    def _write_record(self, kind: str, *, old_hash: str) -> Path:
        if kind == "source":
            source = ROOT / "tests/fixtures/source-audits/valid-structural-auditable-noop.yml"
            record_path = self.root / "data/source-audits/network/audit-demo.yml"
        else:
            source = ROOT / "tests/fixtures/review-records/valid-start-review.yml"
            record_path = self.root / "data/review-records/review-demo.yml"
        record = yaml.safe_load(source.read_text(encoding="utf-8"))
        record.update(
            content_id="demo",
            content_path="docs/network/papers/demo.md",
            body_sha256=old_hash,
        )
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(
            yaml.safe_dump(record, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return record_path

    @staticmethod
    def _run(module: object, root: Path) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(module, "ROOT", root),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = module.main(["--all"])
        return result, stdout.getvalue(), stderr.getvalue()

    def test_all_succeeds_for_empty_record_directories(self) -> None:
        from tools import validate_review_records, validate_source_audits

        expectations = (
            (validate_source_audits, "SOURCE_AUDITS_OK checked=0"),
            (validate_review_records, "REVIEW_RECORDS_OK checked=0"),
        )
        for module, marker in expectations:
            with self.subTest(module=module.__name__):
                result, stdout, stderr = self._run(module, self.root)
                self.assertEqual(0, result)
                self.assertIn(marker, stdout)
                self.assertEqual("", stderr)

    def test_current_source_and_review_records_pass_cli(self) -> None:
        from tools import validate_review_records, validate_source_audits

        document = self._write_document()
        cases = (
            ("source", validate_source_audits, "SOURCE_AUDITS_OK checked=1"),
            ("review", validate_review_records, "REVIEW_RECORDS_OK checked=1"),
        )
        for kind, module, marker in cases:
            with self.subTest(kind=kind):
                for record_dir in ("source-audits", "review-records"):
                    for path in (self.root / "data" / record_dir).glob("**/*.yml"):
                        path.unlink()
                self._write_record(kind, old_hash=document.body_sha256)
                result, stdout, stderr = self._run(module, self.root)
                self.assertEqual(0, result)
                self.assertIn(marker, stdout)
                self.assertEqual("", stderr)

    def test_revoked_stale_source_and_review_records_remain_valid_history(self) -> None:
        from tools import validate_review_records, validate_source_audits

        self._write_document()
        old_hash = hashlib.sha256(b"# Demo\nbody\n").hexdigest()
        cases = (
            (
                "source",
                validate_source_audits,
                ROOT / "tests/fixtures/source-audits/valid-revoked.yml",
                self.root / "data/source-audits/network/revoked.yml",
                "SOURCE_AUDITS_OK checked=1",
            ),
            (
                "review",
                validate_review_records,
                ROOT / "tests/fixtures/review-records/valid-revoked.yml",
                self.root / "data/review-records/revoked.yml",
                "REVIEW_RECORDS_OK checked=1",
            ),
        )
        for kind, module, fixture, record_path, marker in cases:
            with self.subTest(kind=kind):
                for record_dir in ("source-audits", "review-records"):
                    for path in (self.root / "data" / record_dir).glob("**/*.yml"):
                        path.unlink()
                record = yaml.safe_load(fixture.read_text(encoding="utf-8"))
                record.update(
                    content_id="demo",
                    content_path="docs/network/papers/demo.md",
                    body_sha256=old_hash,
                )
                record_path.parent.mkdir(parents=True, exist_ok=True)
                record_path.write_text(
                    yaml.safe_dump(record, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                result, stdout, stderr = self._run(module, self.root)
                self.assertEqual(0, result)
                self.assertIn(marker, stdout)
                self.assertEqual("", stderr)

    def test_hash_mismatch_cli_contract_is_stable_and_path_safe(self) -> None:
        from tools import validate_review_records, validate_source_audits

        document = self._write_document()
        old_hash = hashlib.sha256(b"# Demo\nbody\n").hexdigest()
        expectations = (
            (
                "source",
                validate_source_audits,
                "SOURCE_AUDITS_INVALID",
                "data/source-audits/network/audit-demo.yml",
            ),
            (
                "review",
                validate_review_records,
                "REVIEW_RECORDS_INVALID",
                "data/review-records/review-demo.yml",
            ),
        )
        for kind, module, header, record_path in expectations:
            with self.subTest(kind=kind):
                for record_dir in ("source-audits", "review-records"):
                    for path in (self.root / "data" / record_dir).glob("**/*.yml"):
                        path.unlink()
                self._write_record(kind, old_hash=old_hash)
                result, stdout, stderr = self._run(module, self.root)
                self.assertEqual(1, result)
                self.assertEqual("", stdout)
                self.assertIn(header, stderr)
                self.assertIn("BODY_HASH_MISMATCH", stderr)
                self.assertIn("content_id=demo", stderr)
                self.assertIn(f"record_path={record_path}", stderr)
                self.assertIn(f"expected={document.body_sha256}", stderr)
                self.assertIn(f"actual={old_hash}", stderr)
                self.assertNotIn(str(self.root), stderr)
                self.assertNotIn(str(Path.home()), stderr)

    def test_schema_formats_are_fail_closed_and_instance_values_are_redacted(self) -> None:
        from tools import validate_source_audits

        document = self._write_document()
        fixture = ROOT / "tests/fixtures/source-audits/valid-claim-unverified-to-verified.yml"
        base = yaml.safe_load(fixture.read_text(encoding="utf-8"))
        base.update(
            content_id="demo",
            content_path="docs/network/papers/demo.md",
            body_sha256=document.body_sha256,
        )
        private_fragment = (Path.home() / "private-evidence").as_posix()
        variants = (
            ("date-time", lambda record: record.__setitem__("audited_at", "not-a-date"), "not-a-date"),
            (
                "uri",
                lambda record: record["source_references"][0].__setitem__(
                    "uri", f"https://{private_fragment}"
                ),
                private_fragment,
            ),
        )
        record_path = self.root / "data/source-audits/network/audit-demo.yml"
        record_path.parent.mkdir(parents=True, exist_ok=True)
        for label, mutate, secret_value in variants:
            with self.subTest(label=label):
                record = yaml.safe_load(yaml.safe_dump(base))
                mutate(record)
                record_path.write_text(
                    yaml.safe_dump(record, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                result, stdout, stderr = self._run(validate_source_audits, self.root)
                self.assertEqual(1, result)
                self.assertEqual("", stdout)
                self.assertIn("SCHEMA_VALIDATION_FAILED", stderr)
                self.assertNotIn(secret_value, stderr)
                self.assertNotIn(str(self.root), stderr)

    def test_schema_loader_requires_explicit_draft_2020_12(self) -> None:
        from tools.trust_records import TrustRecordError, load_schema

        schema_path = self.root / "schema.json"
        candidates = (
            {"type": "object"},
            {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"},
            {"$schema": "not a uri", "type": "object"},
        )
        for payload in candidates:
            with self.subTest(schema=payload.get("$schema")):
                schema_path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(TrustRecordError) as caught:
                    load_schema(schema_path)
                self.assertEqual("SCHEMA_DIALECT_MISMATCH", caught.exception.code)

    def test_record_enumeration_errors_are_stable_and_redacted(self) -> None:
        from tools import trust_records, validate_review_records, validate_source_audits

        private_records_path = str(Path.home() / "private" / "records")
        for module in (validate_source_audits, validate_review_records):
            with self.subTest(module=module.__name__):
                with mock.patch.object(
                    trust_records,
                    "iter_record_paths",
                    side_effect=OSError(private_records_path),
                ):
                    result, stdout, stderr = self._run(module, self.root)
                self.assertEqual(2, result)
                self.assertEqual("", stdout)
                self.assertIn("RECORD_ENUMERATION_ERROR", stderr)
                self.assertNotIn(private_records_path, stderr)

    def test_record_root_file_fails_closed_instead_of_looking_empty(self) -> None:
        from tools import validate_review_records, validate_source_audits

        cases = (
            (validate_source_audits, self.root / "data/source-audits"),
            (validate_review_records, self.root / "data/review-records"),
        )
        for module, record_root in cases:
            with self.subTest(module=module.__name__):
                record_root.rmdir()
                record_root.write_text("not a directory", encoding="utf-8")
                try:
                    result, stdout, stderr = self._run(module, self.root)
                finally:
                    record_root.unlink()
                    record_root.mkdir()
                self.assertEqual(2, result)
                self.assertEqual("", stdout)
                self.assertIn("RECORD_ROOT_NOT_DIRECTORY", stderr)
                self.assertNotIn(str(self.root), stderr)

    def test_cli_selection_is_mutually_exclusive_and_scoped_to_record_root(self) -> None:
        from tools import validate_source_audits

        parser_stderr = io.StringIO()
        with redirect_stderr(parser_stderr), self.assertRaises(SystemExit) as caught:
            validate_source_audits.main(["--all", "--path", "data/source-audits/demo.yml"])
        self.assertEqual(2, caught.exception.code)
        self.assertIn("not allowed with argument --all", parser_stderr.getvalue())

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(validate_source_audits, "ROOT", self.root),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = validate_source_audits.main(
                ["--path", "schemas/source-audit.schema.json"]
            )
        self.assertEqual(1, result)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("UNSAFE_RECORD_PATH", stderr.getvalue())
        self.assertNotIn(str(self.root), stderr.getvalue())

    def test_duplicate_yaml_keys_fail_closed(self) -> None:
        from tools import validate_source_audits

        document = self._write_document()
        record_path = self._write_record("source", old_hash=document.body_sha256)
        record_path.write_bytes(
            record_path.read_bytes()
            + f"body_sha256: {document.body_sha256}\n".encode("ascii")
        )
        result, stdout, stderr = self._run(validate_source_audits, self.root)
        self.assertEqual(1, result)
        self.assertEqual("", stdout)
        self.assertIn("RECORD_INVALID_YAML", stderr)

    def test_cli_rejects_absolute_traversal_and_record_symlink_paths(self) -> None:
        from tools import validate_review_records, validate_source_audits

        cases = (
            (validate_source_audits, "data/source-audits"),
            (validate_review_records, "data/review-records"),
        )
        for module, relative_root in cases:
            with self.subTest(module=module.__name__):
                outside = self.root / f"outside-{module.__name__.rsplit('.', 1)[-1]}.yml"
                outside.write_text("{}\n", encoding="utf-8")
                link = self.root / relative_root / "linked.yml"
                link.symlink_to(outside)
                try:
                    values = (
                        str(link),
                        f"{relative_root}/../outside.yml",
                        f"{relative_root}/linked.yml",
                    )
                    for value in values:
                        with self.subTest(value=value):
                            stdout = io.StringIO()
                            stderr = io.StringIO()
                            with (
                                mock.patch.object(module, "ROOT", self.root),
                                redirect_stdout(stdout),
                                redirect_stderr(stderr),
                            ):
                                result = module.main(["--path", value])
                            self.assertEqual(1, result)
                            self.assertEqual("", stdout.getvalue())
                            self.assertIn("UNSAFE_RECORD_PATH", stderr.getvalue())
                            self.assertNotIn(str(self.root), stderr.getvalue())
                            self.assertNotIn(str(Path.home()), stderr.getvalue())
                finally:
                    link.unlink()
                    outside.unlink()

    def test_record_root_and_content_path_symlink_escapes_are_rejected(self) -> None:
        from tools import validate_review_records, validate_source_audits

        root_cases = (
            (validate_source_audits, self.root / "data/source-audits"),
            (validate_review_records, self.root / "data/review-records"),
        )
        for module, record_root in root_cases:
            with self.subTest(module=module.__name__, path_kind="record-root"):
                outside_root = self.root / f"outside-{record_root.name}"
                record_root.rmdir()
                outside_root.mkdir()
                record_root.symlink_to(outside_root, target_is_directory=True)
                try:
                    result, stdout, stderr = self._run(module, self.root)
                finally:
                    record_root.unlink()
                    outside_root.rmdir()
                    record_root.mkdir()
                self.assertEqual(1, result)
                self.assertEqual("", stdout)
                self.assertIn("UNSAFE_RECORD_ROOT", stderr)
                self.assertNotIn(str(self.root), stderr)

        document = self._write_document()
        self._write_record("source", old_hash=document.body_sha256)
        network = self.root / "docs/network"
        moved_network = self.root / "outside-network"
        network.rename(moved_network)
        network.symlink_to(moved_network, target_is_directory=True)
        result, stdout, stderr = self._run(validate_source_audits, self.root)
        self.assertEqual(1, result)
        self.assertEqual("", stdout)
        self.assertIn("INVALID_CONTENT_PATH", stderr)
        self.assertNotIn(str(self.root), stderr)


if __name__ == "__main__":
    unittest.main()
