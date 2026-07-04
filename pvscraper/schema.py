import sqlite3
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class BusinessListing:
    url: str
    category: Optional[str] = None
    area: Optional[str] = None
    business_name: Optional[str] = None
    alternate_names: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    google_maps_cid: Optional[str] = None
    instagram_handle: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    price_range: Optional[str] = None
    verified_date: Optional[str] = None
    operating_status: str = "active"
    raw_html_path: Optional[str] = None
    retrieved_at: Optional[str] = None
    parser_version: str = "0.1"
    http_status: Optional[int] = None
    extraction_warnings: Optional[str] = None
    normalized_phone: Optional[str] = None
    normalized_instagram: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    category TEXT,
    area TEXT,
    business_name TEXT,
    alternate_names TEXT,
    phone TEXT,
    website TEXT,
    google_maps_cid TEXT,
    instagram_handle TEXT,
    instagram_url TEXT,
    facebook_url TEXT,
    description TEXT,
    rating REAL,
    price_range TEXT,
    verified_date TEXT,
    operating_status TEXT DEFAULT 'active',
    raw_html_path TEXT,
    retrieved_at TEXT,
    parser_version TEXT,
    http_status INTEGER,
    extraction_warnings TEXT,
    normalized_phone TEXT,
    normalized_instagram TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS raw_html_cache (
    url TEXT PRIMARY KEY,
    html TEXT,
    retrieved_at TEXT,
    http_status INTEGER,
    headers TEXT
);

CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_url TEXT,
    step TEXT,
    message TEXT,
    timestamp TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_listings_category ON listings(category);
CREATE INDEX IF NOT EXISTS idx_listings_area ON listings(area);
CREATE INDEX IF NOT EXISTS idx_listings_instagram ON listings(instagram_handle);
CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(operating_status);
"""


class ListingStore:
    def __init__(self, db_path: str = "pvscraper.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(SCHEMA_SQL)
            self._conn.commit()
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def conn(self) -> sqlite3.Connection:
        return self.connect()

    def listing_exists(self, url: str) -> bool:
        row = self.conn().execute(
            "SELECT 1 FROM listings WHERE url = ?", (url,)
        ).fetchone()
        return row is not None

    def html_cached(self, url: str) -> Optional[str]:
        row = self.conn().execute(
            "SELECT html FROM raw_html_cache WHERE url = ?", (url,)
        ).fetchone()
        return row["html"] if row else None

    def cache_html(self, url: str, html: str, status: int, headers: dict = None):
        self.conn().execute(
            """INSERT OR REPLACE INTO raw_html_cache (url, html, retrieved_at, http_status, headers)
               VALUES (?, ?, ?, ?, ?)""",
            (url, html, datetime.utcnow().isoformat(), status, json.dumps(headers or {})),
        )
        self.conn().commit()

    def html_cache_key(self, url: str) -> bool:
        row = self.conn().execute(
            "SELECT 1 FROM raw_html_cache WHERE url = ? AND http_status = 200",
            (url,),
        ).fetchone()
        return row is not None

    def save_listing(self, listing: BusinessListing):
        existing = self.conn().execute(
            "SELECT id FROM listings WHERE url = ?", (listing.url,)
        ).fetchone()

        data = asdict(listing)
        data["updated_at"] = datetime.utcnow().isoformat()

        if existing:
            cols = ", ".join(f"{k}=?" for k in data)
            vals = list(data.values()) + [existing["id"]]
            self.conn().execute(
                f"UPDATE listings SET {cols} WHERE id=?", vals
            )
        else:
            cols = ", ".join(data.keys())
            placeholders = ", ".join("?" for _ in data)
            self.conn().execute(
                f"INSERT INTO listings ({cols}) VALUES ({placeholders})",
                list(data.values()),
            )
        self.conn().commit()

    def log_provenance(self, listing_url: str, step: str, message: str):
        self.conn().execute(
            "INSERT INTO provenance (listing_url, step, message) VALUES (?, ?, ?)",
            (listing_url, step, message),
        )
        self.conn().commit()

    def get_all_listings(self) -> list[BusinessListing]:
        rows = self.conn().execute("SELECT * FROM listings").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d.pop("id", None)
            result.append(BusinessListing(**d))
        return result

    def get_pending_urls(self) -> list[str]:
        rows = self.conn().execute(
            """SELECT l.url FROM listing_urls l
               LEFT JOIN raw_html_cache c ON l.url = c.url
               WHERE c.url IS NULL"""
        ).fetchall()
        return [r["url"] for r in rows]

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
