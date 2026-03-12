#!/usr/bin/env python3
"""Run from repo root: python debug_fn.py"""
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

folder = next(
    p for p in Path("posts").iterdir()
    if p.is_dir() and "2022-10-16" in p.name and "Blindspot" in p.name
)
html = (folder / "index.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

for anchor in soup.find_all("a", id=re.compile(r'^footnote-\d+$'), class_="footnote-number"):
    fn_id = anchor["id"]
    print(f"\n=== {fn_id} ===")
    print(f"  anchor tag: {anchor}")
    node = anchor.next_sibling
    i = 0
    while node is not None:
        if isinstance(node, NavigableString):
            s = str(node).strip()
            if s:
                print(f"  sibling[{i}] NavigableString: {repr(s[:80])}")
        elif isinstance(node, Tag):
            print(f"  sibling[{i}] Tag <{node.name}>: {node.outerHTML if hasattr(node,'outerHTML') else str(node)[:200]}")
            # Check for local links
            for a in ([node] if node.name == "a" else node.find_all("a", href=True)):
                href = a.get("href","")
                text = a.get_text(strip=True)
                print(f"    -> link href={href!r}  text={text!r}  is_local={href.startswith('../')}")
        i += 1
        node = node.next_sibling
    if i == 0:
        print("  (no siblings at all)")