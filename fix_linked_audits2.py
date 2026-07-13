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
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    linked_audit_ids = data.get("linked_audit_ids", [])
    valid_linked_ids = []
    
    for audit_id in linked_audit_ids:
        if audit_id in existing_audits:
            valid_linked_ids.append(audit_id)
    
    if valid_linked_ids != linked_audit_ids:
        data["linked_audit_ids"] = valid_linked_ids
        
        content_id = data.get("content_id")
        if len(valid_linked_ids) == 0 and content_id:
            structural_id = f"audit-20260712-structural-{content_id}"
            claim_id = f"audit-20260713-claim-{content_id}"
            if structural_id in existing_audits:
                valid_linked_ids.append(structural_id)
            if claim_id in existing_audits:
                valid_linked_ids.append(claim_id)
            data["linked_audit_ids"] = valid_linked_ids
        
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        fixed_count += 1

print(f"Fixed {fixed_count} review records")
