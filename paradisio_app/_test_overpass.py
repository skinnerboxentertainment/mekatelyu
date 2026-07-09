import httpx

headers = {
    "User-Agent": "Paradisio/1.0 (Puerto Viejo business directory; +https://github.com/skinnerboxentertainment/mekatelyu)",
    "Accept": "application/json",
}
query = '[out:json];node(around:1000,9.655,-82.753)[name];out 2;'
resp = httpx.get("https://overpass-api.de/api/interpreter", params={"data": query}, headers=headers, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Body: {resp.text[:500]}")
if resp.status_code == 200:
    import json
    data = resp.json()
    print(f"Elements: {len(data.get('elements',[]))}")
