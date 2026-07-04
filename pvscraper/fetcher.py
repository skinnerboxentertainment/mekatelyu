import time
import httpx
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from .schema import ListingStore

BASE_URL = "https://www.puertoviejosatellite.com"
MIN_DELAY = 2.5
MAX_RETRIES = 3


class Fetcher:
    def __init__(
        self,
        store: ListingStore,
        base_url: str = BASE_URL,
        min_delay: float = MIN_DELAY,
        cache_dir: str = "cache",
    ):
        self.store = store
        self.base_url = base_url
        self.min_delay = min_delay
        self.cache_dir = cache_dir
        self._last_request = 0.0
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        self.stats = {"fetched": 0, "cached": 0, "failed": 0, "retried": 0}

    def _pace(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self._last_request = time.time()

    def _to_absolute(self, path: str) -> str:
        return urljoin(self.base_url, path)

    def fetch(self, url: str, force: bool = False) -> Optional[str]:
        full_url = self._to_absolute(url)

        if not force:
            cached = self.store.html_cached(full_url)
            if cached is not None:
                self.stats["cached"] += 1
                self.store.log_provenance(
                    full_url, "cache_hit", "Loaded from HTML cache"
                )
                return cached

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._pace()
                resp = self._client.get(full_url)

                if resp.status_code == 200:
                    html = resp.text
                    self.store.cache_html(
                        full_url,
                        html,
                        resp.status_code,
                        dict(resp.headers),
                    )
                    self.stats["fetched"] += 1
                    self.store.log_provenance(
                        full_url,
                        "fetched",
                        f"HTTP 200 ({len(html)} bytes)",
                    )
                    return html
                elif resp.status_code in (429, 503):
                    wait = self.min_delay * (2**attempt)
                    self.store.log_provenance(
                        full_url,
                        "rate_limited",
                        f"HTTP {resp.status_code}, retry {attempt}/{MAX_RETRIES}",
                    )
                    time.sleep(wait)
                    self.stats["retried"] += 1
                    continue
                else:
                    self.store.log_provenance(
                        full_url,
                        "fetch_failed",
                        f"HTTP {resp.status_code}",
                    )
                    self.stats["failed"] += 1
                    return None

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                self.store.log_provenance(
                    full_url,
                    "fetch_error",
                    f"Attempt {attempt}/{MAX_RETRIES}: {e}",
                )
                self.stats["retried"] += 1
                if attempt < MAX_RETRIES:
                    time.sleep(self.min_delay * (2**attempt))
                else:
                    self.stats["failed"] += 1
                    return None

        return None

    def close(self):
        self._client.close()
