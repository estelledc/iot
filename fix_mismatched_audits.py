#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")

mismatched = []
for filename in os.listdir(AUDIT_DIR):
    if not filename.startswith("audit-20260712-structural-"):
        continue
    expected_content_id = filename.replace("audit-20260712-structural-", "").replace(".yml", "")
    filepath = os.path.join(AUDIT_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    actual_content_id = data.get("content_id", "")
    if actual_content_id != expected_content_id:
        mismatched.append((filename, expected_content_id, actual_content_id))

print(f"Found {len(mismatched)} mismatched audit files")
for filename, expected, actual in mismatched:
    print(f"  {filename}: expected={expected}, actual={actual}")

print(f"\nDeleting {len(mismatched)} mismatched files...")
for filename, expected, actual in mismatched:
    os.remove(os.path.join(AUDIT_DIR, filename))

print(f"Deleted {len(mismatched)} files")
