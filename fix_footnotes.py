#!/usr/bin/env python3
"""
fix_footnotes.py -- Fix broken footnote content in archived posts.

TWO DEFECT TYPES
================

TYPE A -- Empty cross-reference link:
  Footnote has a local archive <a href="../folder/index.html"> but link text
  is empty, so it renders invisible. The href is correct; only the text is missing.

  Fix: derive the post title from the linked folder name and set it as link text.
  The href is never touched -- it stays pointing at the local archive.

TYPE B -- Truly empty footnote:
  No sibling elements exist after the footnote-number anchor at all.

  Fix: fetch .footnote-content from the Substack API and inject it.
  NOTE: if the API content contains open.substack.com URLs, those are rewritten
  to local archive relative paths where a matching folder exists.

MATCHING
Posts matched by post_date (YYYY-MM-DD prefix of folder name).
"""

import argparse
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

REPO_ROOT    = Path(".")
POSTS_DIR    = REPO_ROOT / "posts"
SUBSTACK_API = "https://healingearth.substack.com/api/v1/posts"

# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_all_posts() -> list:
    posts, offset = [], 0
    print("Fetching posts from Substack API...", end="", flush=True)
    while True:
        r = requests.get(SUBSTACK_API,
                         params={"limit": 50, "offset": offset, "sort": "new"},
                         timeout=20)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        print(f" {len(posts)}", end="", flush=True)
        if len(batch) < 50:
            break
        offset += 50
        time.sleep(0.3)
    print(f" -- done ({len(posts)} total)")
    return posts

# ── Date -> folder map ────────────────────────────────────────────────────────

def build_date_to_folders() -> dict:
    idx = {}
    for folder in sorted(POSTS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})", folder.name)
        if m:
            idx.setdefault(m.group(1), []).append(folder)
    return idx

# ── Slug -> folder map (for rewriting Substack URLs in Type B) ───────────────

def build_slug_to_folder(all_posts: list, date_to_folders: dict) -> dict:
    """Map Substack slug -> local folder Path."""
    result = {}
    for post in all_posts:
        date = (post.get("post_date") or "")[:10]
        slug = post.get("slug", "")
        if not date or not slug:
            continue
        folders = date_to_folders.get(date, [])
        if folders:
            result[slug] = folders[0]
    return result

# ── Title helpers ─────────────────────────────────────────────────────────────

def title_from_folder_name(folder_name: str) -> str:
    m = re.match(r"^\d{4}-\d{2}-\d{2}_\d+_(.*)", folder_name)
    return m.group(1).strip() if m else folder_name

def title_from_index(index_path: Path) -> str | None:
    if not index_path.exists():
        return None
    soup = BeautifulSoup(index_path.read_text(encoding="utf-8"), "html.parser")
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag:
        t = title_tag.get_text(strip=True)
        return re.sub(r"\s*-\s*Healing Earth.*$", "", t).strip()
    return None

def resolve_link_title(href: str, current_folder: Path) -> str:
    target = (current_folder / href).resolve()
    target_folder = target.parent if target.name == "index.html" else target
    title = title_from_index(target_folder / "index.html")
    return title if title else title_from_folder_name(target_folder.name)

# ── Classify footnotes ────────────────────────────────────────────────────────

def classify_footnotes(local_html: str) -> dict:
    """
    Returns { "footnote-N": ("ok" | "empty_link" | "truly_empty", extra) }

    Key insight: an empty <a href="../..."> has NO text but DOES have a Tag
    sibling. We must check for Tag siblings first before declaring truly_empty.
    """
    soup = BeautifulSoup(local_html, "html.parser")
    results = {}

    for anchor in soup.find_all("a", id=re.compile(r'^footnote-\d+$'),
                                 class_="footnote-number"):
        fn_id = anchor["id"]

        # Collect sibling nodes (Tags and non-empty text strings)
        sibling_tags = []
        node = anchor.next_sibling
        while node is not None:
            if isinstance(node, Tag):
                sibling_tags.append(node)
            node = node.next_sibling

        # No sibling elements at all -> truly empty
        if not sibling_tags:
            results[fn_id] = ("truly_empty", None)
            continue

        # Look for empty local archive links among sibling tags
        empty_local_links = []
        for sib in sibling_tags:
            for a in ([sib] if sib.name == "a" else sib.find_all("a", href=True)):
                href = a.get("href", "")
                is_local = href.startswith("../") or href.startswith("./")
                if is_local and not a.get_text(strip=True):
                    empty_local_links.append((a, href))

        if empty_local_links:
            results[fn_id] = ("empty_link", empty_local_links)
        else:
            results[fn_id] = ("ok", None)

    return results

# ── API footnotes ─────────────────────────────────────────────────────────────

def extract_api_footnotes(body_html: str) -> dict:
    soup = BeautifulSoup(body_html, "html.parser")
    result = {}
    for fn_div in soup.find_all("div", class_="footnote"):
        anchor = fn_div.find("a", id=re.compile(r'^footnote-\d+$'))
        if not anchor:
            continue
        content_div = fn_div.find("div", class_="footnote-content")
        if content_div:
            result[anchor["id"]] = str(content_div)
    return result

# ── Rewrite Substack URLs to local archive paths ──────────────────────────────

SUBSTACK_URL_RE = re.compile(
    r'https?://(?:open\.)?substack\.com/pub/healingearth/p/([^?"&\s]+)'
    r'|https?://healingearth\.substack\.com/p/([^?"&\s]+)'
)

def rewrite_substack_urls(content_div_html: str, slug_to_folder: dict,
                           current_folder: Path) -> str:
    """
    Replace any Substack post URLs inside the content div with local relative paths.
    Preserves link text if present, or uses the folder title as fallback.
    """
    soup = BeautifulSoup(content_div_html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = SUBSTACK_URL_RE.match(href)
        if not m:
            continue
        slug = m.group(1) or m.group(2)
        # Strip any trailing slashes
        slug = slug.rstrip("/")
        target_folder = slug_to_folder.get(slug)
        if not target_folder:
            # Try partial match (slug may have number prefix variations)
            for s, f in slug_to_folder.items():
                if slug in s or s.endswith(slug):
                    target_folder = f
                    break
        if target_folder:
            rel = Path("../") / target_folder.name / "index.html"
            a["href"] = str(rel)
            if not a.get_text(strip=True):
                a.string = title_from_folder_name(target_folder.name)
        # If no match found, leave the Substack URL as-is (better than nothing)
    return str(soup)

# ── Patch: Type A (empty link text) ──────────────────────────────────────────

def fix_empty_link(local_html: str, fn_id: str,
                   empty_links: list, folder: Path) -> tuple[str, str]:
    soup = BeautifulSoup(local_html, "html.parser")
    anchor = soup.find("a", id=fn_id, class_="footnote-number")
    if not anchor:
        return local_html, "ERROR: anchor not found"

    descs = []
    for _orig, href in empty_links:
        # Re-locate in fresh soup
        parent = anchor.parent
        target_a = next(
            (a for a in parent.find_all("a", href=href)
             if not a.get_text(strip=True)),
            None
        )
        if not target_a:
            continue
        title = resolve_link_title(href, folder)
        target_a.string = title
        descs.append(f'"{title}"')

    return str(soup), f"filled link text: {', '.join(descs)}"

# ── Patch: Type B (truly empty) ───────────────────────────────────────────────

def fix_truly_empty(local_html: str, fn_id: str, content_div_html: str,
                    slug_to_folder: dict, folder: Path) -> tuple[str, str]:
    # Rewrite any Substack URLs to local paths first
    content_div_html = rewrite_substack_urls(content_div_html, slug_to_folder, folder)

    soup = BeautifulSoup(local_html, "html.parser")
    anchor = soup.find("a", id=fn_id, class_="footnote-number")
    if not anchor:
        return local_html, "ERROR: anchor not found"

    # Remove any existing empty siblings
    to_remove = []
    node = anchor.next_sibling
    while node is not None:
        to_remove.append(node)
        node = node.next_sibling
    for node in to_remove:
        node.extract()

    content_soup = BeautifulSoup(content_div_html, "html.parser")
    content_div = content_soup.find("div", class_="footnote-content")
    if not content_div:
        return local_html, "ERROR: could not parse API content"

    anchor.parent.append(content_div)
    text = content_div.get_text(strip=True)[:100]
    return str(soup), f"injected from API: {text}"

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--date", type=str, default=None,
                        help="Only process posts on this date (YYYY-MM-DD)")
    args = parser.parse_args()

    all_posts = fetch_all_posts()
    date_to_folders = build_date_to_folders()
    slug_to_folder = build_slug_to_folder(all_posts, date_to_folders)

    posts_by_date: dict[str, str] = {}
    for post in all_posts:
        date = (post.get("post_date") or "")[:10]
        body = post.get("body_html") or ""
        if date and body:
            posts_by_date[date] = body

    fixed = already_ok = 0
    warnings = []

    for date, folders in sorted(date_to_folders.items()):
        if args.date and date != args.date:
            continue

        body_html = posts_by_date.get(date, "")
        api_footnotes = extract_api_footnotes(body_html) if body_html else {}

        for folder in folders:
            local_index = folder / "index.html"
            if not local_index.exists():
                continue

            local_html = local_index.read_text(encoding="utf-8")
            classified = classify_footnotes(local_html)
            broken = {fid: v for fid, v in classified.items() if v[0] != "ok"}

            if not broken:
                already_ok += 1
                continue

            print(f"\n  [{folder.name}]")
            patched_html = local_html
            patch_count = 0

            for fn_id, (defect_type, extra) in sorted(broken.items()):
                prefix = "[DRY] " if args.dry_run else "FIXED "

                if defect_type == "empty_link":
                    if args.dry_run:
                        _, href = extra[0]
                        title = resolve_link_title(href, folder)
                        desc = f'would fill link text: "{title}"'
                    else:
                        patched_html, desc = fix_empty_link(
                            patched_html, fn_id, extra, folder)
                        patch_count += 1
                    print(f"    {prefix}{fn_id} [empty link]: {desc}")

                elif defect_type == "truly_empty":
                    if fn_id not in api_footnotes:
                        msg = f"{fn_id} truly empty and not in API -- manual fix needed"
                        print(f"    WARNING: {msg}")
                        warnings.append(f"{folder.name}: {msg}")
                        continue
                    if args.dry_run:
                        rewritten = rewrite_substack_urls(
                            api_footnotes[fn_id], slug_to_folder, folder)
                        text = BeautifulSoup(rewritten, "html.parser").get_text(strip=True)[:120]
                        desc = f"would inject (local paths): {text}"
                    else:
                        patched_html, desc = fix_truly_empty(
                            patched_html, fn_id, api_footnotes[fn_id],
                            slug_to_folder, folder)
                        patch_count += 1
                    print(f"    {prefix}{fn_id} [truly empty]: {desc}")

            if not args.dry_run and patch_count > 0:
                local_index.write_text(patched_html, encoding="utf-8")
                print(f"    Wrote {local_index}")
                fixed += 1
            elif args.dry_run and broken:
                fixed += 1

    print(f"\n{'='*60}")
    print(f"  {'Would fix' if args.dry_run else 'Fixed'}:    {fixed} post(s)")
    print(f"  Already OK: {already_ok} post(s)")
    if warnings:
        print(f"\n  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"    - {w}")
    print(f"{'='*60}\n")
    if args.dry_run and fixed > 0:
        print("  Run without --dry-run to apply all fixes.\n")

if __name__ == "__main__":
    main()