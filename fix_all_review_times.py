#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
REVIEW_DIR = os.path.join(ROOT, "data", "review-records")

fixed_count = 0
for filename in os.listdir(REVIEW_DIR):
    if not filename.endswith(".yml"):
        continue
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    if filename.startswith("review-20260713-start-"):
        data["reviewed_at"] = "2026-07-12T17:00:00Z"
        fixed_count += 1
    elif filename.startswith("review-20260713-approve-"):
        data["reviewed_at"] = "2026-07-12T18:00:00Z"
        fixed_count += 1
    
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Fixed {fixed_count} review times")
