"""Generate a Google Sheets-importable CSV for collaborative IG handle auditing.

Columns:
  A: Business Name
  B: Instagram Handle (plain text, import friendly)
  C: Instagram URL (HYPERLINK formula for Google Sheets)
  D: Category
  E: Area
  F: Signal Tier
  G: Status
  H: Verified? (TRUE/FALSE — Google Sheets converts to checkbox)
  I: Date of Last Post (manual fill)
  J: Activity Frequency (manual fill: Daily / Weekly / Monthly / Rarely / Never)
  K: Notes
"""

import csv, json
from pathlib import Path

REPORT = Path("ig_triage_report.json")
OUTPUT = Path("ig_audit_sheet.csv")

with open(REPORT, encoding="utf-8") as f:
    data = json.load(f)

rows = data["results"]

fieldnames = [
    "Business Name",
    "Instagram Handle",
    "Instagram URL",
    "Category",
    "Area",
    "Signal Tier",
    "Status",
    "Verified?",
    "Date of Last Post",
    "Activity Frequency",
    "Notes",
]

with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(fieldnames)
    for r in rows:
        handle = (r.get("handle") or "").strip()
        name = (r.get("business_name") or "").strip()
        category = (r.get("category") or "").strip()
        area = (r.get("area") or "").strip()
        tier = r.get("signal_tier")
        if tier is not None:
            tier_label = f"T{tier}"
        else:
            tier_label = "T?"
        status = (r.get("status") or "").strip()
        url = f"https://www.instagram.com/{handle}/"

        w.writerow([
            name,
            handle,
            f'=HYPERLINK("{url}","@{handle}")',
            category,
            area,
            tier_label,
            status,
            "FALSE",  # Verified checkbox, default unchecked
            "",  # Date of Last Post
            "",  # Activity Frequency
            "",  # Notes
        ])

print(f"Generated: {OUTPUT.resolve()}")
print(f"Rows: {len(rows)}")

# Also print instructions
print()
print("=== GOOGLE SHEETS IMPORT ===")
print("1. Go to sheets.new")
print("2. File > Import > Upload > select ig_audit_sheet.csv")
print("3. After import, select column H (Verified?)")
print("4. Format > Data validation > Checkbox")
print("5. Column C will have clickable HYPERLINK formulas")
