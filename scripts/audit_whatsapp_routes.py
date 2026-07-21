"""Audit WhatsApp routes without messaging businesses or enumerating accounts.

The report distinguishes syntactic validity and source evidence from actual account
ownership or availability. It never makes network requests and never changes the
master dataset.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def normalize_whatsapp(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    parsed = urlsplit(value)
    query_number = parse_qs(parsed.query).get("phone", [""])[0]
    path_match = re.search(r"(?:^|/)wa\.me/(\d{8,15})", value, re.I)
    digits = re.sub(r"\D", "", query_number or (path_match.group(1) if path_match else value))
    if len(digits) == 8:
        digits = "506" + digits
    return "+" + digits if re.fullmatch(r"\d{10,15}", digits) else ""


def key(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", type=Path, default=Path("pv_master_unified.csv"))
    parser.add_argument("--crawl", type=Path, default=Path("website_crawl_results.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("audit/launch-readiness/evidence"))
    args = parser.parse_args()

    with args.master.open(encoding="utf-8-sig", newline="") as handle:
        master = list(csv.DictReader(handle))
    with args.crawl.open(encoding="utf-8-sig", newline="") as handle:
        crawl = list(csv.DictReader(handle))

    crawl_by_name = {key(row.get("business_name", "")): row for row in crawl}
    number_owners: dict[str, list[str]] = defaultdict(list)
    rows = []
    for business in master:
        name = business.get("business_name", "").strip()
        raw = business.get("whatsapp", "").strip()
        normalized = normalize_whatsapp(raw)
        crawled = crawl_by_name.get(key(name), {})
        crawl_raw = crawled.get("whatsapp", "").strip()
        crawl_normalized = normalize_whatsapp(crawl_raw)
        evidence = "master_explicit" if raw else ""
        if crawl_normalized and crawl_normalized == normalized:
            evidence = "master_explicit+first_party_crawl"
        elif crawl_normalized and not raw:
            evidence = "first_party_crawl_candidate"
        elif crawl_raw and not crawl_normalized:
            evidence = "crawl_value_invalid"
        status = "no_route"
        if raw and normalized:
            status = "syntax_valid_unconfirmed"
        elif raw:
            status = "invalid_route"
        elif crawl_normalized:
            status = "candidate_not_promoted"
        if normalized:
            number_owners[normalized].append(name)
        rows.append({
            "business_name": name,
            "phone": business.get("phone", "").strip(),
            "whatsapp_raw": raw,
            "whatsapp_normalized": normalized,
            "status": status,
            "evidence": evidence,
            "evidence_url": crawled.get("url", "").strip() if crawl_raw else "",
            "crawl_whatsapp": crawl_raw,
            "last_checked": date.today().isoformat(),
            "note": "No message sent; account ownership/availability not verified.",
        })

    for row in rows:
        owners = number_owners.get(row["whatsapp_normalized"], [])
        row["shared_route_count"] = len(owners) if row["whatsapp_normalized"] else 0
        row["shared_route_businesses"] = " | ".join(owners) if len(owners) > 1 else ""

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "whatsapp-route-audit.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["status"] for row in rows)
    shared = {number: owners for number, owners in number_owners.items() if len(owners) > 1}
    report = [
        "# WhatsApp route audit",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "This is a non-messaging, offline audit. `syntax_valid_unconfirmed` means only that a",
        "route can be safely constructed; it does not establish that the account exists, is",
        "monitored, or belongs to the listed business.",
        "",
        "## Results",
        "",
        f"- Directory records: {len(rows)}",
        f"- Explicit, syntactically valid WhatsApp routes: {counts['syntax_valid_unconfirmed']}",
        f"- Invalid explicit routes: {counts['invalid_route']}",
        f"- First-party crawl candidates not yet promoted: {counts['candidate_not_promoted']}",
        f"- Records without a WhatsApp route: {counts['no_route']}",
        f"- Numbers shared by multiple listings: {len(shared)}",
        "",
        "## Interpretation",
        "",
        "The prior website crawl was reconciled by exact normalized business name. A crawl link",
        "is treated as stronger evidence than an ordinary phone number, but it is not called",
        "verified without owner confirmation. No phone number was inferred to be WhatsApp-capable.",
        "",
        "A live `wa.me` landing-page probe is intentionally excluded: on 2026-07-20 both an",
        "existing candidate and the impossible control number `+50600000000` returned HTTP 200",
        "and redirected to the same generic send page. That mechanism cannot reliably distinguish",
        "working accounts and would produce false positives.",
    ]
    (args.output_dir / "whatsapp-route-audit.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report[8:14]))
    print(f"CSV: {csv_path}")
    return 1 if counts["invalid_route"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
