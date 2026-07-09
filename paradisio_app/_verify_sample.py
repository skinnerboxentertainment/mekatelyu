import json
with open("docs/paradisio_app/data/businesses.json", encoding="utf-8") as f:
    biz = json.load(f)
by_slug = {b["slug"]: b for b in biz}
sample = [
    "black-bamboo-puerto-viejo",
    "gigi-o-restaurant-puerto-viejo",
    "rocking-j-s-hostel-puerto-viejo",
    "old-harbour-supermarket-puerto-viejo",
    "jaguar-rescue-center-playa-chiquita-puerto-viejo-lim-n-costa-rica-playa-chiquita",
    "black-shack-surf-school-playa-cocles-puerto-viejo-lim-n-costa-rica-cocles",
    "tasty-waves-cantina-playa-cocles-puerto-viejo-lim-n-costa-rica-cocles",
    "pizzeria-pulcinella-playa-chiquita-puerto-viejo-lim-n-costa-rica-playa-chiquita",
    "la-tica-y-la-gata-puerto-viejo",
    "tienda-caribe-puerto-viejo",
    "lavander-a-la-estrella-puerto-viejo",
]
for slug in sample:
    if slug in by_slug:
        b = by_slug[slug]
        cid = b.get("channels",{}).get("google_maps_cid","")
        print(f"OK  {b['category']:20s} {cid:20s} {b['name'][:50]}")
    else:
        print(f"MISS {slug}")
