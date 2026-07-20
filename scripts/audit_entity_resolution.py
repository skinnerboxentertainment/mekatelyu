"""Generate a multi-signal entity-resolution queue for the canonical directory."""

from __future__ import annotations

import csv
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
OUT = ROOT / "audit" / "entity-resolution"


def fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char)).casefold()
    value = re.sub(r"\s+-\s+(?:playa |puerto viejo|cahuita|manzanillo|limon|costa rica).*$", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def digits(value: str) -> str:
    number = re.sub(r"\D", "", value or "")
    return number[-8:] if len(number) >= 8 else ""


def instagram(value: str) -> str:
    value = (value or "").strip().casefold().lstrip("@")
    if "instagram.com" in value:
        value = urlparse(value).path.strip("/").split("/")[0]
    return value


def website(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else "https://" + value)
    host = parsed.netloc.casefold().removeprefix("www.")
    if host in {"facebook.com", "instagram.com", "tripadvisor.com", "booking.com"}:
        return ""
    return host


def distance_m(a: dict[str, str], b: dict[str, str]) -> float | None:
    try:
        lat1, lon1, lat2, lon2 = map(float, (a["latitude"], a["longitude"], b["latitude"], b["longitude"]))
    except (ValueError, TypeError):
        return None
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6_371_000 * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def main() -> int:
    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    features = []
    for index, row in enumerate(rows):
        features.append({
            "index": index, "name": fold(row["business_name"]), "phone": digits(row["normalized_phone"] or row["phone"]),
            "whatsapp": digits(row["whatsapp"]), "instagram": instagram(row["instagram_handle"] or row["instagram_url"]),
            "website": website(row["website"]),
        })

    blocks: dict[tuple[str, str], list[int]] = defaultdict(list)
    for item in features:
        for key in ("name", "phone", "whatsapp", "instagram", "website"):
            if item[key]:
                blocks[key, item[key]].append(item["index"])
        tokens = item["name"].split()
        for token in set(tokens):
            if len(token) >= 5:
                blocks["name_token", token].append(item["index"])
    pair_ids = set()
    for members in blocks.values():
        if 1 < len(members) <= 25:
            pair_ids.update(combinations(sorted(set(members)), 2))

    candidates = []
    for left_i, right_i in sorted(pair_ids):
        left, right = rows[left_i], rows[right_i]
        a, b = features[left_i], features[right_i]
        name_similarity = SequenceMatcher(None, a["name"], b["name"]).ratio() if a["name"] and b["name"] else 0
        same_name = bool(a["name"] and a["name"] == b["name"])
        same_phone = bool(a["phone"] and a["phone"] == b["phone"])
        same_whatsapp = bool(a["whatsapp"] and a["whatsapp"] == b["whatsapp"])
        same_instagram = bool(a["instagram"] and a["instagram"] == b["instagram"])
        same_website = bool(a["website"] and a["website"] == b["website"])
        metres = distance_m(left, right)
        near = metres is not None and metres <= 30
        if not any((same_name, same_phone, same_whatsapp, same_instagram, same_website, near, name_similarity >= 0.82)):
            continue
        signals = []
        score = 0
        if same_name: signals.append("exact_name"); score += 5
        elif name_similarity >= 0.92: signals.append("name>=0.92"); score += 3
        elif name_similarity >= 0.82: signals.append("name>=0.82"); score += 2
        if same_phone: signals.append("phone"); score += 2
        if same_whatsapp: signals.append("whatsapp"); score += 2
        if same_instagram: signals.append("instagram"); score += 4
        if same_website: signals.append("website"); score += 3
        if near: signals.append("within_30m"); score += 2
        families = sum((same_name or name_similarity >= 0.82, same_phone or same_whatsapp, same_instagram, same_website, near))
        classification = "strong" if score >= 7 and families >= 2 else "review" if score >= 4 else "shared_signal"
        candidates.append({
            "left_name": left["business_name"], "left_area": left["area"], "left_category": left["category"], "left_cid": left["google_maps_cid"],
            "right_name": right["business_name"], "right_area": right["area"], "right_category": right["category"], "right_cid": right["google_maps_cid"],
            "name_similarity": f"{name_similarity:.3f}", "distance_m": "" if metres is None else f"{metres:.1f}",
            "signals": "|".join(signals), "signal_families": str(families), "score": str(score), "classification": classification,
            "left_phone": left["normalized_phone"], "right_phone": right["normalized_phone"],
            "left_whatsapp": left["whatsapp"], "right_whatsapp": right["whatsapp"],
            "left_instagram": left["instagram_handle"], "right_instagram": right["instagram_handle"],
            "left_website": left["website"], "right_website": right["website"],
            "decision": "", "rationale": "",
        })
    candidates.sort(key=lambda item: (-int(item["score"]), item["left_name"].casefold(), item["right_name"].casefold()))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "candidate-pairs.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidates[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(candidates)
    counts = Counter(item["classification"] for item in candidates)
    report = ["# Broader Entity-Resolution Sweep", "", "## Census", "", f"- Master records: {len(rows)}",
              f"- Candidate pairs: {len(candidates)}", f"- Strong pairs: {counts['strong']}", f"- Review pairs: {counts['review']}",
              f"- Shared-signal pairs: {counts['shared_signal']}", "", "## Strong and review queue", "",
              "| Left | Right | Score | Signals | Distance |", "|---|---|---:|---|---:|"]
    for item in candidates:
        if item["classification"] == "shared_signal": continue
        report.append(f"| {item['left_name'].replace('|','/')} | {item['right_name'].replace('|','/')} | {item['score']} | {item['signals']} | {item['distance_m'] or '—'} m |")
    (OUT / "ENTITY-RESOLUTION-SWEEP.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PASS: records={len(rows)} candidates={len(candidates)} classes={dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
