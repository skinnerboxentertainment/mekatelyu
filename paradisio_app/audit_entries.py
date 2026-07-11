"""
QA Audit — reads every entry, flags issues, outputs action list.
Read-only. No modifications.
"""
import csv
import json
import re
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent.parent
MASTER_CSV = BASE / "pv_master_unified.csv"
ENRICH_V3 = BASE / "docs" / "paradisio_app" / "data" / "maps_parsed_v3.json"
BIZ_JSON = BASE / "docs" / "paradisio_app" / "data" / "businesses.json"
OUTPUT = BASE / "docs" / "paradisio_app" / "data" / "audit_report.json"

# Category keywords for name-based alignment
CAT_KEYWORDS = {
    "hotel": ["hotel", "lodge", "resort", "inn", "villas", "villa",
              "cabinas", "cabañas", "bungalow", "guest", "posada",
              "suites", "apartamentos", "apartotel", "hostel",
              "vacation rental", "beach house", "cottage"],
    "hostel": ["hostel", "backpackers", "dorm", "bunk"],
    "restaurant": ["restaurant", "restaurante", "cafe", "soda", "pizzeria",
                   "grill", "parrilla", "marisqueria", "comida",
                   "ice cream", "heladeria", "panaderia", "bakery",
                   "brewery", "bar & grill", "cocktail"],
    "tour_company": ["tour", "travel", "adventure", "snorkel", "diving",
                     "surf", "kayak", "paragliding", "zipline",
                     "expedition", "charter", "boat tour", "nature"],
    "shopping": ["supermarket", "supermercado", "tienda", "store",
                 "boutique", "mercado", "market", "farmacia",
                 "souvenir", "grocery", "liquor", "hardware"],
    "services": ["massage", "spa", "salon", "barber", "laundry",
                 "gym", "fitness", "yoga", "rental", "alquiler",
                 "taller", "shuttle", "taxi", "transport",
                 "real estate", "bienes raices", "bank", "atm",
                 "clinic", "dentist", "repair"],
    "Wellness": ["massage", "spa", "yoga", "wellness", "masajes", "fitness"],
    "Nightlife": ["bar", "cocktail", "brewery", "pub", "nightclub", "disco"],
    "Transport": ["taxi", "shuttle", "transport", "rental car", "alquiler"],
}

LOCATION_TOKENS = {
    "puerto viejo", "limon", "costa rica", "playa negra", "playa cocles",
    "playa chiquita", "punta uva", "playa punta uva", "cahuita",
    "manzanillo", "hone creek", "bribri", "sixaola", "gandoca", "cocles",
    "talamanca",
}

NAME_ARTICLES = {"the", "el", "la", "los", "las", "un", "una"}


def clean(s):
    return (s or "").strip()


def keyword_categories(name, subcat=""):
    text = f"{name} {subcat}".lower()
    matches = {}
    for cat, kws in CAT_KEYWORDS.items():
        count = sum(1 for k in kws if k in text)
        if count:
            matches[cat] = count
    return matches


def audit_entry(biz, enrich_subcat):
    issues = []
    fixes = []
    name = clean(biz.get("name", "")) or clean(biz.get("business_name", ""))
    cat = clean(biz.get("category", ""))
    area = clean(biz.get("area", ""))
    subcat = clean(enrich_subcat or "")
    desc = clean(biz.get("description", ""))
    phone = clean(biz.get("channels", {}).get("phone", ""))
    cid = clean(biz.get("channels", {}).get("google_maps_cid", ""))
    website = clean(biz.get("channels", {}).get("website", ""))
    wp = clean(biz.get("channels", {}).get("whatsapp", ""))

    # 1. Category alignment
    keyword_hits = keyword_categories(name, subcat)
    if cat and keyword_hits:
        best_cat = max(keyword_hits, key=keyword_hits.get)
        # Check if assigned category matches the best keyword match
        cat_lower = cat.lower()
        assigned_normalized = cat_lower
        best_normalized = best_cat.lower()
        # Allow some aliases
        alias = {"Wellness": "wellness", "Nightlife": "nightlife",
                 "Transport": "transport", "hotel": "hotel",
                 "restaurant": "restaurant", "services": "services",
                 "shopping": "shopping", "tour_company": "tour_company"}
        if alias.get(assigned_normalized, assigned_normalized) != alias.get(best_normalized, best_normalized):
            # Check if the mismatch is severe (big difference)
            cat_groups = {
                "hotel": "lodging", "hostel": "lodging", "vacation_rental": "lodging",
                "restaurant": "food", "tour_company": "activities",
                "shopping": "retail", "services": "services",
                "wellness": "services", "Wellness": "services",
                "nightlife": "food", "Nightlife": "food",
                "transport": "services", "Transport": "services",
                "real_estate": "services",
            }
            assigned_group = cat_groups.get(assigned_normalized, "other")
            best_group = cat_groups.get(best_normalized, "other")
            if assigned_group != best_group:
                issues.append(f"Category mismatch: '{cat}' but name/subcategory suggests '{best_cat}'")
                fixes.append(f"Consider changing category from '{cat}' to '{best_cat}'")
    elif not cat:
        issues.append("No category assigned")
        if keyword_hits:
            best = max(keyword_hits, key=keyword_hits.get)
            fixes.append(f"Assign category '{best}' based on name")

    # 2. Missing critical fields
    if not phone and not wp and not cid:
        issues.append("No phone, WhatsApp, or CID — unreachable")
    if not cid:
        issues.append("Missing Google Maps CID — no enrichment possible")
    if not website:
        issues.append("No website listed")
    if not area:
        issues.append("Area not set")

    # 3. Name quality
    # Check for location suffix in name
    name_lower = name.lower()
    found_locations = [t for t in LOCATION_TOKENS if t in name_lower]
    if found_locations:
        issues.append(f"Name contains location suffix: {found_locations[0]}")
        fixes.append("Strip location suffix from business name")

    # Check name length
    if name and len(name) > 60:
        issues.append(f"Name is very long ({len(name)} chars)")
    if name and len(name) < 5:
        issues.append("Name is very short")

    # Check for generic names (only if name exists and isn't clearly identifiable)
    if name:
        generic_names = {"hotel", "restaurant", "cafe", "bar", "store", "shop",
                         "soda", "cabinas", "supermarket", "farmacia", "tienda"}
        words = set(w.lower().rstrip("s") for w in name.split())
        proper_nouns = [w for w in name.split() if w and w[0].isupper()]
        if not proper_nouns and words.issubset(generic_names | NAME_ARTICLES):
            issues.append("Name is generic — may be ambiguous")

    # 4. Description quality
    if not desc:
        issues.append("Description missing")
    elif len(desc) < 25:
        issues.append(f"Description too short ({len(desc)} chars)")
    else:
        generic_phrases = [
            "gives travelers", "useful for travelers",
            "straightforward stop", "local spot worth checking out",
            "planning a caribbean", "visitors looking for local experiences",
        ]
        for phrase in generic_phrases:
            if phrase in desc.lower():
                issues.append(f"Generic template description — contains '{phrase}'")
                break

    # 5. Subcategory/category conflict
    if subcat and cat:
        sc_lower = subcat.lower()
        # If subcategory clearly indicates lodging but category is restaurant
        if any(kw in sc_lower for kw in ["masajes", "massage", "spa", "yoga"]):
            if cat.lower() not in ("services", "Wellness", "wellness"):
                issues.append(f"Subcategory '{subcat}' suggests Wellness but category is '{cat}'")
                fixes.append(f"Change category to 'Wellness'")
        if any(kw in sc_lower for kw in ["taxi", "shuttle"]):
            if cat.lower() not in ("services", "Transport", "transport"):
                issues.append(f"Subcategory '{subcat}' suggests Transport but category is '{cat}'")
                fixes.append(f"Change category to 'Transport'")
        if any(kw in sc_lower for kw in ["bar", "cocktail"]):
            if cat.lower() not in ("Nightlife", "nightlife", "restaurant"):
                issues.append(f"Subcategory '{subcat}' suggests Nightlife/Bar but category is '{cat}'")
                fixes.append(f"Change category to 'Nightlife' or 'restaurant'")

    # 6. Duplicate check runs at report level, not per-entry

    score = max(0, 100 - len(issues) * 15 - (0 if desc and len(desc) > 30 else 10))
    if not cid:
        score -= 10
    if phone or wp:
        score += 5
    if website:
        score += 5
    score = max(0, min(100, score))

    return {
        "business_name": name,
        "category": cat,
        "area": area,
        "score": score,
        "issues": issues,
        "suggested_fixes": fixes,
    }


def main():
    # Load enrichment subcategories
    enrich = {}
    if ENRICH_V3.exists():
        for rec in json.loads(ENRICH_V3.read_text(encoding="utf-8")):
            cid = rec.get("cid", "")
            if cid:
                fields = rec.get("fields", {})
                sc = fields.get("subcategory", {})
                if isinstance(sc, dict) and sc.get("value"):
                    enrich[cid] = sc["value"]

    # Load businesses
    biz_list = json.loads(BIZ_JSON.read_text(encoding="utf-8"))

    results = []
    by_cat = Counter()
    by_severity = Counter()

    for biz in biz_list:
        cid = biz.get("channels", {}).get("google_maps_cid", "")
        subcat = enrich.get(cid, "")
        entry = audit_entry(biz, subcat)
        results.append(entry)
        by_cat[entry["category"] or "Uncategorized"] += 1
        if entry["issues"]:
            by_severity["has_issues"] += 1
        if entry["score"] < 40:
            by_severity["score_under_40"] += 1
        if entry["score"] < 60:
            by_severity["score_under_60"] += 1

    # Sort by score ascending (worst first)
    results.sort(key=lambda x: x["score"])

    # Duplicate name detection
    name_counts = Counter(r["business_name"].lower().strip() for r in results if r.get("business_name","").strip())
    duplicates = {n: c for n, c in name_counts.items() if c > 1}

    report = {
        "summary": {
            "total_entries": len(biz_list),
            "entries_with_issues": by_severity["has_issues"],
            "entries_under_60": by_severity["score_under_60"],
            "entries_under_40": by_severity["score_under_40"],
            "duplicate_names": len(duplicates),
            "average_score": round(sum(r["score"] for r in results) / len(results), 1),
        },
        "duplicates": [{"name": n, "count": c} for n, c in sorted(duplicates.items())],
        "entries": results,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  QA AUDIT COMPLETE")
    print(f"{'='*60}")
    print(f"  Total entries:     {report['summary']['total_entries']}")
    print(f"  With issues:       {report['summary']['entries_with_issues']}")
    print(f"  Score < 60:        {report['summary']['entries_under_60']}")
    print(f"  Score < 40:        {report['summary']['entries_under_40']}")
    print(f"  Duplicate names:   {report['summary']['duplicate_names']}")
    print(f"  Average score:     {report['summary']['average_score']}%")
    print()
    print("  WORST 10 ENTRIES (lowest scores):")
    print(f"  {'Score':>5}  {'Business':45s} {'Category':18s} {'Issues'}")
    print(f"  {'-----':>5}  {'-'*45} {'-'*18} {'-'*20}")
    for r in results[:10]:
        short = r["business_name"][:45]
        issue_count = len(r["issues"])
        issues_preview = r["issues"][0][:30] if r["issues"] else "OK"
        print(f"  {r['score']:>5}  {short:45s} {r['category'][:18]:18s} {issues_preview}")

    print()
    print("  DUPLICATE NAMES:")
    for d in report["duplicates"]:
        print(f"    {d['name'][:60]:60s} appears {d['count']} times")

    print(f"\n  Full report: {OUTPUT}")


if __name__ == "__main__":
    main()
