#!/usr/bin/env python3

import os
import hashlib
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUTHORITIES_PATH = os.path.join(ROOT, "data", "trust-authorities.yml")

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

with open(AUTHORITIES_PATH, 'r') as f:
    authorities = yaml.safe_load(f)

fixed_count = 0
for entry in authorities['entries']:
    content_path = entry.get('content_path')
    if not content_path:
        continue
    
    full_path = os.path.join(ROOT, content_path)
    if not os.path.exists(full_path):
        continue
    
    try:
        with open(full_path, 'rb') as f:
            raw = f.read()
        body_bytes = get_body_bytes(raw)
        correct_hash = hashlib.sha256(body_bytes).hexdigest()
        
        current_hash = entry.get('body_sha256', '')
        if current_hash != correct_hash:
            entry['body_sha256'] = correct_hash
            fixed_count += 1
    except Exception as e:
        print(f"Error processing {content_path}: {e}")

with open(AUTHORITIES_PATH, 'w') as f:
    yaml.dump(authorities, f, default_flow_style=False, sort_keys=False)

print(f"Fixed {fixed_count} body_sha256 hashes")
print(f"Total entries: {len(authorities['entries'])}")
