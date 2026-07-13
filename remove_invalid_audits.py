#!/usr/bin/env python3

import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = os.path.join(ROOT, "data", "source-audits")
REVIEW_DIR = os.path.join(ROOT, "data", "review-records")

valid_path_pattern = re.compile(r'^docs/(foundation|connectivity|network|computing|intelligence|security|applications|frontier)/papers/[a-z0-9]+(?:-[a-z0-9]+)*\.md$')

invalid_content_ids = {'build-compatibility', 'catalog', 'content-schema', 'index', 'progress', 'release-policy', 'roadmap', 'tags'}

deleted_audits = 0
for filename in os.listdir(AUDIT_DIR):
    content_id = None
    if filename.startswith("audit-20260712-structural-"):
        content_id = filename.replace("audit-20260712-structural-", "").replace(".yml", "")
    elif filename.startswith("audit-20260713-claim-"):
        content_id = filename.replace("audit-20260713-claim-", "").replace(".yml", "")
    
    if content_id in invalid_content_ids:
        os.remove(os.path.join(AUDIT_DIR, filename))
        deleted_audits += 1

deleted_reviews = 0
for filename in os.listdir(REVIEW_DIR):
    content_id = None
    if filename.startswith("review-20260713-start-"):
        content_id = filename.replace("review-20260713-start-", "").replace(".yml", "")
    elif filename.startswith("review-20260713-approve-"):
        content_id = filename.replace("review-20260713-approve-", "").replace(".yml", "")
    
    if content_id in invalid_content_ids:
        os.remove(os.path.join(REVIEW_DIR, filename))
        deleted_reviews += 1

print(f"Deleted {deleted_audits} invalid audit records")
print(f"Deleted {deleted_reviews} invalid review records")
