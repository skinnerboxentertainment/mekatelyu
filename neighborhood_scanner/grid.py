"""
Spatial grid design for the 5 km radius around Puerto Viejo.
Generates scan targets at z16 (all areas) and z17 (dense commercial areas).
Filters out ocean cells using a simple land approximation.
"""
import csv
import json
import math

ORIGIN_LAT, ORIGIN_LON = 9.6554, -82.7533
RADIUS_KM = 5.0

# Approximate commercial zones that deserve higher-density scanning
DENSE_ZONES = [
    (9.658, -82.753, 0.8),  # Puerto Viejo center
    (9.650, -82.738, 0.8),  # Cocles commercial strip
    (9.656, -82.745, 0.6),  # Cocles beach area
    (9.663, -82.770, 0.6),  # Playa Negra
    (9.638, -82.710, 0.6),  # Playa Chiquita
]

# Rough land polygons (simplified bounding boxes for Puerto Viejo area)
# This is an approximation — we'll filter more aggressively with OSM data
LAND_BOXES = [
    # Main coastal strip: Puerto Viejo → Playa Chiquita
    (9.650, 9.670, -82.760, -82.740),
    (9.645, 9.655, -82.745, -82.730),
    (9.635, 9.650, -82.730, -82.705),
    # Playa Negra
    (9.660, 9.670, -82.780, -82.760),
    # Hone Creek inland
    (9.680, 9.700, -82.780, -82.760),
    # Manzanillo
    (9.628, 9.640, -82.660, -82.650),
    # Punta Uva
    (9.625, 9.635, -82.700, -82.690),
]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def is_on_land(lat, lon):
    """Check if a point falls within one of our approximate land boxes."""
    for lat_min, lat_max, lon_min, lon_max in LAND_BOXES:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return True
    return False


def is_in_dense_zone(lat, lon):
    """Check if a point falls within a known commercial zone."""
    for zlat, zlon, zr in DENSE_ZONES:
        if haversine_km(lat, lon, zlat, zlon) <= zr:
            return True
    return False


def generate_grid(spacing_km=0.3):
    """Generate a staggered hexagonal grid within the 5 km radius."""
    targets = []
    # Staggered grid: every other row is offset by half spacing
    spacing_deg_lat = spacing_km / 111.0
    spacing_deg_lon = spacing_km / (111.0 * math.cos(math.radians(ORIGIN_LAT)))

    lat_start = ORIGIN_LAT - (RADIUS_KM / 111.0)
    lat_end = ORIGIN_LAT + (RADIUS_KM / 111.0)
    lon_start = ORIGIN_LON - (RADIUS_KM / (111.0 * math.cos(math.radians(ORIGIN_LAT))))
    lon_end = ORIGIN_LON + (RADIUS_KM / (111.0 * math.cos(math.radians(ORIGIN_LAT))))

    row = 0
    lat = lat_start
    while lat <= lat_end:
        lon = lon_start
        if row % 2 == 1:
            lon += spacing_deg_lon / 2  # stagger
        while lon <= lon_end:
            if haversine_km(lat, lon, ORIGIN_LAT, ORIGIN_LON) <= RADIUS_KM:
                if is_on_land(lat, lon):
                    in_dense = is_in_dense_zone(lat, lon)
                    targets.append({
                        "latitude": round(lat, 6),
                        "longitude": round(lon, 6),
                        "zoom_z16": True,
                        "zoom_z17": in_dense,
                        "zone": "dense" if in_dense else "standard",
                    })
            lon += spacing_deg_lon
        lat += spacing_deg_lat
        row += 1

    return targets


def main():
    targets = generate_grid(spacing_km=0.3)

    z16_targets = [t for t in targets if t["zoom_z16"]]
    z17_targets = [t for t in targets if t["zoom_z17"]]
    dense_targets = [t for t in targets if t["zone"] == "dense"]
    standard_targets = [t for t in targets if t["zone"] == "standard"]

    print(f"Grid generation complete:")
    print(f"  Total land targets within 5 km: {len(targets)}")
    print(f"  Z16 targets (all land):         {len(z16_targets)}")
    print(f"  Z17 targets (dense zones only):  {len(z17_targets)}")
    print(f"  Dense commercial zones:          {len(dense_targets)}")
    print(f"  Standard coverage zones:         {len(standard_targets)}")

    # Write full grid
    with open("neighborhood_scanner/scan_grid.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["latitude", "longitude", "zoom_z16", "zoom_z17", "zone"])
        w.writeheader()
        for t in targets:
            w.writerow(t)

    # Write prioritized list (dense first, then standard)
    with open("neighborhood_scanner/scan_targets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["latitude", "longitude", "z16", "z17", "zone", "priority"])
        w.writeheader()
        for i, t in enumerate(sorted(targets, key=lambda x: (0 if x["zone"] == "dense" else 1, x["latitude"])), 1):
            w.writerow({
                "latitude": t["latitude"],
                "longitude": t["longitude"],
                "z16": "yes" if t["zoom_z16"] else "",
                "z17": "yes" if t["zoom_z17"] else "",
                "zone": t["zone"],
                "priority": i,
            })

    print(f"\nWritten:")
    print(f"  neighborhood_scanner/scan_grid.csv ({len(targets)} targets)")
    print(f"  neighborhood_scanner/scan_targets.csv (prioritized)")

    # Show sample
    print(f"\nSample targets (dense zones, first 5):")
    for t in dense_targets[:5]:
        print(f"  {t['latitude']},{t['longitude']} [z16+z17]")
    print(f"\nSample targets (standard zones, first 5):")
    for t in standard_targets[:5]:
        print(f"  {t['latitude']},{t['longitude']} [z16]")


if __name__ == "__main__":
    main()
