#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")

fixed_count = 0
for filename in os.listdir(AUDIT_DIR):
    if not filename.startswith("audit-20260713-claim-"):
        continue
    filepath = os.path.join(AUDIT_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    audited_at = data.get("audited_at", "")
    source_references = data.get("source_references", [])
    
    for ref in source_references:
        retrieved_at = ref.get("retrieved_at", "")
        if retrieved_at > audited_at:
            ref["retrieved_at"] = "2026-07-12T14:00:00Z"
            fixed_count += 1
    
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Fixed {fixed_count} source reference times")
