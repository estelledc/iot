#!/usr/bin/env python3

import os
import re
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
AUTHORITIES_PATH = os.path.join(ROOT, "data", "trust-authorities.yml")

valid_path_pattern = re.compile(r'^docs/(foundation|connectivity|network|computing|intelligence|security|applications|frontier)/papers/[a-z0-9]+(?:-[a-z0-9]+)*\.md$')

with open(AUTHORITIES_PATH, 'r') as f:
    authorities = yaml.safe_load(f)

original_count = len(authorities['entries'])
valid_entries = []
invalid_entries = []

for entry in authorities['entries']:
    content_path = entry.get('content_path', '')
    if valid_path_pattern.match(content_path):
        valid_entries.append(entry)
    else:
        invalid_entries.append(entry)

authorities['entries'] = valid_entries

with open(AUTHORITIES_PATH, 'w') as f:
    yaml.dump(authorities, f, default_flow_style=False, sort_keys=False)

print(f"Removed {len(invalid_entries)} invalid entries")
print(f"Total entries now: {len(valid_entries)}")
