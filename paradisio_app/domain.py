"""The typed core: what an establishment is, and what may be said about it.

Everything the directory publishes passes through this module. Its job is to turn
untyped CSV rows into validated objects so that the rules which protect people —
never inventing a WhatsApp route, never exposing contact actions for a closed
business, never emitting an insecure external link — live in one place instead of
being re-implemented at each call site.

Design notes
------------
*Dataclasses, not a validation library.* The programme plan originally proposed
Pydantic. It is not used: the production build has exactly two dependencies
(qrcode, pillow) and keeping it that way is a stated property of the system, not
an accident. The validation needed here is narrow and explicit, so the stdlib
covers it without adding weight to the deployed artifact.

*Fail closed.* Every normaliser returns an empty string for input it cannot
vouch for. A missing contact route is a correct outcome; a wrong one is not.

*Provenance is first class.* Fourteen columns of the master CSV record how each
record was acquired and verified. The generator historically ignored all of them
while the project's central claim was that its data is evidence-backed. They are
modelled here so that claim can be made good.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, fields
from urllib.parse import urlsplit, urlunsplit

# Location words that appear as decorative suffixes on scraped business names.
LOCATION_TOKENS = frozenset({
    "puerto viejo", "limon", "costa rica", "playa negra", "playa cocles",
    "playa chiquita", "punta uva", "playa punta uva", "cahuita", "manzanillo",
    "hone creek", "bribri", "sixaola", "gandoca", "cocles",
})

CLOSED_STATUSES = frozenset({"closed", "permanently_closed"})


# ---------------------------------------------------------------------------
# Normalisers — each fails closed
# ---------------------------------------------------------------------------

def normalize_phone(raw: str | None) -> str:
    """Return an international dialling target, or "" if the input is unusable.

    Costa Rican numbers are eight digits and are assumed local, so they gain the
    +506 country code. Anything that does not resolve to 10-15 digits is rejected
    rather than guessed at.
    """
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 8:
        digits = "506" + digits
    if re.fullmatch(r"\d{10,15}", digits):
        return "+" + digits
    return ""


def explicit_whatsapp(raw: str | None) -> str:
    """Return a WhatsApp destination **only** from an explicit source value.

    An ordinary phone number is never promoted to a WhatsApp route. Every route
    the site publishes was confirmed against a real WhatsApp profile; inferring
    them from phone numbers would send people to accounts that may not exist and
    may not belong to the business.
    """
    raw = (raw or "").strip()
    if not raw:
        return ""
    match = re.search(r"(?:phone=|wa\.me/)(\d{8,15})", raw)
    digits = match.group(1) if match else re.sub(r"\D", "", raw)
    if len(digits) == 8:
        digits = "506" + digits
    if not re.fullmatch(r"\d{10,15}", digits):
        return ""
    return "+" + digits


def safe_external_url(raw: str | None) -> str:
    """Return an https URL, or "" — never upgrade or repair a bad one."""
    value = (raw or "").strip()
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment))


def safe_instagram_handle(raw: str | None) -> str:
    """Return a syntactically valid Instagram handle, without the leading @."""
    handle = (raw or "").strip().lstrip("@")
    return handle if re.fullmatch(r"[A-Za-z0-9._]{1,30}", handle) else ""


def clean_display_name(raw_name: str, area: str) -> str:
    """Strip the location decoration that source listings append to names."""
    name = (raw_name or "").strip()
    if not name:
        return name
    area_l = (area or "").lower()
    if " - " in name:
        left, right = name.split(" - ", 1)
        if any(t in right.lower() for t in LOCATION_TOKENS) or (area_l and area_l in right.lower()):
            name = left.strip()
            if " - " in name:
                left2, right2 = name.split(" - ", 1)
                if any(t in right2.lower() for t in LOCATION_TOKENS) or (area_l and area_l in right2.lower()):
                    name = left2.strip()
    name = re.sub(r"[,–—\- ]*Costa Rica$", "", name, flags=re.IGNORECASE).strip()
    parts = re.split(r"\s*,\s*", name)
    if len(parts) > 1:
        suffix = parts[-1].strip().lower()
        if suffix in LOCATION_TOKENS or (area_l and suffix == area_l):
            name = ",".join(parts[:-1]).strip()
    name = re.sub(r"[\s,–—-]+$", "", name).strip()
    return name if name else (raw_name or "").strip()


def slugify(name: str, area: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", f"{name}-{area}".lower().strip()).strip("-")
    return slug[:80]


def record_id(name: str, cid: str, phone: str) -> str:
    return hashlib.md5(f"{name}|{cid}|{phone}".encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ContactRoutes:
    """Every way the public may be routed to a business.

    Constructed only through :meth:`from_row`, so a route present here has already
    passed validation. `whatsapp` is populated exclusively from an explicit
    source column.
    """

    phone_display: str = ""
    phone_e164: str = ""
    whatsapp: str = ""
    instagram: str = ""
    instagram_verified: bool = False
    facebook_url: str = ""
    website: str = ""
    booking_url: str = ""
    tripadvisor_url: str = ""
    google_maps_cid: str = ""
    email: str = ""
    # Channels held in the dataset but not yet surfaced by the renderer.
    tiktok_url: str = ""
    youtube_url: str = ""
    twitter_url: str = ""
    other_social_urls: str = ""

    @classmethod
    def from_row(cls, row: dict[str, str]) -> ContactRoutes:
        phone_e164 = normalize_phone(row.get("normalized_phone", "") or row.get("phone", ""))
        return cls(
            # The display number is suppressed when it does not normalise, so the
            # page never shows a number the Call action would refuse to dial.
            phone_display=row.get("phone", "").strip() if phone_e164 else "",
            phone_e164=phone_e164,
            whatsapp=explicit_whatsapp(row.get("whatsapp", "")),
            instagram=safe_instagram_handle(row.get("instagram_handle", "")),
            instagram_verified=row.get("instagram_confidence", "").strip() == "verified",
            facebook_url=safe_external_url(row.get("facebook_url", "")),
            website=safe_external_url(row.get("website", "")),
            booking_url=safe_external_url(row.get("booking_url", "")),
            tripadvisor_url=safe_external_url(row.get("tripadvisor_url", "")),
            google_maps_cid=row.get("google_maps_cid", "").strip(),
            email=row.get("email", "").strip(),
            tiktok_url=safe_external_url(row.get("tiktok_url", "")),
            youtube_url=safe_external_url(row.get("youtube_url", "")),
            twitter_url=safe_external_url(row.get("twitter_url", "")),
            other_social_urls=row.get("other_social_urls", "").strip(),
        )

    def social_channels(self) -> list[tuple[str, str]]:
        """Secondary social channels the dataset holds. Currently unrendered."""
        pairs = [("TikTok", self.tiktok_url), ("YouTube", self.youtube_url), ("Twitter", self.twitter_url)]
        return [(label, url) for label, url in pairs if url]


@dataclass(frozen=True)
class Provenance:
    """How this record came to exist, and when it was last confirmed.

    These fields are read straight from the master CSV, where they are populated
    for roughly two thirds of records. They answer "how do we know this?" and are
    the raw material for the provenance surface in Leg 3.
    """

    source_url: str = ""
    coordinate_source: str = ""
    geofilter: str = ""
    geofilter_reason: str = ""
    instagram_source: str = ""
    instagram_enriched_on: str = ""
    instagram_enrich_confidence: str = ""
    instagram_confidence: str = ""
    instagram_verified_flag: str = ""
    instagram_verified_on: str = ""
    verified_date: str = ""

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Provenance:
        def value(key: str) -> str:
            return (row.get(key) or "").strip()

        return cls(
            source_url=value("url"),
            coordinate_source=value("coordinate_source"),
            geofilter=value("geofilter"),
            geofilter_reason=value("geofilter_reason"),
            instagram_source=value("instagram_enrich_source"),
            instagram_enriched_on=value("instagram_enrich_date"),
            instagram_enrich_confidence=value("instagram_enrich_confidence"),
            instagram_confidence=value("instagram_confidence"),
            instagram_verified_flag=value("ig_verified"),
            instagram_verified_on=value("ig_verify_date"),
            verified_date=value("verified_date"),
        )

    def has_any(self) -> bool:
        """True when anything is known about how this record was acquired."""
        return any(getattr(self, f.name) for f in fields(self))


@dataclass(frozen=True)
class Establishment:
    """One business in the directory, validated."""

    record_id: str
    display_name: str
    raw_name: str
    category: str
    area: str
    latitude: str
    longitude: str
    distance_km: str
    status: str
    description: str
    contact: ContactRoutes = field(default_factory=ContactRoutes)
    provenance: Provenance = field(default_factory=Provenance)

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Establishment:
        raw_name = (row.get("business_name") or "").strip()
        area = (row.get("area") or "").strip()
        return cls(
            record_id=record_id(raw_name, row.get("google_maps_cid", ""), row.get("phone", "")),
            display_name=clean_display_name(raw_name, area),
            raw_name=raw_name,
            category=(row.get("category") or "").strip(),
            area=area or "Unknown",
            latitude=(row.get("latitude") or "").strip(),
            longitude=(row.get("longitude") or "").strip(),
            distance_km=(row.get("distance_km") or "").strip(),
            status=(row.get("operating_status") or "").strip() or "unknown",
            description=(row.get("description_full") or "").strip(),
            contact=ContactRoutes.from_row(row),
            provenance=Provenance.from_row(row),
        )

    @property
    def is_closed(self) -> bool:
        return self.status.lower() in CLOSED_STATUSES

    @property
    def slug(self) -> str:
        return slugify(self.raw_name, self.area)

    @property
    def has_coordinates(self) -> bool:
        return bool(self.latitude and self.longitude)

    def contactable_routes(self) -> ContactRoutes:
        """Routes that may be published.

        A closed business exposes none. This is enforced here rather than at each
        render site, so a new surface cannot forget it.
        """
        return ContactRoutes() if self.is_closed else self.contact
