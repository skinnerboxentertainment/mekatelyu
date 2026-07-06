#!/usr/bin/env python3
"""
Full crawl: all categories from puertoviejosatellite.com.
"""

import sys, os, time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pvscraper import (
    ListingStore, Fetcher, Enumerator, ListingParser,
    Normalizer, Pipeline, Auditor,
)
from pvscraper.schema import SCHEMA_SQL
from pvscraper.enumerator import CATEGORY_PAGES

DB_PATH = "pvscraper_full.db"


def main():
    start = time.time()

    store = ListingStore(DB_PATH)
    conn = store.connect()
    conn.executescript(
        "DROP TABLE IF EXISTS listings; "
        "DROP TABLE IF EXISTS raw_html_cache; "
        "DROP TABLE IF EXISTS provenance;"
    )
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    print("Clean DB initialized.", flush=True)

    fetcher = Fetcher(store, min_delay=2.0)
    enumerator = Enumerator(fetcher, store)
    parser = ListingParser()
    normalizer = Normalizer()

    print("Enumerating listing URLs across all categories...", flush=True)
    all_urls = enumerator.discover_listing_urls(CATEGORY_PAGES)
    print(f"  Found {len(all_urls)} total listing URLs", flush=True)

    by_cat = defaultdict(list)
    for url, cat, area in all_urls:
        by_cat[cat].append((url, cat, area))
    for cat, items in sorted(by_cat.items()):
        print(f"  {cat}: {len(items)}", flush=True)

    sample_urls = list(all_urls)
    total = len(sample_urls)
    print(f"\nFetching and parsing {total} listings...", flush=True)

    results = {"fetched": 0, "parsed": 0, "failed": 0, "warnings": 0}
    for idx, (url, category, area) in enumerate(sample_urls, 1):
        store.log_provenance(url, "pipeline", f"Processing: {category}/{area}")

        html = fetcher.fetch(url)
        if not html:
            results["failed"] += 1
            store.log_provenance(url, "pipeline_error", "Failed to fetch")
            print(f"  [{idx}/{total}] FAIL {category}/{area}")
            continue

        listing = parser.parse(url, html)
        listing.category = listing.category or category
        listing.area = listing.area or area

        normalizer.normalize(listing)
        store.save_listing(listing)
        results["fetched"] += 1
        results["parsed"] += 1

        if listing.extraction_warnings:
            results["warnings"] += 1

        ig = " IG" if listing.instagram_handle else ""
        name = (listing.business_name or "?")[:40]
        print(f"  [{idx}/{total}] {name} [{category}/{area}]{ig}", flush=True)

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"Enumerated: {len(all_urls)}")
    print(f"Fetched:    {results['fetched']}")
    print(f"Parsed:     {results['parsed']}")
    print(f"Failed:     {results['failed']}")
    print(f"Warnings:   {results['warnings']}")
    print(f"Time:       {elapsed:.1f}s")
    print(f"Fetcher:    {fetcher.stats}")

    print("")
    auditor = Auditor(store)
    report = auditor.report()
    auditor.print_report(report)

    store.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
