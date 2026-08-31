"""Presentation logic, expressed as data rather than markup.

Everything here decides *what* a page shows: which amenities are worth listing,
how a week of opening hours reads, which of thirty attributes deserve the
collapsed summary. Nothing here decides how it looks — no HTML, no escaping, no
class names beyond the semantic ones the template needs.

The split matters because this is the genuinely intricate part of the renderer
and it was previously interleaved with string concatenation, which made it
untestable without parsing the output back out again. As plain functions
returning plain data it can be asserted on directly.
"""

from __future__ import annotations

import json
from typing import Any

try:
    from .semantic_taxonomy import PRIMARY_CATEGORY_TAGS, TAG_LABELS
except ImportError:  # direct execution
    from semantic_taxonomy import PRIMARY_CATEGORY_TAGS, TAG_LABELS

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

CATEGORY_LABELS = {
    "hostel": "Hostel",
    "hotel": "Hotel",
    "nightlife": "Nightlife",
    "real_estate": "Real estate",
    "restaurant": "Restaurant",
    "services": "Services",
    "shopping": "Shopping",
    "tour_company": "Tours",
    "transport": "Transport",
    "vacation_rental": "Vacation rental",
    "wellness": "Wellness",
}

STATUS_LABELS = {
    "closed": "Closed",
    "permanently_closed": "Closed",
    "needs_verification": "Information needs review",
}

WEEKDAY_DISPLAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_FULL = {
    "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday", "thursday": "Thursday",
    "friday": "Friday", "saturday": "Saturday", "sunday": "Sunday",
}
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Volume thresholds for the Details summary.
DETAILS_EXPANSION_THRESHOLD = 8   # at or below this, show everything
DETAILS_SUMMARY_LIMIT = 6         # summary size for 9-20 attributes
DETAILS_LARGE_SUMMARY_LIMIT = 8   # summary size for 21+
AMENITY_EXPANSION_THRESHOLD = 5   # above this, collapse behind a disclosure


def category_label(category: str | None, t=None) -> str:
    key = (category or "").strip().lower()
    if t is not None:
        translated = t(f"category.{key}") if key else t("category.other")
        if translated != f"category.{key}":
            return translated
    return CATEGORY_LABELS.get(key, key.replace("_", " ").title() or "Other")


def status_label(status: str | None, t=None) -> str:
    """Return a reader-facing status, or "" when there is nothing to say.

    `active` and `unknown` deliberately produce nothing: a badge saying "active"
    is noise, and one saying "unknown" undermines records that are simply
    unremarkable.
    """
    key = (status or "").strip().lower()
    if key not in STATUS_LABELS:
        return ""
    if t is not None:
        lookup = "status.closed" if key in ("closed", "permanently_closed") else f"status.{key}"
        translated = t(lookup)
        if translated != lookup:
            return translated
    return STATUS_LABELS[key]


def friendly_month(year_month: str) -> str:
    """'2026-08' -> 'August 2026'."""
    try:
        year, month = year_month.split("-")
        return f"{MONTH_NAMES[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        return year_month


# ---------------------------------------------------------------------------
# Header sections
# ---------------------------------------------------------------------------

def rating(biz: dict, t=None) -> dict | None:
    value = biz.get("rating")
    if value is None:
        return None
    full = int(value)
    return {
        "value": value,
        "full_stars": full,
        "half_star": value % 1 >= 0.3,
        "source": t("biz.rating_source") if t else "from Google Maps",
    }


def address(biz: dict) -> str:
    """The address line, or "" when nothing useful is known.

    Maps addresses beginning with M, F or C are skipped: in this dataset those
    are day-of-week fragments that leaked out of the hours block during the
    original OCR enrichment, not street addresses.
    """
    parts = []
    maps_address = biz.get("maps_address")
    if maps_address and not maps_address.startswith(("M", "F", "C")):
        parts.append(maps_address)
    plus_code = biz.get("plus_code")
    if plus_code:
        parts.append(plus_code)
    if not parts and maps_address:
        parts.append(maps_address)
    if not parts:
        area = biz.get("area", "")
        if area and area != "Unknown":
            parts.append(f"{area}, Puerto Viejo")
    return " · ".join(parts)


def _clean_time(value: str | None) -> str:
    return value.replace("?", "").replace(" ", " ") if value else ""


def hours_header(biz: dict) -> dict:
    """The status line above the fold.

    When verified weekly hours exist the legacy free-text status is suppressed
    entirely and the client computes the live state instead. Showing both
    produced pages that said "Open" in the header and "Closed now" below it.
    """
    has_verified = bool(biz.get("weekly_hours"))
    if has_verified:
        return {"mode": "verified_placeholder"}

    model: dict[str, Any] = {"mode": "legacy", "status": None, "hours_line": None, "check": None}
    raw_status = biz.get("open_status")
    if raw_status:
        clean = raw_status.replace(" ", " ").replace(" ", " ").strip().lower()
        is_open = "abierto" in clean or "open" in clean
        model["status"] = {"is_open": is_open, "label": "Open" if is_open else "Closed"}
    model["hours_line"] = biz.get("hours") or None

    check_in = _clean_time(biz.get("check_in"))
    check_out = _clean_time(biz.get("check_out"))
    if check_in and check_out:
        model["check"] = f"In {check_in} / Out {check_out}"
    elif check_in:
        model["check"] = f"In {check_in}"
    elif check_out:
        model["check"] = f"Out {check_out}"

    if not (model["status"] or model["hours_line"] or model["check"]):
        return {"mode": "none"}
    return model


def _format_period(period: dict) -> str:
    def clock(value: str) -> str:
        try:
            hour_text, minute = value.split(":")
            hour = int(hour_text)
            suffix = "AM" if hour < 12 else "PM"
            display_hour = hour % 12 or 12
            return f"{display_hour} {suffix}" if minute == "00" else f"{display_hour}:{minute} {suffix}"
        except ValueError:
            return value

    closes = clock(period.get("closes", ""))
    if period.get("closesNextDay"):
        closes += " (next day)"
    return f"{clock(period.get('opens', ''))} – {closes}"


def format_day_schedule(day: dict, t=None) -> str:
    closed = t("biz.hours_closed") if t else "Closed"
    if day.get("closed"):
        return closed
    if day.get("open24Hours"):
        return t("biz.hours_open_24") if t else "Open 24 hours"
    periods = day.get("periods", [])
    if not periods:
        return closed
    return " · ".join(_format_period(period) for period in periods)


def weekly_hours(biz: dict, t=None) -> dict | None:
    """The verified week, plus the payload the client uses for 'open now'."""
    weekly = biz.get("weekly_hours") or {}
    if not weekly:
        return None
    meta = biz.get("hours_meta") or {}
    captured_at = (meta.get("capturedAt") or "")[:7]

    rows = []
    for day in WEEKDAY_DISPLAY_ORDER:
        schedule = weekly.get(day)
        if schedule is None:
            rows.append({"day": WEEKDAY_FULL[day], "text": t("biz.hours_not_listed") if t else "Not listed", "unknown": True})
        else:
            rows.append({
                "day": schedule.get("displayDay") or WEEKDAY_FULL[day],
                "text": format_day_schedule(schedule, t),
                "unknown": False,
            })

    provenance = [t("biz.hours_from_maps") if t else "From Google Maps"]
    if captured_at:
        month = friendly_month(captured_at)
        provenance.append(t("biz.hours_updated", month=month) if t else f"Updated {month}")
    if meta.get("completeness", "partial") == "partial":
        provenance.append(t("biz.hours_partial") if t else "some days unavailable")

    # Serialised here rather than in the template. Jinja's `tojson` filter does
    # not escape double quotes — it targets <script> blocks — so using it inside
    # an HTML attribute terminates the attribute early and corrupts the markup.
    # Emitting a plain string lets the template's autoescaping handle quotes,
    # which is what the attribute context actually requires.
    payload_json = json.dumps(
        {
            "timezone": meta.get("timezone", "America/Costa_Rica"),
            "capturedAt": meta.get("capturedAt", ""),
            "weekly": weekly,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return {
        "rows": rows,
        "provenance": provenance,
        "collapsed": len(weekly) > 4,
        "payload_json": payload_json,
    }


def amenities(biz: dict) -> dict | None:
    items = biz.get("amenities", [])
    if not items:
        return None
    return {
        "items": items,
        "total": len(items),
        "collapsed": len(items) > AMENITY_EXPANSION_THRESHOLD,
    }


def semantic_facets(biz: dict, t=None, limit: int = 6) -> list[str]:
    """Type and quality chips, excluding the one implied by the category."""
    primary = PRIMARY_CATEGORY_TAGS.get((biz.get("category") or "").strip().lower())
    facets: list[str] = []
    for tag in list(biz.get("semantic_tags", [])) + list(biz.get("semantic_attributes", [])):
        if tag == primary or tag in facets:
            continue
        facets.append(tag)
    labels = []
    for tag in facets[:limit]:
        default = TAG_LABELS.get(tag, tag.replace("-", " ").title())
        labels.append(t(f"tag.{tag}") if t and t(f"tag.{tag}") != f"tag.{tag}" else default)
    return labels


def freshness(biz: dict, t=None) -> str:
    verified = biz.get("verified_date", "")
    if not verified:
        return ""
    date = verified[:10]
    return t("biz.captured", date=date) if t else f"Data captured {date}"


# ---------------------------------------------------------------------------
# About attributes
# ---------------------------------------------------------------------------

ATTRIBUTE_GROUP_LABELS = {
    "From the business": "From the business", "Accessibility": "Accessibility",
    "Service options": "Service options", "Highlights": "Highlights",
    "Popular for": "Popular for", "Offerings": "Offerings",
    "Dining options": "Dining options", "Amenities": "Amenities",
    "Atmosphere": "Atmosphere", "Crowd": "Crowd", "Planning": "Planning",
    "Payments": "Payments", "Children": "Children", "Parking": "Parking",
    "Pets": "Pets", "Booking options": "Booking options",
    "Location summary": "Location summary", "Essential info": "Essential info",
    "Hotel details": "Hotel details", "Room features": "Room features",
}

ATTRIBUTE_GROUP_PRIORITY = {
    "restaurant": ["Accessibility", "Service options", "Offerings", "Dining options", "Highlights", "Planning", "Parking"],
    "shopping": ["Accessibility", "Service options", "Offerings", "Planning", "Payments", "Parking"],
    "services": ["Accessibility", "Service options", "Planning", "Amenities", "Payments", "Parking"],
    "tour_company": ["Accessibility", "Service options", "Planning", "Children", "Amenities", "Parking"],
    "wellness": ["Accessibility", "Service options", "Planning", "Amenities", "Payments", "Parking"],
    "transport": ["Accessibility", "Service options", "Amenities", "Payments", "Parking"],
    "real_estate": ["Accessibility", "Service options", "Planning", "Parking"],
    "hotel": ["Accessibility", "Essential info", "Hotel details", "Room features", "Parking", "Planning"],
    "hostel": ["Accessibility", "Essential info", "Hotel details", "Parking", "Planning"],
    "vacation_rental": ["Accessibility", "Essential info", "Hotel details", "Room features", "Parking", "Planning"],
}

# Attributes a visitor is most likely to be deciding on.
ATTRIBUTE_HIGHLIGHT = {
    "Wheelchair-accessible entrance", "Wheelchair-accessible car park",
    "Wheelchair-accessible seating", "Wheelchair-accessible toilet",
    "Outdoor seating", "Delivery", "Takeaway", "Dine-in", "Vegan options",
    "Vegetarian options", "Free Wi-Fi", "Wi-Fi", "Accepts reservations",
    "Accepts bookings", "Free parking", "Free parking lot", "On-site parking",
    "Breakfast", "Pet-friendly", "Dogs allowed", "Live music",
}

# True of almost everywhere, so close to useless as a distinguishing signal.
ATTRIBUTE_LOW_VALUE = {
    "Casual", "Cosy", "Groups", "Tourists", "Credit cards", "Debit cards",
    "NFC mobile payments", "Good for kids",
}

# Values that mean the same thing; the richer wording wins.
ATTRIBUTE_DISPLAY_ALIASES = {
    ("Wi-Fi", "Free Wi-Fi"): "Free Wi-Fi",
    ("Parking", "Free parking"): "Free parking",
}


def _presentation_key(value: str) -> str:
    return " ".join(value.split()).casefold()


def clean_groups(groups: list[dict]) -> list[dict]:
    """Deduplicate within each group and collapse exact aliases."""
    cleaned = []
    for group in groups:
        items = [item for item in group.get("items", []) if item and item.strip()]
        if not items:
            continue
        deduped: list[str] = []
        seen: set[str] = set()
        for item in items:
            key = _presentation_key(item)
            replaced = False
            for (first, second), _display in ATTRIBUTE_DISPLAY_ALIASES.items():
                if key == _presentation_key(first) and _presentation_key(second) in seen:
                    replaced = True
                    break
                if key == _presentation_key(second) and _presentation_key(first) in seen:
                    replaced = True
                    break
            if replaced or key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        if deduped:
            name = group.get("group", "")
            cleaned.append({"group": name, "label": ATTRIBUTE_GROUP_LABELS.get(name, name), "items": deduped})
    return cleaned


def group_order(category: str, group_names: list[str]) -> list[str]:
    priority = ATTRIBUTE_GROUP_PRIORITY.get((category or "").lower(), [])
    index = {name: position for position, name in enumerate(priority)}
    return sorted(group_names, key=lambda name: index.get(name, len(priority)))


def rank_summary_items(groups: list[dict], category: str, limit: int) -> list[tuple[str, str, str]]:
    """Choose the attributes worth showing before the reader expands anything.

    Scored by group priority, lifted for decision-relevant attributes and
    lowered for near-universal ones, then capped at two per group on the first
    pass so one rich group cannot crowd out the rest.
    """
    order = {name: position for position, name in enumerate(group_order(category, [g["group"] for g in groups]))}
    candidates = []
    for group in groups:
        position = order.get(group["group"], 999)
        for item in group["items"]:
            score = 50 - position * 10
            if item in ATTRIBUTE_HIGHLIGHT:
                score += 40
            if item in ATTRIBUTE_LOW_VALUE:
                score -= 30
            candidates.append((score, group["group"], group["label"], item))
    candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))

    chosen: list[tuple[str, str, str]] = []
    per_group: dict[str, int] = {}
    for _score, group_name, label, value in candidates:
        if per_group.get(group_name, 0) >= 2:
            continue
        chosen.append((group_name, label, value))
        per_group[group_name] = per_group.get(group_name, 0) + 1
        if len(chosen) >= limit:
            return chosen
    for _score, group_name, label, value in candidates:
        if any(existing == value and name == group_name for name, _, existing in chosen):
            continue
        chosen.append((group_name, label, value))
        if len(chosen) >= limit:
            break
    return chosen


def attributes(biz: dict, t=None) -> dict | None:
    """The Details section, or None when there is nothing worth showing."""
    raw = biz.get("attributes") or []
    if not raw:
        return None
    cleaned = clean_groups(raw)
    if not cleaned:
        return None

    category = (biz.get("category") or "").lower()
    total = sum(len(group["items"]) for group in cleaned)
    ordered_names = group_order(category, [group["group"] for group in cleaned])
    ordered = sorted(
        cleaned,
        key=lambda group: ordered_names.index(group["group"]) if group["group"] in ordered_names else len(ordered_names),
    )

    meta = biz.get("attribute_meta") or {}
    captured_at = (meta.get("capturedAt") or "")[:7]
    model: dict[str, Any] = {
        "total": total,
        "groups": ordered,
        "cid": biz.get("google_maps_cid", ""),
        "updated": (t("biz.updated_month", month=friendly_month(captured_at)) if t else f"Updated {friendly_month(captured_at)}") if captured_at else "",
        "collapsed": total > DETAILS_EXPANSION_THRESHOLD,
        "summary": None,
    }
    if model["collapsed"]:
        limit = DETAILS_LARGE_SUMMARY_LIMIT if total > 20 else DETAILS_SUMMARY_LIMIT
        model["summary"] = [value for _group, _label, value in rank_summary_items(ordered, category, limit)]
    return model


# ---------------------------------------------------------------------------
# Contact and navigation
# ---------------------------------------------------------------------------

def whatsapp_link(value: str) -> str:
    return "https://wa.me/" + value.lstrip("+") if value.startswith("+") else value


def map_links(biz: dict) -> dict:
    """Where the map pin and the Directions action point."""
    lat, lng = biz.get("lat"), biz.get("lng")
    cid = (biz.get("channels") or {}).get("google_maps_cid", "")
    embed = None
    if lat and lng:
        embed = {
            "lat": lat,
            "lng": lng,
            "open_url": f"https://www.google.com/maps?cid={cid}" if cid else f"https://www.google.com/maps?q={lat},{lng}",
        }
    if lat and lng:
        directions = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
    elif cid:
        directions = f"https://www.google.com/maps?cid={cid}"
    else:
        directions = ""
    return {"embed": embed, "directions": directions}


def sticky_actions(biz: dict, t=None) -> list[dict]:
    """The bottom bar. Share is always present; the rest only when routable."""
    channels = biz.get("channels") or {}
    primary = biz.get("primary_contact") or {}
    actions: list[dict] = []

    directions = map_links(biz)["directions"]
    if directions:
        actions.append({"kind": "directions", "icon": "Directions",
                        "label": t("biz.directions") if t else "Directions", "url": directions})

    whatsapp = channels.get("whatsapp") or ""
    phone = channels.get("phone_normalized") or ""
    show_call = bool(phone) and primary.get("type") != "Call"

    if primary.get("type") == "WhatsApp" and whatsapp:
        actions.append({"kind": "call", "icon": "WhatsApp", "label": "WhatsApp",
                        "url": whatsapp_link(whatsapp), "channel": "WhatsApp", "external": True})
    elif show_call:
        actions.append({"kind": "call", "icon": "Call", "label": t("biz.call") if t else "Call",
                        "url": f"tel:{phone}", "channel": "Call", "external": False})
    elif whatsapp:
        actions.append({"kind": "call", "icon": "WhatsApp", "label": "WhatsApp",
                        "url": whatsapp_link(whatsapp), "channel": "WhatsApp", "external": True})

    actions.append({"kind": "share", "icon": "Share", "label": t("biz.share") if t else "Share"})
    return actions


def describe(biz: dict, t=None) -> str:
    """The page's description.

    A description the business wrote is shown as written. One this generator
    composed is rebuilt in the page's language from its recorded facts.
    """
    facts = biz.get("description_facts")
    if facts:
        rendered = []
        for key, params in facts:
            resolved = dict(params)
            if "category_key" in resolved:
                resolved["category"] = category_label(resolved.pop("category_key"), t)
            rendered.append(_EN_DESCRIPTION[key].format(**resolved) if t is None else t(key, **resolved))
        return " ".join(rendered)
    written = biz.get("description")
    if written:
        return written
    return t("biz.no_description") if t else "No description available."


_EN_DESCRIPTION = {
    "desc.category_in_area": "{category} in {area}.",
    "desc.rated": "Rated {rating}/5 on Google Maps.",
    "desc.listed_since": "Listed since {month}.",
    "desc.phone": "Phone available.",
    "desc.instagram": "Active on Instagram.",
    "desc.whatsapp": "Accepts WhatsApp inquiries.",
    "desc.email": "Email available.",
}


CONTACT_LABEL_KEYS = {
    "WhatsApp": "biz.whatsapp",
    "Call": "biz.call",
    "Instagram": "biz.instagram_dm",
    "Website": "biz.website",
    "Map": "biz.open_in_maps",
    "None": "biz.no_contact",
}

SECONDARY_LABEL_KEYS = {"Call": "biz.call", "Website": "biz.website"}


def localise_contact(contact: dict, t=None) -> dict:
    """Translate a contact action's label without touching its target."""
    if not t or not contact:
        return contact
    key = CONTACT_LABEL_KEYS.get(contact.get("type"))
    if not key:
        return contact
    translated = t(key)
    if translated == key:
        return contact
    return {**contact, "label": translated}


def localise_links(links: list[dict], t=None) -> list[dict]:
    if not t:
        return links
    out = []
    for link in links:
        key = SECONDARY_LABEL_KEYS.get(link.get("label"))
        translated = t(key) if key else None
        out.append({**link, "display": translated} if translated and translated != key else {**link, "display": link["label"]})
    return out


def business_page(biz: dict, taxonomy_version: str, t=None) -> dict:
    """The complete model for one business page."""
    return {
        "slug": biz["slug"],
        "name": biz["name"],
        "area": biz["area"],
        "category_label": category_label(biz.get("category"), t),
        "status": biz.get("status", ""),
        "status_label": status_label(biz.get("status"), t),
        "description": describe(biz, t),
        "badges": biz.get("badges", []),
        "facets": semantic_facets(biz, t),
        "rating": rating(biz, t),
        "address": address(biz),
        "hours_header": hours_header(biz),
        "weekly_hours": weekly_hours(biz, t),
        "amenities": amenities(biz),
        "attributes": attributes(biz, t),
        "prices": (biz.get("prices") or [])[:3],
        "freshness": freshness(biz, t),
        "primary_contact": localise_contact(biz.get("primary_contact") or {}, t),
        "secondary_links": localise_links(biz.get("secondary_links") or [], t),
        "sticky_actions": sticky_actions(biz, t),
        "map": map_links(biz)["embed"],
        "taxonomy_version": taxonomy_version,
    }
