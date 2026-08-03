"""Publication-time consistency validator for enriched business records.

Checks the verified enrichment data for structural and editorial consistency
before publication. Structural schedule invariants are ERRORS (exit 1).
Editorial / data-quality disagreements are WARNINGS collected into a report
(they require human review, not a build failure).

Usage:
  python scripts/validate_publication_consistency.py [--report audit/publication-consistency-report.json]

Exit codes:
  0 = no structural errors (warnings may exist)
  1 = one or more structural ERRORS
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paradisio_app import build

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_NAMES = {
    "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday",
    "thursday": "Thursday", "friday": "Friday", "saturday": "Saturday", "sunday": "Sunday",
}

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def _minutes(t: str) -> int | None:
    m = TIME_RE.match(t or "")
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def _interval_ok(p) -> bool:
    o = _minutes(p.get("opens"))
    c = _minutes(p.get("closes"))
    return o is not None and c is not None


def check_weekly_schedule(weekly: dict) -> list[str]:
    """Structural schedule invariants. Returns a list of ERROR strings."""
    errors: list[str] = []
    keys = list(weekly.keys())
    for day in keys:
        if day not in WEEKDAYS:
            errors.append(f"unknown weekday key '{day}'")
    # Duplicate canonical weekday cannot occur in a dict, but guard defensively.
    if len(keys) != len(set(keys)):
        errors.append("duplicate canonical weekday present")
    for day in WEEKDAYS:
        d = weekly.get(day)
        if d is None:
            continue
        if d.get("closed") and d.get("periods"):
            errors.append(f"{WEEKDAY_NAMES[day]}: closed but has periods")
        if d.get("closed") and d.get("open24Hours"):
            errors.append(f"{WEEKDAY_NAMES[day]}: both closed and open24Hours")
        # open24Hours with the canonical 00:00-24:00 period is the normal
        # representation; anything else alongside open24Hours is contradictory.
        if d.get("open24Hours"):
            canonical_24h = d.get("periods") == [{"opens": "00:00", "closes": "24:00", "closesNextDay": False}] or d.get("periods") == [{"opens": "00:00", "closes": "24:00"}]
            if not canonical_24h:
                errors.append(f"{WEEKDAY_NAMES[day]}: open24Hours combined with non-canonical periods {d.get('periods')}")
        for p in d.get("periods", []):
            if not _interval_ok(p):
                errors.append(f"{WEEKDAY_NAMES[day]}: invalid interval {p}")
                continue
            o = _minutes(p["opens"])
            c = _minutes(p["closes"])
            if p.get("closesNextDay") and c is not None and o is not None and c >= o:
                # An overnight period must close numerically earlier than it opens.
                errors.append(f"{WEEKDAY_NAMES[day]}: closesNextDay set but closes ({p['closes']}) >= opens ({p['opens']})")
            if not p.get("closesNextDay") and c is not None and o is not None and c < o:
                errors.append(f"{WEEKDAY_NAMES[day]}: period crosses midnight without closesNextDay ({p['opens']}-{p['closes']})")
        # Overlapping non-overnight periods.
        periods = sorted(
            [p for p in d.get("periods", []) if not p.get("closesNextDay") and _interval_ok(p)],
            key=lambda p: _minutes(p["opens"]),
        )
        for i in range(len(periods) - 1):
            a_end = _minutes(periods[i]["closes"])
            b_start = _minutes(periods[i + 1]["opens"])
            if a_end is not None and b_start is not None and a_end > b_start:
                errors.append(f"{WEEKDAY_NAMES[day]}: overlapping periods {periods[i]['opens']}-{periods[i]['closes']} and {periods[i+1]['opens']}-{periods[i+1]['closes']}")
    return errors


# Phrases in a hand-written description that assert schedule facts.
DESCRIPTION_DAY_CLAIMS = {
    "sunday": re.compile(r"\b(sundays?\b|domingo)", re.I),
    "monday": re.compile(r"\b(mondays?\b|lunes)", re.I),
    "tuesday": re.compile(r"\b(tuesdays?\b|martes)", re.I),
    "wednesday": re.compile(r"\b(wednesdays?\b|mi[eé]rcoles)", re.I),
    "thursday": re.compile(r"\b(thursdays?\b|jueves)", re.I),
    "friday": re.compile(r"\b(fridays?\b|viernes)", re.I),
    "saturday": re.compile(r"\b(saturdays?\b|s[aá]bado)", re.I),
    "24_7": re.compile(r"\b(24[/\\-]?7|open daily|all day,? every day)\b", re.I),
    "closed": re.compile(r"\bclosed\b", re.I),
}


def check_description_hours(business: dict) -> list[str]:
    """Detect description schedule claims that conflict with verified hours.

    Returns WARNING strings. Only flags when the description mentions a day or
    an always-open claim that contradicts the verified schedule.
    """
    warnings: list[str] = []
    weekly = business.get("weekly_hours") or {}
    description = business.get("description") or ""
    name = business.get("name", "")
    if not weekly or not description:
        return warnings

    low = description.lower()
    if "24/7" in low or "24-7" in low or "24 7" in low or "open daily" in low or "open 7 days" in low:
        # Any verified closed day or day without 24h operation conflicts.
        for day in WEEKDAYS:
            d = weekly.get(day)
            if d and (d.get("closed") or not d.get("open24Hours")):
                warnings.append({
                    "listingId": business.get("slug", name),
                    "issue": "description_hours_conflict",
                    "descriptionClaim": "open daily / 24-7",
                    "detail": f"verified {WEEKDAY_NAMES[day]} is {'closed' if d.get('closed') else 'not 24h'}",
                    "action": "human_review",
                })
                break

    for day, pattern in DESCRIPTION_DAY_CLAIMS.items():
        if day in ("24_7", "closed"):
            continue
        if pattern.search(description):
            d = weekly.get(day)
            if d is None:
                continue
            # "except Sunday" / "closed Sundays" style claim: description says the
            # day is closed, but verified hours list it open -> conflict.
            closed_claim = re.search(rf"except\s+{WEEKDAY_NAMES[day].lower()}|\bclosed\s+(?:on\s+)?{WEEKDAY_NAMES[day].lower()}|\b{day}\s+closed\b", description, re.I)
            if closed_claim and not d.get("closed"):
                warnings.append({
                    "listingId": business.get("slug", name),
                    "issue": "description_hours_conflict",
                    "descriptionClaim": f"{WEEKDAY_NAMES[day]} described as closed but verified schedule lists it open",
                    "verifiedHours": "open",
                    "action": "human_review",
                })
            # Open-claims-day where verified says closed.
            if d.get("closed"):
                warnings.append({
                    "listingId": business.get("slug", name),
                    "issue": "description_hours_conflict",
                    "descriptionClaim": f"mentions {WEEKDAY_NAMES[day]} while verified schedule lists it as closed",
                    "verifiedHours": "closed",
                    "action": "human_review",
                })
    return warnings


def check_taxonomy_type(business: dict) -> list[str]:
    """Flag suspicious category/type relationships (e.g. auto shop tagged medical)."""
    warnings: list[str] = []
    tags = set(business.get("semantic_tags", [])) | set(business.get("semantic_attributes", []))
    category = (business.get("category") or "").lower()
    name = business.get("name", "")
    if "medical" in tags:
        # Auto-repair businesses should not be medical (veterinary clinics are a
        # known follow-up, still flagged for review).
        auto_hints = ["taller", "auto", "car ", "automotriz", "mecánico", "mecanico", "repair", "lubric", "tire", "llanta"]
        lowered = f"{name} {business.get('description', '')}".lower()
        if any(h in lowered for h in auto_hints) and "vet" not in lowered and "mascota" not in lowered:
            warnings.append({
                "listingId": business.get("slug", name),
                "issue": "suspicious_taxonomy",
                "detail": f"business '{name}' tagged medical but name/description suggests automotive",
                "action": "human_review",
            })
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default=str(Path(__file__).resolve().parent.parent / "audit" / "publication-consistency-report.json"))
    args = parser.parse_args()

    with build.CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    businesses = [build.build_business(row) for row in rows]

    errors: list[dict] = []
    warnings: list[dict] = []

    for business in businesses:
        weekly = business.get("weekly_hours") or {}
        name = business.get("name", "")
        slug = business.get("slug", name)

        for err in check_weekly_schedule(weekly):
            errors.append({"listingId": slug, "severity": "ERROR", "issue": "schedule", "detail": f"{name}: {err}"})

        for warn in check_description_hours(business):
            warnings.append({"listingId": slug, "severity": "WARNING", **warn})

        for warn in check_taxonomy_type(business):
            warnings.append({"listingId": slug, "severity": "WARNING", **warn})

        # Fewer than seven days (partial schedule) is a WARNING, not an error.
        if weekly and len(weekly) < 7:
            missing = [WEEKDAY_NAMES[d] for d in WEEKDAYS if d not in weekly]
            warnings.append({
                "listingId": slug,
                "severity": "WARNING",
                "issue": "partial_schedule",
                "detail": f"{name}: {len(weekly)} of 7 days listed; missing {', '.join(missing)}",
            })

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generatedAt": __import__("datetime").datetime.now().isoformat(),
        "totalBusinesses": len(businesses),
        "errorCount": len(errors),
        "warningCount": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Validated {len(businesses)} businesses")
    print(f"ERRORS:   {len(errors)}")
    print(f"WARNINGS: {len(warnings)}")
    if errors:
        print(f"FAIL: {len(errors)} structural error(s) — see report")
        for e in errors[:20]:
            print(f"  ERROR {e['detail']}")
        return 1
    print("PASS: no structural schedule errors")
    if warnings:
        print(f"Report: {report_path} ({len(warnings)} warnings for review)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
