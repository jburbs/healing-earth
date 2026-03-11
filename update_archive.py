#!/usr/bin/env python3
"""
update_archive.py
=================
Healing Earth with Technology — Archive Enhancement Script

What this script does:
  1. Fetches all posts from the Substack API (subtitle, cover_image, slug)
  2. Parses index.html, matches each data-folder to a Substack post by date
  3. Replaces boilerplate/missing excerpts with Substack subtitle (if meaningful)
     or calls Claude API to generate one from the post body (for early issues)
  4. Injects cover image thumbnails into each <li> block (pointing to locally
     stored images in posts/<folder>/images/)
  5. Adds subtitle/og:description meta tags into each individual post index.html

Prerequisites:
    pip install requests anthropic beautifulsoup4

Usage:
    # Dry run (no writes) — shows what would change:
    python update_archive.py --dry-run

    # Apply all changes:
    python update_archive.py

    # Only update excerpts (skip thumbnails):
    python update_archive.py --no-thumbnails

    # Only update thumbnails (skip excerpts):
    python update_archive.py --no-excerpts

    # Limit Claude API calls (for testing):
    python update_archive.py --max-ai-calls 5

Configuration:
    Set ANTHROPIC_API_KEY environment variable before running.
    Or paste it directly into API_KEY below (not recommended for shared repos).

    REPO_ROOT should point to the local healing-earth repo root.

"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from typing import Optional, List, Dict
from bs4 import BeautifulSoup  # still used for read_post_body_text

# ── Configuration ─────────────────────────────────────────────────────────────

REPO_ROOT = Path(".")           # Run from inside the repo root, or set absolute path
INDEX_HTML = REPO_ROOT / "index.html"
POSTS_DIR  = REPO_ROOT / "posts"

SUBSTACK_API = "https://healingearth.substack.com/api/v1/posts"
SUBSTACK_LIMIT = 50
MANUAL_COVERS_FILE = REPO_ROOT / "manual_covers.json"

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Substack subtitle patterns that are NOT useful as summaries
USELESS_SUBTITLE_PATTERNS = [
    r"^\[?\d+\s?min(ute)?\s?read\]?\.?$",   # "[8 min read]"
    r"^\[?\d+\s?minute\s?read\]?\.?$",
    r"^$",                                     # empty
]

def is_useless_subtitle(subtitle: str) -> bool:
    s = (subtitle or "").strip()
    return any(re.match(p, s, re.IGNORECASE) for p in USELESS_SUBTITLE_PATTERNS)

def is_boilerplate_excerpt(text: str) -> bool:
    t = (text or "").strip()
    return (
        t.startswith("I'm Jonathan Burbaum") or
        "Healing Earth with Technology: a weekly, Science-based" in t or
        t.startswith("You can read Healing for free") or
        t.startswith("Estimated reading time") or
        t.startswith("In previous installments") or
        t.startswith("In this serial")
    )

# ── Manual covers ─────────────────────────────────────────────────────────────

def load_manual_covers() -> dict:
    """Load manual_covers.json if it exists. Returns {folder: filename}."""
    if not MANUAL_COVERS_FILE.exists():
        return {}
    try:
        with open(MANUAL_COVERS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except Exception as e:
        print(f"  ⚠ Could not load manual_covers.json: {e}")
        return {}

MANUAL_COVERS = load_manual_covers()

# ── Substack API ───────────────────────────────────────────────────────────────

def fetch_all_substack_posts() -> List[Dict]:
    """Paginate through the Substack API and return all posts."""
    all_posts = []
    offset = 0
    print("Fetching Substack posts...", end="", flush=True)
    while True:
        r = requests.get(SUBSTACK_API, params={"limit": SUBSTACK_LIMIT, "offset": offset, "sort": "new"}, timeout=15)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        all_posts.extend(batch)
        print(f" {len(all_posts)}", end="", flush=True)
        if len(batch) < SUBSTACK_LIMIT:
            break
        offset += SUBSTACK_LIMIT
        time.sleep(0.3)   # polite crawling
    print(f" — done ({len(all_posts)} total)")
    return all_posts

def build_date_index(posts: List[Dict]) -> Dict:
    """
    Build a dict keyed by ISO date (YYYY-MM-DD) -> post data.
    When there are reruns (duplicate dates), keep the one that is not a rerun
    (i.e., prefer the one whose slug doesn't contain 'rerun').
    For true ties, keep both and pick best subtitle at match time.
    """
    index = {}
    for p in posts:
        date = (p.get("post_date") or "")[:10]
        if not date:
            continue
        subtitle = (p.get("subtitle") or "").strip()
        cover = p.get("cover_image") or ""

        # Extract S3 UUID from cover URL.
        # Handles direct S3 URLs (/images/UUID_) and CDN proxy URLs
        # where the S3 path is URL-encoded (%2Fimages%2FUUID_)
        cover_uuid = ""
        m = re.search(r'(?:/images/|%2Fimages%2F)([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})_', cover, re.IGNORECASE)
        if m:
            cover_uuid = m.group(1)

        entry = {
            "date": date,
            "title": p.get("title") or "",
            "subtitle": subtitle,
            "slug": p.get("slug") or "",
            "cover_image": cover,
            "cover_uuid": cover_uuid,
            "truncated_body": (p.get("truncated_body_text") or "").strip(),
        }

        if date not in index:
            index[date] = [entry]
        else:
            index[date].append(entry)

    return index

# ── Local file helpers ─────────────────────────────────────────────────────────

def folder_date(folder_name: str) -> str:
    """Extract YYYY-MM-DD from folder name like '2021-05-23_001_Is Global Warming Real'."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", folder_name)
    return m.group(1) if m else ""

def find_cover_image_in_folder(folder_name: str, cover_uuid: str) -> str | None:
    """
    Look in posts/<folder>/images/ for a file whose name starts with cover_uuid.
    Falls back to manual_covers.json for posts with no UUID (YouTube, Unsplash, etc).
    Returns the relative path suitable for use in index.html, or None if not found.
    """
    images_dir = POSTS_DIR / folder_name / "images"

    # Primary: UUID-based match
    if cover_uuid and images_dir.is_dir():
        for f in images_dir.iterdir():
            if f.name.startswith(cover_uuid):
                return f"posts/{folder_name}/images/{f.name}"

    # Fallback: manual_covers.json
    if folder_name in MANUAL_COVERS:
        filename = MANUAL_COVERS[folder_name]
        candidate = images_dir / filename
        if candidate.exists():
            return f"posts/{folder_name}/images/{filename}"

    return None

def read_post_body_text(folder_name: str, max_chars: int = 3000) -> str:
    """
    Read the post's index.html and extract clean body text (skip boilerplate intro).
    Returns up to max_chars of meaningful article content.
    """
    post_html = POSTS_DIR / folder_name / "index.html"
    if not post_html.exists():
        return ""
    soup = BeautifulSoup(post_html.read_text(encoding="utf-8"), "html.parser")
    content = soup.find(class_="post-content")
    if not content:
        content = soup.find("article") or soup.body
    if not content:
        return ""

    paragraphs = content.find_all("p")
    good_paras = []
    for p in paragraphs:
        text = p.get_text(" ", strip=True)
        # Skip boilerplate / subscription / forwarding blurbs
        if is_boilerplate_excerpt(text):
            continue
        if len(text) < 30:
            continue
        good_paras.append(text)
        if sum(len(t) for t in good_paras) >= max_chars:
            break
    return "\n\n".join(good_paras)

# ── Claude API ─────────────────────────────────────────────────────────────────

def generate_summary_with_claude(folder_name: str, title: str, body_text: str) -> str:
    """
    Ask Claude to write a one-sentence archive summary for this post,
    matching Jonathan's voice and the style of his Substack subtitles.
    """
    if not API_KEY:
        return f"[AI summary needed for: {title}]"

    prompt = f"""You are helping Jonathan Burbaum, a former ARPA-E Program Director and PhD chemist, maintain the archive of his newsletter "Healing Earth with Technology." 

Jonathan writes about climate science, energy solutions, and policy — with an empirical, skeptic-friendly voice that prizes data over dogma.

Your task: write a SHORT archive subtitle (one punchy sentence or phrase, 6–15 words) for the post below. This is what appears below the post title in the archive, giving readers a reason to click.

Study these real examples from Jonathan's own subtitles:
- "The data speaks"
- "How can the curious skeptics like me find satisfaction?"
- "Humanity's and technology's roles in forming a more perfect planet"
- "The Supreme Court got it right"
- "Beyond Gatekeepers"
- "...but there are still plenty of issues"
- "A pause or gap in a sequence, series, or process"

Guidelines:
- Capture the post's central argument or question
- Match Jonathan's voice: wry, empirical, occasionally irreverent
- Do NOT use marketing language or hype
- Do NOT start with "In this post..." or "Jonathan explains..."
- Output ONLY the subtitle text — no quotes, no punctuation wrap, no preamble

Post title: {title}

Post content (first portion):
{body_text[:2500]}

Archive subtitle:"""

    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 80,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        r = requests.post(ANTHROPIC_URL, headers=headers, json=body, timeout=30)
        r.raise_for_status()
        text = r.json()["content"][0]["text"].strip().strip('"').strip("'")
        return text
    except Exception as e:
        print(f"  ⚠ Claude API error for '{title}': {e}")
        return f"[AI summary needed for: {title}]"

# ── Main index.html update ─────────────────────────────────────────────────────
#
# Strategy: pure string manipulation on the raw HTML, zero BeautifulSoup
# serialization. We find each <li data-folder="..."> block as a raw string,
# make targeted replacements inside it, and stitch the file back together.
# This preserves every byte of the original file that we don't explicitly change.

def extract_li_blocks(html: str):
    """
    Return a list of (start, end, folder) tuples for every
    <li data-folder="..."> ... </li> block in the raw HTML.
    end is the index just after </li>.
    """
    blocks = []
    pattern = re.compile(r'<li\s+data-folder="([^"]+)"', re.IGNORECASE)
    for m in pattern.finditer(html):
        folder = m.group(1)
        start = m.start()
        # Find the matching </li> — count nesting
        pos = m.end()
        depth = 1
        while pos < len(html) and depth > 0:
            open_tag = html.find('<li', pos)
            close_tag = html.find('</li>', pos)
            if close_tag == -1:
                break
            if open_tag != -1 and open_tag < close_tag:
                depth += 1
                pos = open_tag + 3
            else:
                depth -= 1
                if depth == 0:
                    end = close_tag + len('</li>')
                    blocks.append((start, end, folder))
                pos = close_tag + 5
    return blocks


def get_excerpt_from_block(block_html: str) -> str:
    """Extract the current excerpt text from a raw li block."""
    m = re.search(r'class="post-list-excerpt">(.*?)</p>', block_html, re.DOTALL)
    return m.group(1).strip() if m else ""


def get_href_from_block(block_html: str) -> str:
    """Extract the post href from a raw li block."""
    m = re.search(r'class="post-list-title"[^>]*>\s*<a\s+href="([^"]+)"', block_html)
    return m.group(1) if m else "#"


def update_index_html(
    date_index: dict,
    dry_run: bool = False,
    do_excerpts: bool = True,
    do_thumbnails: bool = True,
    max_ai_calls: int = 999,
) -> dict:
    """
    Update index.html using raw string replacement — no BS4 serialization.
    Finds each li[data-folder] block, makes targeted changes, writes back.
    The file is preserved byte-for-byte except for the changed content.
    """
    html = INDEX_HTML.read_text(encoding="utf-8")
    print(f"  Read index.html ({len(html):,} bytes)")

    report = {
        "excerpt_updated": [],
        "excerpt_ai_generated": [],
        "excerpt_unchanged": [],
        "thumbnail_added": [],
        "thumbnail_missing": [],
        "no_match": [],
    }

    blocks = extract_li_blocks(html)
    print(f"\nProcessing {len(blocks)} post list items...")
    if len(blocks) == 0:
        print("  ERROR: No <li data-folder=...> blocks found in index.html.")
        return report

    ai_calls_made = 0
    # We'll build the new HTML by walking through blocks in reverse order
    # (so that position offsets stay valid as we make substitutions)
    changes = []  # list of (start, end, new_block_html)

    for (start, end, folder) in blocks:
        block_html = html[start:end]
        new_block = block_html  # start with original

        date = folder_date(folder)

        # Match to Substack
        candidates = date_index.get(date, [])
        best = None
        if candidates:
            title_m = re.search(r'class="post-list-title"[^>]*>\s*<a[^>]*>([^<]+)</a>', block_html)
            title = title_m.group(1).strip() if title_m else folder
            for c in candidates:
                if best is None:
                    best = c
                elif not is_useless_subtitle(c["subtitle"]) and is_useless_subtitle(best["subtitle"]):
                    best = c
                elif c["title"].lower() in title.lower() or title.lower() in c["title"].lower():
                    best = c

        if not best:
            report["no_match"].append(folder)
            print(f"  ✗ No Substack match: {folder}")
            continue

        # ── Excerpt ───────────────────────────────────────────────────────
        if do_excerpts:
            current_text = get_excerpt_from_block(block_html)
            needs_update = is_boilerplate_excerpt(current_text) or not current_text

            new_excerpt = None
            if needs_update:
                subtitle = best["subtitle"]
                if not is_useless_subtitle(subtitle):
                    new_excerpt = subtitle
                    report["excerpt_updated"].append((folder, new_excerpt))
                    print(f'  ✓ Substack subtitle: [{folder[:50]}] → "{new_excerpt[:65]}"')
                else:
                    if ai_calls_made < max_ai_calls and not dry_run:
                        body_text = read_post_body_text(folder)
                        title_m = re.search(r'class="post-list-title"[^>]*>\s*<a[^>]*>([^<]+)</a>', block_html)
                        title = title_m.group(1).strip() if title_m else folder
                        print(f"  ⚙ AI summary: {title[:55]}...", end=" ", flush=True)
                        new_excerpt = generate_summary_with_claude(folder, title, body_text)
                        if new_excerpt.startswith("[AI summary needed"):
                            # API failed — fall back to truncated body text
                            truncated = best.get("truncated_body", "").strip()
                            # Strip leading boilerplate sentences
                            sentences = re.split(r'(?<=[.!?])\s+', truncated)
                            good_sentences = [s for s in sentences if not is_boilerplate_excerpt(s) and len(s) > 30]
                            if good_sentences:
                                new_excerpt = good_sentences[0][:160].strip()
                                print(f'→ (truncated body) "{new_excerpt[:65]}"')
                            else:
                                print(f'→ skipped (no usable fallback text)')
                                new_excerpt = None
                        else:
                            ai_calls_made += 1
                            print(f'→ "{new_excerpt[:65]}"')
                            report["excerpt_ai_generated"].append((folder, new_excerpt))
                    else:
                        if dry_run and not is_useless_subtitle(best.get("subtitle", "")):
                            pass  # already counted above
                        report["excerpt_unchanged"].append(folder)
            else:
                report["excerpt_unchanged"].append(folder)

            if new_excerpt:
                # Replace the excerpt text in place
                excerpt_pattern = re.compile(
                    r'(<p\s+class="post-list-excerpt">)(.*?)(</p>)',
                    re.DOTALL
                )
                if excerpt_pattern.search(new_block):
                    new_block = excerpt_pattern.sub(
                        lambda m: m.group(1) + new_excerpt + m.group(3),
                        new_block
                    )
                else:
                    # No excerpt element exists — insert one after post-list-info div
                    new_p = f'\n            <p class="post-list-excerpt">{new_excerpt}</p>'
                    new_block = re.sub(
                        r'(</div>\s*\n)(\s*</li>)',
                        r'\1' + new_p + r'\n\2',
                        new_block,
                        count=1
                    )

        # ── Thumbnail ─────────────────────────────────────────────────────
        if do_thumbnails:
            if 'class="post-thumb"' not in new_block:
                cover_uuid = best.get("cover_uuid", "")
                local_path = find_cover_image_in_folder(folder, cover_uuid)

                if local_path:
                    href = get_href_from_block(block_html)
                    thumb_html = (
                        f'\n            <a href="{href}" class="post-thumb" '
                        f'aria-hidden="true" tabindex="-1">'
                        f'<img src="{local_path}" alt="" loading="lazy" '
                        f'width="120" height="80" '
                        f'style="object-fit:cover;width:120px;height:80px;'
                        f'border-radius:4px;float:right;margin:0 0 0.5rem 1rem;"></a>'
                    )
                    # Insert thumb right after the opening <li ...> tag
                    new_block = re.sub(
                        r'(<li\s+data-folder="[^"]*"[^>]*>)',
                        r'\1' + thumb_html,
                        new_block,
                        count=1
                    )
                    report["thumbnail_added"].append((folder, local_path))
                    print(f"  📷 Thumbnail: [{folder[:55]}]")
                else:
                    report["thumbnail_missing"].append(folder)
                    if cover_uuid:
                        print(f"  ✗ No local cover: [{folder[:45]}] UUID={cover_uuid[:8]}...")

        if new_block != block_html:
            changes.append((start, end, new_block))

    # Apply all changes in reverse order to preserve offsets
    if changes and not dry_run:
        for (start, end, new_block) in sorted(changes, key=lambda x: x[0], reverse=True):
            html = html[:start] + new_block + html[end:]
        INDEX_HTML.write_text(html, encoding="utf-8")
        print(f"\n✅ index.html updated ({len(changes)} blocks changed, {len(html):,} bytes written).")
    elif dry_run:
        print(f"\n[DRY RUN — {len(changes)} blocks would change]")
    else:
        print(f"\n✅ index.html — nothing to change.")

    return report

# ── Individual post meta tags ──────────────────────────────────────────────────

def update_post_meta_tags(date_index: dict, dry_run: bool = False):
    """
    For each post, add <meta name="description"> and <meta property="og:description">
    to its index.html if a good subtitle/summary is available.
    """
    print("\nUpdating post meta tags...")
    updated = 0
    skipped = 0
    for folder_path in sorted(POSTS_DIR.iterdir()):
        if not folder_path.is_dir():
            continue
        folder = folder_path.name
        date = folder_date(folder)
        candidates = date_index.get(date, [])
        if not candidates:
            continue

        best = candidates[0]
        for c in candidates:
            if not is_useless_subtitle(c["subtitle"]):
                best = c
                break

        subtitle = best.get("subtitle", "").strip()
        if is_useless_subtitle(subtitle):
            continue

        post_index = folder_path / "index.html"
        if not post_index.exists():
            continue

        html = post_index.read_text(encoding="utf-8")

        # Skip if description meta already exists
        if 'name="description"' in html or "name='description'" in html:
            skipped += 1
            continue

        # Escape subtitle for HTML attribute
        safe_subtitle = subtitle.replace('&', '&amp;').replace('"', '&quot;')
        meta_block = (
            f'\n    <meta name="description" content="{safe_subtitle}">'
            f'\n    <meta property="og:description" content="{safe_subtitle}">'
        )

        # Insert after the first <meta charset> line
        new_html = re.sub(
            r'(<meta\s+charset[^>]*>)',
            r'\1' + meta_block,
            html,
            count=1,
            flags=re.IGNORECASE
        )

        if new_html == html:
            # Fallback: insert right after <head>
            new_html = re.sub(
                r'(<head[^>]*>)',
                r'\1' + meta_block,
                html,
                count=1,
                flags=re.IGNORECASE
            )

        if not dry_run and new_html != html:
            post_index.write_text(new_html, encoding="utf-8")
        updated += 1

    print(f"  Meta tags added for {updated} posts, {skipped} already had them.")

# ── CSS additions ──────────────────────────────────────────────────────────────

THUMB_CSS = """
/* Post list thumbnails — added by update_archive.py */
.post-thumb {
    display: block;
    float: right;
    margin: 0 0 0.5rem 1.25rem;
    flex-shrink: 0;
    border-radius: 4px;
    overflow: hidden;
    line-height: 0;
}
.post-thumb img {
    display: block;
    width: 120px;
    height: 80px;
    object-fit: cover;
    border-radius: 4px;
    transition: opacity 0.15s ease;
}
.post-thumb:hover img {
    opacity: 0.85;
}
/* Clearfix for post list items with floated thumbs */
li[data-folder]::after {
    content: "";
    display: table;
    clear: both;
}
@media (max-width: 480px) {
    .post-thumb {
        float: none;
        margin: 0 0 0.75rem 0;
    }
    .post-thumb img {
        width: 100%;
        height: auto;
        aspect-ratio: 3/2;
        max-height: 160px;
    }
}
"""

def inject_thumb_css(dry_run: bool = False):
    """Append thumbnail CSS to style.css if not already present."""
    css_file = REPO_ROOT / "style.css"
    if not css_file.exists():
        print("  ⚠ style.css not found, skipping CSS injection")
        return
    current = css_file.read_text(encoding="utf-8")
    if "post-thumb" in current:
        print("  CSS already contains .post-thumb — skipping")
        return
    if not dry_run:
        css_file.write_text(current + "\n" + THUMB_CSS, encoding="utf-8")
        print("  ✓ Thumbnail CSS appended to style.css")
    else:
        print("  [DRY RUN] Would append thumbnail CSS to style.css")

# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Update Healing Earth archive with summaries and thumbnails")
    parser.add_argument("--dry-run",        action="store_true", help="Show what would change without writing files")
    parser.add_argument("--no-thumbnails",  action="store_true", help="Skip thumbnail injection")
    parser.add_argument("--no-excerpts",    action="store_true", help="Skip excerpt updates")
    parser.add_argument("--no-post-meta",   action="store_true", help="Skip per-post meta tag updates")
    parser.add_argument("--no-css",         action="store_true", help="Skip CSS additions")
    parser.add_argument("--max-ai-calls",   type=int, default=999, help="Max number of Claude API calls (default: unlimited)")
    parser.add_argument("--repo",           type=str, default=".", help="Path to repo root (default: current dir)")
    args = parser.parse_args()

    global REPO_ROOT, INDEX_HTML, POSTS_DIR
    REPO_ROOT = Path(args.repo)
    INDEX_HTML = REPO_ROOT / "index.html"
    POSTS_DIR  = REPO_ROOT / "posts"

    if not INDEX_HTML.exists():
        print(f"ERROR: index.html not found at {INDEX_HTML}")
        sys.exit(1)
    if not POSTS_DIR.is_dir():
        print(f"ERROR: posts/ directory not found at {POSTS_DIR}")
        sys.exit(1)
    if not API_KEY and not args.no_excerpts:
        print("WARNING: ANTHROPIC_API_KEY not set. AI-generated summaries will be placeholders.")
        print("         Set the environment variable or edit API_KEY in the script.\n")

    # Step 1: Fetch Substack data
    posts = fetch_all_substack_posts()
    date_index = build_date_index(posts)
    print(f"Indexed {len(date_index)} unique dates from Substack.")

    # Step 2: Update index.html
    if not args.no_excerpts or not args.no_thumbnails:
        report = update_index_html(
            date_index,
            dry_run=args.dry_run,
            do_excerpts=not args.no_excerpts,
            do_thumbnails=not args.no_thumbnails,
            max_ai_calls=args.max_ai_calls,
        )

        print("\n── Summary ───────────────────────────────────────")
        print(f"  Excerpts replaced with Substack subtitle : {len(report['excerpt_updated'])}")
        print(f"  Excerpts replaced with AI summary        : {len(report['excerpt_ai_generated'])}")
        print(f"  Excerpts unchanged (already good)        : {len(report['excerpt_unchanged'])}")
        print(f"  Thumbnails added                         : {len(report['thumbnail_added'])}")
        print(f"  Thumbnails missing (UUID not local)      : {len(report['thumbnail_missing'])}")
        print(f"  Posts with no Substack match             : {len(report['no_match'])}")

        if report["thumbnail_missing"]:
            print("\n── Posts needing cover image download ───────────")
            for folder in report["thumbnail_missing"]:
                date = folder_date(folder)
                candidates = date_index.get(date, [])
                cover = candidates[0]["cover_image"] if candidates else "(unknown)"
                print(f"  {folder}\n    {cover}")

    # Step 3: Inject CSS
    if not args.no_css:
        inject_thumb_css(dry_run=args.dry_run)

    # Step 4: Update per-post meta tags
    if not args.no_post_meta:
        update_post_meta_tags(date_index, dry_run=args.dry_run)

    print("\nDone.")

if __name__ == "__main__":
    main()