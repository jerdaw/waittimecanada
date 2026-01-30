"""Provincial wait time scrapers.

Each scraper implements BaseScraper and knows how to:
1. Fetch data from its provincial source
2. Parse HTML/JSON into Measurement objects
3. Tag with correct ontology values (per ADR-0002)
"""

from waittime.scrapers.base import BaseScraper
from waittime.scrapers.quebec import QuebecScraper, create_quebec_source

__all__ = [
    "BaseScraper",
    "QuebecScraper",
    "create_quebec_source",
]
