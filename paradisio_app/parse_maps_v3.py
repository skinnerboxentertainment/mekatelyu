"""
Maps extractor v3 — re-parses full text from maps_enrich_v2 captures.
Category-aware, confidence-scored, produces structured output + audit trail.
"""
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
V2_CHECKPOINT = BASE / "docs" / "paradisio_app" / "data" / "maps_checkpoint_v2.json"
V2_ENRICH = BASE / "docs" / "paradisio_app" / "data" / "maps_enrich_v2.json"
OUTPUT = BASE / "docs" / "paradisio_app" / "data" / "maps_parsed_v3.json"
AUDIT = BASE / "docs" / "paradisio_app" / "data" / "maps_audit_v3.json"

MONTHS_ES = {
    "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
    "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12,
}

CATEGORY_SUBCATEGORIES = {
    "hotel": ["hotel", "hostel", "bed & breakfast", "b&b", "guest house", "inn",
              "lodge", "resort", "cabin", "chalet", "apartotel", "motel",
              "cabaña", "albergue", "posada"],
    "restaurant": ["restaurant", "restaurante", "cafe", "cafeteria", "bar",
                   "pizzeria", "soda", "comida rapida", "fast food", "ice cream",
                   "heladeria", "panaderia", "bakery", "cocktail bar", "brewery",
                   "marisqueria", "grill", "parrilla", "sushi", "taqueria"],
    "shopping": ["supermarket", "supermercado", "grocery", "tienda", "shop",
                 "store", "boutique", "mercado", "market", "souvenir",
                 "liquor store", "pharmacy", "farmacia", "hardware", "ferreteria",
                 "bakery", "panaderia"],
    "tour_company": ["tour", "travel", "agency", "aventura", "adventure",
                     "snorkel", "diving", "surf", "kayak", "boat", "charter",
                     "nature", "wildlife", "jaguar", "rescue", "conservation",
                     "paragliding", "zipline", "canopy"],
    "services": ["massage", "masajes", "spa", "salon", "barber", "laundry",
                 "lavanderia", "gym", "fitness", "yoga", "rental", "alquiler",
                 "repair", "taller", "transport", "shuttle", "taxi",
                 "real estate", "bienes raices", "bank", "banco", "atm",
                 "pharmacy", "farmacia", "clinic", "clinica", "dentist",
                 "veterinary", "school", "iglesia", "church"],
    "hostel": ["hostel", "albergue", "backpackers", "dorm"],
}

CATEGORY_KEYWORDS = {
    "hotel": ["hotel", "lodge", "resort", "inn", "villa", "cabinas", "cabañas",
              "suites", "apartamentos", "bungalow", "guesthouse", "posada"],
    "restaurant": ["restaurant", "restaurante", "cafe", "soda", "pizzeria",
                   "grill", "parrilla", "marisqueria", "comida"],
    "shopping": ["supermarket", "supermercado", "tienda", "store", "boutique",
                 "mercado", "mini super"],
    "tour_company": ["tour", "travel", "adventure", "snorkel", "diving", "surf",
                     "kayak", "paragliding", "zipline", "expedition"],
    "services": ["massage", "spa", "salon", "laundry", "gym", "yoga", "rental",
                 "alquiler", "taller", "shuttle", "transport"],
    "hostel": ["hostel", "backpackers"],
}

WEEKDAYS_EN = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
WEEKDAYS_ES = ["lunes","martes","miercoles","miércoles","jueves","viernes","sabado","sábado","domingo"]


def has_any(text, keywords):
    tl = text.lower()
    for k in keywords:
        if k in tl:
            return True
    return False


def infer_category(name, subcat, full_text):
    text = f"{name} {subcat or ''} {full_text[:500]}".lower()
    scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for k in kws if k in text)
    if subcat:
        for cat, kws in CATEGORY_SUBCATEGORIES.items():
            if subcat.lower().strip() in [s.lower() for s in kws]:
                scores[cat] = scores.get(cat, 0) + 5
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def extract_rating(lines):
    for line in lines:
        m = re.match(r"^(\d\.\d)$", line)
        if m:
            return {"value": float(m.group(1)), "confidence": 0.9, "evidence": line}
    return None


def extract_phone(lines):
    for line in lines:
        m = re.search(r"(\+506[\s\-]*\d{4}[\s\-]*\d{3}[\s\-]*\d{3})", line)
        if not m:
            m = re.search(r"(\+506[\s\-]*\d{4}[\s\-]*\d{3,4})", line)
        if not m:
            m = re.search(r"(\d{4}[\s\-]*\d{3}[\s\-]*\d{3})", line)
        if not m:
            # Plain 8-digit CR number
            m = re.search(r"(?<!\d)(\d{4}[\s\-]?\d{4})(?!\d)", line)
        if m and len(m.group(0).strip()) >= 8:
            return {"value": m.group(0).strip(), "confidence": 0.85, "evidence": line.strip()}
    return None


def extract_website(lines):
    for line in lines:
        if re.match(r"^[a-z0-9][a-z0-9.\-]+\.[a-z]{2,}$", line, re.IGNORECASE) and "google" not in line.lower():
            return {"value": line, "confidence": 0.7, "evidence": line}
    return None


def extract_address(lines):
    result = {"street": None, "plus_code": None, "full_address": None, "raw": []}
    for line in lines:
        # Descriptive address: has numbers + street-like words
        if re.search(r"\d{1,4}\s", line) and re.search(r"(calle|avenida|av\.|street|road|blvd|boulevard)", line, re.IGNORECASE):
            result["street"] = line
            result["raw"].append(line)
        # Plus code: M742+8M pattern
        elif re.match(r"^[A-Z]\d{3,}", line):
            result["plus_code"] = line
            result["raw"].append(line)
    if result["street"]:
        result["full_address"] = result["street"]
    elif result["plus_code"]:
        result["full_address"] = result["plus_code"]
    if result["full_address"]:
        return {"value": result["full_address"], "plus_code": result["plus_code"],
                "confidence": 0.8 if result["street"] else 0.5, "evidence": result["raw"][0] if result["raw"] else ""}
    return None


def extract_open_status(lines):
    for line in lines:
        ls = line.lower().strip()
        if ls in ("abierto", "cerrado", "open", "closed", "abierto ahora", "cerrado ahora"):
            return {"value": line.strip(), "status": "open" if "abierto" in ls or "open" in ls else "closed",
                    "confidence": 0.9, "evidence": line.strip()}
    return None


def extract_hours(lines):
    candidates = []
    for line in lines:
        ls = line.lower().strip()
        # Skip check-in/out lines
        if re.search(r"(hora de entrada|hora de salida|check.in|check.out)", ls, re.IGNORECASE):
            continue
        # Day-of-week + time pattern (operating hours)
        has_day = any(day in ls for day in WEEKDAYS_ES + WEEKDAYS_EN)
        has_time = bool(re.search(r"\d{1,2}:\d{2}\s*(a\.?m\.?|p\.?m\.?)", ls, re.IGNORECASE))
        if has_day and has_time and len(ls) < 60:
            candidates.append((line.strip(), 0.8))
        # Just a time range like "7:30 a.m. - 6 p.m."
        elif re.match(r"^\d{1,2}:\d{2}\s*(a\.?m\.?|p\.?m\.?)\s*[-–to]+\s*\d{1,2}:\d{2}", ls, re.IGNORECASE):
            candidates.append((line.strip(), 0.6))
        # Single time not matching check-in/out patterns
        elif has_time and not re.match(r"^\d{1,2}:\d{2}", ls) and len(ls) < 50:
            candidates.append((line.strip(), 0.5))
    if candidates:
        best = max(candidates, key=lambda x: x[1])
        return {"value": best[0], "confidence": best[1], "evidence": best[0]}
    return None


def extract_check_in_out(lines):
    result = {"check_in": None, "check_out": None}
    for line in lines:
        ls = line.lower().strip()
        entrada = re.search(r"(?:hora de\s*)?entrada[:\s]+([\d:.\s]+[ap]\.?\s*m\.?)", ls, re.IGNORECASE)
        if entrada and result["check_in"] is None:
            result["check_in"] = entrada.group(1).strip()
        salida = re.search(r"(?:hora de\s*)?salida[:\s]+([\d:.\s]+[ap]\.?\s*m\.?)", ls, re.IGNORECASE)
        if salida and result["check_out"] is None:
            result["check_out"] = salida.group(1).strip()
    return result if (result["check_in"] or result["check_out"]) else None


AMENITY_BLACKLIST = {
    "bares", "restaurantes", "restaurant", "cosas que hacer",
    "farmacias", "estacionamientos", "cafes",
    "terrazas del caribe hotel", "lotus garden",
    "koki beach restaurant & bar", "casa ambar",
    "chill and cheese snackbar", "the goddess garden eco resort",
    "beach break bar & restaurant",
}


AMENITY_KEYWORDS = [
    "wifi", "wi-fi", "estacionamiento gratuito", "free parking",
    "parking", "piscina", "pool", "aire acondicionado", "air conditioning",
    "desayuno incluido", "desayuno", "breakfast",
    "gimnasio", "gym", "spa",
    "mascotas", "pet friendly", "pets allowed", "se permiten mascotas",
    "accesible", "wheelchair", "silla de ruedas",
    "lavanderia", "laundry",
    "cocina", "kitchen", "refrigerador", "fridge",
    "servicio en la habitacion", "room service",
    "transporte desde/hacia el aeropuerto", "airport shuttle",
    "piscina al aire libre", "outdoor pool",
    "restaurante en el hotel", "restaurant on site",
    "bar", "centro de negocios", "business center",
    "libre de humo", "non-smoking",
    "terraza", "patio", "jardin", "garden",
    "vista al mar", "ocean view", "frente a la playa", "beachfront",
    "hamacas", "hammock",
    "caja de seguridad", "safe",
    "agua caliente", "hot water",
    "ventilador", "fan",
    "cunas", "cribs",
    "estacionamiento gratuito", "free parking",
    "wifi gratis", "free wifi",
]


AMENITY_NOISE_PATTERNS = [
    r"\d+\s*habitaciones?", r"\d+\s*bedroom", r"\d\s*br\b",
    r"beachfront", r"garden view", r"ocean view", r"\bview\b",
    r"deluxe", r"\bsuite\b", r"\bapartment\b",
    r"\dpax", r"\d\s*guest", r"\bhouse\b", r"\bvilla\b",
    r"\u00b7",  # middle dot separator
    r"-\s*\d+\s*(pax|bed|bedroom|guest|person)",
    r"\d\s*-\s*bedroom",
]


def extract_amenities(lines):
    found = []
    seen = set()
    for line in lines:
        ls = line.lower().strip()
        if not ls or ls in UI_NOISE or ls in AMENITY_BLACKLIST:
            continue
        if len(ls) > 45:
            continue
        if any(re.search(p, ls) for p in AMENITY_NOISE_PATTERNS):
            continue
        # Skip business names (capitalized multi-word sequences that aren't amenity-focused)
        if re.match(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){2,5}$", line.strip()):
            # Only skip if it doesn't start with a known amenity prefix
            if not any(ls.startswith(kw) for kw in ("wi-fi", "wifi", "incluye", "desayuno", "estacionamiento", "piscina", "aire acondicionado", "accesible", "se permiten", "transporte", "spa")):
                continue
        for kw in AMENITY_KEYWORDS:
            if kw in ls and ls not in seen:
                seen.add(ls)
                found.append(line.strip())
                break
    return {"value": found[:12], "count": len(found), "confidence": 0.7} if found else None


UI_NOISE = {
    "hoteles cercanos", "restaurantes cercanos", "cosas que hacer",
    "acerca de", "indicaciones", "guardado", "recientes", "compartir",
    "cerca", "fotos y videos", "opiniones", "agregar la informacion que falta",
    "sugerir una edicion", "actualizaciones de los visitantes",
    "menu y platos destacados", "alquileres de vacaciones cerca de mi",
    "ver mas propiedades", "resultados web", "street view",
    "aprovecha al maximo google maps", "acceder", "capas",
    "detalles del mapa", "herramientas del mapa", "tipo de mapa",
    "predeterminado", "satelite", "etiquetas", "incendios",
    "calidad del aire", "duracion del viaje", "medicion",
    "hoteles similares cercanos", "tambien te puede interesar",
    "farmacias", "bares", "cafes", "estaciones de transporte publico",
    "cajeros automaticos", "transporte publico",
}


def extract_subcategory(lines, category):
    kws = CATEGORY_SUBCATEGORIES.get(category, [])
    # Score each candidate line: prefer exact matches, penalize length
    scored = []
    for line in lines:
        ls = line.lower().strip()
        if not ls or ls in UI_NOISE:
            continue
        if len(ls) > 35:
            continue
        # Skip if line is clearly a business name (multiple capitalized words + type suffix)
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+ (Lodge|Hotel|Hostel|Inn|Resort|Retreat|Casitas|Cabinas|Villas|Bungalows|Apartments|House|Place|Restaurant|Bar|Cafe|Tours)$", line.strip()):
            continue
        best_score = 0
        for kw in kws:
            if ls == kw:
                best_score = 10  # exact match
            elif ls.startswith(kw) or ls.endswith(kw):
                best_score = 8
            elif kw in ls:
                best_score = 5
        if best_score >= 5:
            scored.append((line.strip(), best_score, len(ls)))
    if not scored:
        return None
    # Pick highest score, then shortest line
    scored.sort(key=lambda x: (-x[1], x[2]))
    best = scored[0][0]
    return {"value": best, "confidence": 0.6, "evidence": best}


CUISINE_KEYWORDS = [
    "italian", "italiano", "mexican", "mexicano", "japanese", "japones",
    "chinese", "chino", "thai", "indian", "indio", "french", "frances",
    "mediterranean", "mediterraneo", "seafood", "mariscos", "sushi",
    "pizza", "burger", "hamburguesa", "vegan", "vegano", "vegetarian",
    "vegetariano", "organic", "organico", "grill", "parrilla",
    "caribbean", "caribeno", "fusion", "tradicional",
    "costarican", "costarricense", "tipico", "local food",
    "ice cream", "helado", "heladeria", "bakery", "panaderia",
    "cocktail", "coctel", "brewery", "cerveza", "coffee", "cafe",
    "brunch", "lunch", "dinner", "cena",
    "steak", "asado", "pasta", "taco", "ceviche", "empanada",
    "chocolate", "crepe", "gourmet", "bufet", "buffet",
]

CUISINE_NOISE_PATTERNS = [
    r"local guide", r"\d+\s*habitaciones?", r"\d+\s*bedroom",
    r"\d+\s*bañ", r"\d+\s*bath", r"\.\.\.", r"\u00b7", r"opinion",
    r"fotos", r"hace \d+", r"alojamiento para",
    r"\d\s*-\s*bedroom", r"\d\s*bdr", r"\d\s*br\b",
    r"beachfront", r"garden view", r"ocean view", r"pool view",
    r"jungle view", r"deluxe", r"standard", r"superior",
    r"\broom\b", r"\bsuite\b", r"\bapartment\b", r"\bhouse\b",
    r"\bvilla\b", r"\bbungalow\b", r"\bcabin\b", r"\bcasita\b",
    r"-\s*one\b", r"-\s*two\b", r"-\s*three\b",
    r"\dpax", r"\d\s*guest",
]

CUISINE_MAX_LEN = 35


CUISINE_BLACKLIST = {
    "caribbean surf school & shop",
    "caribbeans beach cahuita",
    "caribbean costa rica real estate",
    "tienda caribbean moon",
    "caribbean life",
    "caribbean tours puerto viejo",
    "the caribbean is waiting for you.",
    "caribbeanbluemorpho.com",
    "manzanillo caribbean resort",
    "caribbean flow",
    "caribbean blue morpho",
    "caribbean comfort",
    "caribbean courtyard villa",
}


KNOWN_BIZ_NAMES = None


def load_biz_names():
    global KNOWN_BIZ_NAMES
    if KNOWN_BIZ_NAMES is not None:
        return KNOWN_BIZ_NAMES
    import csv
    names = set()
    with open(BASE / "pv_master_unified.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            n = row.get("business_name", "").strip().lower()
            if n:
                names.add(n)
    KNOWN_BIZ_NAMES = names
    return names


def extract_cuisine(lines, business_name=""):
    biz_lower = business_name.lower().strip() if business_name else ""
    biz_words = set(biz_lower.split()) if biz_lower else set()
    known_names = load_biz_names()

    scored = []
    for line in lines:
        ls = line.lower().strip()
        if len(ls) > CUISINE_MAX_LEN or not ls:
            continue
        # Skip noise patterns
        if any(re.search(p, ls) for p in CUISINE_NOISE_PATTERNS):
            continue
        # Skip known business names
        if ls in known_names:
            continue
        is_known_biz = False
        for kn in known_names:
            if len(kn) > 15 and kn in ls:
                is_known_biz = True
                break
        if is_known_biz:
            continue
        # Check if line looks like a nearby listing
        if re.search(r"\d+\s*(habitaci.n|bedroom|ba.o|bañ|bath|persona|guest)", ls):
            continue
        # Skip known false-positive cuisine lines
        if ls in CUISINE_BLACKLIST:
            continue
        # Check if line looks like a named business/place (capitalized multi-word)
        if re.match(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){1,5}$", line.strip()):
            continue
        for kw in CUISINE_KEYWORDS:
            if kw in ls:
                # Priority: short lines with exact-ish matches are better than long partial matches
                kw_ratio = len(kw) / max(len(ls), 1)
                confidence = 0.6 if kw_ratio > 0.4 else 0.5
                if kw_ratio > 0.3:
                    scored.append((line.strip(), confidence, kw_ratio))
                break
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[2], -x[1]))
    best = scored[0]
    return {"value": best[0], "confidence": best[1], "evidence": best[0]}


def process_record(record, category):
    cid = record.get("cid", "")
    name = record.get("business", "")
    text = record.get("full_text", "")
    if not text:
        return None

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    parsed = {
        "cid": cid,
        "business": name,
        "captured_at": record.get("captured_at", ""),
        "text_length": len(text),
        "category": category,
        "fields": {},
        "inferred_category": None,
        "warnings": [],
    }

    # Common fields
    if r := extract_rating(lines):
        parsed["fields"]["rating"] = r
    if r := extract_phone(lines):
        parsed["fields"]["phone"] = r
    if r := extract_website(lines):
        parsed["fields"]["website"] = r
    if r := extract_address(lines):
        parsed["fields"]["address"] = r
    if r := extract_open_status(lines):
        parsed["fields"]["open_status"] = r
    if r := extract_hours(lines):
        parsed["fields"]["hours"] = r
    if r := extract_amenities(lines):
        parsed["fields"]["amenities"] = r
    if r := extract_subcategory(lines, category):
        parsed["fields"]["subcategory"] = r
    if r := extract_cuisine(lines, name):
        parsed["fields"]["cuisine"] = r

    # Check-in/out (lodging-specific)
    if category in ("hotel", "hostel", "vacation_rental"):
        if r := extract_check_in_out(lines):
            if r.get("check_in"):
                parsed["fields"]["check_in"] = {"value": r["check_in"], "confidence": 0.8}
            if r.get("check_out"):
                parsed["fields"]["check_out"] = {"value": r["check_out"], "confidence": 0.8}

    # Infer category if blank
    if not category or category == "unknown":
        inferred = infer_category(name, parsed["fields"].get("subcategory", {}).get("value"), text)
        parsed["inferred_category"] = inferred

    if not parsed["fields"]:
        parsed["warnings"].append("No fields extracted from text")

    return parsed


def main():
    print("=" * 60)
    print("MAPS EXTRACTOR v3 — re-parsing full text corpus")
    print("=" * 60)

    # Load v2 captures from checkpoint (has full_text)
    cp = json.load(open(V2_CHECKPOINT, encoding="utf-8"))
    records = cp["results"]
    print(f"Records loaded: {len(records)}")

    # Load master CSV for category mapping
    import csv
    master_by_cid = {}
    with open(BASE / "pv_master_unified.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid = row.get("google_maps_cid", "").strip()
            if cid:
                master_by_cid[cid] = {
                    "category": row.get("category", "").strip(),
                    "name": row.get("business_name", "").strip(),
                }

    output = []
    audit = {
        "run_at": datetime.now().isoformat(),
        "total": len(records),
        "extracted": 0,
        "by_category": Counter(),
        "field_coverage": Counter(),
        "inferred_categories": Counter(),
        "warnings": [],
    }

    for record in records:
        cid = record.get("cid", "")
        master = master_by_cid.get(cid, {})
        category = master.get("category", "")

        parsed = process_record(record, category)
        if not parsed:
            audit["warnings"].append(f"No text for CID {cid}")
            continue

        output.append(parsed)
        audit["extracted"] += 1
        cat = parsed["inferred_category"] or category or "unknown"
        audit["by_category"][cat] += 1
        for field in parsed["fields"]:
            audit["field_coverage"][field] += 1
        if parsed["inferred_category"]:
            audit["inferred_categories"][parsed["inferred_category"]] += 1
        if parsed["warnings"]:
            audit["warnings"].extend(parsed["warnings"])

    # Print summary before converting Counters
    print(f"\nField coverage:")
    for field, count in audit["field_coverage"].most_common():
        print(f"  {field:20s}: {count}/{audit['extracted']}")

    if audit["inferred_categories"]:
        print(f"\nInferred categories (for records with blank master category):")
        for cat, count in audit["inferred_categories"].most_common():
            print(f"  {cat:20s}: {count}")

    # Write outputs
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nWritten: {OUTPUT.name} — {len(output)} records")

    with open(AUDIT, "w", encoding="utf-8") as f:
        # Convert Counters to dicts for JSON
        audit["by_category"] = dict(audit["by_category"])
        audit["field_coverage"] = dict(audit["field_coverage"])
        audit["inferred_categories"] = dict(audit["inferred_categories"])
        json.dump(audit, f, indent=2, ensure_ascii=False)
    print(f"Written: {AUDIT.name}")

    if audit["inferred_categories"]:
        print(f"\nInferred categories (for records with blank master category):")
        for cat, count in audit["inferred_categories"].items():
            print(f"  {cat:20s}: {count}")


if __name__ == "__main__":
    main()
