"""
Generate base descriptions for businesses that lack them.
Reads enrichment data, produces factual 1-2 sentence descriptions.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE / ".desc_all_input.json"
OUTPUT_PATH = BASE / ".desc_all_output.json"

AMENITY_MAP = {
    "Accesible": "wheelchair accessible",
    "Se permiten mascotas": "pet-friendly",
    "Piscina": "a pool",
    "Piscina al aire libre": "an outdoor pool",
    "Wi-Fi gratis": "free Wi-Fi",
    "Estacionamiento gratuito": "free parking",
    "Cocina": "kitchen access",
    "Aire acondicionado": "air conditioning",
    "Desayuno incluido": "included breakfast",
    "Desayuno": "breakfast",
    "Desayuno pago": "paid breakfast",
    "Gimnasio": "a gym",
    "Spa": "a spa",
    "Spa de masajes": "a massage spa",
    "Transporte desde/hacia el aeropuerto": "airport shuttle",
    "Incluye desayuno": "breakfast included",
    "Incluye Wi-Fi": "Wi-Fi included",
    "Incluye Wi-Fi y estacionamiento": "Wi-Fi and parking included",
    "Incluye desayuno, Wi-Fi y estacionamiento": "breakfast, Wi-Fi, and parking included",
    "Incluye desayuno y estacionamiento": "breakfast and parking included",
    "Bar": "a bar",
    "Se permiten mascotas": "pet-friendly",
    "cocina": "kitchen access",
    "Cocina latinoamericana": "kitchen access",
    "Libre de humo": "non-smoking",
    "Servicio en la habitacion": "room service",
    "Restaurante": "an on-site restaurant",
    "Restaurante en el hotel": "an on-site restaurant",
}


def clean(val):
    return str(val or "").strip()


def join_items(items):
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def article(word):
    return "an" if word and word[0].lower() in "aeiou" else "a"


def describe(biz):
    name = clean(biz.get("business_name"))
    area = clean(biz.get("area")) or "Puerto Viejo"
    cat = clean(biz.get("category"))
    sub_raw = clean(biz.get("subcategory"))
    cuisine = clean(biz.get("cuisine"))
    status = clean(biz.get("open_status"))
    raw_amenities = biz.get("amenities", []) or []

    # Filter subcategory noise — prefer master category over noisy subcategories
    SUBCAT_NOISE = {"restaurantes", "restaurante", "transporte público", "farmacia", "farmacias",
                    "bares", "hoteles", "cafes", "estacionamientos"}
    sub = sub_raw.lower() if sub_raw.lower() not in SUBCAT_NOISE else ""

    # Name-based category inference (for when enrichment data is sparse)
    NAME_TO_CAT = {
        "hotel": "hotel", "cabinas": "hotel", "lodge": "hotel", "villa": "hotel",
        "inn": "hotel", "bungalow": "hotel", "cabañas": "hotel", "resort": "hotel",
        "hostel": "hostel", "backpackers": "hostel",
        "masajes": "services", "tattoo": "services", "spa": "services",
        "massage": "services", "gym": "services", "yoga": "services",
        "rental": "services", "alquiler": "services", "taxi": "services",
        "restaurant": "restaurant", "restaurante": "restaurant", "pizzeria": "restaurant",
        "cafe": "restaurant", "cafeteria": "restaurant", "soda": "restaurant",
        "farmacia": "shopping", "supermarket": "shopping", "supermercado": "shopping",
        "tienda": "shopping", "store": "shopping", "boutique": "shopping",
        "tour": "tour_company", "travel": "tour_company", "adventure": "tour_company",
        "surf": "tour_company", "kayak": "tour_company", "snorkel": "tour_company",
    }
    if cat.lower() == "restaurant" or not cat:
        name_lower = name.lower()
        for keyword, mapped_cat in NAME_TO_CAT.items():
            if keyword in name_lower:
                cat = mapped_cat
                break

    # Smart category inference: override if amenities clearly indicate a different type
    LODGING_AMENITIES = {"piscina", "piscina al aire libre", "cocina", "kitchen",
                         "desayuno incluido", "gimnasio", "servicio en la habitacion",
                         "estacionamiento gratuito", "aire acondicionado"}
    MASSAGE_AMENITIES = {"masajes", "spa", "spa de masajes"}
    FOOD_KEYWORDS = {"pizza", "sushi", "ceviche", "helado", "ice cream", "crepe",
                     "hamburguesa", "taco", "empanada"}
    has_lodging = any(clean(a).lower() in LODGING_AMENITIES for a in raw_amenities)
    has_massage = any(clean(a).lower() in MASSAGE_AMENITIES for a in raw_amenities)
    has_food = cuisine.lower() in FOOD_KEYWORDS or any(kw in name.lower() for kw in FOOD_KEYWORDS)

    if has_lodging and cat.lower() not in ("hotel", "hostel"):
        cat = "hotel"  # Amenities clearly say lodging
    if has_massage and cat.lower() != "services":
        cat = "services"

    kind = sub if sub else (cat.lower() if cat else "local business")
    cat_group = cat.lower() if cat else ""

    # Pick template style based on category
    ams = []
    for a in raw_amenities:
        a_clean = clean(a)
        if a_clean in AMENITY_MAP:
            ams.append(AMENITY_MAP[a_clean])
        elif a_clean.lower() not in ("accesible",):
            ams.append(a_clean.lower())

    parts = []

    if cat_group in ("hotel", "hostel", "vacation_rental"):
        if ams:
            parts.append(f"{name} offers {kind} accommodations in {area} with {join_items(ams)}.")
        elif area:
            parts.append(f"{name} provides {kind} accommodations in {area}.")
        else:
            parts.append(f"{name} provides {kind} accommodations.")
    elif cat_group in ("restaurant",):
        if cuisine:
            parts.append(f"Find {cuisine.lower()} at {name}, a {kind} in {area}.")
        elif area:
            parts.append(f"{name} is a {kind} in {area}.")
        else:
            parts.append(f"{name} is a {kind}.")
    elif cat_group in ("services",):
        parts.append(f"{name} offers {kind} in {area}.")
    elif cat_group in ("tour_company",):
        parts.append(f"{name} runs tours and activities in the {area} area.")
    elif cat_group in ("shopping",):
        parts.append(f"{name} is a {kind} in {area}.")
    else:
        if cuisine:
            parts.append(f"{name} offers {cuisine.lower()} in {area}.")
        elif area:
            parts.append(f"{name} is located in {area}.")
        else:
            parts.append(f"{name} is a {kind}.")

    if ams and not parts[0].endswith(f"{join_items(ams)}."):
        pass  # already included

    if not ams and not cuisine and cat_group in ("",):
        pass  # only the generic line

    if status:
        s = status.lower().strip().rstrip(".")
        if s in ("abierto", "open", "abierto ahora"):
            parts.append("Open now.")
        elif s in ("cerrado", "closed"):
            parts.append("Closed now.")
        else:
            for prefix in ("abierto,", "abierto ", "open,", "open "):
                if s.startswith(prefix):
                    s = s[len(prefix):].strip()
                    break
            if not s.endswith("."):
                s += "."
            parts.append(f"Open {s}")

    desc = " ".join(parts)
    if not desc.endswith("."):
        desc += "."

    return {
        "business_name": name,
        "description_full": desc,
    }


def main():
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(f"Generating descriptions for {len(data)} businesses...")
    results = [describe(b) for b in data]
    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Written: {OUTPUT_PATH}")

    # Show sample
    for r in results[:5]:
        print(f"\n  {r['business_name']}:")
        print(f"    {r['description_full']}")


if __name__ == "__main__":
    main()
