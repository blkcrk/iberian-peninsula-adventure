#!/usr/bin/env python3
"""
Travel Diary Site Generator
Converts markdown entries → beautiful HTML site
"""

import os
import re
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent
ENTRIES_DIR = REPO_ROOT / "entries"
OUTPUT_DIR = REPO_ROOT / "_site"

def ensure_output_dir():
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "css").mkdir(exist_ok=True)

def generate_index():
    """Generate index page listing all entries"""
    index_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Miller Iberian Peninsula Adventure</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="archive">
        <h1>Miller Iberian Peninsula Adventure</h1>
        <p>Spain & Portugal, May 20–31, 2026</p>
        <p>Entries will appear here as they're added.</p>
    </div>
</body>
</html>
"""
    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(index_html)

def main():
    ensure_output_dir()
    generate_index()
    print("✅ Site generated: _site/index.html")

if __name__ == "__main__":
    main()
