#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")

fixed_count = 0
for filename in os.listdir(AUDIT_DIR):
    if not filename.startswith("audit-20260712-structural-"):
        continue
    
    filepath = os.path.join(AUDIT_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    if data.get("audit_kind") != "STRUCTURAL":
        continue
    
    needs_fix = False
    
    if data.get("outcome") == "PASS":
        data["outcome"] = "AUDITABLE"
        needs_fix = True
    
    transition = data.get("status_transition", {})
    if transition.get("to") == "STRUCTURAL":
        data["status_transition"] = {
            "from": "UNKNOWN",
            "to": "UNKNOWN"
        }
        needs_fix = True
    
    if data.get("claim_coverage") is not None:
        data["claim_coverage"] = None
        needs_fix = True
    
    if needs_fix:
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        fixed_count += 1

print(f"Fixed {fixed_count} STRUCTURAL audits")
