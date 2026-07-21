"""Resolve the broader multi-signal entity queue and apply deterministic merges."""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
AUDIT = ROOT / "audit" / "entity-resolution"
CANDIDATES = AUDIT / "candidate-pairs.csv"
DECISIONS = AUDIT / "pair-decisions.csv"
ARCHIVE = AUDIT / "merged-row-archive.jsonl"
MERGES = AUDIT / "merge-manifest.csv"
REPORT = AUDIT / "ENTITY-RESOLUTION-RESULT.md"

MERGE_PAIRS = {
    frozenset(("Cariblue Beach and Jungle Resort - Playa Cocles, Puerto Viejo, Limón, Costa Rica", "Hotel Cariblue")): {
        "canonical": "Cariblue Beach and Jungle Resort - Playa Cocles, Puerto Viejo, Limón, Costa Rica",
        "alias": "Hotel Cariblue", "reason": "Same hotel brand, WhatsApp, Instagram, and official website; alias is a generic CID-less hotel record.",
    },
    frozenset(("Jaguar Rescue Center - Playa Chiquita, Puerto Viejo, Limón, Costa Rica", "Refugio de animales Jaguar")): {
        "canonical": "Jaguar Rescue Center - Playa Chiquita, Puerto Viejo, Limón, Costa Rica",
        "alias": "Refugio de animales Jaguar", "reason": "Bilingual name variants share phone, Instagram, near-identical location, and organization identity; alias is CID-less.",
    },
    frozenset(("Douglasville Guesthouse", "Douglas Ville guest house")): {
        "canonical": "Douglasville Guesthouse", "alias": "Douglas Ville guest house",
        "reason": "Near-identical name, same phone, same lodging identity, and nearby coordinates; captured CID is transferred to the richer canonical record.",
    },
    frozenset(("Chile Rojo", "Chili Rojo")): {
        "canonical": "Chile Rojo", "alias": "Chili Rojo",
        "reason": "Spelling variants share phone and identical TripAdvisor identity; the richer CID-bearing record is canonical.",
    },
}

FILL_FIELDS = ("phone", "normalized_phone", "whatsapp", "email", "instagram_handle", "instagram_url",
               "facebook_url", "website", "booking_url", "tripadvisor_url", "tiktok_url", "youtube_url", "twitter_url")


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def add_other(row: dict[str, str], value: str) -> None:
    value = value.strip()
    if not value: return
    existing = [item.strip() for item in row.get("other_social_urls", "").split("|") if item.strip()]
    if value.rstrip("/").casefold() not in {item.rstrip("/").casefold() for item in existing}:
        existing.append(value)
    row["other_social_urls"] = "|".join(existing)


def merge(canonical: dict[str, str], alias: dict[str, str]) -> list[str]:
    changes = []
    if not canonical["google_maps_cid"] and alias["google_maps_cid"]:
        canonical["google_maps_cid"] = alias["google_maps_cid"]
        changes.append("google_maps_cid:transferred")
    for field in FILL_FIELDS:
        incoming, current = alias.get(field, "").strip(), canonical.get(field, "").strip()
        if incoming and not current:
            canonical[field] = incoming
            changes.append(f"{field}:filled")
        elif incoming and current and incoming.rstrip("/").casefold() != current.rstrip("/").casefold():
            if field.endswith("_url") or field in {"website", "instagram_handle"}:
                url = incoming
                if field == "instagram_handle": url = alias.get("instagram_url", "") or f"https://www.instagram.com/{incoming.lstrip('@')}/"
                add_other(canonical, url)
    if len(alias.get("description_full", "")) > len(canonical.get("description_full", "")) + 80:
        canonical["description_full"] = alias["description_full"]
        changes.append("description:longer-promoted")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--apply", action="store_true")
    apply = parser.parse_args().apply
    candidates, candidate_fields = load_csv(CANDIDATES)
    rows, master_fields = load_csv(MASTER)
    by_name = {row["business_name"]: row for row in rows}

    decisions = []
    for item in candidates:
        pair = frozenset((item["left_name"], item["right_name"]))
        if pair in MERGE_PAIRS:
            decision, rationale = "deterministic_merge", MERGE_PAIRS[pair]["reason"]
        elif item["left_cid"] and item["right_cid"] and item["left_cid"] != item["right_cid"]:
            decision, rationale = "distinct_cids", "Separate Google Maps identities; shared signals indicate proximity, management, brand family, or related operations."
        elif int(item["score"]) >= 4:
            decision, rationale = "related_or_shared_contact", "Names/roles differ; shared contact, website, social account, or coordinates are insufficient to merge without matching identity evidence."
        else:
            decision, rationale = "not_duplicate_single_signal", "Only one weak or fuzzy signal; names and available identity evidence do not establish the same entity."
        resolved = dict(item); resolved["decision"] = decision; resolved["rationale"] = rationale
        decisions.append(resolved)
    write_csv(DECISIONS, decisions, candidate_fields)

    aliases = {spec["alias"] for spec in MERGE_PAIRS.values()}
    present = aliases & set(by_name)
    if not present:
        if not ARCHIVE.exists(): raise SystemExit("merge aliases absent but archive missing")
        print(f"PASS: broader entity resolution already applied; pairs={len(decisions)} merges=4")
        return 0
    if present != aliases: raise SystemExit("partial broader entity merge detected")

    working = deepcopy(rows); work_by_name = {row["business_name"]: row for row in working}
    archived, manifest = [], []
    for spec in MERGE_PAIRS.values():
        canonical, alias = work_by_name[spec["canonical"]], work_by_name[spec["alias"]]
        before = deepcopy(canonical)
        changes = merge(canonical, alias)
        archived.extend((
            {"role": "canonical_before", "record": before}, {"role": "alias", "record": deepcopy(alias)},
            {"role": "canonical_after", "record": deepcopy(canonical)},
        ))
        manifest.append({"canonical": spec["canonical"], "removed_alias": spec["alias"],
                         "changes": "|".join(changes), "rationale": spec["reason"], "status": "applied" if apply else "ready"})
    consolidated = [row for row in working if row["business_name"] not in aliases]
    cids = [row["google_maps_cid"] for row in consolidated if row["google_maps_cid"]]
    if len(consolidated) != len(rows) - 4 or len(cids) != len(set(cids)):
        raise SystemExit("post-merge cardinality or CID uniqueness failed")
    if apply:
        ARCHIVE.write_text("".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in archived), encoding="utf-8")
        write_csv(MASTER, consolidated, master_fields)
    write_csv(MERGES, manifest, list(manifest[0]))
    counts = {key: sum(row["decision"] == key for row in decisions) for key in {row["decision"] for row in decisions}}
    report = ["# Broader Entity-Resolution Result", "", "## Outcome", "", f"- Candidate pairs resolved: {len(decisions)}",
              f"- Deterministic duplicate merges: {counts.get('deterministic_merge', 0)}", f"- Separate-CID relationships retained: {counts.get('distinct_cids', 0)}",
              f"- Related/shared-contact pairs retained: {counts.get('related_or_shared_contact', 0)}",
              f"- Single-signal pairs rejected: {counts.get('not_duplicate_single_signal', 0)}",
              f"- Canonical records after applied merges: {len(consolidated) if apply else len(rows)}", "",
              "All removed rows and canonical before/after states are preserved in `merged-row-archive.jsonl`.", "",
              "| Canonical | Removed alias | Preserved changes |", "|---|---|---|"]
    for item in manifest:
        report.append(f"| {item['canonical']} | {item['removed_alias']} | {item['changes'] or 'No field change'} |")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PASS: pairs={len(decisions)} merges=4 rows_before={len(rows)} rows_after={len(consolidated)} applied={apply} decisions={counts}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
