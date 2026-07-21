"""Resolve and apply the final post-dedup Maps evidence queue."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
AUDIT = ROOT / "audit" / "maps-cid-discovery"
RESULTS = AUDIT / "current-25" / "results.json"
LEDGER = AUDIT / "remaining-evidence-decisions.csv"
REPORT = AUDIT / "REMAINING-EVIDENCE-RESOLUTION.md"

ACCEPT = {
    "Hidden Jungle Beach House - Playa Negra, Puerto Viejo, Limón, Costa Rica": "Fresh capture exactly matches the business identity after the legacy CID was moved away.",
    "La Ceiba Nature Reserve - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica": "Observed Spanish identity La Ceiba Reserva Natural matches the bilingual canonical name and reserve description.",
    "Samasati Yoga and Wellness Retreat - Hone Creek, Limón, Costa Rica": "Observed Samasati Retreat Center matches the distinctive retreat name, lodging, yoga, and wellness identity.",
    "Flor del Caribe - Playa Cocles, Puerto Viejo, Limón, Costa Rica": "Fresh capture exactly matches the business identity after the legacy CID was moved away.",
    "Villa Laurel - Playa Cocles, Puerto Viejo, Limón, Costa Rica": "Fresh capture exactly matches the business identity after the legacy CID was moved away.",
    "Ginger and Cacao - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica": "Observed Cabinas Ginger & Cacao matches the distinctive property name and lodging identity.",
    "We Do Laundry - Hone Creek, Limón, Costa Rica": "Observed WeDOlaundry - Caribe matches the distinctive name, area, and laundry-service identity.",
    "Centro Educativo Playa Chiquita Punta Uva - Playa Chiquita, Puerto Viejo, Limón, Costa Rica": "English-translated observed name matches the full Spanish school identity and location.",
    "Proyecto Educativo Semillas de Paz - Playa Chiquita, Puerto Viejo, Limón, Costa Rica": "Observed Jardín Infantil Las Semillas is explicitly documented as the establishment's former name.",
    "Servicentro Hone Creek - Hone Creek, Limón, Costa Rica": "Observed Hone Creek Gas Station is the direct English identity for the distinctive local servicentro.",
    "El Colibri Rojo - Cahuita, Limón, Costa Rica": "Observed Le Colibri Rouge is the French translation of the canonical hotel name in Cahuita.",
    "La Fundación Cahuita Playing for Change - Cahuita, Limón, Costa Rica": "Observed Playing for Change Cahuita matches the foundation/program identity and location.",
    "Se Ua Bed and Breakfast - Manzanillo, Limón, Costa Rica": "Observed Se Ua is a 3-star hotel at the canonical Manzanillo identity; canonical name adds the lodging type.",
}

REJECT = {
    "Estrellas Cabinas": "Generic results; extracted CID belongs to Cabinas Monte Sol, not Estrellas.",
    "Ceibo Adventure - Playa Chiquita, Puerto Viejo, Limón, Costa Rica": "Resolved Jungle Green House is the host location, not the Ceibo Adventure activity identity.",
    "Talamanca Chocolate - Playa Negra, Puerto Viejo, Limón, Costa Rica": "Resolved Cacao Huasi has a different business name; chocolate-class similarity alone is insufficient.",
    "Hotel Posada Nena": "Resolved CID is a room-level vacation listing, not a verified primary hotel identity.",
    "Paula's and Daniel's Homestay": "Generic results returned unrelated lodging candidates.",
    "Panadería Francés": "Resolved De Gustibus Bakery is a differently named business with no corroborating canonical contact.",
    "Casa Alegre": "Resolved Casa Rio is a different named restaurant.",
    "Casa Miluca": "Resolved Casa Maryluz is a different named vacation rental.",
    "Boca Chica Bar Restaurante y Piscina - Cahuita, Limón, Costa Rica": "Search resolved unrelated restaurants rather than Boca Chica.",
    "TKD Caribe - Cahuita, Limón, Costa Rica": "Resolved gym identity does not match TKD Caribe.",
    "Kinawe Cabinas": "Generic results; extracted CID belongs to Cabinas Apse Playa Negra.",
    "Puerto Viejo de Talamanca": "Generic place-name record resolved to an unrelated Playa Negra/Shenanigans CID.",
}


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle); return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--apply", action="store_true")
    apply = parser.parse_args().apply
    master, fields = load_csv(MASTER); by_name = {row["business_name"]: row for row in master}
    results = json.loads(RESULTS.read_text(encoding="utf-8")); by_result = {item["business_name"]: item for item in results}
    if len(results) != 25 or set(by_result) != set(ACCEPT) | set(REJECT):
        raise SystemExit("current 25-record result set does not match reviewed decisions")
    existing = {row["google_maps_cid"]: row["business_name"] for row in master if row["google_maps_cid"]}
    ledger = []; applied = 0
    for name in sorted(by_result, key=str.casefold):
        item, target = by_result[name], by_name[name]
        accepted = name in ACCEPT; cid = item["resolved_cid"]
        if accepted:
            shot = AUDIT / item["screenshot"]
            if not cid.isdigit() or cid in existing and existing[cid] != name:
                raise SystemExit(f"CID collision or invalid CID: {name}")
            if not shot.is_file() or hashlib.sha256(shot.read_bytes()).hexdigest() != item["screenshot_sha256"]:
                raise SystemExit(f"screenshot evidence failed: {name}")
            if target["google_maps_cid"] not in {"", cid}:
                raise SystemExit(f"target CID precondition failed: {name}")
            if apply and not target["google_maps_cid"]:
                target["google_maps_cid"] = cid; applied += 1
            decision, reason = "accepted" if apply or target["google_maps_cid"] == cid else "accept_ready", ACCEPT[name]
        else:
            decision, reason = "rejected_wrong_target", REJECT[name]
        ledger.append({"business_name": name, "decision": decision, "resolved_cid": cid,
                       "capture_class": item["classification"], "observed_name": item["observed_name"],
                       "identity_similarity": item["identity_similarity"], "rationale": reason,
                       "screenshot": item["screenshot"], "screenshot_sha256": item["screenshot_sha256"]})
    if apply: write_csv(MASTER, master, fields)
    write_csv(LEDGER, ledger, list(ledger[0]))
    report = ["# Remaining Maps Evidence Resolution", "", "## Outcome", "", "- Current canonical queue: 25",
              f"- Accepted identity-supported CIDs: {len(ACCEPT)}", f"- Rejected wrong-target or insufficient captures: {len(REJECT)}",
              f"- Newly applied in this run: {applied}", "- Forced or guessed identities: 0", "",
              "| Business | Decision | Observed Maps identity | CID | Rationale |", "|---|---|---|---|---|"]
    for row in ledger:
        cells = [row["business_name"], row["decision"], row["observed_name"], row["resolved_cid"], row["rationale"]]
        report.append("| " + " | ".join(str(cell).replace("|", "/") for cell in cells) + " |")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PASS: queue=25 accepted=13 rejected=12 applied={applied}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
