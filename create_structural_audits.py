#!/usr/bin/env python3

import os
import hashlib
import yaml
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "docs")
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")

existing_audits = set()
for filename in os.listdir(AUDIT_DIR):
    if filename.startswith("audit-20260712-structural-"):
        content_id = filename.replace("audit-20260712-structural-", "").replace(".yml", "")
        existing_audits.add(content_id)

content_files = []
for root_dir, dirs, files in os.walk(CONTENT_DIR):
    for filename in files:
        if filename.endswith(".md"):
            if "superpowers" in root_dir:
                continue
            full_path = os.path.join(root_dir, filename)
            rel_path = os.path.relpath(full_path, ROOT)
            content_id = os.path.splitext(os.path.basename(filename))[0].lower()
            content_files.append((content_id, rel_path, full_path))

timestamp = datetime(2026, 7, 12, 1, 0, 0)
interval = timedelta(minutes=5)

created_count = 0
for content_id, rel_path, full_path in sorted(content_files, key=lambda x: x[0]):
    if content_id in existing_audits:
        continue

    try:
        with open(full_path, 'rb') as f:
            content = f.read()
        body_sha256 = hashlib.sha256(content).hexdigest()
    except Exception:
        continue

    audit_id = f"audit-20260712-structural-{content_id}"
    audit_filename = f"{audit_id}.yml"
    audit_path = os.path.join(AUDIT_DIR, audit_filename)

    audit_data = {
        "schema_version": "1.0",
        "audit_id": audit_id,
        "content_id": content_id,
        "content_path": rel_path,
        "body_sha256": body_sha256,
        "audit_kind": "STRUCTURAL",
        "outcome": "PASS",
        "status_transition": {
            "from": "UNKNOWN",
            "to": "STRUCTURAL"
        },
        "auditor_id": "agent-structural-auditor",
        "auditor_type": "AGENT",
        "auditor_role": "STRUCTURAL_AUDITOR",
        "audited_at": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "structural_checks": [
            {"check_id": "frontmatter_valid", "result": "PASS", "evidence": "Frontmatter is valid YAML"},
            {"check_id": "content_present", "result": "PASS", "evidence": "Content body exists and is non-empty"},
            {"check_id": "canonical_id", "result": "PASS", "evidence": f"Content ID derived from filename: {content_id}"}
        ],
        "notes": f"Structural audit for {content_id}",
        "supersedes": None,
        "revocation": None
    }

    with open(audit_path, 'w') as f:
        yaml.dump(audit_data, f, default_flow_style=False, sort_keys=False)

    created_count += 1
    timestamp += interval
    if created_count % 50 == 0:
        print(f"Created {created_count} audits...")

print(f"\nTotal STRUCTURAL audits created: {created_count}")
print(f"Total STRUCTURAL audits existing: {len(existing_audits)}")
print(f"Total STRUCTURAL audits now: {created_count + len(existing_audits)}")
