import os
import re
from pathlib import Path
from datetime import datetime

# Configuration
REPO_ROOT = Path(__file__).parent
ENTRIES_DIR = REPO_ROOT / "entries"
PHOTOS_DIR = REPO_ROOT / "photos"
OUTPUT_DIR = REPO_ROOT / "_site"
CSS_DIR = REPO_ROOT / "css"

SITE_TITLE = "Miller Iberian Peninsula Adventure"
SITE_SUBTITLE = "Spain & Portugal, May 20–31, 2026"

def ensure_directories():
    """Create necessary directories."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "css").mkdir(exist_ok=True)
    (OUTPUT_DIR / "photos").mkdir(exist_ok=True)

def parse_entry(filepath):
    """
    Parse markdown entry file.

    Returns dict with:
    - title, date, city, mood
    - narrative, locations, restaurants, wines, photos
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    entry = {
        "filepath": filepath,
        "filename": filepath.stem,
        "title": "",
        "date": "",
        "city": "",
        "mood": "",
        "narrative": "",
        "locations": [],
        "restaurants": [],
        "wines": [],
        "photos": [],
        "reflections": ""
    }

    # Extract title (# May XX — City: Theme)
    title_match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
    if title_match:
        entry["title"] = title_match.group(1)
        # Extract city
        city_match = re.search(r"—\s+([^:]+):", entry["title"])
        if city_match:
            entry["city"] = city_match.group(1).strip()

    # Extract metadata (Date, Mood)
    date_match = re.search(r"\*\*Date:\*\*\s+(\d{4}-\d{2}-\d{2})", content)
    if date_match:
        entry["date"] = date_match.group(1)

    mood_match = re.search(r"\*\*Mood:\*\*\s+(.+?)(?:\n|$)", content)
    if mood_match:
        entry["mood"] = mood_match.group(1).strip()

    # Extract narrative (between "## 📖 Day" and next ##)
    narrative_match = re.search(r"## 📖 Day\n\n(.+?)\n\n##", content, re.DOTALL)
    if narrative_match:
        entry["narrative"] = narrative_match.group(1).strip()

    # Extract locations
    locations_match = re.search(r"## 📍 Locations Visited\n\n(.+?)(?:\n\n##|$)", content, re.DOTALL)
    if locations_match:
        location_text = locations_match.group(1)
        location_blocks = re.findall(r"- \*\*(.+?)\*\*\s+\(([^,]+),\s*([^)]+)\)\n\s+(.+?)(?=\n-|\n\n|$)", location_text)
        for name, lat, lon, note in location_blocks:
            entry["locations"].append({
                "name": name.strip(),
                "lat": float(lat.strip()),
                "lon": float(lon.strip()),
                "note": note.strip()
            })

    # Extract restaurants
    restaurants_match = re.search(r"## 🍴 Food & Restaurants\n\n(.+?)(?:\n\n##|$)", content, re.DOTALL)
    if restaurants_match:
        restaurant_text = restaurants_match.group(1)
        restaurant_blocks = re.findall(r"### (.+?)\n(.*?)(?=###|$)", restaurant_text, re.DOTALL)
        for name, details in restaurant_blocks:
            entry["restaurants"].append({
                "name": name.strip(),
                "html": format_details(details.strip())
            })

    # Extract wines
    wines_match = re.search(r"## 🍷 Wine & Drinks\n\n(.+?)(?:\n\n##|$)", content, re.DOTALL)
    if wines_match:
        wine_text = wines_match.group(1)
        wine_blocks = re.findall(r"### (.+?)\n(.*?)(?=###|$)", wine_text, re.DOTALL)
        for name, details in wine_blocks:
            entry["wines"].append({
                "name": name.strip(),
                "html": format_details(details.strip())
            })

    # Extract photos
    photos_match = re.search(r"## 📸 Photos\n\n(.+?)(?:\n\n##|$)", content, re.DOTALL)
    if photos_match:
        photo_text = photos_match.group(1)
        photos = re.findall(r"- (.+?\.(?:jpg|jpeg|png))", photo_text, re.IGNORECASE)
        entry["photos"] = [p.strip() for p in photos]

    # Extract reflections
    reflections_match = re.search(r"## 🧠 Reflections\n\n(.+?)(?:\n\n##|$)", content, re.DOTALL)
    if reflections_match:
        entry["reflections"] = reflections_match.group(1).strip()

    return entry

def format_details(text):
    """Convert markdown-style details to HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.strip():
            html_lines.append(f"<p>{line.strip()}</p>")
    return "".join(html_lines)

def generate_entry_html(entry):
    """Generate HTML for a single entry."""
    # Build map if locations exist
    map_html = ""
    if entry["locations"]:
        map_id = f"map_{entry['date']}"
        map_html = f"""
        <section class="locations">
            <h2>📍 Locations Visited</h2>
            <div id="{map_id}" class="map"></div>
            <ul class="locations-list">
        """
        for loc in entry["locations"]:
            map_html += f'<li><strong>{loc["name"]}</strong> - {loc["note"]}</li>'
        map_html += "</ul>"

        center_lat = entry["locations"][0]["lat"]
        center_lon = entry["locations"][0]["lon"]
        map_html += f"""
        <script>
            var map = L.map('{map_id}').setView([{center_lat}, {center_lon}], 13);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
        """
        for loc in entry["locations"]:
            map_html += f"L.marker([{loc['lat']}, {loc['lon']}]).bindPopup('<strong>{loc['name']}</strong><br>{loc['note']}').addTo(map);"
        map_html += """
        </script>
        </section>
        """

    # Build restaurants section
    restaurants_html = ""
    if entry["restaurants"]:
        restaurants_html = "<section class='food'><h2>🍴 Food & Restaurants</h2>"
        for restaurant in entry["restaurants"]:
            restaurants_html += f'<div class="restaurant"><h3>{restaurant["name"]}</h3>{restaurant["html"]}</div>'
        restaurants_html += "</section>"

    # Build wines section
    wines_html = ""
    if entry["wines"]:
        wines_html = "<section class='wine'><h2>🍷 Wine & Drinks</h2>"
        for wine in entry["wines"]:
            wines_html += f'<div class="wine-entry"><h3>{wine["name"]}</h3>{wine["html"]}</div>'
        wines_html += "</section>"

    # Build photos section
    photos_html = ""
    if entry["photos"]:
        photos_html = "<section class='photos'><h2>📸 Photos</h2><div class='photo-gallery'>"
        city_folder = entry["city"].lower().replace(" ", "-")
        for photo in entry["photos"]:
            photo_path = f"photos/{city_folder}/{photo}"
            photos_html += f'<img src="/{photo_path}" alt="{photo}" loading="lazy">'
        photos_html += "</div></section>"

    # Build reflections section
    reflections_html = ""
    if entry["reflections"]:
        reflections_html = f"<section class='reflections'><h2>🧠 Reflections</h2><p>{entry['reflections']}</p></section>"

    # Assemble entry
    html = f"""
    <article class="entry">
        <h1>{entry['title']}</h1>
        <meta-info>
            <span class="date">{entry['date']}</span>
            <span class="city">{entry['city']}</span>
            <span class="mood">Mood: {entry['mood']}</span>
        </meta-info>
        
        <section class="narrative">
            <h2>📖 Day</h2>
            <p>{entry['narrative']}</p>
        </section>
        
        {map_html}
        {restaurants_html}
        {wines_html}
        {photos_html}
        {reflections_html}
    </article>
    """

    return html

def generate_entry_page(entry):
    """Generate complete HTML page for an entry."""
    entry_html = generate_entry_html(entry)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{entry['title']}</title>
    <link rel="stylesheet" href="/iberian-peninsula-adventure/css/style.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
    <a href="/iberian-peninsula-adventure/" class="back-link">← Back to Adventure</a>
    {entry_html}
    <footer>
        <p><small>Miller Iberian Peninsula Adventure | May 20–31, 2026</small></p>
    </footer>
</body>
</html>
"""

    return page

def generate_index(entries):
    """Generate index/archive page."""
    sorted_entries = sorted(entries, key=lambda e: e['date'] if e['date'] else '0000-00-00')

    entries_list = ""
    for entry in sorted_entries:
        entries_list += f"""
        <a href="/iberian-peninsula-adventure/{entry['filename']}.html" class="archive-item">
            <span class="date">{entry['date']}</span>
            <span class="title">{entry['title']}</span>
        </a>
        """

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Miller Iberian Peninsula Adventure</title>
    <link rel="stylesheet" href="/iberian-peninsula-adventure/css/style.css">
</head>
<body>
    <div class="index">
        <h1>Miller Iberian Peninsula Adventure</h1>
        <p>Spain & Portugal, May 20–31, 2026</p>
        
        <div class="archive">
            {entries_list if entries_list else '<p style="color: #999;">Entries coming soon...</p>'}
        </div>
    </div>
    
    <footer>
        <p><small>Private travel diary | Share with friends & family</small></p>
    </footer>
</body>
</html>
"""

    return page

def copy_static_files():
    """Copy CSS file to output."""
    css_src = CSS_DIR / "style.css"
    css_dest = OUTPUT_DIR / "css" / "style.css"

    if css_src.exists():
        with open(css_src, "r") as f:
            css_content = f.read()
        with open(css_dest, "w") as f:
            f.write(css_content)

def main():
    """Main build process."""
    print("🔨 Building travel diary site...")

    ensure_directories()

    # Parse all entries
    entries = []
    if ENTRIES_DIR.exists():
        for entry_file in sorted(ENTRIES_DIR.glob("*.md")):
            if entry_file.name == "template-example.md":
                continue  # Skip template
            try:
                entry = parse_entry(entry_file)
                entries.append(entry)
                print(f"  ✅ Parsed: {entry['title']}")
            except Exception as e:
                print(f"  ⚠️  Error parsing {entry_file.name}: {e}")

    # Generate index page
    index_html = generate_index(entries)
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  ✅ Generated index.html")

    # Generate individual entry pages
    for entry in entries:
        entry_html = generate_entry_page(entry)
        output_file = OUTPUT_DIR / f"{entry['filename']}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(entry_html)
        print(f"  ✅ Generated {entry['filename']}.html")

    # Copy CSS
    copy_static_files()
    print(f"  ✅ Copied CSS")

    # Summary
    print(f"\n🌍 Build complete!")
    print(f"   Entries: {len(entries)}")
    print(f"   Output: {OUTPUT_DIR}")
    print(f"   Ready for GitHub Pages: _site/")

if __name__ == "__main__":
    main()
