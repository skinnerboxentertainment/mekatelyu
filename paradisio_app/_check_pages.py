import subprocess, json
result = subprocess.run(["gh", "api", "repos/skinnerboxentertainment/mekatelyu/pages/builds", "--paginate"], capture_output=True, text=True)
data = json.loads(result.stdout)
for b in data[:3]:
    status = b["status"]
    err = b.get("error", {})
    msg = err.get("message", "") if err else ""
    print(f"Status: {status}")
    if msg:
        print(f"  Error: {msg}")
    print(f"  Created: {b['created_at'][:19]}")
    print()
