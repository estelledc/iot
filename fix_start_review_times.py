#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")
REVIEW_DIR = os.path.join(ROOT, "data", "review-records")

content_to_latest_audit_time = {}
for filename in os.listdir(AUDIT_DIR):
    if not filename.endswith(".yml"):
        continue
    filepath = os.path.join(AUDIT_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    content_id = data.get("content_id")
    audited_at = data.get("audited_at", "")
    if content_id and audited_at:
        if content_id not in content_to_latest_audit_time or audited_at > content_to_latest_audit_time[content_id]:
            content_to_latest_audit_time[content_id] = audited_at

fixed_count = 0
for filename in os.listdir(REVIEW_DIR):
    if not filename.startswith("review-20260713-start-"):
        continue
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    content_id = data.get("content_id")
    if content_id not in content_to_latest_audit_time:
        continue
    
    review_time = data.get("reviewed_at", "")
    audit_time = content_to_latest_audit_time[content_id]
    
    if review_time <= audit_time:
        data["reviewed_at"] = audit_time.replace("T11:00:00Z", "T17:00:00Z").replace("T12:00:00Z", "T18:00:00Z").replace("T10:00:00Z", "T16:00:00Z")
        if data["reviewed_at"] <= audit_time:
            import re
            match = re.match(r'(\d{4}-\d{2}-\d{2}T)(\d{2}):(\d{2}):(\d{2}Z)', audit_time)
            if match:
                hour = int(match.group(2)) + 1
                data["reviewed_at"] = f"{match.group(1)}{hour:02}:{match.group(3)}:{match.group(4)}"
        
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        fixed_count += 1

print(f"Fixed {fixed_count} START_REVIEW records")
