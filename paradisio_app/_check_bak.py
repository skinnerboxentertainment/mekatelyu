import json
with open("CODEX_ENDPOINT/sessions/13f60523.bak", encoding="utf-8") as f:
    raw = json.load(f)
conv = raw.get("conversation", [])
print(f"Entries in bak: {len(conv)}")
for e in conv:
    print(f"  Turn {e['turn']}: from={e['from']} type={e['type']} msg_len={len(e['message'])}")
if len(conv) > 1:
    msg = conv[-1]["message"]
    print(f"\nCodex response ({len(msg)} chars):")
    print(msg[:3000])
