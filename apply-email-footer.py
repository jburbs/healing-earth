#!/usr/bin/env python3
"""
Adds 'Email the author' footer to all post pages and creates aha.html.
Run from the 'Substack Site Localized' directory:
    python3 apply-email-footer.py
"""

import os
import urllib.parse
from pathlib import Path

# ──────────────────────────────────────────
# 1. Add email footer to all 182 post pages
# ──────────────────────────────────────────

posts_dir = Path("posts")
count = 0
errors = []

CONTACT_BLOCK = '<div class="post-contact">\n    <p>Questions, pushback, or just want to talk? <a href="mailto:jonathan@healingearthwithtech.com">Email the author</a></p>\n</div>'

for folder in sorted(posts_dir.iterdir()):
    fpath = folder / "index.html"
    if not fpath.is_file():
        continue

    content = fpath.read_text(encoding="utf-8")

    # Skip if already added
    if "post-contact" in content:
        count += 1
        continue

    # Insert before post-nav-bottom or </article>
    if '<div id="post-nav-bottom">' in content:
        content = content.replace(
            '<div id="post-nav-bottom">',
            CONTACT_BLOCK + '\n<div id="post-nav-bottom">'
        )
    elif '</article>' in content:
        content = content.replace(
            '</article>',
            CONTACT_BLOCK + '\n</article>'
        )
    else:
        errors.append(str(fpath))
        continue

    fpath.write_text(content, encoding="utf-8")
    count += 1

print(f"[1/3] Added email footer to {count} post pages")
if errors:
    print(f"  Errors: {errors}")

# ──────────────────────────────────────────
# 2. Add post title to mailto subject line
# ──────────────────────────────────────────

import re

count2 = 0
for folder in sorted(posts_dir.iterdir()):
    fpath = folder / "index.html"
    if not fpath.is_file():
        continue

    content = fpath.read_text(encoding="utf-8")

    if "post-contact" not in content:
        continue

    # Already has a subject?
    if "?subject=" in content:
        count2 += 1
        continue

    # Extract title from <h1 class="post-title">...</h1>
    m = re.search(r'<h1[^>]*class="post-title"[^>]*>(.*?)</h1>', content, re.DOTALL)
    if not m:
        continue

    title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    subject = urllib.parse.quote(f"Re: {title}", safe="")
    new_mailto = f"mailto:jonathan@healingearthwithtech.com?subject={subject}"

    content = content.replace(
        "mailto:jonathan@healingearthwithtech.com",
        new_mailto
    )
    fpath.write_text(content, encoding="utf-8")
    count2 += 1

print(f"[2/3] Added subject lines to {count2} mailto links")

# ──────────────────────────────────────────
# 3. Add post-contact CSS to style.css
# ──────────────────────────────────────────

css_path = Path("style.css")
css = css_path.read_text(encoding="utf-8")

if ".post-contact" not in css:
    new_css = """
/* ===== POST CONTACT FOOTER ===== */
.post-contact {
    margin: 3rem 0 1.5rem;
    padding: 1.25rem 1.5rem;
    background: var(--bg-warm);
    border-radius: 6px;
    text-align: center;
    font-family: var(--font-sans);
}

.post-contact p {
    margin: 0;
    font-size: 1rem;
    color: var(--text-secondary);
}

.post-contact a {
    color: var(--link-color);
    font-weight: 600;
    text-decoration: none;
}

.post-contact a:hover {
    text-decoration: underline;
    color: var(--link-hover);
}

"""
    css = css.replace("/* ===== RESPONSIVE =====", new_css + "/* ===== RESPONSIVE =====")
    css_path.write_text(css, encoding="utf-8")
    print("[3/3] Added post-contact CSS to style.css")
else:
    print("[3/3] post-contact CSS already present")

print("\nDone! Now run:")
print("  git add aha.html style.css posts/")
print('  git commit -m "Add email-the-author footer and redesign aha moments page"')
print("  git push origin redesign-landing-v2")
