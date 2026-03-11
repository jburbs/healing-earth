#!/usr/bin/env python3
"""
pick_covers.py — interactively select body images as cover replacements
for posts that currently have the generic globe-logo thumbnail.

Usage:
    python pick_covers.py [--dry-run] [--no-browser]

Workflow:
    - Scans all post folders for covers that are the generic globe logo
      (detected by UUID prefix 93adbdcf OR cover_976x511.* placeholder)
    - For each such post, opens a browser preview showing all body images
      side by side with numbered labels
    - You type a number to select, 's' to skip, 'q' to quit
    - Saves choices to manual_covers.json incrementally (resume-safe)

After running, execute:
    python update_archive.py
to apply the new covers to index.html.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 not installed. Run: pip install beautifulsoup4")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent
POSTS_DIR = REPO_ROOT / "posts"
MANUAL_COVERS_FILE = REPO_ROOT / "manual_covers.json"

# Known generic globe UUID prefixes
GLOBE_UUIDS = {"93adbdcf"}

# Exact byte size of the globe logo PNG (976x511 version downloaded by download_covers.py)
GLOBE_EXACT_SIZE = 151_378

# Fallback: if it's the ONLY image and under this size, also treat as globe
GLOBE_SIZE_THRESHOLD = 50_000

PREVIEW_HTML = Path(tempfile.gettempdir()) / "pick_covers_preview.html"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_manual_covers() -> dict:
    if MANUAL_COVERS_FILE.exists():
        try:
            data = json.loads(MANUAL_COVERS_FILE.read_text(encoding="utf-8"))
            return {k: v for k, v in data.items() if not k.startswith("_")}
        except json.JSONDecodeError as e:
            print(f"WARNING: Could not parse {MANUAL_COVERS_FILE}: {e}")
    return {}


def save_manual_covers(new_entry: dict):
    existing = {}
    if MANUAL_COVERS_FILE.exists():
        try:
            existing = json.loads(MANUAL_COVERS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    existing.update(new_entry)
    MANUAL_COVERS_FILE.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def is_globe_file(f: Path) -> bool:
    """Return True if this image file is the generic globe logo."""
    size = f.stat().st_size
    # Confirmed exact byte size from live site scan
    if size == GLOBE_EXACT_SIZE:
        return True
    # Known globe UUID prefix
    for uuid in GLOBE_UUIDS:
        if f.name.lower().startswith(uuid):
            return True
    # Named placeholder
    if f.stem == "cover_976x511":
        return True
    # Single tiny file fallback
    if size < GLOBE_SIZE_THRESHOLD:
        return True
    return False


def get_cover_file(folder: Path):
    """Return the file used as the cover image (the 976x511 one), or None."""
    images_dir = folder / "images"
    if not images_dir.is_dir():
        return None
    # Prefer 976x511 in filename, else largest file
    image_files = [
        f for f in images_dir.iterdir()
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif")
    ]
    if not image_files:
        return None
    for f in image_files:
        if "976x511" in f.name:
            return f
    return max(image_files, key=lambda f: f.stat().st_size)


def is_globe_cover(folder: Path) -> bool:
    """Return True if the post's cover image is the generic globe logo."""
    cover = get_cover_file(folder)
    if cover is None:
        return False
    return is_globe_file(cover)


def get_body_images(folder: Path) -> list:
    post_html = folder / "index.html"
    if not post_html.exists():
        return []
    soup = BeautifulSoup(post_html.read_text(encoding="utf-8"), "html.parser")
    content = (
        soup.find(class_="post-content")
        or soup.find("article")
        or soup.body
    )
    if not content:
        return []

    results = []
    seen = set()
    for img in content.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("data:") or src.startswith("http"):
            continue
        img_path = (folder / src).resolve()
        if not img_path.exists() or img_path in seen:
            continue
        seen.add(img_path)
        w, h = 0, 0
        m = re.search(r"_(\d+)x(\d+)", img_path.stem)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
        results.append({
            "path": img_path,
            "filename": img_path.name,
            "width": w,
            "height": h,
            "size": img_path.stat().st_size,
        })
    return results


def render_preview(folder_name: str, images: list, globe_file=None) -> Path:
    items = ""
    if globe_file:
        size_kb = globe_file.stat().st_size // 1024
        items += f"""
        <div class="card" style="border:2px solid #555">
          <div class="num" style="color:#888">[0] KEEP GLOBE</div>
          <img class="thumb" src="file://{globe_file}" alt="globe">
          <img class="full"  src="file://{globe_file}" alt="globe full">
          <div class="label">{globe_file.name} &nbsp; {size_kb} KB</div>
        </div>"""
    for i, img in enumerate(images, 1):
        dims = f"{img['width']}x{img['height']}" if img["width"] else "?"
        size_kb = img["size"] // 1024
        items += f"""
        <div class="card">
          <div class="num">[{i}]</div>
          <div class="sublabel">AS THUMBNAIL (120x80, center crop)</div>
          <img class="thumb" src="file://{img['path']}" alt="{img['filename']}">
          <div class="sublabel" style="margin-top:10px">FULL IMAGE</div>
          <img class="full"  src="file://{img['path']}" alt="{img['filename']} full">
          <div class="label">{img['filename']}<br><small>{dims} &nbsp; {size_kb} KB</small></div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{folder_name}</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #111; color: #eee;
         margin: 0; padding: 20px; }}
  h2 {{ font-size: 13px; color: #888; margin: 0 0 16px; word-break: break-all; }}
  .grid {{ display: flex; flex-wrap: wrap; gap: 20px; }}
  .card {{ background: #222; border-radius: 10px; padding: 12px;
           width: 380px; box-shadow: 0 2px 8px #0006; }}
  .thumb {{ width: 360px; height: 240px; object-fit: cover; object-position: 50% 50%;
              border-radius: 6px; display: block; }}
  .full  {{ width: 360px; height: auto; max-height: 300px; object-fit: contain;
              border-radius: 6px; display: block; background: #1a1a1a; margin-top: 8px; }}
  .num {{ font-size: 32px; font-weight: 700; color: #f90; margin-bottom: 8px; }}
  .label {{ font-size: 11px; color: #bbb; margin-top: 8px; word-break: break-all; }}
  small {{ color: #666; }}
  .sublabel {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin: 6px 0 4px; }}
</style>
</head>
<body>
<h2>{folder_name}</h2>
<div class="grid">{items}</div>
</body>
</html>"""
    PREVIEW_HTML.write_text(html, encoding="utf-8")
    return PREVIEW_HTML


def open_browser(path: Path):
    url = f"file://{path}"
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            import webbrowser
            webbrowser.open(url)
    except Exception as e:
        print(f"  (browser open failed: {e})")


def copy_as_cover(src_path: Path, folder: Path) -> str:
    images_dir = folder / "images"
    images_dir.mkdir(exist_ok=True)
    dest_name = f"cover_picked{src_path.suffix.lower()}"
    dest = images_dir / dest_name
    if src_path.resolve() != dest.resolve():
        shutil.copy2(src_path, dest)
    return dest_name


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-browser", action="store_true",
                        help="Skip browser preview (terminal only)")
    args = parser.parse_args()

    manual_covers = load_manual_covers()

    candidates = []
    for folder in sorted(POSTS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name in manual_covers:
            continue
        if is_globe_cover(folder):
            candidates.append(folder)

    total = len(candidates)
    if total == 0:
        print("Nothing to do.")
        return

    print(f"\n{'='*60}")
    print(f"  pick_covers.py  --  {total} posts to review")
    print(f"{'='*60}")
    print("  Commands:  <number> select    s skip    q quit\n")

    picked = skipped = no_images = 0

    for i, folder in enumerate(candidates, 1):
        body_images = get_body_images(folder)
        print(f"\n[{i}/{total}] {folder.name}")

        if not body_images:
            print("  (no body images found -- skipping)")
            no_images += 1
            continue

        # Build option list: [0] = keep globe, [1..n] = body images
        # Auto-select if there's only one body image (skip globe option)
        if len(body_images) == 1:
            chosen = body_images[0]
            dims = f"{chosen['width']}x{chosen['height']}" if chosen["width"] else "?"
            if not args.dry_run:
                dest = copy_as_cover(chosen["path"], folder)
                save_manual_covers({folder.name: dest})
                print(f"  Auto-selected: {chosen['filename']} ({dims}) -> images/{dest}")
            else:
                print(f"  [dry-run] auto-select: {chosen['filename']} ({dims})")
            picked += 1
            continue

        # Multiple options -- show browser preview and prompt
        # Get the current globe cover file to show as option [0]
        globe_option = get_cover_file(folder)

        all_options = body_images[:]  # options [1..n]

        if not args.no_browser:
            render_preview(folder.name, all_options, globe_option)
            open_browser(PREVIEW_HTML)
            time.sleep(0.3)

        if globe_option:
            print(f"  [0] KEEP GLOBE  ({globe_option.name})")
        for j, img in enumerate(all_options, 1):
            dims = f"{img['width']}x{img['height']}" if img["width"] else "?"
            print(f"  [{j}] {img['filename']}  ({dims}, {img['size']//1024}KB)")

        while True:
            try:
                raw = input("  > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(f"\nInterrupted. picked={picked} skipped={skipped} no_images={no_images}")
                return

            if raw == "q":
                print(f"\nDone. picked={picked} skipped={skipped} no_images={no_images}")
                return
            if raw == "s":
                skipped += 1
                break
            try:
                n = int(raw)
                if n == 0 and globe_option:
                    # Keep the globe -- record it in manual_covers so we skip next time
                    if not args.dry_run:
                        save_manual_covers({folder.name: globe_option.name})
                        print(f"  Kept globe: {globe_option.name}")
                    else:
                        print(f"  [dry-run] would keep globe: {globe_option.name}")
                    picked += 1
                    break
                elif 1 <= n <= len(all_options):
                    chosen = all_options[n - 1]
                    if not args.dry_run:
                        dest = copy_as_cover(chosen["path"], folder)
                        save_manual_covers({folder.name: dest})
                        print(f"  Saved: images/{dest}")
                    else:
                        print(f"  [dry-run] would pick: {chosen['filename']}")
                    picked += 1
                    break
                else:
                    hi = len(all_options)
                    lo = "0/" if globe_option else ""
                    print(f"  Enter {lo}1-{hi}, s, or q.")
            except ValueError:
                hi = len(all_options)
                lo = "0/" if globe_option else ""
                print(f"  Enter {lo}1-{hi}, s, or q.")

    print(f"\n{'='*60}")
    print(f"  picked={picked}  skipped={skipped}  no_images={no_images}")
    if picked and not args.dry_run:
        print("  Run: python update_archive.py")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()