import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools import check_duplicates, check_workflow_policy


class DuplicatePolicyTests(unittest.TestCase):
    def test_declared_sources_have_no_drift(self):
        errors, counts = check_duplicates.validate_policy(
            check_duplicates.ROOT / "data/canonical-sources.yml"
        )
        self.assertEqual(errors, [])
        self.assertEqual(counts, {"canonical_css": 2, "legacy_markdown_mirrors": 2})

    @staticmethod
    def _write_mirror_fixture(
        root: Path,
        *,
        canonical: str = "docs/network/papers/a.md",
        mirror: str = "papers/a/index.md",
    ) -> Path:
        for raw_path, content in ((canonical, "canonical\n"), (mirror, "stale\n")):
            relative = Path(raw_path)
            if relative.is_absolute() or ".." in relative.parts:
                continue
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        policy = root / "data" / "canonical-sources.yml"
        policy.parent.mkdir(parents=True)
        policy.write_text(
            "schema_version: 1\n"
            "canonical_css: []\n"
            "legacy_markdown_mirrors:\n"
            f"  - canonical: {canonical}\n"
            f"    mirror: {mirror}\n"
            "    policy: READ_ONLY_MIRROR\n",
            encoding="utf-8",
        )
        return policy

    def test_legacy_mirror_sync_is_one_way_and_idempotent(self):
        from tools import sync_legacy_mirrors

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = self._write_mirror_fixture(root)
            canonical = root / "docs/network/papers/a.md"
            mirror = root / "papers/a/index.md"
            canonical_before = hashlib.sha256(canonical.read_bytes()).hexdigest()
            errors, updated = sync_legacy_mirrors.sync_policy(
                policy,
                root=root,
                write=False,
            )
            self.assertEqual(1, len(errors))
            self.assertEqual(0, updated)
            self.assertEqual(b"stale\n", mirror.read_bytes())
            errors, updated = sync_legacy_mirrors.sync_policy(
                policy,
                root=root,
                write=True,
            )
            self.assertEqual([], errors)
            self.assertEqual(1, updated)
            self.assertEqual(canonical.read_bytes(), mirror.read_bytes())
            self.assertEqual(
                canonical_before,
                hashlib.sha256(canonical.read_bytes()).hexdigest(),
            )
            errors, updated = sync_legacy_mirrors.sync_policy(
                policy,
                root=root,
                write=True,
            )
            self.assertEqual([], errors)
            self.assertEqual(0, updated)

    def test_legacy_mirror_sync_rejects_path_traversal(self):
        from tools import sync_legacy_mirrors

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = self._write_mirror_fixture(
                root,
                mirror="../outside.md",
            )
            with self.assertRaisesRegex(ValueError, "safe repository-relative path"):
                sync_legacy_mirrors.sync_policy(policy, root=root, write=True)

    def test_legacy_mirror_sync_rejects_reverse_direction(self):
        from tools import sync_legacy_mirrors

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = self._write_mirror_fixture(
                root,
                canonical="papers/a/index.md",
                mirror="docs/network/papers/a.md",
            )
            with self.assertRaisesRegex(ValueError, "canonical must be under docs/"):
                sync_legacy_mirrors.sync_policy(policy, root=root, write=True)

    def test_legacy_mirror_sync_rejects_absolute_path(self):
        from tools import sync_legacy_mirrors

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / f"{root.name}-outside.md"
            policy = self._write_mirror_fixture(root)
            policy.write_text(
                "schema_version: 1\n"
                "canonical_css: []\n"
                "legacy_markdown_mirrors:\n"
                "  - canonical: docs/network/papers/a.md\n"
                f"    mirror: {outside}\n"
                "    policy: READ_ONLY_MIRROR\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "safe repository-relative path"):
                sync_legacy_mirrors.sync_policy(policy, root=root, write=True)

    def test_legacy_mirror_sync_rejects_missing_paths(self):
        from tools import sync_legacy_mirrors

        missing_paths = (("canonical", "missing canonical"), ("mirror", "missing mirror"))
        for missing, message in missing_paths:
            with (
                self.subTest(missing=missing),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                policy = self._write_mirror_fixture(root)
                target = (
                    root / "docs/network/papers/a.md"
                    if missing == "canonical"
                    else root / "papers/a/index.md"
                )
                target.unlink()
                with self.assertRaisesRegex(ValueError, message):
                    sync_legacy_mirrors.sync_policy(policy, root=root, write=True)

    def test_legacy_mirror_sync_preflights_all_pairs_before_writing(self):
        from tools import sync_legacy_mirrors

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = self._write_mirror_fixture(root)
            second = root / "docs/computing/papers/b.md"
            second.parent.mkdir(parents=True)
            second.write_text("second\n", encoding="utf-8")
            policy.write_text(
                policy.read_text(encoding="utf-8")
                + "  - canonical: docs/computing/papers/b.md\n"
                + "    mirror: papers/b/index.md\n"
                + "    policy: READ_ONLY_MIRROR\n",
                encoding="utf-8",
            )
            first_mirror = root / "papers/a/index.md"
            with self.assertRaisesRegex(ValueError, "missing mirror"):
                sync_legacy_mirrors.sync_policy(policy, root=root, write=True)
            self.assertEqual(b"stale\n", first_mirror.read_bytes())

    def test_legacy_mirror_sync_rejects_duplicate_target(self):
        from tools import sync_legacy_mirrors

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = self._write_mirror_fixture(root)
            second = root / "docs/computing/papers/b.md"
            second.parent.mkdir(parents=True)
            second.write_text("second\n", encoding="utf-8")
            policy.write_text(
                policy.read_text(encoding="utf-8")
                + "  - canonical: docs/computing/papers/b.md\n"
                + "    mirror: papers/a/index.md\n"
                + "    policy: READ_ONLY_MIRROR\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate mirror target"):
                sync_legacy_mirrors.sync_policy(policy, root=root, write=True)

    def test_legacy_mirror_sync_rejects_symlink_escape(self):
        from tools import sync_legacy_mirrors

        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory() as outside_directory,
        ):
            root = Path(directory)
            policy = self._write_mirror_fixture(root)
            mirror = root / "papers/a/index.md"
            outside = Path(outside_directory) / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            mirror.unlink()
            mirror.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "safe repository-relative path"):
                sync_legacy_mirrors.sync_policy(policy, root=root, write=True)

    def test_canonical_change_drifts_mirror_and_stales_trust_until_reaudit(self):
        """One body edit couples mirror refresh to trust invalidation.

        Refreshing the derived mirror must not make the immutable old audit
        current again; only the canonical docs identity can own trust.
        """

        from tools import sync_legacy_mirrors
        from tools.iot_domain import ContentError, parse_document
        from tools.trust_records import record_validity

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = self._write_mirror_fixture(root)
            canonical = root / "docs/network/papers/a.md"
            mirror = root / "papers/a/index.md"
            original = (
                b"---\n"
                b"schema_version: '1.0'\n"
                b"id: a\n"
                b"title: A\n"
                b"layer: 3\n"
                b"---\n"
                b"# A\nbody\n"
            )
            canonical.write_bytes(original)
            mirror.write_bytes(original)
            before = parse_document(canonical, repo_root=root)
            record = {
                "audit_id": "audit-20260711-a",
                "content_id": "a",
                "content_path": "docs/network/papers/a.md",
                "body_sha256": before.body_sha256,
                "revocation": None,
            }
            self.assertTrue(record_validity(record, before).is_current)

            canonical.write_bytes(original.replace(b"body\n", b"Body\n"))
            changed = parse_document(canonical, repo_root=root)
            errors, updated = sync_legacy_mirrors.sync_policy(
                policy,
                root=root,
                write=False,
            )
            self.assertEqual(1, len(errors))
            self.assertEqual(0, updated)
            self.assertNotEqual(canonical.read_bytes(), mirror.read_bytes())
            self.assertEqual(
                "BODY_HASH_MISMATCH",
                record_validity(record, changed).code,
            )

            errors, updated = sync_legacy_mirrors.sync_policy(
                policy,
                root=root,
                write=True,
            )
            self.assertEqual([], errors)
            self.assertEqual(1, updated)
            self.assertEqual(canonical.read_bytes(), mirror.read_bytes())
            self.assertEqual(
                "BODY_HASH_MISMATCH",
                record_validity(record, changed).code,
            )
            with self.assertRaises(ContentError) as caught:
                parse_document(mirror, repo_root=root)
            self.assertEqual("INVALID_CONTENT_PATH", caught.exception.issue.code)


class WorkflowPolicyTests(unittest.TestCase):
    @staticmethod
    def _workflow_cases():
        root = check_workflow_policy.ROOT
        return (
            (
                "ci",
                root / ".github/workflows/ci.yml",
                "quality",
                check_workflow_policy.validate_ci,
            ),
            (
                "deploy",
                root / ".github/workflows/deploy.yml",
                "build",
                check_workflow_policy.validate_deploy,
            ),
        )

    @staticmethod
    def _replace_command(workflow, job_name, old, new):
        replacements = 0
        for step in workflow["jobs"][job_name]["steps"]:
            run = step.get("run")
            if not isinstance(run, str):
                continue
            lines = run.splitlines()
            changed_lines = [new if line.strip() == old else line for line in lines]
            replacements += sum(line.strip() == old for line in lines)
            step["run"] = "\n".join(changed_lines)
        if replacements != 1:
            raise AssertionError(f"expected one occurrence of {old!r}, got {replacements}")

    def test_repository_workflows_follow_policy(self):
        ci = check_workflow_policy.load_workflow(check_workflow_policy.ROOT / ".github/workflows/ci.yml")
        deploy = check_workflow_policy.load_workflow(
            check_workflow_policy.ROOT / ".github/workflows/deploy.yml"
        )
        self.assertEqual(check_workflow_policy.validate_ci(check_workflow_policy.ROOT / ".github/workflows/ci.yml", ci), [])
        self.assertEqual(
            check_workflow_policy.validate_deploy(
                check_workflow_policy.ROOT / ".github/workflows/deploy.yml", deploy
            ),
            [],
        )

    def test_mutable_action_ref_is_rejected(self):
        ci = check_workflow_policy.load_workflow(check_workflow_policy.ROOT / ".github/workflows/ci.yml")
        changed = copy.deepcopy(ci)
        changed["jobs"]["quality"]["steps"][0]["uses"] = "actions/checkout@v4"
        errors = check_workflow_policy.validate_ci(
            check_workflow_policy.ROOT / ".github/workflows/ci.yml", changed
        )
        self.assertTrue(any("mutable" in error for error in errors))

    def test_each_required_trust_validation_command_is_enforced(self):
        for workflow_name, path, job_name, validator in self._workflow_cases():
            workflow = check_workflow_policy.load_workflow(path)
            for command in check_workflow_policy.REQUIRED_TRUST_VALIDATION_COMMANDS:
                with self.subTest(workflow=workflow_name, command=command):
                    changed = copy.deepcopy(workflow)
                    self._replace_command(changed, job_name, command, "")
                    errors = validator(path, changed)
                    self.assertTrue(
                        any(
                            "missing required command" in error and command in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_trust_validation_command_order_is_enforced(self):
        first, second, _ = (
            check_workflow_policy.REQUIRED_TRUST_VALIDATION_COMMANDS
        )
        for workflow_name, path, job_name, validator in self._workflow_cases():
            with self.subTest(workflow=workflow_name):
                changed = check_workflow_policy.load_workflow(path)
                self._replace_command(changed, job_name, first, "__SWAP__")
                self._replace_command(changed, job_name, second, first)
                self._replace_command(changed, job_name, "__SWAP__", second)
                errors = validator(path, changed)
                self.assertTrue(
                    any("trust validation commands must run in order" in error for error in errors),
                    errors,
                )

    def test_trust_validation_commands_cannot_be_wrapped_or_skipped(self):
        command = check_workflow_policy.REQUIRED_TRUST_VALIDATION_COMMANDS[0]
        mutations = (
            (
                "shell wrapper",
                lambda step: step.update(run=f"if false; then\n  {command}\nfi"),
                "missing required command",
            ),
            (
                "step condition",
                lambda step: step.update({"if": "false"}),
                "must not have an if condition",
            ),
            (
                "continue on error",
                lambda step: step.update({"continue-on-error": True}),
                "must fail closed",
            ),
            (
                "custom shell",
                lambda step: step.update(shell="bash -c 'exit 0' -- {0}"),
                "default shell",
            ),
            (
                "working directory",
                lambda step: step.update({"working-directory": "fake-validator-root"}),
                "repository root",
            ),
            (
                "step environment",
                lambda step: step.update(env={"PYTHONPATH": "fake-validator-root"}),
                "must not override its environment",
            ),
        )
        for workflow_name, path, job_name, validator in self._workflow_cases():
            for mutation_name, mutate, expected in mutations:
                with self.subTest(workflow=workflow_name, mutation=mutation_name):
                    changed = check_workflow_policy.load_workflow(path)
                    step = next(
                        item
                        for item in changed["jobs"][job_name]["steps"]
                        if isinstance(item.get("run"), str)
                        and item["run"].strip() == command
                    )
                    mutate(step)
                    errors = validator(path, changed)
                    self.assertTrue(
                        any(expected in error for error in errors),
                        errors,
                    )

    def test_trust_validation_job_cannot_be_conditionally_skipped(self):
        for workflow_name, path, job_name, validator in self._workflow_cases():
            for field, value, expected in (
                ("if", "false", "must not conditionally skip"),
                ("continue-on-error", True, "must not continue"),
            ):
                with self.subTest(workflow=workflow_name, field=field):
                    changed = check_workflow_policy.load_workflow(path)
                    changed["jobs"][job_name][field] = value
                    errors = validator(path, changed)
                    self.assertTrue(
                        any(expected in error for error in errors),
                        errors,
                    )

    def test_trust_validation_defaults_and_environment_are_rejected(self):
        for workflow_name, path, job_name, validator in self._workflow_cases():
            mutations = (
                (
                    "workflow defaults",
                    lambda workflow: workflow.update(
                        defaults={"run": {"working-directory": "fake-validator-root"}}
                    ),
                    "workflow defaults",
                ),
                (
                    "workflow env",
                    lambda workflow: workflow.update(
                        env={"PYTHONPATH": "fake-validator-root"}
                    ),
                    "workflow env",
                ),
                (
                    "job defaults",
                    lambda workflow: workflow["jobs"][job_name].update(
                        defaults={"run": {"shell": "bash -c 'exit 0' -- {0}"}}
                    ),
                    "job quality defaults" if job_name == "quality" else "job build defaults",
                ),
                (
                    "job env",
                    lambda workflow: workflow["jobs"][job_name].update(
                        env={"PATH": "fake-validator-root"}
                    ),
                    "job quality env" if job_name == "quality" else "job build env",
                ),
            )
            for mutation_name, mutate, expected in mutations:
                with self.subTest(workflow=workflow_name, mutation=mutation_name):
                    changed = check_workflow_policy.load_workflow(path)
                    mutate(changed)
                    errors = validator(path, changed)
                    self.assertTrue(
                        any(expected in error for error in errors),
                        errors,
                    )

    def test_full_checkout_history_is_required_for_ledger_provenance(self):
        for workflow_name, path, job_name, validator in self._workflow_cases():
            with self.subTest(workflow=workflow_name):
                changed = check_workflow_policy.load_workflow(path)
                checkout = next(
                    step
                    for step in changed["jobs"][job_name]["steps"]
                    if str(step.get("uses", "")).startswith("actions/checkout@")
                )
                checkout["with"] = {"fetch-depth": 1}
                errors = validator(path, changed)
                self.assertTrue(
                    any("fetch-depth: 0" in error for error in errors),
                    errors,
                )


class PublicDiscoveryTests(unittest.TestCase):
    def test_robots_points_to_public_sitemap(self):
        robots = (Path(__file__).resolve().parents[1] / "docs" / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://estelledc.github.io/iot/sitemap.xml", robots)


if __name__ == "__main__":
    unittest.main()
