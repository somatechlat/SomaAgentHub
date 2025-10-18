#!/usr/bin/env python3
"""Simple markdown internal link checker.

Finds links of the forms:
 - [text](path/to/file.md)
 - [text](../other.md#anchor)
 - ![alt](image.png)

Checks only relative links (not starting with http:// or https:// or mailto: or #).
Reports missing target files. Anchor checks are not performed (fast pass).

Usage: python scripts/check_md_links.py
"""

import re
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_EXTS = {'.md', '.markdown', '.mdown'}

link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

results = []

for md_path in ROOT.rglob('*.md'):
    # skip .git and .venv directories implicitly
    if any(part.startswith('.git') or part.startswith('.venv') for part in md_path.parts):
        continue
    text = md_path.read_text(encoding='utf-8', errors='ignore')
    links = link_pattern.findall(text)
    images = image_pattern.findall(text)
    all_links = [m[1] for m in links] + [m[1] for m in images]
    for link in all_links:
        link = link.strip()
        # skip external URLs and mailto and anchors-only
        if link.startswith('http://') or link.startswith('https://') or link.startswith('mailto:'):
            continue
        if link.startswith('#'):
            continue
        # split off the anchor portion
        target = link.split('#', 1)[0]
        # if link is absolute unix-style (starts with /) treat as repo-root relative
        if target.startswith('/'):
            candidate = ROOT.joinpath(target.lstrip('/'))
        else:
            candidate = (md_path.parent / target).resolve()
        # if candidate has no extension, try adding .md
        if not candidate.exists():
            if candidate.suffix == '':
                candidate_md = Path(str(candidate) + '.md')
                if candidate_md.exists():
                    continue
            # also try index.md in directory
            if candidate.is_dir():
                index_md = candidate / 'README.md'
                if index_md.exists():
                    continue
                index_md2 = candidate / 'index.md'
                if index_md2.exists():
                    continue
            results.append({
                'source': str(md_path.relative_to(ROOT)),
                'link': link,
                'resolved_candidate': str(candidate.relative_to(ROOT)) if candidate.exists() else str(candidate.relative_to(ROOT)) if candidate.exists() else str(candidate)
            })

out = {'root': str(ROOT), 'broken_links': results}
print(json.dumps(out, indent=2))

# also print a short human-friendly summary
if results:
    print('\nBroken internal links found:')
    for r in results:
        print(f"- in {r['source']}: {r['link']} -> {r['resolved_candidate']}")
else:
    print('\nNo broken internal links found.')
