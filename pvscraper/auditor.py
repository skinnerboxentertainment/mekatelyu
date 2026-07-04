from collections import Counter
from typing import Optional
from .schema import ListingStore


class Auditor:
    def __init__(self, store: ListingStore):
        self.store = store

    def report(self) -> dict:
        conn = self.store.conn()

        total = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
        by_category = dict(
            conn.execute(
                "SELECT COALESCE(category, 'unknown'), COUNT(*) FROM listings GROUP BY category"
            ).fetchall()
        )
        by_area = dict(
            conn.execute(
                "SELECT COALESCE(area, 'unknown'), COUNT(*) FROM listings GROUP BY area"
            ).fetchall()
        )
        by_status = dict(
            conn.execute(
                "SELECT operating_status, COUNT(*) FROM listings GROUP BY operating_status"
            ).fetchall()
        )

        # Instagram coverage
        with_instagram = conn.execute(
            "SELECT COUNT(*) FROM listings WHERE instagram_handle IS NOT NULL AND instagram_handle != ''"
        ).fetchone()[0]
        ig_pct = round(with_instagram / total * 100, 1) if total else 0

        # Instagram coverage per category
        ig_rows = conn.execute(
            """SELECT COALESCE(category, 'unknown'),
                      COUNT(*) as total,
                      SUM(CASE WHEN instagram_handle IS NOT NULL AND instagram_handle != '' THEN 1 ELSE 0 END) as with_ig
               FROM listings GROUP BY category"""
        ).fetchall()
        ig_by_cat_pct = {}
        for row in ig_rows:
            cat, t, ig_count = row[0], row[1], row[2]
            ig_by_cat_pct[cat] = {"total": t, "with_instagram": ig_count, "pct": round(ig_count / t * 100, 1) if t else 0}

        # Missing fields
        missing = {}
        for field in ("phone", "website", "google_maps_cid", "instagram_handle", "facebook_url", "verified_date"):
            count_missing = conn.execute(
                f"SELECT COUNT(*) FROM listings WHERE ({field} IS NULL OR {field} = '')"
            ).fetchone()[0]
            missing[field] = {"missing": count_missing, "pct": round(count_missing / total * 100, 1) if total else 0}

        # Parser warnings
        with_warnings = conn.execute(
            "SELECT COUNT(*) FROM listings WHERE extraction_warnings IS NOT NULL AND extraction_warnings != ''"
        ).fetchone()[0]

        # Duplicates by name similarity (exact name match in same area)
        duplicates = list(
            conn.execute(
                """SELECT business_name, area, COUNT(*) as cnt
                   FROM listings
                   WHERE business_name IS NOT NULL AND business_name != ''
                   GROUP BY business_name, area
                   HAVING cnt > 1"""
            ).fetchall()
        )

        report = {
            "total_listings": total,
            "by_category": by_category,
            "by_area": by_area,
            "by_status": by_status,
            "instagram_coverage": {
                "total": with_instagram,
                "percentage": ig_pct,
                "by_category": ig_by_cat_pct,
            },
            "missing_fields": missing,
            "parser_warnings": {
                "total": with_warnings,
                "percentage": round(with_warnings / total * 100, 1) if total else 0,
            },
            "duplicates": {
                "count": len(duplicates),
                "records": [{"name": r[0], "area": r[1], "occurrences": r[2]} for r in duplicates],
            },
        }

        return report

    def print_report(self, report: Optional[dict] = None):
        if report is None:
            report = self.report()

        print("=" * 60)
        print("PV SATELLITE CRAWL AUDIT REPORT")
        print("=" * 60)
        print(f"\nTotal listings: {report['total_listings']}")
        print(f"Categories: {report['by_category']}")
        print(f"Areas: {report['by_area']}")
        print(f"Statuses: {report['by_status']}")
        print(f"\n--- Instagram Coverage ---")
        print(f"  Overall: {report['instagram_coverage']['total']} ({report['instagram_coverage']['percentage']}%)")
        for cat, data in report['instagram_coverage']['by_category'].items():
            print(f"  {cat}: {data['with_instagram']}/{data['total']} ({data['pct']}%)")
        print(f"\n--- Missing Fields ---")
        for field, data in report['missing_fields'].items():
            print(f"  {field}: {data['missing']} missing ({data['pct']}%)")
        print(f"\nParser warnings: {report['parser_warnings']['total']} ({report['parser_warnings']['percentage']}%)")
        print(f"Duplicate name+area groups: {report['duplicates']['count']}")
        if report['duplicates']['records']:
            for d in report['duplicates']['records'][:10]:
                print(f"  '{d['name']}' in {d['area']}: {d['occurrences']}x")
        print("=" * 60)
