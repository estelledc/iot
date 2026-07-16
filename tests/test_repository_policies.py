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

    @staticmethod
    def _setup_python_step(workflow, job_name):
        return next(
            step
            for step in workflow["jobs"][job_name]["steps"]
            if str(step.get("uses", "")).startswith("actions/setup-python@")
        )

    @staticmethod
    def _insert_pip_check(workflow, job_name):
        steps = workflow["jobs"][job_name]["steps"]
        if any(step.get("run") == "python -m pip check" for step in steps):
            return
        install_index = next(
            index
            for index, step in enumerate(steps)
            if step.get("run")
            == "python -m pip install --require-hashes -r requirements.lock"
        )
        steps.insert(
            install_index + 1,
            {"name": "Verify installed dependencies", "run": "python -m pip check"},
        )

    @staticmethod
    def _insert_active_goal_check(workflow, job_name):
        steps = workflow["jobs"][job_name]["steps"]
        if any(
            step.get("run") == "python tools/check_active_goal.py"
            for step in steps
        ):
            return
        check_index = next(
            index
            for index, step in enumerate(steps)
            if step.get("run") == "python -m pip check"
        )
        steps.insert(
            check_index + 1,
            {
                "name": "Validate active goal contract",
                "run": "python tools/check_active_goal.py",
            },
        )

    @staticmethod
    def _remove_active_goal_check(workflow, job_name):
        steps = workflow["jobs"][job_name]["steps"]
        workflow["jobs"][job_name]["steps"] = [
            step
            for step in steps
            if step.get("run") != "python tools/check_active_goal.py"
        ]

    @classmethod
    def _duplicate_active_goal_check(cls, workflow, job_name):
        cls._insert_active_goal_check(workflow, job_name)
        step = cls._step_with_command(
            workflow,
            job_name,
            "python tools/check_active_goal.py",
        )
        workflow["jobs"][job_name]["steps"].append(copy.deepcopy(step))

    @staticmethod
    def _step_with_command(workflow, job_name, command):
        return next(
            step
            for step in workflow["jobs"][job_name]["steps"]
            if isinstance(step.get("run"), str)
            and command in {line.strip() for line in step["run"].splitlines()}
        )

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

    def test_python_runtime_must_come_from_repository_version_file(self):
        for workflow_name, path, job_name, validator in self._workflow_cases():
            for mutation_name, setup_with, expected in (
                (
                    "hard-coded runtime",
                    {"python-version": "3.10"},
                    "python-version-file: .python-version",
                ),
                (
                    "wrong version file",
                    {"python-version-file": "requirements.txt"},
                    "python-version-file: .python-version",
                ),
            ):
                with self.subTest(workflow=workflow_name, mutation=mutation_name):
                    changed = check_workflow_policy.load_workflow(path)
                    setup = self._setup_python_step(changed, job_name)
                    setup["with"] = setup_with
                    errors = validator(path, changed)
                    self.assertTrue(
                        any(expected in error for error in errors),
                        errors,
                    )

            with self.subTest(workflow=workflow_name, mutation="duplicate setup"):
                changed = check_workflow_policy.load_workflow(path)
                setup = copy.deepcopy(self._setup_python_step(changed, job_name))
                changed["jobs"][job_name]["steps"].append(setup)
                errors = validator(path, changed)
                self.assertTrue(
                    any("exactly one setup-python step" in error for error in errors),
                    errors,
                )

            with self.subTest(workflow=workflow_name, mutation="skipped setup"):
                changed = check_workflow_policy.load_workflow(path)
                setup = self._setup_python_step(changed, job_name)
                setup["if"] = "false"
                errors = validator(path, changed)
                self.assertTrue(
                    any("setup-python step must not have an if condition" in error for error in errors),
                    errors,
                )

    def test_dependency_health_check_is_required_and_fail_closed(self):
        for workflow_name, path, job_name, validator in self._workflow_cases():
            workflow = check_workflow_policy.load_workflow(path)
            self._insert_pip_check(workflow, job_name)
            for mutation_name, mutate, expected in (
                (
                    "missing pip check",
                    lambda step: step.update(run=""),
                    "missing required command: python -m pip check",
                ),
                (
                    "wrapped pip check",
                    lambda step: step.update(run="if false; then\n  python -m pip check\nfi"),
                    "missing required command: python -m pip check",
                ),
                (
                    "conditional pip check",
                    lambda step: step.update({"if": "false"}),
                    "pip check step must not have an if condition",
                ),
                (
                    "continue on error",
                    lambda step: step.update({"continue-on-error": True}),
                    "pip check step must fail closed",
                ),
            ):
                with self.subTest(workflow=workflow_name, mutation=mutation_name):
                    changed = copy.deepcopy(workflow)
                    step = next(
                        item
                        for item in changed["jobs"][job_name]["steps"]
                        if item.get("run") == "python -m pip check"
                    )
                    mutate(step)
                    errors = validator(path, changed)
                    self.assertTrue(
                        any(expected in error for error in errors),
                        errors,
                    )

    def test_active_goal_check_is_required_exactly_once_and_unwrapped(self):
        command = "python tools/check_active_goal.py"
        for workflow_name, path, job_name, validator in self._workflow_cases():
            for mutation_name, mutate, expected in (
                (
                    "missing",
                    lambda workflow: self._remove_active_goal_check(
                        workflow,
                        job_name,
                    ),
                    f"missing required command: {command}",
                ),
                (
                    "duplicate",
                    lambda workflow: self._duplicate_active_goal_check(
                        workflow,
                        job_name,
                    ),
                    f"must run required command exactly once: {command}",
                ),
                (
                    "wrapped",
                    lambda workflow: (
                        self._insert_active_goal_check(workflow, job_name),
                        self._step_with_command(
                            workflow,
                            job_name,
                            command,
                        ).update(run=f"if false; then\n  {command}\nfi"),
                    ),
                    f"missing required command: {command}",
                ),
            ):
                with self.subTest(workflow=workflow_name, mutation=mutation_name):
                    changed = check_workflow_policy.load_workflow(path)
                    mutate(changed)
                    errors = validator(path, changed)
                    self.assertTrue(
                        any(expected in error for error in errors),
                        errors,
                    )

    def test_active_goal_check_is_fail_closed(self):
        command = "python tools/check_active_goal.py"
        mutations = (
            (
                "step condition",
                lambda step: step.update({"if": "false"}),
                "active-goal check step must not have an if condition",
            ),
            (
                "continue on error",
                lambda step: step.update({"continue-on-error": True}),
                "active-goal check step must fail closed",
            ),
            (
                "custom shell",
                lambda step: step.update(shell="bash -c 'exit 0' -- {0}"),
                "active-goal check step must use the default shell",
            ),
            (
                "working directory",
                lambda step: step.update({"working-directory": "fake-validator-root"}),
                "active-goal check step must run at repository root",
            ),
            (
                "step environment",
                lambda step: step.update(env={"PYTHONPATH": "fake-validator-root"}),
                "active-goal check step must not override its environment",
            ),
        )
        for workflow_name, path, job_name, validator in self._workflow_cases():
            for mutation_name, mutate, expected in mutations:
                with self.subTest(workflow=workflow_name, mutation=mutation_name):
                    changed = check_workflow_policy.load_workflow(path)
                    self._insert_active_goal_check(changed, job_name)
                    step = self._step_with_command(changed, job_name, command)
                    mutate(step)
                    errors = validator(path, changed)
                    self.assertTrue(
                        any(expected in error for error in errors),
                        errors,
                    )

    def test_active_goal_check_order_is_enforced(self):
        command = "python tools/check_active_goal.py"
        for workflow_name, path, job_name, validator in self._workflow_cases():
            changed = check_workflow_policy.load_workflow(path)
            self._insert_active_goal_check(changed, job_name)
            steps = changed["jobs"][job_name]["steps"]
            check_step = self._step_with_command(changed, job_name, command)
            check_index = steps.index(check_step)

            with self.subTest(workflow=workflow_name, mutation="before setup-python"):
                reordered = copy.deepcopy(changed)
                reordered_steps = reordered["jobs"][job_name]["steps"]
                moved = reordered_steps.pop(check_index)
                setup_step = self._setup_python_step(reordered, job_name)
                reordered_steps.insert(reordered_steps.index(setup_step), moved)
                errors = validator(path, reordered)
                self.assertTrue(
                    any(
                        "active-goal check must run after setup-python, "
                        "hash-locked install, and pip check" in error
                        for error in errors
                    ),
                    errors,
                )

            for prerequisite in (
                "python -m pip install --require-hashes -r requirements.lock",
                "python -m pip check",
            ):
                with self.subTest(
                    workflow=workflow_name,
                    mutation=f"before {prerequisite}",
                ):
                    reordered = copy.deepcopy(changed)
                    reordered_steps = reordered["jobs"][job_name]["steps"]
                    moved = reordered_steps.pop(check_index)
                    prerequisite_step = self._step_with_command(
                        reordered,
                        job_name,
                        prerequisite,
                    )
                    reordered_steps.insert(reordered_steps.index(prerequisite_step), moved)
                    errors = validator(path, reordered)
                    self.assertTrue(
                        any(
                            "active-goal check must run after setup-python, "
                            "hash-locked install, and pip check" in error
                            for error in errors
                        ),
                        errors,
                    )

            for successor in (
                "python tools/content_inventory.py --check",
                "python tools/validate_source_audits.py --all",
                "python -m unittest discover -s tests -v",
                (
                    "mkdocs build --strict --site-dir .tmp/site"
                    if workflow_name == "ci"
                    else "mkdocs build --strict"
                ),
            ):
                with self.subTest(
                    workflow=workflow_name,
                    mutation=f"after {successor}",
                ):
                    reordered = copy.deepcopy(changed)
                    reordered_steps = reordered["jobs"][job_name]["steps"]
                    moved = reordered_steps.pop(check_index)
                    successor_step = self._step_with_command(
                        reordered,
                        job_name,
                        successor,
                    )
                    successor_index = reordered_steps.index(successor_step)
                    reordered_steps.insert(successor_index + 1, moved)
                    errors = validator(path, reordered)
                    self.assertTrue(
                        any(
                            "active-goal check must run before inventory, trust, "
                            "tests, and build" in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_python_bootstrap_order_and_lock_install_are_enforced(self):
        install_command = "python -m pip install --require-hashes -r requirements.lock"
        for workflow_name, path, job_name, validator in self._workflow_cases():
            with self.subTest(workflow=workflow_name, mutation="unlocked install"):
                changed = check_workflow_policy.load_workflow(path)
                self._replace_command(
                    changed,
                    job_name,
                    install_command,
                    "python -m pip install -r requirements.txt",
                )
                errors = validator(path, changed)
                self.assertTrue(
                    any(
                        f"missing required command: {install_command}" in error
                        for error in errors
                    ),
                    errors,
                )

            with self.subTest(workflow=workflow_name, mutation="pip check before install"):
                changed = check_workflow_policy.load_workflow(path)
                steps = changed["jobs"][job_name]["steps"]
                install_index = next(
                    index
                    for index, step in enumerate(steps)
                    if step.get("run") == install_command
                )
                check_index = next(
                    index
                    for index, step in enumerate(steps)
                    if step.get("run") == "python -m pip check"
                )
                steps[install_index], steps[check_index] = (
                    steps[check_index],
                    steps[install_index],
                )
                errors = validator(path, changed)
                self.assertTrue(
                    any("Python bootstrap order" in error for error in errors),
                    errors,
                )

            with self.subTest(workflow=workflow_name, mutation="additional unlocked install"):
                changed = check_workflow_policy.load_workflow(path)
                steps = changed["jobs"][job_name]["steps"]
                check_index = next(
                    index
                    for index, step in enumerate(steps)
                    if step.get("run") == "python -m pip check"
                )
                steps.insert(
                    check_index + 1,
                    {"run": "python -m pip install unexpected-package"},
                )
                errors = validator(path, changed)
                self.assertTrue(
                    any("unlocked or additional pip install" in error for error in errors),
                    errors,
                )

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
