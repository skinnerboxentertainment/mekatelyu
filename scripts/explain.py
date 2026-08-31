"""Ask the dataset where a published fact came from.

    python scripts/explain.py "Ice Creams"
    python scripts/explain.py --cid 5579537716284560393
    python scripts/explain.py "Ice Creams" --field hours

This is the tool that turns "our data is evidence-backed" from a claim into
something anyone can check in under a minute. It reads only; it changes nothing.
"""

from __future__ import annotations

import argparse
import csv
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from paradisio_app.provenance import ProvenanceIndex  # noqa: E402

CSV_PATH = REPO / "pv_master_unified.csv"


def normalise(value: str) -> str:
    stripped = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    return " ".join(stripped.lower().split())


def load_rows() -> list[dict]:
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def find(rows: list[dict], query: str = "", cid: str = "") -> list[dict]:
    if cid:
        return [r for r in rows if r.get("google_maps_cid", "").strip() == cid.strip()]
    needle = normalise(query)
    return [r for r in rows if needle and needle in normalise(r.get("business_name", ""))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", nargs="?", default="", help="part of a business name")
    parser.add_argument("--cid", default="", help="exact Google Maps CID")
    parser.add_argument("--field", default="", help="only show evidence for fields containing this")
    args = parser.parse_args()

    if not args.query and not args.cid:
        parser.print_help()
        return 2

    rows = load_rows()
    matches = find(rows, args.query, args.cid)
    if not matches:
        print(f"No business matches {args.query or args.cid!r}.")
        return 1
    if len(matches) > 6:
        print(f"{len(matches)} businesses match. Narrow the query:")
        for row in matches[:20]:
            print(f"   {row['business_name']}")
        return 1

    index = ProvenanceIndex()
    for row in matches:
        print("=" * 72)
        print(f"{row['business_name']}   [{row.get('area', '')}]")
        cid = row.get("google_maps_cid", "").strip()
        print(f"CID: {cid or '(none)'}")
        print("=" * 72)
        evidence = index.explain(row)
        if args.field:
            needle = args.field.lower()
            evidence = [e for e in evidence if needle in e.field.lower()]
            if not evidence:
                print(f"No evidence recorded for a field matching {args.field!r}.")
                continue
        for item in evidence:
            print(item.describe())
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
