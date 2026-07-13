#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")
REVIEW_DIR = os.path.join(ROOT, "data", "review-records")

existing_audits = set()
for filename in os.listdir(AUDIT_DIR):
    if filename.endswith(".yml"):
        existing_audits.add(filename.replace(".yml", ""))

fixed_count = 0
for filename in os.listdir(REVIEW_DIR):
    if not filename.startswith("review-20260713-start-"):
        continue
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    content_id = data.get("content_id")
    if not content_id:
        continue
    
    expected_audits = []
    structural_id = f"audit-20260712-structural-{content_id}"
    claim_id = f"audit-20260713-claim-{content_id}"
    if structural_id in existing_audits:
        expected_audits.append(structural_id)
    if claim_id in existing_audits:
        expected_audits.append(claim_id)
    
    current_audits = data.get("linked_audit_ids", [])
    
    if expected_audits != current_audits:
        data["linked_audit_ids"] = expected_audits
        
        expected_auditors = []
        if structural_id in expected_audits:
            expected_auditors.append("agent-structural-auditor")
        if claim_id in expected_audits:
            expected_auditors.append("human-fact-auditor")
        
        independence = data.get("independence", {})
        independence["linked_auditor_ids"] = expected_auditors
        data["independence"] = independence
        
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        fixed_count += 1

print(f"Fixed {fixed_count} START_REVIEW records")
