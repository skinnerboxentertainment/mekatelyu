"""
Find the most complete restaurant in the database.
"""
import json
from pathlib import Path

with open("docs/paradisio_app/data/businesses.json", encoding="utf-8") as f:
    businesses = json.load(f)

# Score each restaurant on data completeness
restaurants = [b for b in businesses if b.get("category","").lower() == "restaurant"]

def completeness_score(b):
    score = 0
    fields = {
        "rating": 15, "subcategory": 10, "description": 10,
        "check_in": 5, "check_out": 5,
        "whatsapp": 10, "phone": 10, "website": 10, "instagram": 10,
        "facebook_url": 5, "booking_url": 5, "tripadvisor_url": 5,
        "google_maps_cid": 5, "lat": 5, "lng": 5,
        "maps_address": 5,
    }
    for field, weight in fields.items():
        if field == "whatsapp":
            if b.get("channels",{}).get("whatsapp"):
                score += weight
        elif field in ("lat", "lng"):
            if b.get(field):
                score += weight
        else:
            if b.get(field) or (field in ("instagram","phone","website","facebook_url","booking_url","tripadvisor_url") and b.get("channels",{}).get(field)):
                score += weight
    return score

scored = [(completeness_score(r), r) for r in restaurants]
scored.sort(key=lambda x: -x[0])

print("Top 10 most complete restaurants:\n")
for score, r in scored[:10]:
    channels = r.get("channels",{})
    amenities = r.get("amenities",[])
    print(f"  Score {score:3d}/110 | {r['name'][:45]:45s} | {r['area']:20s}")
    print(f"        Rating={r.get('rating','-')} Subcat={r.get('subcategory','-')}")
    print(f"        WP={channels.get('whatsapp','')[:8]:8s} Phone={channels.get('phone','')[:15]:15s} IG={channels.get('instagram','')[:20]:20s}")
    print(f"        Web={channels.get('website','')[:30]}")
    print(f"        Address={r.get('maps_address','')[:40] if r.get('maps_address') else '-':40s}")
    print(f"        Amenities={len(amenities)} items: {', '.join(amenities[:4])}")
    print()

# The best one
best_score, best = scored[0]
print(f"=== MOST COMPLETE RESTAURANT ===")
print(f"Name: {best['name']}")
print(f"Score: {best_score}/110")
print(f"Slug: {best['slug']}")
print(f"URL: businesses/{best['slug']}.html")
print(f"Rating: {best.get('rating')}")
print(f"Subcategory: {best.get('subcategory','')}")
print(f"Description: {best.get('description','')[:200]}")
