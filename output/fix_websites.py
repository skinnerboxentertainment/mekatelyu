"""Resolve affiliate-wrapped URLs to real websites in the master dataset."""
import csv
import re
from urllib.parse import unquote, urlparse

AFFILIATE_DOMAINS = {
    'anrdoezrs.net', 'kqzyfj.com', 'dpbolvw.net', 'tkqlhce.com',
    'jdoqocy.com', 'awltovhc.com', 'emjcd.com', 'ftjcfx.com',
    'lduhtrp.net', 'qksz.net', 'tqlkg.com',
    'pjatr.com', 'apmebf.com',
}


def resolve_url(url):
    """Extract real destination URL from an affiliate wrapper."""
    original = url
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')

    # Pattern 1: anrdoezrs.net/links/XXXX/type/dlg/https://real.url/
    if domain in AFFILIATE_DOMAINS:
        # Try to extract from path after /type/dlg/
        m = re.search(r'/type/dlg/(https?://\S+)', url, re.I)
        if m:
            return m.group(1).rstrip('/')
        # Try to extract from query param 'url'
        m = re.search(r'[?&]url=(https?%3A%2F%2F[^&]+)', url, re.I)
        if m:
            real = unquote(m.group(1))
            return real.rstrip('/')
        # Try to extract from path after /links/XXXX/
        m = re.search(r'/links/\d+/(?:type/dlg/)?(https?://\S+)', url, re.I)
        if m:
            return m.group(1).rstrip('/')

    # Pattern 2: booking.com/hotel/... links — keep as-is (it's a real booking page)
    # Pattern 3: VRBO/Airbnb — keep as-is (it's a real listing)

    return original


# Load master
with open('pv_master_unified.csv', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

fixed = 0
for row in rows:
    website = row.get('website', '').strip()
    if not website:
        continue
    resolved = resolve_url(website)
    if resolved != website:
        row['website'] = resolved
        fixed += 1
        print(f'{row["business_name"][:40]:40s} {website[:50]:50s} -> {resolved[:50]}')

# Write
with open('pv_master_unified.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f'\nFixed {fixed} websites.')
