"""Answer "why does this page say this?" for any published field.

The project's central claim is that its data is evidence-backed. Until now that
was true in the sense that evidence had been *collected* — ARIA snapshots for
amenities and hours, screenshots for WhatsApp routes, a crawl log for the
original records — but not in the sense that anyone could ask a question of it.
The evidence sat in files nobody joined back to the pages.

This module does the join. Given a business and a field, it names the source,
when it was captured, and what it asserted, so a correction request from an
owner can be adjudicated by looking rather than by remembering.

Sources, in the order they are consulted:

* the master CSV's own provenance columns — where the record came from and when
  it was last confirmed;
* the CID-keyed verified sidecars written by the extraction pipeline, each of
  which records its capture time and the name Google showed at capture;
* the semantic taxonomy, which records for every tag the rule that fired, the
  text it matched, and a confidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# Origin evidence — the raw crawl cache and its fetch log — is not held in this
# repository. It lives in the acquisition ancestor and is preserved separately.
# Recording that here means a lookup can say where to go rather than implying
# the trail simply ends.
ORIGIN_EVIDENCE_NOTE = (
    "Raw crawl HTML and the fetch log live in the acquisition archive "
    "(puerto-viejo-business-discovery), not in this repository."
)

# `coordinate_source` reads "array" for 448 of 736 records — a Python list that
# was stringified during the original acquisition rather than a source name.
# It is meaningless, so it is reported as unrecorded instead of being displayed
# as though it told you something. Recovering the real values means going back
# to the archived crawl evidence.
CORRUPT_PROVENANCE_VALUES = frozenset({"array", "list", "none", "nan"})

SOURCE_LABELS = {
    "maps_stealth": "Google Maps (manual search)",
    "maps_stealth_manual_review": "Google Maps (manual search, reviewed)",
    "osm": "OpenStreetMap",
    "pv_satellite": "PV Satellite listing",
    "handle_guess": "name-derived guess, then verified",
    "direct_profile_check": "checked directly against the profile",
    "osm_tags": "OpenStreetMap contact tags",
    "ddg_search": "web search",
    "codex_web": "web research",
}


def clean_source(value: str | None) -> str:
    """Return a trustworthy source name, or "" when the record does not have one."""
    text = (value or "").strip()
    if not text or text.lower() in CORRUPT_PROVENANCE_VALUES:
        return ""
    return SOURCE_LABELS.get(text, text)


@dataclass(frozen=True)
class Evidence:
    """One answer to 'how do we know this?'."""

    field: str
    value: str
    source: str
    captured: str = ""
    detail: str = ""
    confidence: str = ""

    def describe(self) -> str:
        parts = [f"{self.field}: {self.value or '(empty)'}", f"  source: {self.source}"]
        if self.captured:
            parts.append(f"  captured: {self.captured}")
        if self.confidence:
            parts.append(f"  confidence: {self.confidence}")
        if self.detail:
            parts.append(f"  detail: {self.detail}")
        return "\n".join(parts)


def _load(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


class ProvenanceIndex:
    """Joins a record to every piece of evidence held about it."""

    def __init__(self) -> None:
        self.amenities = _load("verified_amenities.json")
        self.attributes = _load("verified_attributes.json")
        self.hours = _load("verified_hours.json")
        # Operating status and place identity, re-read from Maps on each sweep.
        # Without this store both aspects fall back to the CSV's verified_date,
        # which nothing has written since the original crawl.
        self.status = _load("verified_status.json")
        taxonomy = _load("semantic_taxonomy.json")
        self.taxonomy = taxonomy.get("records", {})
        self.taxonomy_version = taxonomy.get("taxonomy_version", "")

    # -- individual fields ---------------------------------------------------

    def identity(self, row: dict) -> list[Evidence]:
        out = [Evidence(
            field="business_name",
            value=row.get("business_name", ""),
            source=row.get("url") or "master CSV",
            captured=row.get("verified_date", ""),
            detail=ORIGIN_EVIDENCE_NOTE if not row.get("url") else "",
        )]
        for field in ("category", "area"):
            out.append(Evidence(
                field=field, value=row.get(field, ""),
                source="master CSV (curated, with QA corrections)",
                captured=row.get("verified_date", ""),
            ))
        return out

    def location(self, row: dict) -> list[Evidence]:
        if not row.get("latitude"):
            return []
        source = clean_source(row.get("coordinate_source"))
        return [Evidence(
            field="coordinates",
            value=f"{row.get('latitude')}, {row.get('longitude')}",
            source=source or "not recorded",
            detail=(f"geofilter: {row.get('geofilter')} — {row.get('geofilter_reason')}"
                    if row.get("geofilter") else ""),
        )]

    def instagram(self, row: dict) -> list[Evidence]:
        handle = row.get("instagram_handle", "").strip()
        if not handle:
            return []
        return [Evidence(
            field="instagram_handle",
            value=handle,
            source=clean_source(row.get("instagram_enrich_source")) or "master CSV",
            captured=row.get("ig_verify_date") or row.get("instagram_enrich_date", ""),
            confidence=row.get("instagram_confidence", ""),
            detail=("screenshot-verified against the live profile"
                    if row.get("ig_verified", "").strip().lower() in ("true", "1", "yes") else ""),
        )]

    def whatsapp(self, row: dict) -> list[Evidence]:
        raw = row.get("whatsapp", "").strip()
        if not raw:
            return []
        return [Evidence(
            field="whatsapp",
            value=raw,
            source="explicit validated route (visual WhatsApp audit)",
            captured=row.get("verified_date", ""),
            detail="never inferred from a phone number",
        )]

    def _sidecar(self, cid: str, store: dict, field: str, summarise) -> list[Evidence]:
        record = store.get(cid)
        if not record:
            return []
        detected = record.get("detectedGoogleName") or record.get("sourceName") or ""
        return [Evidence(
            field=field,
            value=summarise(record),
            source="Google Maps, read from the page's accessibility tree",
            captured=record.get("capturedAt", ""),
            detail=f"matched Google listing: {detected}" if detected else "",
        )]

    def enrichment(self, row: dict) -> list[Evidence]:
        cid = row.get("google_maps_cid", "").strip()
        if not cid:
            return []
        out: list[Evidence] = []
        out += self._sidecar(cid, self.amenities, "amenities",
                             lambda r: f"{len(r.get('availableNames', []))} available")
        out += self._sidecar(cid, self.attributes, "attributes",
                             lambda r: f"{r.get('attributeCount', 0)} attributes")
        out += self._sidecar(cid, self.hours, "hours",
                             lambda r: f"{len(r.get('weeklyHours', {}))} days, {r.get('completeness', 'partial')}")
        return out

    def semantics(self, row: dict) -> list[Evidence]:
        cid = row.get("google_maps_cid", "").strip()
        key = f"cid:{cid}" if cid else None
        record = self.taxonomy.get(key) if key else None
        if not record:
            return []
        out = []
        for tag, assertion in sorted(record.get("assertions", {}).items()):
            out.append(Evidence(
                field=f"tag:{tag}",
                value=tag,
                source=assertion.get("source", ""),
                confidence=f"{assertion.get('confidence', 0):.2f}",
                detail=f"rule {assertion.get('rule', '')} matched {assertion.get('evidence', '')!r}",
            ))
        if record.get("conflicts"):
            out.append(Evidence(
                field="taxonomy_review", value=", ".join(record["conflicts"]),
                source="taxonomy conflict detector",
                detail="flagged for review rather than resolved automatically",
            ))
        return out

    # -- whole record --------------------------------------------------------

    def explain(self, row: dict) -> list[Evidence]:
        return (
            self.identity(row)
            + self.location(row)
            + self.instagram(row)
            + self.whatsapp(row)
            + self.enrichment(row)
            + self.semantics(row)
        )

    def capture_dates(self, cid: str) -> dict[str, str]:
        """Capture timestamps per aspect, for the freshness assessment."""
        if not cid:
            return {}
        pairs = (
            ("amenities", self.amenities),
            ("attributes", self.attributes),
            ("hours", self.hours),
            # One sweep re-reads the place page, so a single capture dates both
            # what Google calls it and whether it says the place is still open.
            ("identity", self.status),
            ("operating_status", self.status),
        )
        return {aspect: record.get("capturedAt", "") for aspect, store in pairs if (record := store.get(cid))}

    def summary(self, row: dict) -> dict:
        """A compact model for the page's 'how we know this' disclosure."""
        cid = row.get("google_maps_cid", "").strip()
        captured = [
            record.get("capturedAt", "")[:10]
            for store in (self.amenities, self.attributes, self.hours, self.status)
            if (record := store.get(cid))
        ]
        return {
            "source_url": row.get("url", ""),
            "coordinate_source": clean_source(row.get("coordinate_source")),
            "verified_date": (row.get("verified_date", "") or "")[:10],
            "instagram_confidence": row.get("instagram_confidence", ""),
            "google_captured": max(captured) if captured else "",
            "has_maps_evidence": bool(captured),
        }
