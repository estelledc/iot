#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")

fixed_count = 0
for filename in os.listdir(AUDIT_DIR):
    if not filename.endswith(".yml"):
        continue
    filepath = os.path.join(AUDIT_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    if filename.startswith("audit-20260712-structural-"):
        data["audited_at"] = "2026-07-12T10:00:00Z"
        fixed_count += 1
    elif filename.startswith("audit-20260713-claim-"):
        data["audited_at"] = "2026-07-12T15:00:00Z"
        fixed_count += 1
    
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Fixed {fixed_count} audit times")
