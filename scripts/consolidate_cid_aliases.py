"""Field-preserving consolidation of reviewed same-CID alias records."""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
AUDIT = ROOT / "audit" / "maps-cid-discovery"
DECISIONS = AUDIT / "collision-decisions.csv"
ARCHIVE = AUDIT / "alias-row-archive.jsonl"
MANIFEST = AUDIT / "alias-consolidation.csv"
REPORT = AUDIT / "ALIAS-CONSOLIDATION.md"

OFFICIAL_WEBSITE_ALIASES = {
    "Ecotourism and Conservation Association of Talamanca",
    "Le Cameleon Boutique Hotel",
    "Café Rico",
    "Repazul",
}

CONTACT_FIELDS = (
    "phone", "normalized_phone", "whatsapp", "email", "tiktok_url",
    "youtube_url", "twitter_url", "booking_url", "tripadvisor_url",
)

SKIP_FIELDS_BY_ALIAS = {
    "Casa Pallalita": {"email"},
    "Casa Pallita": {"email"},
    "Da Lime Beach Club & Restaurant at Hotel Aguas Claras": {"email", "tripadvisor_url"},
}


def clear_nonpublic_alias_contacts(rows: list[dict[str, str]]) -> int:
    """Remove contacts intentionally retained only in the verbatim audit archive."""
    cleared = 0
    for row in rows:
        if row["business_name"] == "Casa Palliata" and row.get("email") == "angelin.sirbu@gmail.com":
            row["email"] = ""
            cleared += 1
    return cleared


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalized_url(url: str) -> str:
    return (url or "").strip().rstrip("/").casefold()


def add_other_url(row: dict[str, str], url: str) -> None:
    url = (url or "").strip()
    if not url:
        return
    existing = [value.strip() for value in row.get("other_social_urls", "").split("|") if value.strip()]
    if normalized_url(url) not in {normalized_url(value) for value in existing}:
        existing.append(url)
    row["other_social_urls"] = "|".join(existing)


def route_url(row: dict[str, str], url: str) -> bool:
    host = urlparse(url).netloc.casefold().removeprefix("www.")
    if "booking.com" in host:
        field = "booking_url"
    elif "tripadvisor." in host:
        field = "tripadvisor_url"
    elif "facebook.com" in host:
        field = "facebook_url"
    elif "instagram.com" in host:
        add_other_url(row, url)
        return True
    else:
        return False
    if not row.get(field, "").strip():
        row[field] = url
    elif normalized_url(row[field]) != normalized_url(url):
        add_other_url(row, url)
    return True


def merge_alias(canonical: dict[str, str], alias: dict[str, str]) -> list[str]:
    changes = []
    for field in CONTACT_FIELDS:
        if field in SKIP_FIELDS_BY_ALIAS.get(alias["business_name"], set()):
            continue
        incoming = alias.get(field, "").strip()
        if field == "email" and incoming.casefold().startswith("https:"):
            incoming = incoming[6:]
        current = canonical.get(field, "").strip()
        if incoming and not current:
            canonical[field] = incoming
            changes.append(f"{field}:filled")

    incoming_web = alias.get("website", "").strip()
    current_web = canonical.get("website", "").strip()
    if incoming_web:
        if alias["business_name"] in OFFICIAL_WEBSITE_ALIASES:
            if current_web and normalized_url(current_web) != normalized_url(incoming_web):
                if not route_url(canonical, current_web):
                    add_other_url(canonical, current_web)
            canonical["website"] = incoming_web
            changes.append("website:official-promoted")
        elif not current_web and not route_url(canonical, incoming_web):
            canonical["website"] = incoming_web
            changes.append("website:filled")
        elif normalized_url(current_web) != normalized_url(incoming_web):
            route_url(canonical, incoming_web) or add_other_url(canonical, incoming_web)

    incoming_ig = alias.get("instagram_handle", "").strip().lstrip("@")
    current_ig = canonical.get("instagram_handle", "").strip().lstrip("@")
    if incoming_ig and not current_ig:
        canonical["instagram_handle"] = incoming_ig
        canonical["instagram_url"] = alias.get("instagram_url", "").strip() or f"https://www.instagram.com/{incoming_ig}/"
        changes.append("instagram:filled")
    elif incoming_ig and incoming_ig.casefold() != current_ig.casefold():
        add_other_url(canonical, alias.get("instagram_url", "").strip() or f"https://www.instagram.com/{incoming_ig}/")

    incoming_fb = alias.get("facebook_url", "").strip()
    current_fb = canonical.get("facebook_url", "").strip()
    if incoming_fb and not current_fb:
        canonical["facebook_url"] = incoming_fb
        changes.append("facebook:filled")
    elif incoming_fb and normalized_url(incoming_fb) != normalized_url(current_fb):
        add_other_url(canonical, incoming_fb)

    if len(alias.get("description_full", "").strip()) > len(canonical.get("description_full", "").strip()) + 80:
        canonical["description_full"] = alias["description_full"].strip()
        changes.append("description:longer-promoted")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    apply = parser.parse_args().apply
    rows, fields = load_csv(MASTER)
    decisions, _ = load_csv(DECISIONS)
    clusters = [row for row in decisions if row["disposition"] == "duplicate_alias_review"]
    if len(clusters) != 23:
        raise SystemExit(f"expected 23 alias clusters, found {len(clusters)}")

    by_name = {row["business_name"]: row for row in rows}
    archive_existing = ARCHIVE.exists()
    aliases_expected = [name for cluster in clusters for name in cluster["alias_records"].split(" | ") if name]
    aliases_present = [name for name in aliases_expected if name in by_name]
    if not aliases_present:
        if not archive_existing:
            raise SystemExit("aliases absent but consolidation archive is missing")
        cleared = clear_nonpublic_alias_contacts(rows)
        if apply and cleared:
            write_csv(MASTER, rows, fields)
        print(f"PASS: consolidation already applied; clusters=23 aliases={len(aliases_expected)}")
        return 0
    if set(aliases_present) != set(aliases_expected):
        raise SystemExit("partial alias consolidation detected")

    working = deepcopy(rows)
    work_by_name = {row["business_name"]: row for row in working}
    archive_rows = []
    manifest_rows = []
    remove_names = set()
    for cluster in clusters:
        canonical_name = cluster["canonical_holder"]
        if " | " in canonical_name or canonical_name not in work_by_name:
            raise SystemExit(f"invalid canonical holder: {canonical_name}")
        canonical = work_by_name[canonical_name]
        if canonical["google_maps_cid"] != cluster["cid"]:
            raise SystemExit(f"canonical CID mismatch: {canonical_name}")
        before = deepcopy(canonical)
        aliases = [name for name in cluster["alias_records"].split(" | ") if name]
        cluster_changes = []
        conflicts = []
        for alias_name in aliases:
            alias = work_by_name[alias_name]
            archive_rows.append({"cid": cluster["cid"], "role": "alias", "record": deepcopy(alias)})
            for field in ("category", "area", "normalized_phone", "whatsapp", "website", "instagram_handle", "facebook_url"):
                left, right = canonical.get(field, "").strip(), alias.get(field, "").strip()
                if left and right and left.casefold() != right.casefold():
                    conflicts.append(f"{alias_name}:{field}={right}")
            cluster_changes.extend(f"{alias_name}:{change}" for change in merge_alias(canonical, alias))
            remove_names.add(alias_name)
        archive_rows.append({"cid": cluster["cid"], "role": "canonical_before", "record": before})
        archive_rows.append({"cid": cluster["cid"], "role": "canonical_after", "record": deepcopy(canonical)})
        manifest_rows.append({
            "cid": cluster["cid"], "canonical_holder": canonical_name,
            "removed_aliases": " | ".join(aliases), "removed_count": str(len(aliases)),
            "merged_changes": " | ".join(cluster_changes),
            "preserved_conflicts_in_archive": " | ".join(conflicts),
            "status": "applied" if apply else "ready",
        })

    if len(remove_names) != 29:
        raise SystemExit(f"expected 29 unique alias rows, found {len(remove_names)}")
    consolidated = [row for row in working if row["business_name"] not in remove_names]
    clear_nonpublic_alias_contacts(consolidated)
    if len(consolidated) != len(rows) - 29:
        raise SystemExit("unexpected consolidated row count")

    if apply:
        ARCHIVE.write_text("".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in archive_rows), encoding="utf-8")
        write_csv(MASTER, consolidated, fields)
    write_csv(MANIFEST, manifest_rows, list(manifest_rows[0]))
    report = [
        "# Field-Preserving CID Alias Consolidation", "", "## Outcome", "",
        f"- Same-CID clusters consolidated: {len(clusters)}",
        f"- Redundant alias rows removed: {len(remove_names) if apply else 0}",
        f"- Canonical rows retained: {len(clusters)}",
        f"- Master rows after consolidation: {len(consolidated) if apply else len(rows)}",
        "- Original alias rows and canonical before/after states: archived verbatim in `alias-row-archive.jsonl`.",
        "- Conflicting values: retained in the archive and summarized in `alias-consolidation.csv`.", "",
        "| CID | Canonical record | Removed aliases | Merged fields |", "|---|---|---|---|",
    ]
    for item in manifest_rows:
        cells = [item["cid"], item["canonical_holder"], item["removed_aliases"], item["merged_changes"] or "No canonical field change"]
        report.append("| " + " | ".join(cell.replace("|", "/") for cell in cells) + " |")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PASS: clusters=23 aliases=29 rows_before={len(rows)} rows_after={len(consolidated)} applied={apply}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
