import csv, re
with open('pv_master_unified.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
suffixes = {}
for r in rows:
    n = r.get('business_name','').strip()
    a = r.get('area','').strip()
    parts = re.split(r'\s*[,–—|]\s*', n)
    if len(parts) > 1:
        suffix = parts[-1].strip()
        key = (suffix, suffix.lower() == a.lower())
        suffixes[key] = suffixes.get(key, 0) + 1
sorted_s = sorted(suffixes.items(), key=lambda x: -x[1])
for (s, match), c in sorted_s[:40]:
    print(f'  suffix="{s}" matches_area={match} count={c}')
print(f'\nTotal names with separators: {sum(c for (s,m),c in sorted_s)}')
# Show some examples of the longest names
print('\nLongest names:')
sorted_names = sorted(rows, key=lambda r: -len(r.get('business_name','')))
for r in sorted_names[:10]:
    print(f'  [{len(r.get("business_name","")):3d}] {r["business_name"]}  (area={r["area"]})')
