import json
import re
from pathlib import Path


INPUT = Path(".desc_all_output.json")
OUTPUT = Path(".desc_polished.json")


TYPE_LABELS = {
    "restaurant": "restaurant",
    "bar": "bar",
    "cafe": "cafe",
    "soda": "local soda",
    "lodging": "place to stay",
    "hotel": "hotel",
    "hostel": "hostel",
    "lodge": "lodge",
    "vacation_rental": "vacation rental",
    "tour": "tour operator",
    "service": "local service",
    "wellness": "wellness service",
    "tattoo": "tattoo studio",
    "pharmacy": "pharmacy",
    "shopping": "shop",
    "bank": "bank",
    "emergency": "public safety service",
    "school": "school",
    "gym": "gym",
    "parking": "parking option",
    "transport": "transport stop",
    "attraction": "local point of interest",
    "beach": "beach",
    "nature": "nature-focused place",
    "farm": "farm or cacao stop",
}


FEATURE_MAP = {
    "mariscos": "seafood",
    "ceviche": "ceviche",
    "sushi": "sushi",
    "parrilla": "grilled food",
    "italiana": "Italian food",
    "japonesa": "Japanese food",
    "hamburguesa": "burgers",
    "cocktail": "cocktails",
    "cerveza": "beer",
    "pizza": "pizza",
    "vegetarianos": "vegetarian options",
    "casado": "casados",
    "cafetería": "cafe fare",
    "chocolate": "chocolate",
    "thai massage": "Thai massage",
    "vegano": "vegan options",
}


TYPE_PATTERNS = [
    ("emergency", r"\b(bomberos|cruz roja|polic[ií]a|tourist police|oij)\b"),
    ("school", r"\b(escuela|centro educativo)\b"),
    ("bank", r"\b(banco)\b"),
    ("pharmacy", r"\b(farmacia)\b"),
    ("wellness", r"\b(masaje|massage|spa|fisioterapia|clinica|cl[ií]nica|dental|dentista|medicina)\b"),
    ("tattoo", r"\b(tattoo|tinta)\b"),
    ("gym", r"\b(gym|functional training|tkd|training)\b"),
    ("parking", r"\b(parking|parqueo)\b"),
    ("transport", r"\b(bus station|terminal de buses)\b"),
    ("tour", r"\b(tour|tours|paragliding|rides|observatorio|redfrogteam|ara manzanillo|explora)\b"),
    ("beach", r"\b(playa|beach)\b"),
    ("attraction", r"\b(viewpoint|sloth sanctuary|sloth crossing|piscina natural|puerto viejo de talamanca)\b"),
    ("farm", r"\b(finca|permaculture|cacao|chocolate|chocorart)\b"),
    ("hostel", r"\b(hostel|albergue|selina)\b"),
    ("lodge", r"\b(lodge|ecolodge)\b"),
    ("hotel", r"\b(hotel|inn|resort|cabinas|cabina|cabañas|cabana|cabaña|alojamiento|hospedaje|bed and breakfast|b&b|guest house|guesthouse|apart hotel)\b"),
    ("vacation_rental", r"\b(casa|casas|casita|casitas|villa|villas|apartment|apartments|bungalow|bungalows|home|house|treehouse|studio|glamping|retreat|cabin|cabins|jungalow)\b"),
    ("restaurant", r"\b(restaurant|restaurante|ristorante|bistro|soda|pizzeria|parrilla|comida|cafe|caf[eé]|breakfast|sushi)\b"),
    ("bar", r"\b(bar|beach club)\b"),
    ("shopping", r"\b(boutique|super|supermercado|taller|tablas de surf|surf side)\b"),
]


def clean_name(name):
    return re.sub(r"\s+", " ", name).strip()


def extract_location(name, description):
    for text in (description, name):
        m = re.search(
            r"\bin ([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ ]+?)(?: featuring|\.|$)",
            text,
        )
        if m:
            loc = m.group(1).strip()
            if loc:
                return loc
    parts = [p.strip() for p in name.split(" - ")]
    if len(parts) > 1:
        return parts[-1].split(",")[0].strip()
    return "Puerto Viejo"


def display_name(name):
    parts = [p.strip() for p in name.split(" - ")]
    return parts[0] if len(parts) > 1 else clean_name(name)


def original_category(description):
    m = re.search(r" is an? ([^.]+?) in ", description)
    return (m.group(1).strip().lower() if m else "")


def infer_type(name, description):
    haystack = f"{name} {description}".lower()
    for kind, pattern in TYPE_PATTERNS:
        if re.search(pattern, haystack, re.IGNORECASE):
            return kind

    cat = original_category(description)
    if cat in {"restaurant", "bar", "hotel", "hostel", "lodge", "vacation_rental", "tour_company", "shopping"}:
        return "tour" if cat == "tour_company" else cat
    if cat in {"bed & breakfast", "albergue"}:
        return "hostel" if cat == "albergue" else "hotel"
    if cat in {"restaurante asiático", "parrilla", "sushi", "cafetería", "restaurante familiar"}:
        return "restaurant"
    if cat in {"banco", "dentista", "supermercado", "boutique"}:
        return {"banco": "bank", "dentista": "wellness", "supermercado": "shopping", "boutique": "shopping"}[cat]
    return "service" if cat == "services" else "attraction"


def extract_feature(description):
    m = re.search(r" featuring ([^.]+)", description)
    if not m:
        return ""
    raw = m.group(1).strip().lower()
    if "." in raw or "www" in raw or ".com" in raw:
        return ""
    return FEATURE_MAP.get(raw, raw.replace("_", " "))


def status_sentence(description):
    if "Open now" in description:
        return "Listed as open now."
    if "Closed now" in description:
        return "Listed as closed now."
    return ""


def polish(record, idx):
    name = clean_name(record.get("business_name", ""))
    desc = record.get("description_full", "")
    short = display_name(name)
    loc = extract_location(name, desc)
    kind = infer_type(name, desc)
    label = TYPE_LABELS[kind]
    feature = extract_feature(desc)
    status = status_sentence(desc)

    nearby = "" if loc == "Puerto Viejo" else f" in {loc}, near Puerto Viejo"
    in_loc = f" in {loc}"

    if kind in {"hotel", "hostel", "lodge", "vacation_rental", "lodging"}:
        templates = [
            f"{short} is a {label}{nearby}, useful for travelers planning a Caribbean coast stay.",
            f"For visitors looking around {loc}, {short} offers a {label} option in the area.",
            f"{short} gives travelers another {label} choice{nearby}.",
        ]
    elif kind in {"restaurant", "bar", "cafe", "soda"}:
        extra = f" with {feature}" if feature else ""
        templates = [
            f"{short} is a {label}{in_loc}{extra}, a straightforward stop for visitors exploring the area.",
            f"Travelers around {loc} can keep {short} in mind as a {label}{extra}.",
            f"{short} adds a {label} option to the {loc} map{extra}.",
        ]
    elif kind == "tour":
        templates = [
            f"{short} is a tour and activity option{nearby} for travelers planning time on the Caribbean side.",
            f"Visitors looking for local experiences around {loc} can start with {short}.",
            f"{short} helps round out the activity options{nearby}.",
        ]
    elif kind in {"wellness", "tattoo", "gym"}:
        extra = f", with {feature} mentioned" if feature else ""
        templates = [
            f"{short} is a {label}{in_loc}{extra}, useful to know while staying in the area.",
            f"For travelers spending time around {loc}, {short} is a local {label}{extra}.",
            f"{short} offers a {label} option{nearby}{extra}.",
        ]
    elif kind in {"pharmacy", "bank", "emergency", "parking", "transport", "shopping", "service", "school"}:
        templates = [
            f"{short} is a {label}{in_loc}, practical information for visitors navigating the area.",
            f"Travelers may find {short} useful as a {label}{nearby}.",
            f"{short} is listed as a {label}{in_loc}.",
        ]
    elif kind in {"beach", "attraction", "nature", "farm"}:
        templates = [
            f"{short} is a local point of interest{nearby} for visitors exploring the Caribbean coast.",
            f"Travelers building an itinerary around {loc} may want to note {short}.",
            f"{short} adds another stop to consider{nearby}.",
        ]
    else:
        templates = [f"{short} is a local listing{nearby} for visitors exploring the area."]

    text = templates[idx % len(templates)]
    if status:
        text = f"{text} {status}"

    out = dict(record)
    out["description_full"] = text
    return out


def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    polished = [polish(record, idx) for idx, record in enumerate(data)]
    OUTPUT.write_text(json.dumps(polished, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(polished)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
