"""
Read-only Category Exposure Audit.

For every business in the master dataset, compare the discovery groups it
currently carries against every group its available evidence (name,
description, Maps subcategory/cuisine/amenities) COULD support. Businesses
with a supported group they do not currently carry are surfaced as
multi-category exposure candidates for human review.

This is intentionally a suggestion generator, not a classifier: it uses a
broader per-group lexicon than the production taxonomy so it can also find
businesses the current (conservative) rules miss entirely. A human reviews the
output and decides add / keep / skip. No source data is modified.

Usage:
    python scripts/exposure_audit.py

Outputs (writes to audit/category-exposure/):
    exposure_matrix.csv        business x group  (current / potential / none)
    exposure_candidates.csv    one row per suggested group + evidence snippet
    exposure_summary.md        per-group before/after counts + candidate list
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "paradisio_app"))

from semantic_taxonomy import GROUP_LABELS, TAXONOMY_VERSION  # noqa: E402
from build import maps_data, semantic_data  # noqa: E402

CSV_PATH = BASE_DIR / "pv_master_unified.csv"
OUT_DIR = BASE_DIR / "audit" / "category-exposure"

# Report order: nightlife first because it is the known pain point.
GROUPS = [
    "nightlife",
    "eat",
    "stay",
    "things-to-do",
    "shopping",
    "services",
    "wellness",
    "transport",
]

# Broader-than-production lexicon. Each entry: (label, regex).
# Matches are treated as *candidates*, never as decisions.
LEXICON: dict[str, list[tuple[str, str]]] = {
    "nightlife": [
        ("bar", r"\bbar(?:es)?\b"),
        ("pub", r"\bpub\b"),
        ("cocktail", r"\bcocktails?\b"),
        ("cantina", r"\bcantina\b"),
        ("grill house", r"\bgrill(?:house|er[íi]a)?\b"),
        ("beach club", r"\bbeach\s*club\b"),
        ("nightclub/disco", r"\bnight\s*club(?:s)?\b|\bnightclub\b|\bdiscoteca\b|\bdisco\b"),
        ("dancing", r"\bdanc(?:e|ing|ero)\b|\b[bá]iles?\b"),
        ("karaoke", r"\bkaraoke\b"),
        ("lounge", r"\blounge\b"),
        ("sports bar", r"\bsports?\s*bar\b"),
        ("reggae bar", r"\breggae\s*bar\b"),
        ("brewery/taproom", r"\bbrewery\b|\bmicrobrewery\b|\btaproom\b|\bbeer\s*garden\b"),
        ("live music", r"\blive\s*music\b|\bm[uú]sica\s*en\s*vivo\b"),
        ("party/evening", r"\bhappy\s*hour\b|\bparty\s*(?:bar|venue|place|house)\b|\brumba\b|\bfiesta\b|\breggaet[oó]n\b|\bsalsa\s*club\b"),
    ],
    "eat": [
        ("restaurant", r"\brestaurant\b|\brestaurante\b|\bbistro\b|\bbrasserie\b"),
        ("cafe", r"\bcaf[eé]\b|\bcafeter[ií]a\b|\bcoffee\s*(?:shop|house)?\b"),
        ("food service", r"\bsoda\b|\bcomida\b|\bcocina\b|\beatery\b|\bkitchen\b|\bdeli(?:catessen)?\b|\bmen[uú]\b"),
        ("cuisine types", r"\bpizz(?:a|eria)\b|\bsushi\b|\bburger(?:s)?\b|\btaco(?:s)?\b|\bparrilla\b|\basado(?:r)?\b|\bwok\b"),
        ("meals", r"(?<!bed\sand\s)(?<!bed\s&\s)\bbreakfast\b|\blunch\b|\bdinner\b|\bgastropub\b|\bgastro\s*pub\b"),
        ("bar food", r"\btavern\b|\bpub\b|\bcantina\b|\bgrill(?:house)?\b"),
    ],
    "stay": [
        ("hotel", r"\bhotel(?:es)?\b|\blodge(?:s)?\b|\blodging\b|\bposada(?:s)?\b"),
        ("hostel", r"\bhostel(?:es)?\b|\balbergue\b"),
        ("cabins", r"\bcabinas?\b|\bcabins?\b|\bcaba[ñn]as?\b"),
        ("vacation rental", r"\bvacation\s*rental\b|\bholiday\s*home\b|\bapartments?\b|\bvillas?\b|\bguest\s*house\b|\bguesthouse\b|\bbungalows?\b|\bcasitas?\b"),
        ("bed & breakfast", r"\bbed\s*(?:&|and)\s*breakfast\b|\bb\s*&\s*b\b"),
        ("ecolodge", r"\beco[ -]?lodge\b|\becological\s*lodge\b"),
        ("rooms/resort", r"\bresort\b|\bretreat\b|\brooms?\b|\binn\b|\btreehouse\b"),
        ("espanol lodging", r"\bhospedaje\b|\balojamiento\b"),
    ],
    "things-to-do": [
        ("tours", r"\btours?\b|\btour\s*operator\b"),
        ("surf", r"\bsurf(?:ing)?\b|\b(?:surf|wave)\s*(?:school|lessons|coach)\b|\bescuela\s*de\s*surf\b"),
        ("diving", r"\bdiv(?:e|ing)\b|\bscuba\b|\bbuceo\b"),
        ("snorkeling", r"\bsnorkel(?:ing)?\b"),
        ("paddle", r"\bkayak(?:ing)?\b|\bpaddle(?:board|ing)?\b|\bstand\s*up\s*paddle\b"),
        ("fishing", r"\bfishing\b|\bpesca\b|\bcharter(?:s)?\b"),
        ("wildlife", r"\bwildlife\b|\banimal\s*rescue\b|\brescate\s*animal\b|\bjaguar\s*rescue\b|\bsloth\s*sanctuary\b"),
        ("yoga", r"\byoga\b|\bacroyoga\b"),
        ("adventure", r"\bzip(?:[- ])?line\b|\bcanopy\b|\badventure(?:s)?\b|\bsafari\b|\bhorseback\b|\bcacao\s*tour\b|\bchocolate\s*tour\b|\brafting\b|\btubing\b|\batv\b|\bquad(?:s)?\b"),
        ("hiking/nature", r"\bhik(?:e|ing)\b|\btrails?\b|\bnature\s*reserve\b|\bbotanical\b|\bnational\s*park\b"),
        ("bike rental", r"\bbike\s*rental\b|\bsurf\s*rental\b|\brent\s*a\s*bike\b"),
        ("classes", r"\bdance\s*studio\b|\bschool\b|\blessons?\b|\bclasses?\b|\bacademy\b"),
    ],
    "shopping": [
        ("shop/store", r"\bshop(?:s)?\b|\bstore(?:s)?\b|\btienda(?:s)?\b|(?<!hotel\s)\bboutique\b(?!\s*(?:hotel|inn|resort|rooms?|suites?))"),
        ("market", r"\bmarket(?:s)?\b|\bmercado(?:s)?\b|\bsupermarket\b|\bsupermercado\b|\bmega\s*super\b|\bvalue\s*mart\b"),
        ("pharmacy", r"\bpharmacy\b|\bfarmacia\b"),
        ("goods", r"\bclothing\b|\bropa\b|\bsouvenir(?:s)?\b|\bbakery\b|\bpanader[íi]a\b|\bice\s*cream\b|\bhelader[íi]a\b|\bgelato\b|\bgrocery\b|\bliquor\b|\bbookstore\b|\blibrer[íi]a\b|\bhardware\b|\bferreter[íi]a\b|\bcrafts?\b|\bartisan(?:al)?\b"),
    ],
    "services": [
        ("services", r"\bservices?\b|\bservicios\b"),
        ("repair/auto", r"\brepair(?:s)?\b|\btaller\b|\bmechanic(?:al)?\b|\bautomotriz\b"),
        ("laundry", r"\blaundry\b|\blavander[íi]a\b"),
        ("medical", r"\bmedical\b|\bclinic(?:a)?\b|\bcl[íi]nica\b|\bdoctor(?:s)?\b|\bmedic(?:al|o)?\b|\bhospital\b"),
        ("dental", r"\bdent(?:al|ist)\b|\bdentista\b|\bodontolog"),
        ("veterinary", r"\bvet(?:erinary)?\b|\bveterinari[ao]\b|\bpet\s*care\b|\bmascotas?\b"),
        ("banking", r"\bbank\b|\bbanco\b|\batm\b|\bcajero\b|\binsurance\b|\bseguros?\b"),
        ("personal care", r"\bsalon\b|\bsal[oó]n\b|\bbarber(?:s)?\b|\bbeauty\b|\bnails?\b|\btattoo\b"),
        ("education", r"\bschool\b|\bescuela\b|\blessons?\b|\bclasses?\b|\bacademy\b|\btutor(?:ing)?\b"),
        ("real estate", r"\breal\s*estate\b|\bbienes\s*ra[íi]ces\b|\binmobiliaria\b"),
        ("locksmith/tech", r"\blocksmith\b|\bcerrajer[íi]a\b|\bpc\s*repair\b|\bcomputers?\b|\bprinting\b|\bcopias\b"),
        ("public services", r"\bpolice\b|\bpolic[íi]a\b|\bbomberos\b|\bfire\s*department\b|\bcorreos\b|\bpost\s*office\b"),
    ],
    "wellness": [
        ("spa/massage", r"\bspa\b|\bmassage(?:s)?\b|\bmasajes?\b|\bwellness\b|\bbienestar\b"),
        ("mind-body", r"\byoga\b|\bmeditation\b|\bmindfulness\b|\btherapy\b|\bphysio\b|\bfisioterapia\b|\bacupuncture\b|\bdetox\b"),
        ("fitness", r"\bgym\b|\bgimnasio\b|\bfitness\b|\bcrossfit\b|\btraining\b|\bworkout\b"),
        ("beauty", r"\bbeauty\b|\best[ée]tica\b|\bsalon\b|\bhair\b|\bnails?\b|\btanning\b|\btattoo\b"),
        ("sanctuary", r"\bretreat\b|\bhealing\b|\bchakra\b|\bsound\s*healing\b|\bwellness\s*sanctuary\b"),
    ],
    "transport": [
        ("transport", r"\btransport\b|\btransporte\b"),
        ("shuttle", r"\bshuttle\b|\btransfer(?:s)?\b"),
        ("taxi", r"\btaxi(?:s)?\b"),
        ("bus", r"\bbus(?:es)?\b|\bterminal\b"),
        ("car rental", r"\bcar\s*rental\b|\brent\s*a\s*car\b|\balquiler\s*de\s*(?:autos|carros|coches)\b|\bgolf\s*carts?\b"),
    ],
}

# Identity fields (a match here is a strong signal the business IS this kind of
# place). Context fields (description) only flag for verification — Maps
# subcategory/amenities are facility or access attributes ("Transporte público",
# "airport transfer"), never identity, so they are excluded from matching.
IDENTITY_FIELDS = ["name", "cuisine"]
CONTEXT_FIELDS = ["description"]


def compile_lexicon() -> dict[str, list[tuple[str, re.Pattern]]]:
    return {
        group: [(label, re.compile(pattern, re.IGNORECASE)) for label, pattern in patterns]
        for group, patterns in LEXICON.items()
    }


def collect_evidence(row: dict[str, str]) -> dict[str, str]:
    enrich = maps_data(row.get("google_maps_cid", "").strip())
    fields: dict[str, str] = {
        "name": row.get("business_name", "") or "",
        "description": row.get("description_full", "") or "",
    }
    if enrich:
        for key in ("subcategory", "cuisine"):
            value = enrich.get(key)
            if isinstance(value, list):
                value = " ".join(str(item) for item in value)
            if value:
                fields[key] = str(value)
        amenities = enrich.get("amenities")
        if isinstance(amenities, list):
            amenities = " ".join(str(item) for item in amenities)
        elif not isinstance(amenities, str):
            amenities = ""
        if amenities:
            fields["amenities"] = amenities
    return fields


def snippet(text: str, match: re.Match, width: int = 40) -> str:
    start = max(0, match.start() - width)
    end = min(len(text), match.end() + width)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:match.start()]}«{match.group(0)}»{text[match.end():end]}{suffix}"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    compiled = compile_lexicon()

    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))

    current_counts: dict[str, int] = defaultdict(int)
    potential_counts: dict[str, int] = defaultdict(int)
    candidates: list[dict] = []
    matrix_rows: list[dict] = []
    evidence_coverage = {"description": 0, "subcategory": 0, "cuisine": 0, "amenities": 0}
    skipped = 0

    for row in rows:
        try:
            semantic = semantic_data(row)
            current = set(semantic.get("groups") or [])
        except Exception:
            skipped += 1
            current = set()

        evidence = collect_evidence(row)
        evidence_coverage["description"] += bool(evidence.get("description"))
        evidence_coverage["subcategory"] += bool(evidence.get("subcategory"))
        evidence_coverage["cuisine"] += bool(evidence.get("cuisine"))
        evidence_coverage["amenities"] += bool(evidence.get("amenities"))

        matched_identity: dict[str, list[dict]] = defaultdict(list)
        matched_context: dict[str, list[dict]] = defaultdict(list)
        for group, patterns in compiled.items():
            for label, pattern in patterns:
                identity_hit = None
                for field in IDENTITY_FIELDS:
                    text = evidence.get(field, "")
                    match = pattern.search(text)
                    if match:
                        identity_hit = (field, match)
                        break
                if identity_hit:
                    field, match = identity_hit
                    matched_identity[group].append(
                        {"label": label, "field": field, "snippet": snippet(evidence[field], match)}
                    )
                    continue
                for field in CONTEXT_FIELDS:
                    text = evidence.get(field, "")
                    match = pattern.search(text)
                    if match:
                        matched_context[group].append(
                            {"label": label, "field": field, "snippet": snippet(evidence[field], match)}
                        )
                        break

        # "Potential" exposure uses identity-level matches only; context matches
        # are recorded as lower-confidence flags, never as headline suggestions.
        potential = set(current)
        potential.update(matched_identity.keys())
        context_only = set(matched_context.keys()) - potential
        for group in GROUPS:
            if group in current:
                current_counts[group] += 1
            if group in potential:
                potential_counts[group] += 1

        # Matrix row: full exposure state per business.
        matrix_rows.append({
            "business_name": row.get("business_name", ""),
            "category": row.get("category", ""),
            "area": row.get("area", ""),
            "google_maps_cid": row.get("google_maps_cid", ""),
            **{f"group_{g}": ("current" if g in current else ("suggested" if g in matched_identity else ("context" if g in context_only else ""))) for g in GROUPS},
            "current_groups": "|".join(sorted(current)) or "-",
            "potential_groups": "|".join(sorted(potential)) or "-",
        })

        for group, matches in matched_identity.items():
            if group not in current:
                best = matches[0]
                candidates.append({
                    "tier": "identity",
                    "business_name": row.get("business_name", ""),
                    "category": row.get("category", ""),
                    "area": row.get("area", ""),
                    "google_maps_cid": row.get("google_maps_cid", ""),
                    "suggested_group": group,
                    "current_groups": "|".join(sorted(current)) or "-",
                    "matched_field": best["field"],
                    "matched_label": best["label"],
                    "evidence": best["snippet"],
                    "match_count": len(matches),
                })
        for group, matches in matched_context.items():
            if group not in current and group not in matched_identity:
                best = matches[0]
                candidates.append({
                    "tier": "context",
                    "business_name": row.get("business_name", ""),
                    "category": row.get("category", ""),
                    "area": row.get("area", ""),
                    "google_maps_cid": row.get("google_maps_cid", ""),
                    "suggested_group": group,
                    "current_groups": "|".join(sorted(current)) or "-",
                    "matched_field": best["field"],
                    "matched_label": best["label"],
                    "evidence": best["snippet"],
                    "match_count": len(matches),
                })

    matrix_path = OUT_DIR / "exposure_matrix.csv"
    with open(matrix_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(matrix_rows[0].keys()))
        writer.writeheader()
        writer.writerows(matrix_rows)

    candidates_path = OUT_DIR / "exposure_candidates.csv"
    candidate_fields = [
        "tier", "suggested_group", "business_name", "category", "area", "google_maps_cid",
        "current_groups", "matched_field", "matched_label", "evidence", "match_count",
    ]
    with open(candidates_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=candidate_fields)
        writer.writeheader()
        for cand in sorted(candidates, key=lambda c: (c["tier"] != "identity", GROUPS.index(c["suggested_group"]), c["business_name"])):
            writer.writerow(cand)

    # Markdown summary.
    summary = [
        "# Category Exposure Audit",
        "",
        f"- Taxonomy version: `{TAXONOMY_VERSION}`",
        f"- Businesses analyzed: `{len(rows)}` (skipped: `{skipped}`)",
        f"- Evidence coverage: {evidence_coverage['description']}/{len(rows)} descriptions · "
        f"{evidence_coverage['subcategory']} subcategory · {evidence_coverage['cuisine']} cuisine · "
        f"{evidence_coverage['amenities']} amenity sets",
        f"- Candidate businesses (≥1 identity-level suggestion): `{len({c['business_name'] for c in candidates if c['tier'] == 'identity'})}`",
        f"- Identity suggestions: `{sum(1 for c in candidates if c['tier'] == 'identity')}` · "
        f"Context flags (description only, verify): `{sum(1 for c in candidates if c['tier'] == 'context')}`",
        "",
        "> Read-only output. This file changes nothing; it exists so a human can review",
        "> which businesses deserve **more exposure** than the current taxonomy gives them.",
        "> - **identity** = group word appears in the business name/cuisine (strong signal).",
        "> - **context** = group word appears only in the description (flag for verification).",
        "> Maps subcategory/amenities are excluded (facility/access attributes, not identity).",
        "",
        "## Counts per group (identity-level potential)",
        "",
        "| Group | Current | Potential | Delta |",
        "|---|---:|---:|---:|",
    ]
    for group in GROUPS:
        cur = current_counts.get(group, 0)
        pot = potential_counts.get(group, 0)
        delta = pot - cur
        summary.append(f"| {GROUP_LABELS.get(group, group)} ({group}) | {cur} | {pot} | **+{delta}** |")

    summary.append("")
    summary.append("## Suggested additions by group")
    summary.append("")
    by_group: dict[str, list[dict]] = defaultdict(list)
    for cand in candidates:
        by_group[cand["suggested_group"]].append(cand)
    for group in GROUPS:
        group_cands = sorted(by_group.get(group, []), key=lambda c: (c["tier"] != "identity", c["business_name"]))
        identity_count = sum(1 for c in group_cands if c["tier"] == "identity")
        context_count = len(group_cands) - identity_count
        summary.append(f"### {GROUP_LABELS.get(group, group)} ({group}) — {identity_count} identity · {context_count} context")
        summary.append("")
        if not group_cands:
            summary.append("_No candidates._")
            summary.append("")
            continue
        for cand in group_cands:
            tier = "**identity**" if cand["tier"] == "identity" else "context"
            summary.append(
                f"- {tier} **{cand['business_name']}** `[{cand['category']}]` — "
                f"matches `{cand['matched_label']}` in {cand['matched_field']}: {cand['evidence']}"
            )
        summary.append("")

    summary_path = OUT_DIR / "exposure_summary.md"
    summary_path.write_text("\n".join(summary), encoding="utf-8")

    # Console report.
    identity_n = sum(1 for c in candidates if c["tier"] == "identity")
    context_n = len(candidates) - identity_n
    print(f"Category exposure audit — {len(rows)} businesses, {identity_n} identity suggestions + {context_n} context flags")
    print(f"  candidates -> {candidates_path}")
    print(f"  matrix     -> {matrix_path}")
    print(f"  summary    -> {summary_path}")
    print()
    print(f"{'Group':<20}{'Current':>9}{'Potential':>11}{'Delta':>7}")
    print("-" * 47)
    for group in GROUPS:
        cur = current_counts.get(group, 0)
        pot = potential_counts.get(group, 0)
        print(f"{GROUP_LABELS.get(group, group):<20}{cur:>9}{pot:>11}{pot - cur:>+7}")


if __name__ == "__main__":
    main()
