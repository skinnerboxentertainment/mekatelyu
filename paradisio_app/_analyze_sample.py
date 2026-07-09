"""
Analyze the 11 CID samples, identify field patterns per category.
"""
import json, re
from collections import defaultdict
from pathlib import Path

with open("docs/paradisio_app/data/cid_v2_samples/batch_results.json", encoding="utf-8") as f:
    samples = json.load(f)

# Determine what data fields are present in each sample
def analyze_text(text, name, category):
    lines = text.split("\n")
    fields = {}
    lines_clean = [l.strip() for l in lines if l.strip()]

    # Business name (first substantive line)
    for l in lines_clean:
        if l not in ["Arrastra para cambiar.", "Arrastra para cambiar, haz clic para eliminar.", "Obtener app", "Ver fotos", "Hoteles cercanos", "Restaurantes", "Restaurantes cercanos", "Cosas que hacer", "Bares", "Cafes", "Farmacias", "Estacionamientos", "Guardado", "Recientes", "Hoteles", "Cosas que hacer", "Bares", "Cafes", "Para llevar", "Tiendas de comestibles"] and len(l) > 5:
            fields["business_name"] = l
            break

    # Rating
    for l in lines_clean:
        if re.match(r"^\d\.\d$", l):
            fields["rating"] = float(l)
            break

    # Subcategory (line after rating)
    for i, l in enumerate(lines_clean):
        if re.match(r"^\d\.\d$", l):
            for j in range(i+1, min(i+5, len(lines_clean))):
                nxt = lines_clean[j]
                if nxt and not re.match(r"^\d\.\d$", nxt) and len(nxt) > 2 and len(nxt) < 60:
                    fields["subcategory"] = nxt
                    break
            break

    # Hours of operation
    hours = [l for l in lines_clean if re.match(r"\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?\s*[–\-to]\s*\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?", l, re.IGNORECASE)]
    if hours:
        fields["hours_of_operation"] = hours[0]

    # Open/closed status
    for l in lines_clean:
        if re.match(r"Abierto|Cerrado|Open|Closed", l, re.IGNORECASE):
            fields["open_status"] = l
            break

    # Check-in/out
    ci = re.search(r"(?:hora de )?entrada[:\s]+([\d:.ap\s]+)", text, re.IGNORECASE)
    if ci: fields["check_in"] = ci.group(1).strip()
    co = re.search(r"(?:hora de )?salida[:\s]+([\d:.ap\s]+)", text, re.IGNORECASE)
    if co: fields["check_out"] = co.group(1).strip()

    # Phone
    for l in lines_clean:
        phone = re.search(r"(\+506\s*\d{4}\s*\d{4})|(\d{4}\s*\d{4})", l)
        if phone and "CRC" not in l and len(l) < 30:
            fields["phone"] = phone.group(0).strip()
            break

    # Website
    for l in lines_clean:
        if re.match(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}$", l, re.IGNORECASE) and "google" not in l.lower() and "Booking" not in l:
            fields["website"] = l
            break

    # Street address (long descriptive line)
    for l in lines_clean:
        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Za-z]+){1,10},\s*(?:Costa Rica|Limón|Puerto Viejo)", l):
            fields["street_address"] = l
            break

    # Plus Code
    for l in lines_clean:
        if re.match(r"[A-Z]\d{3,}", l):
            fields["plus_code"] = l
            break

    # Amenities
    amenity_keywords = ["Wi-Fi", "Estacionamiento", "Piscina", "Aire acondicionado", "Restaurante", "Gimnasio", "Desayuno", "Transporte", "Acceso", "Admite"]
    amenities_list = []
    for l in lines_clean:
        for kw in amenity_keywords:
            if re.search(kw, l, re.IGNORECASE) and len(l) < 60:
                amenities_list.append(l)
                break
    if amenities_list:
        fields["amenities"] = list(set(amenities_list))

    # Prices
    prices = [l.strip() for l in lines_clean if re.search(r"CRC\s*[\d,]+", l)]
    if prices:
        fields["prices"] = prices[:3]

    # Review count
    for l in lines_clean:
        rc = re.search(r"\((\d+)\)", l)
        if rc and "CRC" not in l and len(l) < 20:
            if int(rc.group(1)) > 20:
                fields["review_count"] = int(rc.group(1))
                break

    return fields, lines


# Generate report
report_lines = []
report_lines.append("=" * 70)
report_lines.append("CID v2 SAMPLE ANALYSIS — 11 Businesses Across 6 Categories")
report_lines.append("=" * 70)

all_fields = set()
by_category = defaultdict(list)

for s in samples:
    fields, lines = analyze_text(s["visible_text"], s["name"], s["category"])
    by_category[s["category"]].append({"name": s["name"], "fields": fields, "lines": len(lines), "links": len(s["links"]), "images": len(s["images"])})
    for k in fields.keys():
        all_fields.add(k)

report_lines.append(f"\nCommon fields across all samples: {len(all_fields)}\n")

# Per-category breakdown
report_lines.append("\n" + "=" * 70)
report_lines.append("PER-CATEGORY FIELD PATTERNS")
report_lines.append("=" * 70)

FIELD_LABELS = {
    "business_name": "Business Name", "rating": "Rating", "subcategory": "Subcategory",
    "hours_of_operation": "Hours of Operation", "open_status": "Open/Closed Status",
    "check_in": "Check-in Time", "check_out": "Check-out Time",
    "phone": "Phone", "website": "Website",
    "street_address": "Street Address", "plus_code": "Plus Code",
    "amenities": "Amenities List", "prices": "Prices",
    "review_count": "Review Count",
}

for cat in sorted(by_category.keys()):
    items = by_category[cat]
    report_lines.append(f"\n{'-' * 60}")
    report_lines.append(f"CATEGORY: {cat.upper()} ({len(items)} samples)")
    report_lines.append(f"{'-' * 60}")
    
    # Count field prevalence
    field_count = defaultdict(int)
    for item in items:
        for k in item["fields"]:
            field_count[k] += 1
    
    report_lines.append(f"\n  {'Field':30s} {'Found':>6s} {'Rate':>6s}")
    report_lines.append(f"  {'-'*30} {'-'*6} {'-'*6}")
    for field in sorted(all_fields, key=lambda f: -field_count.get(f, 0)):
        count = field_count.get(field, 0)
        rate = f"{count}/{len(items)}"
        label = FIELD_LABELS.get(field, field)
        report_lines.append(f"  {label:30s} {rate:>6s}")
    
    report_lines.append(f"\n  Raw text sizes: {', '.join(str(item['lines']) for item in items)} lines")
    report_lines.append(f"  Links per page: {', '.join(str(item['links']) for item in items)}")
    report_lines.append(f"  Images per page: {', '.join(str(item['images']) for item in items)}")
    
    # Show actual data for first sample in category
    first = items[0]
    report_lines.append(f"\n  --- {first['name']} (sample data) ---")
    for k, v in first["fields"].items():
        label = FIELD_LABELS.get(k, k)
        if isinstance(v, list):
            report_lines.append(f"    {label}: {', '.join(v[:3])}")
        else:
            report_lines.append(f"    {label}: {v}")

# Summary
report_lines.append("\n\n" + "=" * 70)
report_lines.append("SUMMARY: AVAILABLE BUT NOT EXTRACTED IN v1")
report_lines.append("=" * 70)

v1_captured = {"rating", "subcategory", "phone", "website", "plus_code", "check_in", "check_out", "amenities", "prices", "review_count"}
v2_discovered = all_fields - v1_captured
v2_frequency = {}
for s in samples:
    fields, _ = analyze_text(s["visible_text"], s["name"], s["category"])
    for f in v2_discovered:
        if f in fields:
            v2_frequency[f] = v2_frequency.get(f, 0) + 1

report_lines.append(f"\n  {'Field':25s} {'Found in':>8s} {'Rate'}")
report_lines.append(f"  {'-'*25} {'-'*8} {'-'*6}")
for field in sorted(v2_discovered, key=lambda f: -v2_frequency.get(f, 0)):
    label = FIELD_LABELS.get(field, field)
    count = v2_frequency.get(field, 0)
    report_lines.append(f"  {label:25s} {count:3d}/11 samples")

report_lines.append(f"\n\nNOTE: Fields like street_address and hours_of_operation")
report_lines.append(f"are category-specific — hotels show check-in/out, restaurants show")
report_lines.append(f"daily hours, shops show open/closed. A single universal parser")
report_lines.append(f"will always miss something. Category-aware parsing is required.")

report = "\n".join(report_lines)
out_path = Path("docs/paradisio_app/data/cid_v2_samples/analysis_report.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(report)
print(f"Report written to {out_path}")
