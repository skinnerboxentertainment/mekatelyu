import json, sys
d = json.load(sys.stdin)
print(f"Status: {d.get('status')}")
print(f"URL: {d.get('html_url')}")
