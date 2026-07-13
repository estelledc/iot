#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")
REVIEW_DIR = os.path.join(ROOT, "data", "review-records")

content_to_auditors = {}
for filename in os.listdir(AUDIT_DIR):
    filepath = os.path.join(AUDIT_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    content_id = data.get("content_id")
    auditor_id = data.get("auditor_id")
    if content_id and auditor_id:
        if content_id not in content_to_auditors:
            content_to_auditors[content_id] = set()
        content_to_auditors[content_id].add(auditor_id)

fixed_count = 0
for filename in os.listdir(REVIEW_DIR):
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    content_id = data.get("content_id")
    if content_id in content_to_auditors:
        expected_auditors = sorted(content_to_auditors[content_id])
        independence = data.get("independence", {})
        current_auditors = sorted(independence.get("linked_auditor_ids", []))
        
        if expected_auditors != current_auditors:
            independence["linked_auditor_ids"] = expected_auditors
            data["independence"] = independence
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            fixed_count += 1

print(f"Fixed {fixed_count} review records with correct linked_auditor_ids")
