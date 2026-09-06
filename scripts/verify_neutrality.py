"""
Prove that money cannot buy position or inclusion in the directory.

The founding promise is that every business in town is listed by default and the
burden is on them to leave. Every revenue idea — premium listings, featured
placement, QR tiers — works by making some businesses more visible than others.
Run that far enough and the directory becomes an advertising surface, at which
point its one real differentiator is gone and no amount of later engineering
brings it back. Trust is not recoverable by apology.

So the line is drawn here rather than in intentions: payment may buy
**presentation** — better photos, a longer description, a claimed-and-maintained
badge — and may never buy **position** or **inclusion**.

This check is deliberately written before any revenue mechanism exists. Writing
it afterwards would mean asking whether the thing already built happens to be
fair, which is a much weaker question than refusing to build anything that is
not.

Three properties, each mechanically checked:

1. Inclusion is unconditional. Every canonical record becomes a page.
2. Ordering reads only data-completeness fields. Enforced by recording every
   field the scoring functions actually touch and comparing against an
   allowlist — so a new input is caught even if it is innocently named.
3. Nothing resembling a payment signal reaches the browser.

Usage:
  python scripts/verify_neutrality.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from paradisio_app import build  # noqa: E402

CSV_PATH = REPO / "pv_master_unified.csv"
RELEASE = REPO / "release"

# The only fields ordering is permitted to consider. Every one describes how
# complete a record is, never who paid. Adding to this list is a deliberate act
# and should be argued for in review.
ORDERING_MAY_READ = frozenset({
    "area",
    "booking_url",
    "business_name",
    "category",
    "description_full",
    "email",
    "facebook_url",
    "google_maps_cid",
    "instagram_confidence",
    "instagram_handle",
    "latitude",
    "normalized_phone",
    "operating_status",
    "phone",
    "tripadvisor_url",
    "verified_date",
    "website",
    "whatsapp",
})

# Words that would indicate money has entered the ordering or the payload.
# Matched case-insensitively against field names and client-facing text.
PAYMENT_WORDS = (
    "sponsor", "premium", "paid", "payment", "invoice", "subscription",
    "featured", "promoted", "boost", "tier", "billing", "sinpe",
)


class RecordingRow(dict):
    """A row that remembers which fields were read from it.

    This is the mechanism the whole check rests on. Rather than reading the
    scoring code and judging it fair, it runs the scoring code and reports what
    it actually touched — so a payment signal cannot hide behind a harmless
    field name, and nobody has to remember to update this file when the scoring
    changes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read: set[str] = set()

    def get(self, key, default=None):
        self.read.add(key)
        return super().get(key, default)

    def __getitem__(self, key):
        self.read.add(key)
        return super().__getitem__(key)


def fields_ordering_reads(sample: dict) -> set[str]:
    """Run every ordering input and report which fields it consulted."""
    row = RecordingRow(sample)
    build.contactability_score(row)
    build.visibility_score(row)
    build.completeness_score(row)
    return set(row.read)


def check_ordering_inputs(sample: dict) -> list[str]:
    errors = []
    touched = fields_ordering_reads(sample)
    unexpected = sorted(touched - ORDERING_MAY_READ)
    if unexpected:
        errors.append(
            f"ordering now reads {len(unexpected)} undeclared field(s): {unexpected}. "
            f"If any of these carry a payment signal, position is for sale. Add them "
            f"to ORDERING_MAY_READ only if they describe how complete a record is."
        )
    for field in sorted(touched):
        lowered = field.lower()
        for word in PAYMENT_WORDS:
            if word in lowered:
                errors.append(f"ordering reads a payment-shaped field: {field!r}")
    return errors


def check_payment_cannot_change_a_score(sample: dict) -> list[str]:
    """A record that has 'paid' must score exactly what it scored before."""
    plain = dict(sample)
    paying = dict(sample)
    paying.update({
        "sponsor": "yes", "premium": "true", "paid": "2026-09-05",
        "tier": "gold", "featured": "1", "promoted": "true",
        "payment_status": "settled", "sponsorship_level": "platinum",
    })
    before = (
        build.contactability_score(plain),
        build.visibility_score(plain),
        build.completeness_score(plain),
    )
    after = (
        build.contactability_score(paying),
        build.visibility_score(paying),
        build.completeness_score(paying),
    )
    if before != after:
        return [f"paying changed a record's scores: {before} -> {after}"]
    return []


def check_inclusion_is_unconditional(rows: list[dict]) -> list[str]:
    """Every canonical record must reach the directory, with nothing to earn."""
    if not RELEASE.is_dir():
        return ["release/ not built; cannot check inclusion"]
    pages = {p.stem for p in (RELEASE / "businesses").glob("*.html")}
    businesses = [build.build_business(row) for row in rows]
    businesses.sort(key=lambda b: b["name"].lower())
    build.dedup_slugs(businesses)
    missing = [b["name"] for b in businesses if b["slug"] not in pages]
    if missing:
        shown = ", ".join(missing[:5])
        return [f"{len(missing)} canonical record(s) did not get a page: {shown}"]
    return []


def check_payload_is_clean() -> list[str]:
    """No payment vocabulary may reach the browser, in any language."""
    payloads = sorted((RELEASE / "static").glob("directory-data*.js"))
    if not payloads:
        return ["no release/static/directory-data*.js; cannot check the payload"]
    errors = []
    for payload in payloads:
        text = payload.read_text(encoding="utf-8", errors="replace").lower()
        for word in PAYMENT_WORDS:
            # Match as a word so "tier" does not fire on "frontier".
            # (This line once held literal backspace characters after a
            # shell heredoc ate the escapes, which made the check
            # incapable of ever matching. Hence the test below.)
            if re.search(rf"\b{re.escape(word)}\b", text):
                errors.append(f"{payload.name} mentions {word!r}")
    return errors


def main() -> int:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    sample = rows[0] if rows else {}

    errors: list[str] = []
    errors += check_ordering_inputs(sample)
    errors += check_payment_cannot_change_a_score(sample)
    errors += check_payload_is_clean()
    errors += check_inclusion_is_unconditional(rows)

    touched = sorted(fields_ordering_reads(sample))
    print("Neutrality check")
    print(f"  canonical records      {len(rows)}")
    payloads = sorted((RELEASE / "static").glob("directory-data*.js"))
    print(f"  ordering reads         {len(touched)} fields, all data-completeness")
    print(f"  payloads checked       {len(payloads)}")
    if errors:
        print()
        print(f"FAIL: {len(errors)} neutrality error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print()
    print("PASS: payment cannot buy position or inclusion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
