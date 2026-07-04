import re
from typing import Iterator, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .fetcher import Fetcher
from .schema import ListingStore

BASE_URL = "https://www.puertoviejosatellite.com"

CATEGORY_PAGES = {
    "hotel": "/en/hotels/",
    "hostel": "/en/hostels/",
    "vacation_rental": "/en/vacation-rentals/",
    "restaurant": "/en/restaurants/",
    "shopping": "/en/shopping/",
    "services": "/en/services/",
    "tour_company": "/en/tour-companies/",
    "real_estate": "/en/real-estate/",
}

PILOT_CATEGORIES = {
    "hotel": "/en/hotels/",
    "restaurant": "/en/restaurants/",
}

# Areas served by puertoviejosatellite.com
KNOWN_AREAS = {
    "puerto-viejo", "playa-negra", "cocles", "playa-chiquita",
    "punta-uva", "manzanillo", "cahuita", "hone-creek",
    "bribri", "gandoca", "sixaola",
}


class Enumerator:
    def __init__(self, fetcher: Fetcher, store: ListingStore):
        self.fetcher = fetcher
        self.store = store

    def discover_listing_urls(
        self, category_pages: dict[str, str] = None
    ) -> list[tuple[str, str, str]]:
        if category_pages is None:
            category_pages = CATEGORY_PAGES

        results: list[tuple[str, str, str]] = []
        for category, path in category_pages.items():
            urls = self._parse_category_page(path, category)
            results.extend(urls)
            self.store.log_provenance(
                path,
                "enumerate",
                f"Found {len(urls)} listings in category '{category}'",
            )
        return results

    def _parse_category_page(
        self, path: str, category: str
    ) -> list[tuple[str, str, str]]:
        full_url = urljoin(BASE_URL, path)
        html = self.fetcher.fetch(full_url, force=True)
        if not html:
            self.store.log_provenance(
                path, "enumerate_failed", "Could not fetch category page"
            )
            return []

        soup = BeautifulSoup(html, "html.parser")
        seen: set[str] = set()
        urls: list[tuple[str, str, str]] = []

        # Collect all links in the page body (skip header/nav/footer)
        content = soup.find("body")
        if not content:
            content = soup

        for a in content.find_all("a", href=True):
            href = a["href"].strip()

            # Normalize to absolute URL
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = urljoin(BASE_URL, href)
            elif not href.startswith("http"):
                continue

            # Check if this is a listing page URL
            listing_url = self._is_listing_url(href)
            if not listing_url:
                continue

            if listing_url in seen:
                continue
            seen.add(listing_url)

            # Extract area from URL path
            parsed = urlparse(listing_url)
            parts = parsed.path.strip("/").split("/")
            area = parts[1] if len(parts) >= 2 else "unknown"

            urls.append((listing_url, category, area))

        return urls

    def _is_listing_url(self, url: str) -> Optional[str]:
        """Check if a URL points to a PVS business listing page.
        Returns the cleaned URL or None."""
        parsed = urlparse(url)

        # Must be puertoviejosatellite.com
        if "puertoviejosatellite.com" not in parsed.netloc:
            return None

        path = parsed.path.strip("/")
        parts = path.split("/")

        # Pattern: en/{area}/{business-slug}/
        if len(parts) < 3:
            return None
        if parts[0] != "en":
            return None

        area = parts[1]
        # Must be a known travel/listing area, not a static page
        if area not in KNOWN_AREAS:
            return None

        # Must have a business slug (third part)
        slug = parts[2]
        if not slug or slug == "index" or slug.startswith("?"):
            return None

        # Reconstruct canonical URL (no trailing slash for consistency)
        clean = f"https://www.puertoviejosatellite.com/en/{area}/{slug}/"
        return clean
