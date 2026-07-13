#!/usr/bin/env python3

import os
import hashlib
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "docs")
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")
REVIEW_DIR = os.path.join(ROOT, "data", "review-records")

def _is_delimiter(line: bytes) -> bool:
    return line.rstrip(b"\r\n") == b"---"

def get_body_bytes(raw: bytes) -> bytes:
    lines = raw.splitlines(keepends=True)
    if not lines or not _is_delimiter(lines[0]):
        return raw
    
    offset = len(lines[0])
    for line in lines[1:]:
        start = offset
        offset += len(line)
        if _is_delimiter(line):
            return raw[offset:]
    
    return raw

content_hashes = {}
for root_dir, dirs, files in os.walk(CONTENT_DIR):
    for filename in files:
        if filename.endswith(".md") and "superpowers" not in root_dir:
            full_path = os.path.join(root_dir, filename)
            content_id = os.path.splitext(filename)[0].lower()
            try:
                with open(full_path, 'rb') as f:
                    raw = f.read()
                body_bytes = get_body_bytes(raw)
                content_hashes[content_id] = hashlib.sha256(body_bytes).hexdigest()
            except Exception:
                pass

updated_audits = 0
for filename in os.listdir(AUDIT_DIR):
    filepath = os.path.join(AUDIT_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    content_id = data.get("content_id")
    if content_id in content_hashes:
        new_hash = content_hashes[content_id]
        if data.get("body_sha256") != new_hash:
            data["body_sha256"] = new_hash
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            updated_audits += 1

updated_reviews = 0
for filename in os.listdir(REVIEW_DIR):
    filepath = os.path.join(REVIEW_DIR, filename)
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    content_id = data.get("content_id")
    if content_id in content_hashes:
        new_hash = content_hashes[content_id]
        if data.get("body_sha256") != new_hash:
            data["body_sha256"] = new_hash
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            updated_reviews += 1

print(f"Updated {updated_audits} audit records")
print(f"Updated {updated_reviews} review records")
