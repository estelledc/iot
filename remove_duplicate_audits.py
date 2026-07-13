#!/usr/bin/env python3

import os

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")

content_to_files = {}
for filename in os.listdir(AUDIT_DIR):
    if not filename.startswith("audit-20260712-structural-"):
        continue
    content_id = filename.replace("audit-20260712-structural-", "").replace(".yml", "")
    if content_id not in content_to_files:
        content_to_files[content_id] = []
    content_to_files[content_id].append(filename)

duplicates = {k: v for k, v in content_to_files.items() if len(v) > 1}
print(f"Found {len(duplicates)} content_ids with duplicate audits")

deleted_count = 0
for content_id, files in duplicates.items():
    files.sort()
    keep = files[-1]
    for f in files:
        if f != keep:
            os.remove(os.path.join(AUDIT_DIR, f))
            deleted_count += 1
            print(f"Deleted: {f}")

print(f"\nTotal deleted: {deleted_count}")
