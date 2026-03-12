#!/usr/bin/env python3
"""
audit_archive.py -- Full integrity audit of the healing-earth static archive.

Runs entirely from the local filesystem (no browser needed). Produces:
  audit_report.md   -- human-readable report sorted by severity
  audit_report.json -- machine-readable full issue list

Run from repo root:
  python audit_archive.py
  python audit_archive.py --no-external   # skip external URL checks (faster)
  python audit_archive.py --post "2022-10-16_062_Blindspotting (Part 1)"

Issue severity levels:
  ERROR   -- broken: missing file, unresolvable link, footnote with no content
  WARNING -- degraded: empty link text, orphaned anchor, Substack URL remaining
  INFO    -- cosmetic: missing subtitle, missing excerpt

Checks performed
================
INDEX (index.html):
  [I1] Post listed in index has no matching folder in posts/
  [I2] Folder in posts/ not listed in index
  [I3] Listed post has no thumbnail img src
  [I4] Listed post thumbnail src points to non-existent file
  [I5] Listed post has no excerpt text

PER POST (posts/*/index.html):
  [P1] index.html missing entirely
  [P2] Relative link (../) points to folder that does not exist
  [P3] Relative link (../) has empty link text
  [P4] Local image src (./images/ or ../../images/) points to non-existent file
  [P5] Footnote anchor (#footnote-N) has no matching definition (footnote-number anchor)
  [P6] Footnote definition has no matching in-body anchor
  [P7] Footnote definition exists but has no visible text content
  [P8] Any link still pointing to substack.com or open.substack.com
  [P9] Post has no <h1> title
  [P10] Post has no .post-meta date
"""

import argparse
import json
import re
import time
from collections import defaultdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

REPO_ROOT  = Path(".")
POSTS_DIR  = REPO_ROOT / "posts"
INDEX_HTML = REPO_ROOT / "index.html"
SUBSTACK_API = "https://healingearth.substack.com/api/v1/posts"

SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}


# ── Utilities ─────────────────────────────────────────────────────────────────

def soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def issue(severity: str, code: str, context: str, detail: str) -> dict:
    return {"severity": severity, "code": code, "context": context, "detail": detail}


def visible_text(tag) -> str:
    return tag.get_text(strip=True) if tag else ""


# ── INDEX checks ──────────────────────────────────────────────────────────────

def audit_index(issues: list) -> tuple[list, set]:
    """
    Returns (issues, set_of_listed_folder_names).
    """
    if not INDEX_HTML.exists():
        issues.append(issue("ERROR", "I0", "index.html", "index.html not found at repo root"))
        return issues, set()

    s = soup(INDEX_HTML)
    listed_folders = set()

    for li in s.find_all("li", attrs={"data-folder": True}):
        folder_name = li["data-folder"]
        listed_folders.add(folder_name)
        folder_path = POSTS_DIR / folder_name

        # I1: folder missing
        if not folder_path.is_dir():
            issues.append(issue("ERROR", "I1", f"index > {folder_name}",
                                "Listed in index but posts/ folder does not exist"))
            continue

        # I3/I4: thumbnail
        thumb_img = li.select_one("a.post-thumb img")
        if not thumb_img:
            issues.append(issue("WARNING", "I3", f"index > {folder_name}",
                                "No thumbnail <img> in post list item"))
        else:
            src = thumb_img.get("src", "")
            if src:
                # src is relative to repo root (e.g. "posts/folder/images/file.png")
                img_path = REPO_ROOT / src
                if not img_path.exists():
                    issues.append(issue("ERROR", "I4", f"index > {folder_name}",
                                        f"Thumbnail src not found on disk: {src}"))
            else:
                issues.append(issue("WARNING", "I3", f"index > {folder_name}",
                                    "Thumbnail <img> has empty src"))

        # I5: excerpt
        excerpt = li.select_one("p.post-list-excerpt")
        if not excerpt or not visible_text(excerpt):
            issues.append(issue("INFO", "I5", f"index > {folder_name}",
                                "No excerpt text in post list item"))

    # I2: folders not listed in index
    for folder_path in sorted(POSTS_DIR.iterdir()):
        if not folder_path.is_dir():
            continue
        if folder_path.name not in listed_folders:
            issues.append(issue("WARNING", "I2", f"posts/{folder_path.name}",
                                "Folder exists in posts/ but is not listed in index"))

    return issues, listed_folders


# ── PER-POST checks ───────────────────────────────────────────────────────────

def audit_post(folder: Path, issues: list, check_external: bool) -> None:
    ctx = folder.name
    index = folder / "index.html"

    # P1: index.html missing
    if not index.exists():
        issues.append(issue("ERROR", "P1", ctx, "index.html missing from post folder"))
        return

    s = soup(index)

    # P9: no <h1>
    h1 = s.find("h1", class_="post-title")
    if not h1 or not visible_text(h1):
        issues.append(issue("WARNING", "P9", ctx, "No <h1 class='post-title'> found"))

    # P10: no date
    meta = s.find(class_="post-meta")
    if not meta or not visible_text(meta):
        issues.append(issue("INFO", "P10", ctx, "No .post-meta date element found"))

    # ── Links ─────────────────────────────────────────────────────────────────
    for a in s.find_all("a", href=True):
        href = a.get("href", "")
        link_text = visible_text(a)

        # Skip: fragment-only, root-relative (site nav), mailto, javascript
        if (href.startswith("#")
                or href.startswith("/")
                or href.startswith("mailto:")
                or href.startswith("javascript:")):
            continue

        # P2 + P3: relative cross-post links (../)
        # Exclude site-asset relative links (../../images/, ../../style.css, etc.)
        if href.startswith("../"):
            # If the link goes above the posts/ directory it's a site asset, not a post link
            resolved = (folder / href).resolve()
            try:
                resolved.relative_to(POSTS_DIR.resolve())
                is_post_link = True
            except ValueError:
                is_post_link = False

            if not is_post_link:
                continue  # site asset (wordmark, style.css, favicon) -- skip

            target_folder = resolved.parent if resolved.name == "index.html" else resolved

            if not target_folder.is_dir():
                issues.append(issue("ERROR", "P2", ctx,
                                    f"Broken relative link -> {href}"))
            elif not (target_folder / "index.html").exists():
                issues.append(issue("ERROR", "P2", ctx,
                                    f"Target folder exists but has no index.html -> {href}"))

            if not link_text:
                issues.append(issue("WARNING", "P3", ctx,
                                    f"Empty link text on relative link -> {href}"))

        # P8: remaining healingearth.substack.com post URLs (not yet rewritten to local)
        # Only flag THIS newsletter's URLs -- external Substack newsletters are legitimate
        elif "substack.com" in href:
            is_this_newsletter = (
                "healingearth.substack.com" in href
                or "pub/healingearth" in href
            )
            if is_this_newsletter and ("/p/" in href or "pub/healingearth" in href):
                issues.append(issue("WARNING", "P8", ctx,
                                    f"Healingearth Substack URL not rewritten to local: {href[:100]}"))

    # ── Images ────────────────────────────────────────────────────────────────
    for img in s.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("http"):
            continue
        # Resolve relative to post folder
        img_path = (folder / src).resolve()
        if not img_path.exists():
            issues.append(issue("ERROR", "P4", ctx,
                                f"Image src not found on disk: {src}"))

    # ── Footnotes ─────────────────────────────────────────────────────────────

    # Collect in-body anchors: <a class="footnote-anchor" href="#footnote-N">
    body_anchors = {}  # N -> element
    for a in s.find_all("a", class_="footnote-anchor", href=True):
        href = a.get("href", "")
        m = re.match(r"#footnote-(\d+)$", href)
        if m:
            body_anchors[m.group(1)] = a

    # Collect definitions: <a class="footnote-number" id="footnote-N">
    fn_defs = {}  # N -> element
    for a in s.find_all("a", class_="footnote-number", id=True):
        m = re.match(r"footnote-(\d+)$", a.get("id", ""))
        if m:
            fn_defs[m.group(1)] = a

    # P5: anchor with no definition
    for n in sorted(body_anchors.keys(), key=int):
        if n not in fn_defs:
            issues.append(issue("ERROR", "P5", ctx,
                                f"footnote-anchor-{n} in body but no footnote-{n} definition"))

    # P6: definition with no body anchor
    for n in sorted(fn_defs.keys(), key=int):
        if n not in body_anchors:
            issues.append(issue("WARNING", "P6", ctx,
                                f"footnote-{n} definition exists but no footnote-anchor-{n} in body"))

    # P7: definition has no visible text content
    for n, def_anchor in sorted(fn_defs.items(), key=lambda x: int(x[0])):
        parent = def_anchor.parent
        # Collect text from siblings after the anchor
        sibling_text = ""
        node = def_anchor.next_sibling
        while node is not None:
            if isinstance(node, Tag):
                sibling_text += node.get_text()
            elif isinstance(node, NavigableString):
                sibling_text += str(node)
            node = node.next_sibling
        if not sibling_text.strip():
            issues.append(issue("ERROR", "P7", ctx,
                                f"footnote-{n} definition has no visible text content"))


# ── Substack cross-check ──────────────────────────────────────────────────────

def fetch_substack_posts() -> list:
    posts, offset = [], 0
    print("  Fetching Substack API...", end="", flush=True)
    try:
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
    except Exception as e:
        print(f" -- FAILED: {e}")
    return posts


def audit_substack_coverage(issues: list, listed_folders: set) -> None:
    """
    Check that every Substack post has a corresponding local folder,
    matched by post_date prefix.
    """
    posts = fetch_substack_posts()
    if not posts:
        return

    # Build date -> folders map
    date_to_folders = defaultdict(list)
    for folder in POSTS_DIR.iterdir():
        if not folder.is_dir():
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})", folder.name)
        if m:
            date_to_folders[m.group(1)].append(folder.name)

    for post in posts:
        date = (post.get("post_date") or "")[:10]
        title = post.get("title", "?")
        slug = post.get("slug", "?")

        # Skip rerun posts -- Substack republished issues 1-74 as a daily burst
        # in early 2024. Most end in "-rerun" but three do not; all share the
        # same date range (Jan-May 2024) and numbered-title slug pattern.
        if slug.endswith("-rerun"):
            continue
        if re.match(r"^\d+[-]", slug) and date and "2024-01" <= date <= "2024-05-31":
            continue  # numbered rerun without -rerun suffix

        # Skip posts that announce or describe the archive but are not archive content
        EXCLUDED_SLUGS = {"four-years-182-issues-and-a-new-home"}
        if slug in EXCLUDED_SLUGS:
            continue

        if date and date not in date_to_folders:
            issues.append(issue("WARNING", "S1", f"Substack:{slug}",
                                f"Substack post '{title}' ({date}) has no matching local folder"))


# ── Report generation ─────────────────────────────────────────────────────────

def generate_report(issues: list) -> str:
    by_severity = defaultdict(list)
    for iss in issues:
        by_severity[iss["severity"]].append(iss)

    counts = {s: len(by_severity[s]) for s in ["ERROR", "WARNING", "INFO"]}
    total = sum(counts.values())

    lines = [
        "# Healing Earth Archive — Integrity Audit Report",
        "",
        f"**Total issues: {total}** "
        f"({counts['ERROR']} errors, {counts['WARNING']} warnings, {counts['INFO']} info)",
        "",
    ]

    # Group by code within each severity
    for severity in ["ERROR", "WARNING", "INFO"]:
        sev_issues = by_severity.get(severity, [])
        if not sev_issues:
            continue
        lines.append(f"## {severity} ({len(sev_issues)})")
        lines.append("")

        by_code = defaultdict(list)
        for iss in sev_issues:
            by_code[iss["code"]].append(iss)

        for code in sorted(by_code.keys()):
            code_issues = by_code[code]
            lines.append(f"### [{code}] — {len(code_issues)} occurrence(s)")
            lines.append("")
            for iss in code_issues:
                lines.append(f"- **{iss['context']}**: {iss['detail']}")
            lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-external", action="store_true",
                        help="Skip Substack API cross-check")
    parser.add_argument("--post", type=str, default=None,
                        help="Audit only this post folder name")
    args = parser.parse_args()

    print("\nHealing Earth Archive Audit")
    print("=" * 50)

    issues = []

    # Index audit
    print("\n[1/3] Auditing index.html...")
    issues, listed_folders = audit_index(issues)
    print(f"      {len(listed_folders)} posts listed in index")

    # Per-post audit
    print("\n[2/3] Auditing post files...")
    post_folders = sorted(POSTS_DIR.iterdir())
    for i, folder in enumerate(post_folders):
        if not folder.is_dir():
            continue
        if args.post and folder.name != args.post:
            continue
        print(f"      [{i+1}/{len(post_folders)}] {folder.name[:65]}", end="\r")
        audit_post(folder, issues, check_external=not args.no_external)
    print(f"      Done. {len(post_folders)} folders checked.        ")

    # Substack cross-check
    if not args.no_external and not args.post:
        print("\n[3/3] Cross-checking against Substack API...")
        audit_substack_coverage(issues, listed_folders)
    else:
        print("\n[3/3] Skipping Substack API cross-check")

    # Sort issues: ERROR first, then WARNING, then INFO; within each by context
    issues.sort(key=lambda x: (SEVERITY_ORDER[x["severity"]], x["context"], x["code"]))

    # Write JSON
    json_path = REPO_ROOT / "audit_report.json"
    json_path.write_text(json.dumps(issues, indent=2), encoding="utf-8")

    # Write Markdown
    md_path = REPO_ROOT / "audit_report.md"
    md_path.write_text(generate_report(issues), encoding="utf-8")

    # Print summary
    counts = defaultdict(int)
    for iss in issues:
        counts[iss["severity"]] += 1

    print(f"\n{'='*50}")
    print(f"  ERRORS:   {counts['ERROR']}")
    print(f"  WARNINGS: {counts['WARNING']}")
    print(f"  INFO:     {counts['INFO']}")
    print(f"  TOTAL:    {sum(counts.values())}")
    print(f"{'='*50}")
    print(f"\n  audit_report.md   -- human-readable")
    print(f"  audit_report.json -- machine-readable")
    print()


if __name__ == "__main__":
    main()