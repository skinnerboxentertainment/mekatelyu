"""Export the pilot database to CSV."""

import csv
import sqlite3
from datetime import datetime

DB = "pvscraper_full.db"
OUTPUT = "pv_businesses_export.csv"
FIELDS = [
    "business_name",
    "category",
    "area",
    "phone",
    "normalized_phone",
    "website",
    "instagram_handle",
    "instagram_url",
    "normalized_instagram",
    "facebook_url",
    "google_maps_cid",
    "verified_date",
    "operating_status",
    "rating",
    "price_range",
    "description",
    "alternate_names",
    "extraction_warnings",
    "url",
]

conn = sqlite3.connect(DB)
rows = conn.execute(f"SELECT {', '.join(FIELDS)} FROM listings ORDER BY category, area, business_name").fetchall()
conn.close()

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(FIELDS)
    w.writerows(rows)

print(f"Exported {len(rows)} records to {OUTPUT}")
