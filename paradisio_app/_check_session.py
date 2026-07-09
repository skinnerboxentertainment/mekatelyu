import json
with open("CODEX_ENDPOINT/sessions/13f60523.json", encoding="utf-8") as f:
    raw = json.load(f)
conv = raw.get("conversation", [])
print(f"Entries: {len(conv)}, State: {raw.get('state')}, Turn: {raw.get('turn')}")
for e in conv:
    print(f"  Turn {e['turn']}: from={e['from']} type={e['type']} msg_len={len(e['message'])}")
if len(conv) > 1:
    msg = conv[-1]["message"]
    print(f"\nLast message ({len(msg)} chars):")
    print(msg[:2000])
