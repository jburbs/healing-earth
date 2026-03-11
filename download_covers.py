#!/usr/bin/env python3
"""
download_covers.py
==================
Downloads missing cover images for the Healing Earth archive.

Fetches all Substack posts, finds the ones whose cover image UUID is not
already present locally, and downloads them into the correct location:
  posts/<folder>/images/<uuid>_<WxH>.<ext>

Skips:
  - YouTube thumbnails (substackcdn.com/image/youtube/...)
  - Unsplash URLs
  - Posts with no local folder

Usage:
    python download_covers.py           # download all missing
    python download_covers.py --dry-run # show what would be downloaded
"""

from __future__ import annotations

import os
import re
import sys
import time
import argparse
import requests
from pathlib import Path
from urllib.parse import unquote

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT    = Path(".")
POSTS_DIR    = REPO_ROOT / "posts"
SUBSTACK_API = "https://healingearth.substack.com/api/v1/posts"

# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_all_posts():
    posts = []
    offset = 0
    print("Fetching Substack posts...", end="", flush=True)
    while True:
        r = requests.get(SUBSTACK_API, params={"limit": 50, "offset": offset, "sort": "new"}, timeout=15)
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
    print(f" — done ({len(posts)} total)")
    return posts


def folder_date(name: str) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else ""


def extract_uuid(url: str) -> str:
    """Extract S3 image UUID from direct or CDN-proxied Substack URL."""
    m = re.search(
        r'(?:/images/|%2Fimages%2F)([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})_',
        url, re.IGNORECASE
    )
    return m.group(1) if m else ""


def extract_filename_from_url(url: str) -> str:
    """
    Get the filename (uuid_WxH.ext) from the URL.
    For CDN proxy URLs, decode the inner S3 path.
    """
    # CDN proxy: extract the encoded inner URL
    inner_match = re.search(r'https?%3A%2F%2F.+?(%2Fpublic%2Fimages%2F[^&"\']+)', url, re.IGNORECASE)
    if inner_match:
        path = unquote(inner_match.group(1))  # e.g. /public/images/uuid_WxH.png
        return Path(path).name

    # Direct S3 URL: just take the filename
    clean = url.split("?")[0]
    return Path(clean).name


def resolve_download_url(cover_url: str) -> str | None:
    """
    Return the best URL to actually download the image from.
    For CDN proxy URLs, extract and use the direct S3 URL.
    Skip YouTube and Unsplash.
    """
    if not cover_url:
        return None
    if "youtube" in cover_url:
        return None
    if "unsplash.com" in cover_url:
        return None

    # CDN proxy — extract the inner S3 URL
    inner_match = re.search(
        r'https?%3A%2F%2F((?:substack-post-media|bucketeer-[a-z0-9\-]+)\.s3\.amazonaws\.com%2F[^&"\']+)',
        cover_url, re.IGNORECASE
    )
    if inner_match:
        return "https://" + unquote(inner_match.group(1))

    # Bucketeer direct S3 URL — must proxy through Substack CDN
    if "bucketeer-e05bbc84" in cover_url and "s3.amazonaws.com" in cover_url:
        from urllib.parse import quote
        encoded = quote(cover_url, safe="")
        return f"https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/{encoded}"

    # Already a direct substack-post-media S3 URL (these work fine directly)
    if "substack-post-media.s3.amazonaws.com" in cover_url:
        return cover_url

    # Fallback: try downloading the CDN URL as-is
    return cover_url


def find_local_cover(folder: str, uuid: str) -> bool:
    """Return True if a file starting with uuid exists in posts/folder/images/."""
    if not uuid:
        return False
    images_dir = POSTS_DIR / folder / "images"
    if not images_dir.is_dir():
        return False
    return any(f.name.startswith(uuid) for f in images_dir.iterdir())


def find_folder_for_date(date: str) -> list[str]:
    """Return all post folder names matching a given YYYY-MM-DD date."""
    results = []
    if not POSTS_DIR.is_dir():
        return results
    for d in POSTS_DIR.iterdir():
        if d.is_dir() and folder_date(d.name) == date:
            results.append(d.name)
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Download missing Healing Earth cover images")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without downloading")
    args = parser.parse_args()

    posts = fetch_all_posts()

    to_download = []   # list of (folder, filename, download_url, cover_url)
    skipped_youtube = []
    skipped_unsplash = []
    skipped_no_folder = []

    for p in posts:
        cover_url = p.get("cover_image") or ""
        if not cover_url:
            continue

        date = (p.get("post_date") or "")[:10]
        if not date:
            continue

        # Skip non-image covers
        if "youtube" in cover_url:
            skipped_youtube.append((date, p.get("title", "")))
            continue
        if "unsplash.com" in cover_url:
            skipped_unsplash.append((date, p.get("title", "")))
            continue

        uuid = extract_uuid(cover_url)
        if not uuid:
            continue

        folders = find_folder_for_date(date)
        if not folders:
            skipped_no_folder.append((date, p.get("title", ""), uuid))
            continue

        for folder in folders:
            if find_local_cover(folder, uuid):
                continue  # already have it

            download_url = resolve_download_url(cover_url)
            if not download_url:
                continue

            filename = extract_filename_from_url(cover_url)
            if not filename or filename == ".":
                # Fallback: construct from UUID + extension guess
                ext = "png" if cover_url.endswith(".png") else "jpeg" if "jpeg" in cover_url else "png"
                filename = f"{uuid}_976x511.{ext}"

            to_download.append((folder, filename, download_url, cover_url))

    print(f"\n── Download plan ────────────────────────────────")
    print(f"  To download   : {len(to_download)}")
    print(f"  Skip YouTube  : {len(skipped_youtube)}")
    print(f"  Skip Unsplash : {len(skipped_unsplash)}")
    print(f"  No local folder: {len(skipped_no_folder)}")

    if skipped_no_folder:
        print("\n  Posts with no local folder (not in archive):")
        for date, title, uuid in skipped_no_folder[:5]:
            print(f"    {date} — {title[:60]}")
        if len(skipped_no_folder) > 5:
            print(f"    ...and {len(skipped_no_folder) - 5} more")

    if args.dry_run:
        print(f"\n[DRY RUN — would download {len(to_download)} images]\n")
        for folder, filename, dl_url, _ in to_download:
            print(f"  {folder[:60]}")
            print(f"    → images/{filename}")
        return

    print()
    downloaded = 0
    failed = []

    for folder, filename, download_url, original_url in to_download:
        images_dir = POSTS_DIR / folder / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        dest = images_dir / filename

        print(f"  ↓ {folder[:55]}", end=" ", flush=True)
        try:
            r = requests.get(download_url, timeout=20, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://healingearth.substack.com/",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            })
            r.raise_for_status()
            dest.write_bytes(r.content)
            size_kb = len(r.content) // 1024
            print(f"✓ ({size_kb}KB)")
            downloaded += 1
        except Exception as e:
            print(f"✗ {e}")
            failed.append((folder, download_url, str(e)))
        time.sleep(0.2)

    print(f"\n── Result ───────────────────────────────────────")
    print(f"  Downloaded : {downloaded}")
    print(f"  Failed     : {len(failed)}")
    if failed:
        print("\n  Failed downloads:")
        for folder, url, err in failed:
            print(f"    {folder[:55]}")
            print(f"      {err}")
        print("\n  You can retry failed ones manually using the URLs")
        print("  printed by: python update_archive.py --dry-run")

    print("\nDone. Re-run update_archive.py to pick up the new images.")


if __name__ == "__main__":
    main()