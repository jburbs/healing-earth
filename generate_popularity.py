#!/usr/bin/env python3
"""
Generate popularity-data.js by fuzzy-matching Substack titles to local folders.
"""

import os
import re
from difflib import SequenceMatcher

# Substack "Top" rankings (rank, title)
SUBSTACK_TOP = [
    (1, "46. Low-cost Desalination and the ARPA-E Summit"),
    (2, "22. Healing (Part 12). Reducing the only solution to practice"),
    (3, "1. Is Global Warming Real?"),
    (4, "17. Healing (Part 7). So...what's it gonna cost me?"),
    (5, "4. Where did all that carbon come from?"),
    (6, "8. What do we know now about Climate Change?"),
    (7, "57. Another solution? (Part 1)"),
    (8, "70. Why the news about fusion is bad"),
    (9, "19. Healing (Part 9). Avoiding enthusiasm and superstition."),
    (10, "3. Earth is getting warmer. So what? (Part 1)"),
    (11, "2. Carbon. Hero or villain?"),
    (12, "21. Healing (Part 11). The Only Solution."),
    (13, "84. Developing a third solution (Part 3)"),
    (14, "9. Healing (Part 1). What can we do?"),
    (15, "13. Earth is getting warmer. So what? (AR6 IPCC WGI Readout)"),
    (16, "12. Healing (Part 4). A ray of hope."),
    (17, "55. Does it matter what we plant? (Part 2)"),
    (18, "7. Earth is getting warmer. So what? (Part 2)"),
    (19, "Academic Fan-Fic of a Painless Net Zero Future"),
    (20, "82. Developing a third solution (Part 1)"),
    (21, "10. Healing (Part 2). Is decarbonization a solution?"),
    (22, "14. Tying up a few loose ends"),
    (23, "92. John Doerr and me"),
    (24, "76. Returning to the prime directive"),
    (25, "69. Why climate innovation is off track"),
    (26, "Water. There is no substitute."),
    (27, "6. Is Carbon exonerated by Henry's Law?"),
    (28, "AI is turning the corner"),
    (29, "Making Agrivoltaics Work"),
    (30, "50. Solar power at the cost of coal (Part 1)"),
    (31, "52. A Trillion trees?"),
    (32, "104. STEM, DEI, and Academic Freedom"),
    (33, "99. Developing a Third Solution (Part 11)"),
    (34, "53. Are trees the best use of land?"),
    (35, "41. How to Heal Earth for the Visual Learner"),
    (36, "80. Hydrogen. Atomic #1"),
    (37, "Beyond the Limits: A Critical Look at Cultured Meat"),
    (38, "5. Leading with Data"),
    (39, "61. What's the point of 'fighting' climate change?"),
    (40, "11. Healing (Part 3). What can the STEM crowd do about it?"),
    (41, "Questions to be answered. With data."),
    (42, "93. Seriously, how much money are we talking about?"),
    (43, "18. Healing (Part 8). Can water alone be the complete solution?"),
    (44, "42. IPCC WG III and reality (Part 1)"),
    (45, "27. Healing revisited, or \"Don't we already have a solution?\""),
    (46, "24. Evaluating a \"carbon footprint\" (Part 2): Crypto vs Credit"),
    (47, "87. Heilmeier and Climate Control"),
    (48, "100. Reflections"),
    (49, "89. ChatGPT is a fraud"),
    (50, "30. Adapting Christmas to Climate Change"),
]

def strip_issue_number(title):
    """Strip leading issue number from Substack title."""
    # Remove patterns like "46. " or "1. "
    return re.sub(r'^\d+\.\s+', '', title)

def similarity_score(s1, s2):
    """Calculate similarity between two strings (0-1)."""
    # Normalize for comparison
    s1_norm = s1.lower().strip('?.,;')
    s2_norm = s2.lower().strip('?.,;')

    # Use sequence matcher for similarity
    matcher = SequenceMatcher(None, s1_norm, s2_norm)
    return matcher.ratio()

def extract_title_from_folder(folder_name):
    """Extract title portion from folder name like '2021-05-23_001_Is Global Warming Real'."""
    # Remove date and issue number prefix
    parts = folder_name.split('_', 2)
    if len(parts) >= 3:
        return parts[2]
    return folder_name

def find_best_match(substack_title, folder_names):
    """Find the best matching folder for a Substack title."""
    best_score = 0.0
    best_folder = None

    for folder in folder_names:
        folder_title = extract_title_from_folder(folder)
        score = similarity_score(substack_title, folder_title)

        if score > best_score:
            best_score = score
            best_folder = folder

    return best_folder, best_score

def main():
    posts_dir = "/sessions/zen-eloquent-wozniak/mnt/Substack Site Localized/posts"

    # Get all folder names
    if not os.path.exists(posts_dir):
        print(f"Error: {posts_dir} not found")
        return

    folder_names = sorted([f for f in os.listdir(posts_dir)
                          if os.path.isdir(os.path.join(posts_dir, f))])

    print(f"Found {len(folder_names)} folders")

    # Build popularity map
    popularity_map = {}
    unmatched = []

    for rank, substack_title in SUBSTACK_TOP:
        clean_title = strip_issue_number(substack_title)
        folder, score = find_best_match(clean_title, folder_names)

        if folder:
            popularity_map[folder] = rank
            print(f"Rank {rank:2d} ({score:.2f}): {clean_title[:50]:50s} -> {folder}")
        else:
            print(f"Rank {rank:2d} (NOMATCH): {clean_title}")
            unmatched.append((rank, substack_title))

    print(f"\nMatched: {len(popularity_map)}/{len(SUBSTACK_TOP)}")
    if unmatched:
        print(f"Unmatched:")
        for rank, title in unmatched:
            print(f"  Rank {rank}: {title}")

    # Generate JavaScript file
    js_lines = [
        "// Post popularity rankings from Substack \"Top\" sort",
        "// Rank 1 = most popular. Posts without a rank default to 999.",
        "const postPopularity = {",
    ]

    # Sort by folder name for consistency
    for folder in sorted(folder_names):
        rank = popularity_map.get(folder, 999)
        js_lines.append(f'    "{folder}": {rank},')

    js_lines.append("};")

    js_content = '\n'.join(js_lines)

    # Write to file
    output_path = "/sessions/zen-eloquent-wozniak/mnt/Substack Site Localized/popularity-data.js"
    with open(output_path, 'w') as f:
        f.write(js_content)

    print(f"\nWrote {output_path}")

if __name__ == '__main__':
    main()
