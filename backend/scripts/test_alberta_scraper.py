"""Test script to inspect Alberta wait times page structure."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from waittime.scrapers.alberta import AlbertaScraper
from waittime.services.database import DatabaseService


def main():
    """Run Alberta scraper and save HTML for inspection."""
    db = DatabaseService()
    source = db.get_source("alberta-ahs")

    if not source:
        print("Error: Alberta source not found in database")
        return

    scraper = AlbertaScraper(source=source, db=db)

    print("Fetching Alberta wait times page...")
    html = scraper.fetch()

    # Save full HTML for inspection
    output_path = Path(__file__).parent / "alberta_output.html"
    output_path.write_text(html, encoding="utf-8")

    print(f"\nFull HTML saved to: {output_path}")
    print(f"HTML length: {len(html)} characters")

    # Try to parse
    print("\nAttempting to parse...")
    measurements = scraper.parse(html)
    print(f"Measurements found: {len(measurements)}")

    # Show snippet of relevant sections
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    print("\n=== Tables Found ===")
    tables = soup.find_all("table")
    print(f"Number of tables: {len(tables)}")
    for i, table in enumerate(tables[:3]):  # First 3 tables
        print(f"\nTable {i+1} snippet:")
        print(str(table)[:300])

    print("\n=== Divs with 'wait' in class ===")
    wait_divs = soup.find_all("div", class_=lambda x: x and "wait" in x.lower())
    print(f"Number of wait divs: {len(wait_divs)}")
    for div in wait_divs[:3]:
        print(f"\n{div.get('class')}:")
        print(str(div)[:200])

    print("\n=== Any lists found ===")
    lists = soup.find_all(["ul", "ol"])
    print(f"Number of lists: {len(lists)}")
    for lst in lists[:2]:
        print(f"\n{lst.name}:")
        print(str(lst)[:200])


if __name__ == "__main__":
    main()
