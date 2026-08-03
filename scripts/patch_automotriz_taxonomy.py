"""Surgical fix: correct the Automotriz Danny taxonomy record only.

Removes the false `medical` tag (driven by the stale "Car Clinic" subcategory),
drops the now-empty `wellness` group, and prunes medical-derived synonyms and
assertions. Every other record is left byte-identical.

Usage: python scripts/patch_automotriz_taxonomy.py
"""
import json
from pathlib import Path

TAXONOMY = Path(__file__).resolve().parent.parent / "paradisio_app" / "data" / "semantic_taxonomy.json"

MEDICAL_SYNONYMS = {"medical", "health", "salud", "wellness", "bienestar"}


def main() -> int:
    data = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    records = data.get("records", data)
    target = None
    key = None
    for k, rec in records.items():
        if (rec.get("business_name") or "").startswith("Automotriz Danny"):
            target = rec
            key = k
            break
    if target is None:
        raise SystemExit("Automotriz Danny not found in taxonomy")

    # Remove the medical tag and its assertion.
    target["tags"] = [t for t in target.get("tags", []) if t != "medical"]
    target["assertions"].pop("medical", None)
    # Drop the wellness group (only present because of medical).
    target["groups"] = [g for g in target.get("groups", []) if g != "wellness"]
    # Prune medical-derived synonyms.
    target["search_synonyms"] = [s for s in target.get("search_synonyms", []) if s not in MEDICAL_SYNONYMS]
    # Drop any medical attribute if present.
    target["attributes"] = [a for a in target.get("attributes", []) if a != "medical"]

    TAXONOMY.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"patched {key}: tags={target['tags']} groups={target['groups']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
