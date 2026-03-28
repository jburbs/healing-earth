#!/usr/bin/env python3
"""
build_search_index.py
=====================
Rebuilds search-index.json and search.js for healingearthwithtech.com.

Reads every post's index.html, extracts clean body text (full length, no truncation),
and writes:
  - search-index.json  (raw JSON array)
  - search.js          (const searchIndex = [...]; + searchPosts/highlight functions)

Usage:
    python build_search_index.py                # rebuild from repo root
    python build_search_index.py --repo /path   # specify repo path
    python build_search_index.py --dry-run      # show stats without writing
"""

from __future__ import annotations

import os
import re
import sys
import json
import argparse
from pathlib import Path
from bs4 import BeautifulSoup


# ── Configuration ─────────────────────────────────────────────────────────────

REPO_ROOT = Path(".")
POSTS_DIR = REPO_ROOT / "posts"
SEARCH_INDEX_JSON = REPO_ROOT / "search-index.json"
SEARCH_JS = REPO_ROOT / "search.js"

# Boilerplate patterns to skip when extracting body text
BOILERPLATE_PATTERNS = [
    r"^I'm Jonathan Burbaum",
    r"Healing Earth with Technology: a weekly, Science-based",
    r"^You can read Healing for free",
    r"^Estimated reading time",
    r"^Share$",
    r"^Subscribe$",
    r"^Leave a comment$",
    r"^Thanks for reading",
    r"^Like$",
    r"^Comment$",
    r"^Restack$",
]


def is_boilerplate(text: str) -> bool:
    """Check if a paragraph is boilerplate/subscription text."""
    t = text.strip()
    return any(re.match(p, t, re.IGNORECASE) for p in BOILERPLATE_PATTERNS)


def extract_post_text(html_path: Path) -> tuple[str, str, str]:
    """
    Extract title, date, and full body text from a post's index.html.
    Returns (title, date, content_text).
    """
    html = html_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    # Extract title
    title = ""
    title_el = soup.find("h1", class_="post-title")
    if not title_el:
        title_el = soup.find("h1")
    if title_el:
        title = title_el.get_text(strip=True)

    # Extract date from folder name
    folder_name = html_path.parent.name
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", folder_name)
    date = date_match.group(1) if date_match else ""

    # Extract body text
    content_el = soup.find(class_="post-content")
    if not content_el:
        content_el = soup.find("article")
    if not content_el:
        content_el = soup.body
    if not content_el:
        return title, date, ""

    # Get all text-bearing elements
    paragraphs = []
    for tag in content_el.find_all(["p", "h2", "h3", "h4", "li", "blockquote", "figcaption"]):
        text = tag.get_text(" ", strip=True)
        if not text or len(text) < 10:
            continue
        if is_boilerplate(text):
            continue
        paragraphs.append(text)

    content = "\n\n".join(paragraphs)

    # Also extract alt text from images (can contain searchable descriptions)
    for img in content_el.find_all("img"):
        alt = (img.get("alt") or "").strip()
        if alt and len(alt) > 15 and not alt.startswith("http"):
            content += f"\n\n{alt}"

    return title, date, content


# ── JS function text (preserved from existing search.js) ─────────────────────

SEARCH_JS_FUNCTIONS = """
function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
}

function searchPosts(query) {
    if (!searchIndex || !query.trim()) return null;

    const queryLower = query.toLowerCase().trim();
    if (queryLower.length < 2) return null;

    const results = [];

    for (const post of searchIndex) {
        const titleLower = post.title.toLowerCase();
        const contentLower = post.content.toLowerCase();

        // Search for the ENTIRE phrase, not individual words
        const titleMatches = titleLower.includes(queryLower);
        const contentMatchCount = (contentLower.split(queryLower).length - 1);

        if (titleMatches || contentMatchCount > 0) {
            // Score: title match worth 10, plus content matches
            const score = (titleMatches ? 10 : 0) + contentMatchCount;
            results.push({ ...post, score, matchCount: contentMatchCount + (titleMatches ? 1 : 0) });
        }
    }

    // Sort by score descending
    results.sort((a, b) => b.score - a.score);
    return results;
}

function highlightMatch(text, query) {
    if (!query.trim()) return text;
    const escaped = escapeRegex(query.trim());
    const regex = new RegExp(`(${escaped})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function getContextSnippet(content, query, maxLength = 250) {
    const queryLower = query.toLowerCase().trim();
    if (!queryLower) return content.slice(0, maxLength) + '...';

    const contentLower = content.toLowerCase();
    const pos = contentLower.indexOf(queryLower);

    let bestPos = 0;
    if (pos !== -1) {
        bestPos = Math.max(0, pos - 60);
    }

    let snippet = content.slice(bestPos, bestPos + maxLength);
    if (bestPos > 0) snippet = '...' + snippet;
    if (bestPos + maxLength < content.length) snippet += '...';

    return highlightMatch(snippet, query);
}
"""


def build_index(repo_root: Path, dry_run: bool = False) -> list[dict]:
    """Build the search index from all post folders."""
    posts_dir = repo_root / "posts"
    if not posts_dir.is_dir():
        print(f"ERROR: posts/ directory not found at {posts_dir}")
        sys.exit(1)

    entries = []
    skipped = []

    folders = sorted(
        [d for d in posts_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,  # newest first
    )

    print(f"Scanning {len(folders)} post folders...")

    for folder in folders:
        index_html = folder / "index.html"
        if not index_html.exists():
            skipped.append(folder.name)
            continue

        try:
            title, date, content = extract_post_text(index_html)
        except OSError as e:
            print(f"  ⚠ Could not read {folder.name}: {e}")
            skipped.append(folder.name)
            continue
        if not title:
            title = folder.name  # fallback

        href = f"posts/{folder.name}/index.html"

        entries.append({
            "title": title,
            "date": date,
            "href": href,
            "content": content,
        })

    # Stats
    lengths = [len(e["content"]) for e in entries]
    print(f"\nIndex built: {len(entries)} entries")
    if lengths:
        print(f"  Content lengths — min: {min(lengths):,}, max: {max(lengths):,}, avg: {sum(lengths) // len(lengths):,}")
        print(f"  Median: {sorted(lengths)[len(lengths) // 2]:,}")
        at_old_cap = sum(1 for l in lengths if l >= 9900)
        print(f"  Entries >= 9,900 chars (would've been truncated before): {at_old_cap}")
    if skipped:
        print(f"  Skipped (no index.html): {len(skipped)}")

    if not dry_run:
        # Write search-index.json
        json_path = repo_root / "search-index.json"
        json_str = json.dumps(entries, ensure_ascii=False)
        json_path.write_text(json_str, encoding="utf-8")
        print(f"\n✅ {json_path.name} written ({len(json_str):,} bytes)")

        # Write search.js
        js_path = repo_root / "search.js"
        js_content = (
            "\n// Full-text search using embedded search index\n"
            "// (Embedded to avoid CORS issues when opening as local file)\n"
            f"const searchIndex = {json_str};\n"
            f"{SEARCH_JS_FUNCTIONS}"
        )
        js_path.write_text(js_content, encoding="utf-8")
        print(f"✅ {js_path.name} written ({len(js_content):,} bytes)")
    else:
        print("\n[DRY RUN — no files written]")

    return entries


def main():
    parser = argparse.ArgumentParser(description="Rebuild search index for Healing Earth")
    parser.add_argument("--repo", type=str, default=".", help="Path to repo root")
    parser.add_argument("--dry-run", action="store_true", help="Show stats without writing files")
    args = parser.parse_args()

    repo = Path(args.repo)
    entries = build_index(repo, dry_run=args.dry_run)

    # Quick verification: check a few search terms
    if entries:
        test_terms = ["arpa-e", "diurnal", "nuclear", "desalination", "photosynthesis"]
        print("\n── Search term spot-check ──")
        for term in test_terms:
            matches = sum(
                1 for e in entries
                if term in e["content"].lower() or term in e["title"].lower()
            )
            print(f"  '{term}': {matches} posts")


if __name__ == "__main__":
    main()
