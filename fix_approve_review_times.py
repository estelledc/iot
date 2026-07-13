#!/usr/bin/env python3

import os
import yaml
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
REVIEW_DIR = os.path.join(ROOT, "data", "review-records")

content_to_start_time = {}
for filename in os.listdir(REVIEW_DIR):
    if not filename.startswith("review-20260713-start-"):
        continue
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    content_id = data.get("content_id")
    reviewed_at = data.get("reviewed_at", "")
    if content_id and reviewed_at:
        content_to_start_time[content_id] = reviewed_at

fixed_count = 0
for filename in os.listdir(REVIEW_DIR):
    if not filename.startswith("review-20260713-approve-"):
        continue
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    content_id = data.get("content_id")
    if content_id not in content_to_start_time:
        continue
    
    approve_time = data.get("reviewed_at", "")
    start_time = content_to_start_time[content_id]
    
    if approve_time <= start_time:
        match = re.match(r'(\d{4}-\d{2}-\d{2}T)(\d{2}):(\d{2}):(\d{2}Z)', start_time)
        if match:
            hour = int(match.group(2)) + 1
            data["reviewed_at"] = f"{match.group(1)}{hour:02}:{match.group(3)}:{match.group(4)}"
        
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        fixed_count += 1

print(f"Fixed {fixed_count} APPROVE records")
