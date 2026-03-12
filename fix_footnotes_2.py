#!/usr/bin/env python3
"""
fix_footnotes.py -- Fix broken footnote content in archived posts.

TWO DEFECT TYPES
================

TYPE A -- Empty cross-reference link (most common):
  The footnote contains a local archive link (<a href="../folder/index.html">)
  but the link text is empty, so it renders as an invisible blank link.

  Local HTML:
    <div>
      <a class="footnote-number" id="footnote-N">N</a>
      <p><a href="../2022-02-13_000_Post Title/index.html" title="Local archive link"></a></p>
    </div>

  Fix: extract the post title from the linked folder name (or its <h1>), set
  it as the link text. Stays 100% local -- no API call needed.

TYPE B -- Truly empty footnote (no sibling content at all):
  The footnote number anchor has nothing after it.

  Local HTML:
    <div>
      <a class="footnote-number" id="footnote-N">N</a>
      [nothing]
    </div>

  Fix: fetch .footnote-content from the Substack API body_html and inject it.
  The API uses:
    <div class="footnote" data-component-name="FootnoteToDOM">
      <a id="footnote-N" class="footnote-number">N</a>
      <div class="footnote-content"><p>...</p></div>
    </div>

MATCHING
Posts are matched by post_date (YYYY-MM-DD prefix of folder name).
Substack slugs evolved over time and don't match local folder names reliably.

Usage:
    python fix_footnotes.py --dry-run          # show all changes, write nothing
    python fix_footnotes.py                    # apply all fixes
    python fix_footnotes.py --date 2022-10-16  # one date only
"""

import argparse
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT    = Path(".")
POSTS_DIR    = REPO_ROOT / "posts"
SUBSTACK_API = "https://healingearth.substack.com/api/v1/posts"

# ── Fetch Substack API ────────────────────────────────────────────────────────

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


# ── Title extraction from local folder ───────────────────────────────────────

def title_from_folder_name(folder_name: str) -> str:
    """
    Extract a human-readable title from a folder name like:
      2022-02-13_000_A second pseudo-political diversion
    Returns: "A second pseudo-political diversion"
    """
    # Strip date and sequence prefix
    m = re.match(r"^\d{4}-\d{2}-\d{2}_\d+_(.*)", folder_name)
    return m.group(1).strip() if m else folder_name


def title_from_index(index_path: Path) -> str | None:
    """Read <h1> or <title> from a post's index.html."""
    if not index_path.exists():
        return None
    html = index_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title = soup.find("title")
    if title:
        # Strip " - Healing Earth with Technology" suffix
        t = title.get_text(strip=True)
        return re.sub(r"\s*-\s*Healing Earth.*$", "", t).strip()
    return None


def resolve_link_title(href: str, current_folder: Path) -> str:
    """
    Given a relative href like ../2022-02-13_000_Post Title/index.html,
    return the best available title string.
    """
    # Resolve the target folder
    target = (current_folder / href).resolve()
    target_folder = target.parent if target.name == "index.html" else target

    # Try reading title from the linked index.html
    linked_index = target_folder / "index.html"
    title = title_from_index(linked_index)
    if title:
        return title

    # Fallback: parse from folder name
    return title_from_folder_name(target_folder.name)


# ── Defect detection ──────────────────────────────────────────────────────────

def classify_footnotes(local_html: str, folder: Path) -> dict:
    """
    Walk every footnote-number anchor and classify each as:
      "ok"         -- has real visible text content after it
      "empty_link" -- has a local archive <a> with empty link text (Type A)
      "truly_empty" -- has no sibling content at all (Type B)

    Returns: { "footnote-1": ("ok"|"empty_link"|"truly_empty", extra_info), ... }
    """
    soup = BeautifulSoup(local_html, "html.parser")
    results = {}

    for anchor in soup.find_all("a", id=re.compile(r'^footnote-\d+$'),
                                 class_="footnote-number"):
        fn_id = anchor["id"]

        # Collect siblings after the anchor
        siblings = []
        node = anchor.next_sibling
        while node is not None:
            siblings.append(node)
            node = node.next_sibling

        # Get all visible text from siblings
        sibling_text = "".join(
            n.get_text() if isinstance(n, Tag) else str(n)
            for n in siblings
        ).strip()

        if not sibling_text:
            # Type B: truly empty
            results[fn_id] = ("truly_empty", None)
            continue

        # Check for empty local archive links (Type A)
        empty_local_links = []
        for sib in siblings:
            if not isinstance(sib, Tag):
                continue
            for a in (sib.find_all("a", href=True) if sib.name != "a" else [sib]):
                href = a.get("href", "")
                link_text = a.get_text(strip=True)
                is_local = href.startswith("../") or href.startswith("./")
                if is_local and not link_text:
                    empty_local_links.append((a, href))

        if empty_local_links:
            results[fn_id] = ("empty_link", empty_local_links)
        else:
            results[fn_id] = ("ok", None)

    return results


# ── API footnote extraction ───────────────────────────────────────────────────

def extract_api_footnotes(body_html: str) -> dict:
    """
    { "footnote-1": "<div class='footnote-content'>...</div>", ... }
    from Substack body_html.
    """
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


# ── Patching ──────────────────────────────────────────────────────────────────

def fix_empty_link(local_html: str, fn_id: str,
                   empty_links: list, folder: Path) -> tuple[str, str]:
    """
    Type A fix: fill in empty link text for local archive cross-references.
    Returns (patched_html, description).
    """
    soup = BeautifulSoup(local_html, "html.parser")
    anchor = soup.find("a", id=fn_id, class_="footnote-number")
    if not anchor:
        return local_html, "ERROR: anchor not found"

    descriptions = []
    for _orig_tag, href in empty_links:
        # Re-find the tag in the new soup (soup was re-parsed)
        parent = anchor.parent
        target_a = None
        for a in parent.find_all("a", href=True):
            if a.get("href") == href and not a.get_text(strip=True):
                target_a = a
                break
        if not target_a:
            continue

        title = resolve_link_title(href, folder)
        target_a.string = title
        descriptions.append(f'"{title}"')

    return str(soup), f"filled link text: {', '.join(descriptions)}"


def fix_truly_empty(local_html: str, fn_id: str, content_div_html: str) -> tuple[str, str]:
    """
    Type B fix: inject .footnote-content from API after the number anchor.
    Returns (patched_html, description).
    """
    soup = BeautifulSoup(local_html, "html.parser")
    anchor = soup.find("a", id=fn_id, class_="footnote-number")
    if not anchor:
        return local_html, "ERROR: anchor not found"

    # Remove any (empty) sibling content
    to_remove = []
    node = anchor.next_sibling
    while node is not None:
        to_remove.append(node)
        node = node.next_sibling
    for node in to_remove:
        node.extract()

    # Parse and inject API content
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
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing files")
    parser.add_argument("--date", type=str, default=None,
                        help="Only process posts on this date (YYYY-MM-DD)")
    args = parser.parse_args()

    # Always fetch API (needed for Type B; cheap for Type A-only posts)
    posts_by_date: dict[str, str] = {}  # date -> body_html
    for post in fetch_all_posts():
        date = (post.get("post_date") or "")[:10]
        body = post.get("body_html") or ""
        if date and body:
            posts_by_date[date] = body  # last post wins if same date (rare)

    date_to_folders = build_date_to_folders()

    fixed = already_ok = no_local = 0
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
            classified = classify_footnotes(local_html, folder)

            broken = {fid: info for fid, info in classified.items()
                      if info[0] != "ok"}

            if not broken:
                already_ok += 1
                continue

            print(f"\n  [{folder.name}]")
            patched_html = local_html
            patch_count = 0

            for fn_id, (defect_type, extra) in sorted(broken.items()):
                prefix = "[DRY] " if args.dry_run else "FIXED "

                if defect_type == "empty_link":
                    if not args.dry_run:
                        patched_html, desc = fix_empty_link(
                            patched_html, fn_id, extra, folder)
                        patch_count += 1
                    else:
                        # Dry run: compute title without patching
                        _, href = extra[0]
                        title = resolve_link_title(href, folder)
                        desc = f'would fill link text: "{title}"'
                    print(f"    {prefix}{fn_id} [empty link]: {desc}")

                elif defect_type == "truly_empty":
                    if fn_id not in api_footnotes:
                        msg = f"{fn_id} truly empty but not in API -- needs manual fix"
                        print(f"    WARNING: {msg}")
                        warnings.append(f"{folder.name}: {msg}")
                        continue
                    if not args.dry_run:
                        patched_html, desc = fix_truly_empty(
                            patched_html, fn_id, api_footnotes[fn_id])
                        patch_count += 1
                    else:
                        content = BeautifulSoup(
                            api_footnotes[fn_id], "html.parser").get_text(strip=True)[:100]
                        desc = f"would inject from API: {content}"
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