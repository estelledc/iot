#!/usr/bin/env python3
"""Enforce immutable Actions references and least-privilege Pages jobs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ACTION_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")


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


def validate_ci(path: Path, workflow: dict) -> list[str]:
    errors = validate_action_refs(path, workflow)
    if workflow.get("permissions") != {"contents": "read"}:
        errors.append(f"{path}: global permissions must be contents: read")
    triggers = workflow.get("on", {})
    if not isinstance(triggers, dict) or "pull_request" not in triggers:
        errors.append(f"{path}: pull_request trigger is required")
    return errors


def validate_deploy(path: Path, workflow: dict) -> list[str]:
    errors = validate_action_refs(path, workflow)
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
    print("WORKFLOW_POLICY_OK: immutable action refs and least-privilege jobs verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
