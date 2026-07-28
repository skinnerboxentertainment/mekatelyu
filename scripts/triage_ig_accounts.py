"""
IG account triage: check all 444 handles, extract profile metadata,
sort by business category + activity level, output a prioritized watchlist.
"""

import csv
import json
import re
import time
import httpx
from pathlib import Path
from collections import Counter

MASTER_CSV = Path("pv_master_unified.csv")
OUTPUT_REPORT = Path("ig_triage_report.json")
OUTPUT_CSV = Path("ig_triage_results.csv")
DELAY = 1.5

# Event-producing categories (high signal probability)
HIGH_SIGNAL_CATEGORIES = {
    "bar", "nightclub", "live_music_venue", "restaurant",
    "yoga_studio", "gym", "wellness_center", "dance_school",
    "art_gallery", "cultural_center", "market", "tour_operator",
    "hostel", "community_organization", "music_venue",
}

MEDIUM_SIGNAL_CATEGORIES = {
    "cafe", "hotel", "surf_school", "spa", "retreat_center",
    "brewery", "store",
}


def check_account(handle: str, client: httpx.Client) -> dict:
    result = {
        "handle": handle,
        "alive": False,
        "status": "unknown",
        "post_count": None,
        "bio": None,
        "error": None,
    }
    try:
        resp = client.get(
            f"https://www.instagram.com/{handle}/",
            timeout=20.0,
            follow_redirects=True,
        )
        html = resp.text

        if "Sorry, this page isn't available" in html:
            result["status"] = "not_found"
            return result
        if "The link you followed may be broken" in html:
            result["status"] = "broken_link"
            return result
        if "login" in resp.url.path.lower():
            result["alive"] = True
            result["status"] = "login_wall"
            return result
        if "hcaptcha" in html or "challenge" in resp.url.path.lower():
            result["status"] = "challenged"
            return result

        result["alive"] = True
        result["status"] = "ok"

        # Extract shared data JSON
        m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                user = data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user", {})
                if user:
                    result["post_count"] = user.get("edge_owner_to_timeline_media", {}).get("count")
                    result["bio"] = user.get("biography")
            except (json.JSONDecodeError, IndexError, KeyError):
                pass

        # Fallback: try meta description for bio
        if not result["bio"]:
            m2 = re.search(r'<meta\s+[^>]*name="description"\s+[^>]*content="([^"]+)"', html, re.IGNORECASE)
            if m2:
                result["bio"] = m2.group(1)[:300]

    except httpx.TimeoutException:
        result["status"] = "timeout"
        result["error"] = "timeout"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:100]
    return result


def signal_tier(category: str) -> int:
    cat = (category or "").strip().lower()
    if cat in HIGH_SIGNAL_CATEGORIES:
        return 1
    if cat in MEDIUM_SIGNAL_CATEGORIES:
        return 2
    return 3


def main():
    with open(MASTER_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    businesses_with_ig = [r for r in rows if r.get("instagram_handle", "").strip()]
    print(f"Businesses with IG handles: {len(businesses_with_ig)}")

    client = httpx.Client(
        timeout=20.0,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        },
    )

    results = []
    checked = 0
    alive = 0
    dead = 0

    for biz in businesses_with_ig:
        handle = biz["instagram_handle"].strip()
        name = biz.get("business_name", "")
        category = biz.get("category", "")
        tier = signal_tier(category)

        checked += 1
        print(f"  [{checked}/{len(businesses_with_ig)}] @{handle} ({name[:35]})", end="", flush=True)

        result = check_account(handle, client)
        result["business_name"] = name
        result["category"] = category
        result["signal_tier"] = tier
        result["area"] = biz.get("area", "")
        result["ig_verified"] = biz.get("ig_verified", "")
        result["status_raw"] = biz.get("operating_status", "")

        if result["alive"]:
            alive += 1
            print(f" -> ALIVE (posts:{result['post_count'] or '?'})")
        else:
            dead += 1
            print(f" -> {result['status']}")

        results.append(result)
        time.sleep(DELAY)

    client.close()

    # Sort: signal_tier first (1=highest), then post_count descending, then alive first
    def sort_key(r):
        post_count = r["post_count"] or 0
        return (r["signal_tier"], 0 if r["alive"] else 1, -post_count)

    results.sort(key=sort_key)

    # Write report
    report = {
        "summary": {
            "total_checked": checked,
            "alive": alive,
            "dead": dead,
            "alive_pct": round(alive / checked * 100, 1) if checked else 0,
        },
        "by_status": dict(Counter(r["status"] for r in results)),
        "by_signal_tier": {
            "tier_1_high": sum(1 for r in results if r["signal_tier"] == 1),
            "tier_2_medium": sum(1 for r in results if r["signal_tier"] == 2),
            "tier_3_low": sum(1 for r in results if r["signal_tier"] == 3),
        },
        "results": results,
    }

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport: {OUTPUT_REPORT}")

    # Write CSV for easy browsing
    fieldnames = [
        "signal_tier", "business_name", "category", "area",
        "handle", "alive", "status", "post_count", "bio", "error",
        "ig_verified", "status_raw",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(results)
    print(f"CSV: {OUTPUT_CSV}")

    # Print top candidates
    print("\n=== TOP CANDIDATES FOR MONITORING ===")
    shown = 0
    for r in results:
        if r["alive"] and r["signal_tier"] == 1 and shown < 30:
            print(f"  [T1] @{r['handle']:30s} {r['business_name'][:30]:30s} posts:{r['post_count'] or '?'}")
            shown += 1

    print(f"\nAlive tier-2 candidates:")
    shown = 0
    for r in results:
        if r["alive"] and r["signal_tier"] == 2 and shown < 20:
            print(f"  [T2] @{r['handle']:30s} {r['business_name'][:30]:30s} posts:{r['post_count'] or '?'}")
            shown += 1


if __name__ == "__main__":
    main()
