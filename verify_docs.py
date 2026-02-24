import os
import re

docs_dir = 'docs'
all_md = []
for root, _, files in os.walk(docs_dir):
    for f in files:
        if f.endswith('.md'):
            all_md.append(os.path.join(root, f))

broken = []
for path in all_md:
    with open(path, encoding='utf-8') as f:
        content = f.read()
    links = re.findall(r'\[.*?\]\((.*?\.md[^)]*)\)', content)
    for link in links:
        link_clean = link.split('#')[0]
        if link_clean.startswith('http'):
            continue
        base = os.path.dirname(path)
        target = os.path.normpath(os.path.join(base, link_clean))
        if not os.path.exists(target):
            broken.append(f'{path}: broken link -> {link}')

if broken:
    print(f'BROKEN LINKS ({len(broken)}):')
    for b in broken: print(f'  {b}')
else:
    print(f'All links OK ({len(all_md)} pages checked)')
