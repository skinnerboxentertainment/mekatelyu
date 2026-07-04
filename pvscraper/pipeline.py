from .enumerator import Enumerator
from .fetcher import Fetcher
from .parser import ListingParser
from .normalizer import Normalizer
from .schema import ListingStore


class Pipeline:
    def __init__(
        self,
        store: ListingStore,
        fetcher: Fetcher,
        enumerator: Enumerator,
        parser: ListingParser,
        normalizer: Normalizer,
    ):
        self.store = store
        self.fetcher = fetcher
        self.enumerator = enumerator
        self.parser = parser
        self.normalizer = normalizer

    def run(self, category_pages: dict[str, str] = None) -> dict:
        results = {"enumerated": 0, "fetched": 0, "parsed": 0, "failed": 0, "warnings": []}

        # Step 1: Enumerate listing URLs
        listings = self.enumerator.discover_listing_urls(category_pages)
        results["enumerated"] = len(listings)

        # Step 2: Fetch, parse, normalize, store
        for url, category, area in listings:
            self.store.log_provenance(url, "pipeline", f"Processing: {category}/{area}")

            html = self.fetcher.fetch(url)
            if not html:
                results["failed"] += 1
                self.store.log_provenance(url, "pipeline_error", "Failed to fetch")
                continue

            listing = self.parser.parse(url, html)
            listing.category = listing.category or category
            listing.area = listing.area or area

            self.normalizer.normalize(listing)

            self.store.save_listing(listing)
            results["fetched"] += 1
            results["parsed"] += 1

            if listing.extraction_warnings:
                results["warnings"].append({
                    "url": url,
                    "warnings": listing.extraction_warnings,
                })

        return results
