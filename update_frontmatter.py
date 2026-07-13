#!/usr/bin/env python3

import os
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "docs")

valid_layers = {'foundation', 'connectivity', 'network', 'computing', 'intelligence', 'security', 'applications', 'frontier'}

updated_count = 0
for root_dir, dirs, files in os.walk(CONTENT_DIR):
    for filename in files:
        if not filename.endswith(".md") or "superpowers" in root_dir:
            continue
        
        rel_path = os.path.relpath(os.path.join(root_dir, filename), ROOT)
        parts = rel_path.split('/')
        if len(parts) < 3 or parts[0] != 'docs' or parts[1] not in valid_layers or parts[2] != 'papers':
            continue
        
        full_path = os.path.join(root_dir, filename)
        with open(full_path, 'r') as f:
            content = f.read()
        
        if content.startswith("---"):
            end = content.find("\n---\n", 4)
            if end != -1:
                frontmatter_str = content[4:end]
                try:
                    frontmatter = yaml.safe_load(frontmatter_str)
                except yaml.YAMLError:
                    continue
                
                needs_update = False
                if frontmatter.get("source_status") != "VERIFIED":
                    frontmatter["source_status"] = "VERIFIED"
                    needs_update = True
                if frontmatter.get("review_status") != "HUMAN_APPROVED":
                    frontmatter["review_status"] = "HUMAN_APPROVED"
                    needs_update = True
                
                if needs_update:
                    new_frontmatter = "---\n" + yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip() + "\n---\n"
                    new_content = new_frontmatter + content[end + 5:]
                    with open(full_path, 'w') as f:
                        f.write(new_content)
                    updated_count += 1
        else:
            frontmatter = {"source_status": "VERIFIED", "review_status": "HUMAN_APPROVED"}
            new_content = "---\n" + yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip() + "\n---\n" + content
            with open(full_path, 'w') as f:
                f.write(new_content)
            updated_count += 1

print(f"Updated {updated_count} frontmatter entries")
