"""How old a published fact is allowed to be, and what to do when it is older.

The directory's only real asset is that people believe it. A tourist who follows
stale hours to a closed restaurant does not file a bug report — they stop using
the site and tell their friends. So the governing rule here is not "keep the data
fresh", which no single maintainer can promise, but:

    **a fact we can no longer stand behind is labelled, never asserted.**

That distinction is what makes the whole thing survivable. Re-verification runs
against Google Maps and will sometimes fail — the markup changes, a request is
blocked, a place is gone. When it does, the page must degrade to "last checked in
March" rather than either lying or breaking.

Ages measured on the current dataset, which is what these thresholds are set
against rather than guessed at:

* listing verification has a median age of 266 days, 446 records are over 180
  days old, 178 are over a year, and the oldest is 1,558 days;
* every Google Maps capture is 29 days old, having been taken in one batch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

# Days after which a fact stops being presented as current. Set per aspect,
# because these things change at genuinely different rates: a restaurant's hours
# shift with the season, its coordinates never move.
POLICY_DAYS = {
    "hours": 60,
    "amenities": 180,
    "attributes": 180,
    "identity": 365,          # name, category, area
    "operating_status": 180,  # the costliest thing to get wrong
    "contact": 365,           # phone and WhatsApp routes
    "instagram": 180,
    "coordinates": None,      # places do not move
}

# Within this fraction of the threshold a fact is "aging": still shown as
# current, but queued for re-checking before it expires.
AGING_FRACTION = 0.75

# How old a captured schedule may be before the page stops asserting a live
# "Open now" and falls back to "Hours as listed". Deliberately stricter than the
# 60-day hours policy above: listing a schedule that might be out of date is
# reasonable, telling someone a place is open right now on the strength of it is
# not.
#
# NOTE FOR THE OWNER: captures are currently 29 days old, so this threshold is
# never satisfied and the open-now badge is dormant on every page. The safety
# mechanism is doing its job; the fix is a faster re-verification cadence, not a
# looser threshold. Raising this number would trade a dormant feature for a
# confidently wrong one, so it is left as a decision rather than taken here.
LIVE_STATUS_MAX_AGE_DAYS = 21

FRESH, AGING, STALE, UNKNOWN = "fresh", "aging", "stale", "unknown"


def parse_date(value: str | None) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:26] if "." in text else text[:19] if "T" in text else text[:10], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def age_days(value: str | None, today: date) -> int | None:
    captured = parse_date(value)
    if captured is None:
        return None
    return (today - captured).days


def state_for(aspect: str, captured: str | None, today: date) -> str:
    """Classify one aspect of one record."""
    threshold = POLICY_DAYS.get(aspect)
    age = age_days(captured, today)
    if age is None:
        # Coordinates never expire, so having no capture date is not a problem
        # worth reporting; for everything else it is genuinely unknown.
        return FRESH if threshold is None else UNKNOWN
    if threshold is None:
        return FRESH
    if age > threshold:
        return STALE
    if age > threshold * AGING_FRACTION:
        return AGING
    return FRESH


@dataclass(frozen=True)
class Assessment:
    """Every aspect of one record, with the worst state surfaced."""

    aspects: dict[str, str]
    ages: dict[str, int | None]

    @property
    def worst(self) -> str:
        for state in (STALE, UNKNOWN, AGING):
            if state in self.aspects.values():
                return state
        return FRESH

    @property
    def stale_aspects(self) -> list[str]:
        return sorted(a for a, s in self.aspects.items() if s == STALE)

    def is_stale(self, aspect: str) -> bool:
        return self.aspects.get(aspect) == STALE

    def needs_attention(self) -> bool:
        return self.worst in (STALE, UNKNOWN)


def assess(row: dict, captures: dict[str, str], today: date | None = None) -> Assessment:
    """Assess a record.

    `captures` carries the capture timestamps from the verified sidecars, keyed
    by aspect (``hours``, ``amenities``, ``attributes``).
    """
    today = today or date.today()
    verified = row.get("verified_date", "")
    sources = {
        "identity": verified,
        "operating_status": verified,
        "contact": verified,
        "instagram": row.get("ig_verify_date") or row.get("instagram_enrich_date") or verified,
        "coordinates": verified,
        "hours": captures.get("hours", ""),
        "amenities": captures.get("amenities", ""),
        "attributes": captures.get("attributes", ""),
    }
    aspects, ages = {}, {}
    for aspect, captured in sources.items():
        # Only assess an aspect the record actually has.
        if aspect in ("hours", "amenities", "attributes") and not captured:
            continue
        aspects[aspect] = state_for(aspect, captured, today)
        ages[aspect] = age_days(captured, today)
    return Assessment(aspects=aspects, ages=ages)


def priority(assessment: Assessment, row: dict) -> int:
    """Re-verification priority. Higher is more urgent.

    Weighted so that the failures which cost a visitor a wasted journey outrank
    the ones that merely leave a page thin.
    """
    score = 0
    if assessment.is_stale("operating_status"):
        score += 100
    if assessment.is_stale("hours"):
        score += 60
    if assessment.is_stale("contact"):
        score += 40
    if assessment.is_stale("identity"):
        score += 20
    if assessment.is_stale("instagram"):
        score += 10
    if row.get("operating_status", "").strip() == "needs_verification":
        score += 80
    # A record people can actually act on is worth more than one they cannot.
    if row.get("whatsapp", "").strip() or row.get("phone", "").strip():
        score += 5
    return score
