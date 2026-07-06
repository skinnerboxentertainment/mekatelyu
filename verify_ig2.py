"""
Verify all Instagram handles by checking for "page not available" message.
Instagram serves a distinct error page for dead handles:
  "Sorry, this page isn't available. The link you followed may be broken..."
Only working profiles lack this text.
"""

import csv
import json
import re
import time
import httpx
import os

INPUT_CSV = "pv_within_5km_clean.csv"
OUTPUT_CSV = "pv_within_5km_verified.csv"
LOG_FILE = "ig_verify_log.json"
PROGRESS_FILE = "ig_verify_progress.json"

DELAY = 2.0  # seconds between requests


def check_handle(handle: str, client: httpx.Client) -> dict:
    """Check if an Instagram handle resolves to a working profile."""
    result = {"handle": handle, "working": False, "reason": ""}

    try:
        resp = client.get(
            f"https://www.instagram.com/{handle}/",
            timeout=15.0,
            follow_redirects=True,
        )

        html = resp.text

        # Check for the telltale "not found" text
        if "Sorry, this page isn't available" in html:
            result["reason"] = "page_not_found"
            return result

        if "The link you followed may be broken" in html:
            result["reason"] = "broken_link"
            return result

        # Check if redirected to login (private profile or blocked)
        if "login" in resp.url.path.lower() or "accounts/login" in resp.url.path.lower():
            # This could be a private profile — still a real account, just locked
            result["working"] = True
            result["reason"] = "login_required_but_exists"
            return result

        # Also check for "hcaptcha" which means Instagram is challenging us
        if "hcaptcha" in html or "challenge" in resp.url.path.lower():
            result["reason"] = "challenged"
            return result

        # If we got here and have a real page with content, it's working
        result["working"] = True
        result["reason"] = "ok"

    except httpx.TimeoutException:
        result["reason"] = "timeout"
    except Exception as e:
        result["reason"] = f"error: {str(e)[:80]}"

    return result


def main():
    with open(INPUT_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    total = len(rows)
    print(f"Loaded {total} records", flush=True)

    # Add verification fields
    for col in ["ig_verified", "ig_verify_date"]:
        if col not in fieldnames:
            fieldnames.append(col)

    # Load progress
    processed_urls = set()
    log = []
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
            processed_urls = set(progress.get("processed", []))
            log = progress.get("log", [])
        print(f"Resuming: {len(processed_urls)} already checked", flush=True)

    # Index rows by URL for quick lookup
    row_map = {r["url"]: r for r in rows}

    targets = [(r["url"], r.get("instagram_handle", ""), r.get("business_name", "") or "")
               for r in rows if r.get("instagram_handle") and r["url"] not in processed_urls]

    print(f"Remaining to check: {len(targets)}", flush=True)

    client = httpx.Client(
        timeout=15.0,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        },
    )

    removed = 0
    kept = 0
    now = time.strftime("%Y-%m-%d")

    for idx, (url, handle, name) in enumerate(targets, 1):
        print(f"  [{idx}/{len(targets)}] @{handle} — {name[:40]}", flush=True)

        result = check_handle(handle, client)
        log.append({"url": url, "handle": handle, **result})

        r = row_map[url]
        r["ig_verified"] = str(result["working"]).lower()
        r["ig_verify_date"] = now

        if result["working"]:
            kept += 1
            # Update confidence
            if result["reason"] == "login_required_but_exists":
                # Private profile — still valid but lower confidence
                if r.get("instagram_confidence") == "confirmed":
                    pass  # keep as confirmed
                else:
                    r["instagram_confidence"] = "private"
            else:
                pass  # keep existing confidence
        else:
            removed += 1
            r["instagram_handle"] = ""
            r["instagram_url"] = ""
            r["instagram_confidence"] = "removed"
            print(f"    REMOVED: {result['reason']}", flush=True)

        # Mark as processed
        processed_urls.add(url)
        time.sleep(DELAY)

        # Save progress periodically
        if idx % 30 == 0:
            with open(PROGRESS_FILE, "w") as f:
                json.dump({"processed": list(processed_urls), "log": log}, f)
            print(f"  [progress saved: {kept} kept, {removed} removed]", flush=True)

    client.close()

    # Final save
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"processed": list(processed_urls), "log": log}, f)

    # Count results
    final_with_ig = sum(1 for r in rows if r.get("instagram_handle"))

    print(f"\n{'='*50}", flush=True)
    print(f"VERIFICATION COMPLETE", flush=True)
    print(f"{'='*50}", flush=True)
    print(f"  Checked:   {len(targets)}", flush=True)
    print(f"  Kept:      {kept}", flush=True)
    print(f"  Removed:   {removed}", flush=True)
    print(f"  Final IG:  {final_with_ig} of {total} ({final_with_ig/total*100:.1f}%)", flush=True)

    # Write cleaned CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Written: {OUTPUT_CSV}", flush=True)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"Log: {LOG_FILE}", flush=True)


if __name__ == "__main__":
    main()
