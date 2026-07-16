#!/usr/bin/env python3
"""Enforce immutable Actions references and least-privilege Pages jobs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ACTION_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
PIP_INSTALL_LINE = re.compile(
    r"^(?:python(?:3(?:\.\d+)?)?\s+-m\s+pip|pip(?:3(?:\.\d+)?)?)\s+install(?:\s|$)"
)
REQUIRED_TRUST_VALIDATION_COMMANDS = (
    "python tools/validate_source_audits.py --all",
    "python tools/validate_review_records.py --all",
    "python tools/validate_trust_state.py --all --baseline-mode",
)
REQUIRED_LOCK_INSTALL_COMMAND = (
    "python -m pip install --require-hashes -r requirements.lock"
)
REQUIRED_PIP_CHECK_COMMAND = "python -m pip check"
REQUIRED_ACTIVE_GOAL_COMMAND = "python tools/check_active_goal.py"
ACTIVE_GOAL_SUCCESSOR_COMMANDS = (
    "python tools/content_inventory.py --check",
    "python tools/validate_source_audits.py --all",
    "python -m unittest discover -s tests -v",
)


def load_workflow(path: Path) -> dict:
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: workflow root must be a mapping")
    return data


def validate_action_refs(path: Path, workflow: dict) -> list[str]:
    errors: list[str] = []
    jobs = workflow.get("jobs", {})
    if not isinstance(jobs, dict):
        return [f"{path}: jobs must be a mapping"]
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            errors.append(f"{path}: job {job_name} must be a mapping")
            continue
        if "timeout-minutes" not in job:
            errors.append(f"{path}: job {job_name} has no timeout-minutes")
        for step in job.get("steps", []):
            if not isinstance(step, dict) or "uses" not in step:
                continue
            uses = str(step["uses"])
            if uses.startswith("./"):
                continue
            if not ACTION_REF.fullmatch(uses):
                errors.append(f"{path}: mutable or invalid action ref: {uses}")
    return errors


def validate_trust_validation_commands(
    path: Path,
    workflow: dict,
    *,
    job_name: str,
) -> list[str]:
    jobs = workflow.get("jobs", {})
    job = jobs.get(job_name, {}) if isinstance(jobs, dict) else {}
    if not isinstance(job, dict):
        return [f"{path}: job {job_name} must be a mapping"]

    errors: list[str] = []
    if "defaults" in workflow:
        errors.append(
            f"{path}: workflow defaults must not redirect trust validation"
        )
    if "env" in workflow:
        errors.append(
            f"{path}: workflow env must not override trust validation"
        )
    if "if" in job:
        errors.append(
            f"{path}: job {job_name} must not conditionally skip trust validation"
        )
    if str(job.get("continue-on-error", "false")).lower() not in {"false", ""}:
        errors.append(
            f"{path}: job {job_name} must not continue on trust validation errors"
        )
    if "defaults" in job:
        errors.append(
            f"{path}: job {job_name} defaults must not redirect trust validation"
        )
    if "env" in job:
        errors.append(
            f"{path}: job {job_name} env must not override trust validation"
        )
    steps = job.get("steps", [])
    if not isinstance(steps, list):
        return [*errors, f"{path}: job {job_name} steps must be a sequence"]

    positions: list[int] = []
    for command in REQUIRED_TRUST_VALIDATION_COMMANDS:
        occurrences = [
            (index, step)
            for index, step in enumerate(steps)
            if isinstance(step, dict)
            and isinstance(step.get("run"), str)
            and step["run"].strip() == command
        ]
        if not occurrences:
            errors.append(
                f"{path}: job {job_name} is missing required command: {command}"
            )
            continue
        if len(occurrences) > 1:
            errors.append(
                f"{path}: job {job_name} must run required command exactly once: "
                f"{command}"
            )
        position, step = occurrences[0]
        positions.append(position)
        if "if" in step:
            errors.append(
                f"{path}: required command step must not have an if condition: "
                f"{command}"
            )
        if str(step.get("continue-on-error", "false")).lower() not in {
            "false",
            "",
        }:
            errors.append(
                f"{path}: required command step must fail closed: {command}"
            )
        if "shell" in step:
            errors.append(
                f"{path}: required command step must use the default shell: {command}"
            )
        if "working-directory" in step:
            errors.append(
                f"{path}: required command step must run at repository root: {command}"
            )
        if "env" in step:
            errors.append(
                f"{path}: required command step must not override its environment: "
                f"{command}"
            )

    if len(positions) == len(REQUIRED_TRUST_VALIDATION_COMMANDS) and positions != sorted(
        positions
    ):
        errors.append(
            f"{path}: job {job_name} trust validation commands must run in order: "
            + " -> ".join(REQUIRED_TRUST_VALIDATION_COMMANDS)
        )
    return errors


def validate_full_history_checkout(
    path: Path,
    workflow: dict,
    *,
    job_name: str,
) -> list[str]:
    jobs = workflow.get("jobs", {})
    job = jobs.get(job_name, {}) if isinstance(jobs, dict) else {}
    steps = job.get("steps", []) if isinstance(job, dict) else []
    checkout_steps = [
        step
        for step in steps
        if isinstance(step, dict)
        and str(step.get("uses", "")).startswith("actions/checkout@")
    ]
    if len(checkout_steps) != 1:
        return [f"{path}: job {job_name} must contain exactly one checkout step"]
    checkout_with = checkout_steps[0].get("with", {})
    if (
        not isinstance(checkout_with, dict)
        or str(checkout_with.get("fetch-depth")) != "0"
    ):
        return [
            f"{path}: job {job_name} checkout must set fetch-depth: 0 "
            "for immutable ledger ancestry validation"
        ]
    return []


def validate_python_bootstrap(
    path: Path,
    workflow: dict,
    *,
    job_name: str,
) -> list[str]:
    """Require one repository-pinned Python runtime and a healthy lock install."""

    jobs = workflow.get("jobs", {})
    job = jobs.get(job_name, {}) if isinstance(jobs, dict) else {}
    steps = job.get("steps", []) if isinstance(job, dict) else []
    if not isinstance(steps, list):
        return [f"{path}: job {job_name} steps must be a sequence"]

    errors: list[str] = []
    setup_steps = [
        (index, step)
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and str(step.get("uses", "")).startswith("actions/setup-python@")
    ]
    if len(setup_steps) != 1:
        errors.append(
            f"{path}: job {job_name} must contain exactly one setup-python step"
        )
        setup_position = None
    else:
        setup_position, setup = setup_steps[0]
        setup_with = setup.get("with", {})
        if (
            not isinstance(setup_with, dict)
            or setup_with.get("python-version-file") != ".python-version"
            or "python-version" in setup_with
        ):
            errors.append(
                f"{path}: job {job_name} setup-python must set "
                "python-version-file: .python-version and must not set python-version"
            )
        if "if" in setup:
            errors.append(
                f"{path}: job {job_name} setup-python step must not have an if condition"
            )
        if str(setup.get("continue-on-error", "false")).lower() not in {
            "false",
            "",
        }:
            errors.append(
                f"{path}: job {job_name} setup-python step must fail closed"
            )
        if "env" in setup:
            errors.append(
                f"{path}: job {job_name} setup-python step must not override its environment"
            )

    required_commands = (
        ("hash-locked install", REQUIRED_LOCK_INSTALL_COMMAND),
        ("pip check", REQUIRED_PIP_CHECK_COMMAND),
    )
    command_positions: dict[str, int] = {}
    for label, command in required_commands:
        occurrences = [
            (index, step)
            for index, step in enumerate(steps)
            if isinstance(step, dict)
            and isinstance(step.get("run"), str)
            and step["run"].strip() == command
        ]
        if not occurrences:
            errors.append(
                f"{path}: job {job_name} is missing required command: {command}"
            )
            continue
        if len(occurrences) > 1:
            errors.append(
                f"{path}: job {job_name} must run required command exactly once: "
                f"{command}"
            )
        position, step = occurrences[0]
        command_positions[label] = position
        if "if" in step:
            errors.append(
                f"{path}: job {job_name} {label} step must not have an if condition"
            )
        if str(step.get("continue-on-error", "false")).lower() not in {
            "false",
            "",
        }:
            errors.append(f"{path}: job {job_name} {label} step must fail closed")
        if "shell" in step:
            errors.append(
                f"{path}: job {job_name} {label} step must use the default shell"
            )
        if "working-directory" in step:
            errors.append(
                f"{path}: job {job_name} {label} step must run at repository root"
            )
        if "env" in step:
            errors.append(
                f"{path}: job {job_name} {label} step must not override its environment"
            )

    for step in steps:
        run = step.get("run") if isinstance(step, dict) else None
        if not isinstance(run, str):
            continue
        for line in run.splitlines():
            command = line.strip()
            if PIP_INSTALL_LINE.match(command) and command != REQUIRED_LOCK_INSTALL_COMMAND:
                errors.append(
                    f"{path}: job {job_name} unlocked or additional pip install "
                    f"command is forbidden: {command}"
                )

    install_position = command_positions.get("hash-locked install")
    check_position = command_positions.get("pip check")
    if (
        setup_position is not None
        and install_position is not None
        and check_position is not None
        and not (setup_position < install_position < check_position)
    ):
        errors.append(
            f"{path}: job {job_name} Python bootstrap order must be "
            "setup-python -> hash-locked install -> pip check"
        )

    trust_positions = [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and isinstance(step.get("run"), str)
        and step["run"].strip() in REQUIRED_TRUST_VALIDATION_COMMANDS
    ]
    if (
        check_position is not None
        and trust_positions
        and check_position >= min(trust_positions)
    ):
        errors.append(
            f"{path}: job {job_name} pip check must run before trust validation"
        )
    return errors


def validate_active_goal_check(
    path: Path,
    workflow: dict,
    *,
    job_name: str,
) -> list[str]:
    """Require one unwrapped active-goal gate at the bootstrap boundary."""

    jobs = workflow.get("jobs", {})
    job = jobs.get(job_name, {}) if isinstance(jobs, dict) else {}
    if not isinstance(job, dict):
        return [f"{path}: job {job_name} must be a mapping"]
    steps = job.get("steps", [])
    if not isinstance(steps, list):
        return [f"{path}: job {job_name} steps must be a sequence"]

    exact_occurrences = [
        (index, step)
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and isinstance(step.get("run"), str)
        and step["run"].strip() == REQUIRED_ACTIVE_GOAL_COMMAND
    ]
    embedded_occurrences = [
        (index, step)
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and isinstance(step.get("run"), str)
        for line in step["run"].splitlines()
        if line.strip() == REQUIRED_ACTIVE_GOAL_COMMAND
    ]

    errors: list[str] = []
    if not exact_occurrences:
        errors.append(
            f"{path}: job {job_name} is missing required command: "
            f"{REQUIRED_ACTIVE_GOAL_COMMAND}"
        )
        return errors
    if len(exact_occurrences) != 1 or len(embedded_occurrences) != 1:
        errors.append(
            f"{path}: job {job_name} must run required command exactly once: "
            f"{REQUIRED_ACTIVE_GOAL_COMMAND}"
        )

    active_position, active_step = exact_occurrences[0]
    if "if" in active_step:
        errors.append(
            f"{path}: job {job_name} active-goal check step must not have "
            "an if condition"
        )
    if "continue-on-error" in active_step:
        errors.append(
            f"{path}: job {job_name} active-goal check step must fail closed"
        )
    if "shell" in active_step:
        errors.append(
            f"{path}: job {job_name} active-goal check step must use "
            "the default shell"
        )
    if "working-directory" in active_step:
        errors.append(
            f"{path}: job {job_name} active-goal check step must run "
            "at repository root"
        )
    if "env" in active_step:
        errors.append(
            f"{path}: job {job_name} active-goal check step must not override "
            "its environment"
        )

    setup_positions = [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and str(step.get("uses", "")).startswith("actions/setup-python@")
    ]
    prerequisite_positions = [
        index
        for command in (REQUIRED_LOCK_INSTALL_COMMAND, REQUIRED_PIP_CHECK_COMMAND)
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and isinstance(step.get("run"), str)
        and step["run"].strip() == command
    ]
    if (
        len(setup_positions) == 1
        and len(prerequisite_positions) == 2
        and not (
            setup_positions[0]
            < prerequisite_positions[0]
            < prerequisite_positions[1]
            < active_position
        )
    ):
        errors.append(
            f"{path}: job {job_name} active-goal check must run after "
            "setup-python, hash-locked install, and pip check"
        )

    successor_positions = [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and isinstance(step.get("run"), str)
        and any(
            line.strip() in ACTIVE_GOAL_SUCCESSOR_COMMANDS
            or line.strip().startswith("mkdocs build --strict")
            for line in step["run"].splitlines()
        )
    ]
    if successor_positions and active_position >= min(successor_positions):
        errors.append(
            f"{path}: job {job_name} active-goal check must run before "
            "inventory, trust, tests, and build"
        )
    return errors


def validate_ci(path: Path, workflow: dict) -> list[str]:
    errors = validate_action_refs(path, workflow)
    errors.extend(validate_python_bootstrap(path, workflow, job_name="quality"))
    errors.extend(validate_active_goal_check(path, workflow, job_name="quality"))
    errors.extend(
        validate_trust_validation_commands(path, workflow, job_name="quality")
    )
    errors.extend(validate_full_history_checkout(path, workflow, job_name="quality"))
    if workflow.get("permissions") != {"contents": "read"}:
        errors.append(f"{path}: global permissions must be contents: read")
    triggers = workflow.get("on", {})
    if not isinstance(triggers, dict) or "pull_request" not in triggers:
        errors.append(f"{path}: pull_request trigger is required")
    return errors


def validate_deploy(path: Path, workflow: dict) -> list[str]:
    errors = validate_action_refs(path, workflow)
    errors.extend(validate_python_bootstrap(path, workflow, job_name="build"))
    errors.extend(validate_active_goal_check(path, workflow, job_name="build"))
    errors.extend(validate_trust_validation_commands(path, workflow, job_name="build"))
    errors.extend(validate_full_history_checkout(path, workflow, job_name="build"))
    if workflow.get("permissions") != {"contents": "read"}:
        errors.append(f"{path}: global permissions must be contents: read")

    triggers = workflow.get("on", {})
    push = triggers.get("push", {}) if isinstance(triggers, dict) else {}
    if not isinstance(push, dict) or push.get("branches") != ["main"]:
        errors.append(f"{path}: deployment push trigger must target only main")

    jobs = workflow.get("jobs", {})
    build = jobs.get("build", {}) if isinstance(jobs, dict) else {}
    deploy = jobs.get("deploy", {}) if isinstance(jobs, dict) else {}
    if build.get("permissions") != {"contents": "read"}:
        errors.append(f"{path}: build job must have only contents: read")
    if deploy.get("permissions") != {"pages": "write", "id-token": "write"}:
        errors.append(f"{path}: deploy job must have only pages/id-token write")
    if deploy.get("needs") != "build":
        errors.append(f"{path}: deploy job must depend on build")
    if deploy.get("if") != "github.ref == 'refs/heads/main'":
        errors.append(f"{path}: deploy job must reject non-main workflow_dispatch refs")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", type=Path, default=ROOT / ".github/workflows/ci.yml")
    parser.add_argument("--deploy", type=Path, default=ROOT / ".github/workflows/deploy.yml")
    args = parser.parse_args()

    errors: list[str] = []
    try:
        errors.extend(validate_ci(args.ci, load_workflow(args.ci)))
        errors.extend(validate_deploy(args.deploy, load_workflow(args.deploy)))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"WORKFLOW_POLICY_ERROR: {error}")
        return 1
    print(
        "WORKFLOW_POLICY_OK: immutable action refs, repository Python runtime, "
        "dependency health, active-goal gating, and least-privilege jobs verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
