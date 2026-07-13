#!/usr/bin/env python3

import os
import yaml
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
REVIEW_DIR = os.path.join(ROOT, "data", "review-records")

fixed_count = 0
for filename in os.listdir(REVIEW_DIR):
    if not filename.endswith(".yml"):
        continue
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    reviewed_at = data.get("reviewed_at", "")
    if not reviewed_at:
        continue
    
    match = re.match(r'(\d{4}-\d{2}-\d{2}T)(\d{2}):(\d{2}):(\d{2}Z)', reviewed_at)
    if match:
        hour = int(match.group(2))
        if hour >= 24:
            data["reviewed_at"] = f"{match.group(1)}23:{match.group(3)}:{match.group(4)}"
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            fixed_count += 1

print(f"Fixed {fixed_count} invalid time formats")
