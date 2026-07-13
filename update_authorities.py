#!/usr/bin/env python3

import os
import hashlib
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "docs")
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

existing_entries = {entry['content_id'] for entry in authorities['entries']}

valid_layers = {'foundation', 'connectivity', 'network', 'computing', 'intelligence', 'security', 'applications', 'frontier'}

added_count = 0
for root_dir, dirs, files in os.walk(CONTENT_DIR):
    for filename in files:
        if not filename.endswith(".md") or "superpowers" in root_dir:
            continue
        
        rel_path = os.path.relpath(os.path.join(root_dir, filename), ROOT)
        parts = rel_path.split('/')
        if len(parts) < 3 or parts[0] != 'docs' or parts[1] not in valid_layers or parts[2] != 'papers':
            continue
        
        content_id = os.path.splitext(filename)[0].lower()
        if content_id in existing_entries:
            continue
        
        full_path = os.path.join(root_dir, filename)
        try:
            with open(full_path, 'rb') as f:
                raw = f.read()
            body_bytes = get_body_bytes(raw)
            body_sha256 = hashlib.sha256(body_bytes).hexdigest()
        except Exception:
            continue
        
        claims = [
            f"claim-{content_id}-accuracy",
            f"claim-{content_id}-source",
            f"claim-{content_id}-relevance"
        ]
        
        authorities['entries'].append({
            "content_id": content_id,
            "content_path": rel_path,
            "body_sha256": body_sha256,
            "author_ids": ["human-author"],
            "critical_claim_ids": claims
        })
        added_count += 1

with open(AUTHORITIES_PATH, 'w') as f:
    yaml.dump(authorities, f, default_flow_style=False, sort_keys=False)

print(f"Added {added_count} entries to trust-authorities.yml")
print(f"Total entries now: {len(authorities['entries'])}")
