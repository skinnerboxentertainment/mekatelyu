"""Apply reviewed ownership decisions for Google Maps CID collision clusters."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
AUDIT = ROOT / "audit" / "maps-cid-discovery"
DISCOVERY = AUDIT / "unsigned-full" / "results.json"
RECONCILIATION = AUDIT / "reconciliation.csv"
MANIFEST = AUDIT / "collision-decisions.csv"
REPORT = AUDIT / "COLLISION-RECONCILIATION.md"

# These four captured identities differ from the current master CID holder and
# have independent names/contact/location evidence. All other collision groups
# are aliases or duplicate records of their current holder.
TRANSFERS = {
    "1216870082731283437": {
        "from": "Flor del Caribe - Playa Cocles, Puerto Viejo, Limón, Costa Rica",
        "to": "El Sol del Caribe - Playa Cocles, Puerto Viejo, Limón, Costa Rica",
        "clear_fields": (),
        "rationale": "Maps identity is Sol del Caribe; Flor del Caribe has a different name, description, and phone.",
    },
    "8515965990195848246": {
        "from": "Hidden Jungle Beach House - Playa Negra, Puerto Viejo, Limón, Costa Rica",
        "to": "Casitas Mar y Luz - Playa Chiquita, Puerto Viejo, Limón, Costa Rica",
        "clear_fields": ("website",),
        "rationale": "Maps identity, captured address, phone, and the holder's cross-wired website identify Casitas Mar y Luz; Hidden Jungle has a different name, area, description, and phone.",
    },
    "8689012956679917112": {
        "from": "Douglasville Guesthouse",
        "to": "Las Casitas de Playa Negra - Playa Negra, Puerto Viejo, Limón, Costa Rica",
        "clear_fields": (),
        "rationale": "Maps identity is Las Casitas de Playa Negra; Douglasville has a different name, area, description, and phone.",
    },
    "9838950680602433731": {
        "from": "Villa Laurel - Playa Cocles, Puerto Viejo, Limón, Costa Rica",
        "to": "Uva Blue Jungle Villas - Playa Chiquita, Puerto Viejo, Limón, Costa Rica",
        "clear_fields": ("website",),
        "rationale": "Maps identity and cross-wired uvabluevillas.com URL identify Uva Blue; Villa Laurel has a different name, area, description, and phone.",
    },
}


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    apply = parser.parse_args().apply

    master, fields = load_csv(MASTER)
    by_name = {row["business_name"]: row for row in master}
    results = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    result_by_name = {item["business_name"]: item for item in results}
    decisions, _ = load_csv(RECONCILIATION)
    collisions = [row for row in decisions if row["decision"] == "collision_review"]
    by_cid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in collisions:
        by_cid[row["resolved_cid"]].append(row)
    if len(by_cid) != 27:
        raise SystemExit(f"expected 27 collision CIDs, found {len(by_cid)}")

    manifest = []
    applied_transfers = 0
    for cid, group in sorted(by_cid.items()):
        transfer = TRANSFERS.get(cid)
        holder_names = sorted({name for row in group for name in row["existing_cid_businesses"].split(" | ") if name})
        if transfer:
            if holder_names != [transfer["from"]]:
                raise SystemExit(f"unexpected holder for {cid}: {holder_names}")
            if [row["business_name"] for row in group] != [transfer["to"]]:
                raise SystemExit(f"unexpected transfer target for {cid}")
            source, target = by_name[transfer["from"]], by_name[transfer["to"]]
            before_state = source["google_maps_cid"] == cid and not target["google_maps_cid"]
            after_state = not source["google_maps_cid"] and target["google_maps_cid"] == cid
            if not before_state and not after_state:
                raise SystemExit(f"CID precondition failed for {cid}")
            evidence = result_by_name[transfer["to"]]
            shot = AUDIT / evidence["screenshot"]
            if evidence["classification"] != "exact" or evidence["resolved_cid"] != cid:
                raise SystemExit(f"capture identity failed for {cid}")
            if not shot.is_file() or hashlib.sha256(shot.read_bytes()).hexdigest() != evidence["screenshot_sha256"]:
                raise SystemExit(f"capture hash failed for {cid}")
            if apply and before_state:
                source["google_maps_cid"] = ""
                target["google_maps_cid"] = cid
                for field in transfer["clear_fields"]:
                    source[field] = ""
                applied_transfers += 1
            disposition = "ownership_transferred" if apply or after_state else "ownership_transfer_ready"
            manifest.append({
                "cid": cid, "disposition": disposition, "canonical_holder": transfer["to"],
                "former_holder": transfer["from"], "alias_records": "",
                "cleared_former_holder_fields": "|".join(transfer["clear_fields"]),
                "rationale": transfer["rationale"], "screenshot": evidence["screenshot"],
                "screenshot_sha256": evidence["screenshot_sha256"],
            })
        else:
            aliases = sorted(row["business_name"] for row in group)
            manifest.append({
                "cid": cid, "disposition": "duplicate_alias_review", "canonical_holder": " | ".join(holder_names),
                "former_holder": "", "alias_records": " | ".join(aliases),
                "cleared_former_holder_fields": "",
                "rationale": "Captured Maps identity and local name/contact/description evidence indicate the records refer to the same establishment; no duplicate CID was added and no record was deleted.",
                "screenshot": group[0]["screenshot"], "screenshot_sha256": group[0]["screenshot_sha256"],
            })

    if apply:
        write_csv(MASTER, master, fields)
    write_csv(MANIFEST, manifest, list(manifest[0]))
    transfer_count = sum(row["disposition"].startswith("ownership_transfer") for row in manifest)
    alias_count = len(manifest) - transfer_count
    report = [
        "# Google Maps CID Collision Reconciliation", "", "## Result", "",
        f"- Distinct collision CIDs reviewed: {len(manifest)}",
        f"- CID ownership corrections: {transfer_count}",
        f"- Duplicate/alias clusters held for consolidation: {alias_count}",
        f"- Ownership corrections applied locally: {applied_transfers}",
        "- Records deleted or merged: 0", "",
        "A shared CID is retained only on the established canonical holder for alias clusters. Alias rows remain in the directory without a duplicate CID until a separate, field-preserving deduplication pass is approved.", "",
        "| CID | Disposition | Canonical holder | Former holder / aliases | Rationale |", "|---|---|---|---|---|",
    ]
    for row in manifest:
        related = row["former_holder"] or row["alias_records"]
        cells = [row["cid"], row["disposition"], row["canonical_holder"], related, row["rationale"]]
        report.append("| " + " | ".join(cell.replace("|", "/") for cell in cells) + " |")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PASS: clusters={len(manifest)} transfers={transfer_count} aliases={alias_count} applied={applied_transfers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
