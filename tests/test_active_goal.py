from __future__ import annotations

import copy
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import check_active_goal, trust_records


def _prepared_fixture(payload: dict) -> dict:
    prepared = copy.deepcopy(payload)
    prepared["status"] = "PREPARED"
    prepared["activated_by"] = "PENDING_DEDICATED_AGENT_LAUNCH"
    prepared["review_after"] = "FIRST_SLICE_ACCEPTANCE"
    prepared["external_outcome"]["d_axis"] = "D0"
    prepared["superseded_by"] = None
    prepared["selection"] = {
        "policy": payload["selection"]["policy"],
        "selected_articles": [],
        "rationale": None,
    }
    prepared["progress"] = {
        "completed_batches": 0,
        "completed_articles": 0,
        "completed_commits": 0,
        "no_external_delta_batches": 0,
        "last_result": "NOT_STARTED",
        "last_external_delta": "NONE",
    }
    prepared["activation"] = {
        "ref": None,
        "activated_at": None,
    }
    prepared["next_action"] = {
        "kind": "ACTIVATE_AND_RUN_FIRST_SLICE",
        "requires_activation": True,
        "instruction": "Activate the bounded first slice after a clean Git baseline.",
    }
    return prepared


class RepositoryActiveGoalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = trust_records.load_schema(check_active_goal.SCHEMA_PATH)
        cls.live_payload = trust_records.load_record(check_active_goal.GOAL_PATH)
        cls.prepared = _prepared_fixture(cls.live_payload)
        cls.lock, lock_errors = check_active_goal.load_lock()
        if lock_errors:
            raise AssertionError(lock_errors)

    def test_repository_contract_is_valid_in_its_current_state(self) -> None:
        self.assertEqual(
            [],
            check_active_goal.validate_payload(self.live_payload, self.schema),
        )
        self.assertEqual("IOT-T045", self.live_payload["goal_id"])
        self.assertFalse(
            any(self.live_payload["external_action_authority"].values())
        )
        self.assertIsNotNone(self.lock)
        self.assertEqual(
            [],
            check_active_goal.validate_lock(self.live_payload, self.lock),
        )
        _, errors = check_active_goal.load_and_validate()
        self.assertEqual([], errors)

    def test_agent_entrypoint_keeps_the_stable_safety_rules(self) -> None:
        text = (check_active_goal.ROOT / "AGENTS.md").read_text(encoding="utf-8")
        required_fragments = (
            "ops/active-goal.yml",
            "tools/check_active_goal.py",
            "不得自行从 ROADMAP",
            "`STRUCTURAL`",
            "`HUMAN_APPROVED`",
            "连续 3 个 agent 批次没有 external delta",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_activation_simulation_requires_one_frozen_first_slice(self) -> None:
        active = copy.deepcopy(self.prepared)
        active["status"] = "ACTIVE"
        active["activated_by"] = "dedicated-agent-user-request"
        active["activation"] = {
            "ref": "a" * 40,
            "activated_at": "2026-07-12T10:00:00+08:00",
        }
        active["selection"]["selected_articles"] = [
            "docs/network/papers/iot-app-protocols.md"
        ]
        active["selection"]["rationale"] = "canonical path with no current source audit"
        active["next_action"]["kind"] = "RUN_FIRST_SLICE"
        active["next_action"]["requires_activation"] = False
        active["next_action"]["instruction"] = "Run the frozen one-article pilot."
        self.assertEqual(
            [],
            check_active_goal.validate_payload(active, self.schema),
        )
        self.assertEqual(
            check_active_goal.immutable_sha256(self.prepared),
            check_active_goal.immutable_sha256(active),
        )

        active["selection"]["selected_articles"] = []
        errors = check_active_goal.validate_payload(active, self.schema)
        self.assertIn("SEMANTIC:selection:active-requires-article", errors)

    def test_prepared_contract_cannot_pre_authorize_external_actions(self) -> None:
        changed = copy.deepcopy(self.prepared)
        changed["external_action_authority"]["push"] = True
        errors = check_active_goal.validate_payload(changed, self.schema)
        self.assertIn(
            "SEMANTIC:external_action_authority:prepared-must-be-false",
            errors,
        )

    def test_active_contract_pauses_after_three_no_delta_batches(self) -> None:
        active = copy.deepcopy(self.prepared)
        active["status"] = "ACTIVE"
        active["activated_by"] = "dedicated-agent-user-request"
        active["activation"] = {
            "ref": "b" * 40,
            "activated_at": "2026-07-12T10:00:00+08:00",
        }
        active["selection"]["selected_articles"] = [
            "docs/network/papers/iot-app-protocols.md"
        ]
        active["selection"]["rationale"] = "canonical path with no current source audit"
        active["next_action"]["kind"] = "RUN_FIRST_SLICE"
        active["next_action"]["requires_activation"] = False
        active["next_action"]["instruction"] = "Run the frozen one-article pilot."
        active["progress"]["no_external_delta_batches"] = 3
        errors = check_active_goal.validate_payload(active, self.schema)
        self.assertIn(
            "SEMANTIC:status:active-must-pause-after-three-no-delta-batches",
            errors,
        )

    def test_worker_cannot_expand_immutable_contract_without_new_lock(self) -> None:
        changed = copy.deepcopy(self.prepared)
        changed["budget"]["max_articles"] = 6
        changed["scope"]["max_articles"] = 6
        self.assertEqual(
            [],
            check_active_goal.validate_payload(changed, self.schema),
        )
        self.assertIn(
            "GOAL_LOCK_IMMUTABLE_CONTRACT_MISMATCH",
            check_active_goal.validate_lock(changed, self.lock),
        )

    def test_terminal_states_require_real_progress_and_successor(self) -> None:
        complete = copy.deepcopy(self.prepared)
        complete["status"] = "COMPLETE"
        complete["next_action"]["kind"] = "NONE"
        complete["next_action"]["requires_activation"] = False
        errors = check_active_goal.validate_payload(complete, self.schema)
        self.assertIn("SEMANTIC:progress:complete-requires-finished-slice", errors)

        superseded = copy.deepcopy(self.prepared)
        superseded["status"] = "SUPERSEDED"
        superseded["next_action"]["kind"] = "NONE"
        superseded["next_action"]["requires_activation"] = False
        errors = check_active_goal.validate_payload(superseded, self.schema)
        self.assertIn(
            "SEMANTIC:superseded_by:terminal-successor-required",
            errors,
        )

    def test_closing_state_allows_final_gate_after_budget_is_consumed(self) -> None:
        closing = copy.deepcopy(self.prepared)
        closing["status"] = "CLOSING"
        closing["activated_by"] = "dedicated-agent-user-request"
        closing["activation"] = {
            "ref": "d" * 40,
            "activated_at": "2026-07-12T10:00:00+08:00",
        }
        closing["selection"]["selected_articles"] = [
            "docs/network/papers/iot-app-protocols.md",
            "docs/network/papers/mqtt5-deep-dive.md",
        ]
        closing["selection"]["rationale"] = "two canonical paths in the bounded pilot"
        closing["progress"]["completed_batches"] = 2
        closing["progress"]["completed_articles"] = 2
        closing["progress"]["no_external_delta_batches"] = 2
        closing["next_action"] = {
            "kind": "RUN_GOAL_CLOSE_CHECKS",
            "requires_activation": False,
            "instruction": "Run full tests and strict build before COMPLETE.",
        }
        self.assertEqual(
            [],
            check_active_goal.validate_payload(closing, self.schema),
        )

        closing["status"] = "ACTIVE"
        errors = check_active_goal.validate_payload(closing, self.schema)
        self.assertIn(
            "SEMANTIC:status:active-cannot-have-exhausted-budget",
            errors,
        )

    def test_bounded_goal_can_run_continuously_through_complete(self) -> None:
        state = copy.deepcopy(self.prepared)
        expected_hash = check_active_goal.immutable_sha256(state)

        state["status"] = "ACTIVE"
        state["activated_by"] = "dedicated-agent-user-request"
        state["activation"] = {
            "ref": "e" * 40,
            "activated_at": "2026-07-12T10:00:00+08:00",
        }
        state["selection"]["selected_articles"] = [
            "docs/network/papers/iot-app-protocols.md"
        ]
        state["selection"]["rationale"] = "first bounded canonical pilot"
        state["next_action"] = {
            "kind": "RUN_FIRST_SLICE",
            "requires_activation": False,
            "instruction": "Run the first article without waiting for confirmation.",
        }
        self.assertEqual([], check_active_goal.validate_payload(state, self.schema))

        state["progress"]["completed_batches"] = 1
        state["progress"]["completed_articles"] = 1
        state["progress"]["no_external_delta_batches"] = 1
        state["selection"]["selected_articles"].extend(
            [
                "docs/network/papers/mqtt5-deep-dive.md",
                "docs/network/papers/coap-lwm2m-constrained.md",
                "docs/network/papers/quic-iot-applicability.md",
                "docs/network/papers/tsn-detnet-industrial.md",
            ]
        )
        state["selection"]["rationale"] = (
            "first pilot passed; four additional canonical paths remain within budget"
        )
        state["next_action"] = {
            "kind": "RUN_NEXT_SLICE",
            "requires_activation": False,
            "instruction": "Run the remaining four articles without reconfirmation.",
        }
        self.assertEqual([], check_active_goal.validate_payload(state, self.schema))

        state["status"] = "CLOSING"
        state["progress"]["completed_batches"] = 2
        state["progress"]["completed_articles"] = 5
        state["progress"]["no_external_delta_batches"] = 2
        state["next_action"] = {
            "kind": "RUN_GOAL_CLOSE_CHECKS",
            "requires_activation": False,
            "instruction": "Run every GOAL_CLOSE check.",
        }
        self.assertEqual([], check_active_goal.validate_payload(state, self.schema))

        state["status"] = "COMPLETE"
        state["next_action"] = {
            "kind": "NONE",
            "requires_activation": False,
            "instruction": "The bounded goal is complete.",
        }
        self.assertEqual([], check_active_goal.validate_payload(state, self.schema))
        self.assertEqual(expected_hash, check_active_goal.immutable_sha256(state))

    def test_mutation_paths_reject_traversal_and_prefix_overlap(self) -> None:
        traversal = copy.deepcopy(self.prepared)
        traversal["allowed_mutations"].append("../outside")
        self.assertIn(
            "SEMANTIC:allowed_mutations:unsafe-repository-path",
            check_active_goal.validate_payload(traversal, self.schema),
        )

        overlap = copy.deepcopy(self.prepared)
        overlap["forbidden_mutations"].append("data/source-audits/private")
        self.assertIn(
            "SEMANTIC:mutation-paths:allowed-forbidden-overlap",
            check_active_goal.validate_payload(overlap, self.schema),
        )

    def test_first_slice_runtime_binds_record_selection_and_authority(self) -> None:
        active = copy.deepcopy(self.prepared)
        active["status"] = "ACTIVE"
        active["activated_by"] = "dedicated-agent-user-request"
        active["activation"] = {
            "ref": "c" * 40,
            "activated_at": "2026-07-12T10:00:00+08:00",
        }
        selected = "docs/network/papers/iot-app-protocols.md"
        active["selection"]["selected_articles"] = [selected]
        active["selection"]["rationale"] = "canonical path with no current source audit"
        active["progress"]["completed_batches"] = 1
        active["progress"]["completed_articles"] = 1
        active["progress"]["no_external_delta_batches"] = 1
        active["next_action"] = {
            "kind": "RUN_NEXT_SLICE",
            "requires_activation": False,
            "instruction": "Expand only within the frozen goal budget.",
        }
        self.assertEqual(
            [],
            check_active_goal.validate_payload(active, self.schema),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = root / selected
            content.parent.mkdir(parents=True)
            content.write_text("# IoT application protocols\n", encoding="utf-8")
            audit = root / "data/source-audits/network/record.yml"
            audit.parent.mkdir(parents=True)
            audit.write_text(
                "content_path: docs/network/papers/iot-app-protocols.md\n"
                "audit_kind: STRUCTURAL\n"
                "auditor_type: AGENT\n"
                "auditor_role: STRUCTURAL_AUDITOR\n"
                "status_transition:\n"
                "  from: UNVERIFIED\n"
                "  to: UNVERIFIED\n",
                encoding="utf-8",
            )
            authority = root / "data/trust-authorities.yml"
            authority.write_text(
                "actors:\n"
                "  - actor_id: agent-shadow-auditor\n"
                "    actor_type: AGENT\n"
                "    allowed_roles:\n"
                "      - STRUCTURAL_AUDITOR\n"
                "entries: []\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                check_active_goal.validate_repository_state(active, root=root),
            )

            authority.write_text(
                authority.read_text(encoding="utf-8").replace(
                    "STRUCTURAL_AUDITOR",
                    "FACT_AUDITOR",
                ),
                encoding="utf-8",
            )
            self.assertIn(
                "REPOSITORY:trust-authorities:structural-agent-only",
                check_active_goal.validate_repository_state(active, root=root),
            )

    def test_activation_ref_and_real_changed_paths_are_enforced(self) -> None:
        active = copy.deepcopy(self.prepared)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init", "-q", str(root)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Goal Test"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "config",
                    "user.email",
                    "goal-test@example.invalid",
                ],
                check=True,
            )
            readme = root / "README.md"
            readme.write_text("baseline\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "README.md"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-qm", "baseline"],
                check=True,
            )
            activation_ref = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            active["activation"]["ref"] = activation_ref

            allowed = root / "data/source-audits/one.yml"
            allowed.parent.mkdir(parents=True)
            allowed.write_text("audit_kind: STRUCTURAL\n", encoding="utf-8")
            self.assertEqual(
                [],
                check_active_goal.validate_git_scope(active, root=root),
            )

            forbidden = root / "tools/escape.py"
            forbidden.parent.mkdir(parents=True)
            forbidden.write_text("pass\n", encoding="utf-8")
            self.assertIn(
                "GIT:worktree:change-outside-allowed-mutations",
                check_active_goal.validate_git_scope(active, root=root),
            )

            active["activation"]["ref"] = "f" * 40
            self.assertEqual(
                ["GIT:activation-ref:not-a-local-commit"],
                check_active_goal.validate_git_scope(active, root=root),
            )

    def test_duplicate_yaml_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "goal.yml"
            path.write_text(
                "schema_version: '1.0'\n"
                "goal_id: IOT-T045\n"
                "goal_id: IOT-T046\n",
                encoding="utf-8",
            )
            _, errors = check_active_goal.load_and_validate(
                path,
                check_active_goal.SCHEMA_PATH,
            )
        self.assertEqual(["GOAL_RECORD_INVALID_YAML"], errors)
