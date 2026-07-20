"""Discover missing Google Maps CIDs with resumable screenshot-backed evidence."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote, unquote

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "audit" / "semantic-taxonomy" / "evidence-poor-records.csv"
WORKSPACE = ROOT / "audit" / "maps-cid-discovery"
SAMPLE = WORKSPACE / "sample.json"
FULL_QUEUE = WORKSPACE / "queue-113.json"
CURRENT_QUEUE = WORKSPACE / "queue-current.json"
PROFILE = WORKSPACE / "signed-profile"
CHROME_PROFILE = WORKSPACE / "chrome-profile"
CHROME_EXECUTABLE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

SAMPLE_NAMES = (
    "Secret Garden - Cahuita, Limón, Costa Rica",
    "Blue Dreams Hotel",
    "Cabinas KiAMiMi",
    "Café Rico",
    "Casa Alegre",
    "We Do Laundry - Hone Creek, Limón, Costa Rica",
    "CHOCORART",
    "Refugio de animales Jaguar",
    "Douglas Ville guest house",
    "Habitat Vacation Rentals - Playa Cocles, Puerto Viejo, Limón, Costa Rica",
)


def fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char)).casefold()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def repair_mojibake(value: str) -> str:
    if "Ã" not in value and "Â" not in value:
        return value
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def clean_business_name(value: str) -> str:
    value = repair_mojibake(value)
    return re.split(
        r"\s+-\s+(?:Playa |Cahuita|Manzanillo|Puerto Viejo|Hone Creek|Sixaola|Gandoca|Punta Uva|Lim[oó]n|Costa Rica)",
        value,
        maxsplit=1,
    )[0].strip()


def similarity(expected: str, observed: str) -> float:
    a, b = fold(clean_business_name(expected)), fold(observed)
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    tokens_a, tokens_b = set(a.split()), set(b.split())
    overlap = len(tokens_a & tokens_b) / max(1, len(tokens_a))
    return round(max(ratio, overlap), 3)


def cid_from_value(value: str) -> str:
    decoded = unquote(value or "")
    patterns = (
        r"[?&]cid=(\d{6,25})",
        r"!1s0x[0-9a-f]+:0x([0-9a-f]+)",
        r"0x[0-9a-f]+:0x([0-9a-f]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, decoded, flags=re.IGNORECASE)
        if not match:
            continue
        token = match.group(1)
        return str(int(token, 16)) if re.search(r"[a-f]", token, flags=re.IGNORECASE) or "0x" in match.group(0) else token
    return ""


def prepare() -> int:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    by_name = {row["business_name"]: row for row in records}
    missing = [name for name in SAMPLE_NAMES if name not in by_name]
    if missing:
        raise SystemExit(f"sample names missing from 113-record source: {missing}")
    sample = []
    for name in SAMPLE_NAMES:
        row = by_name[name]
        query = f"{clean_business_name(name)} {repair_mojibake(row['area'])} Limón Costa Rica"
        sample.append({
            "business_name": name, "search_name": clean_business_name(name), "area": row["area"],
            "category": row["primary_category"], "query": query,
            "search_url": f"https://www.google.com/maps/search/?api=1&query={quote(query)}&hl=en",
        })
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    SAMPLE.write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: prepared 10 actual missing-CID searches")
    for item in sample:
        print(f"- {item['category']}: {item['business_name']} -> {item['query']}")
    return 0


def prepare_all() -> int:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    queue = []
    for row in records:
        name = row["business_name"]
        query = f"{clean_business_name(name)} {repair_mojibake(row['area'])} Limón Costa Rica"
        queue.append({
            "business_name": name, "search_name": clean_business_name(name), "area": row["area"],
            "category": row["primary_category"], "query": query,
            "search_url": f"https://www.google.com/maps/search/?api=1&query={quote(query)}&hl=en",
        })
    if len(queue) != 113:
        raise SystemExit(f"expected 113 missing-CID records, found {len(queue)}")
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    FULL_QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: prepared full missing-CID queue with {len(queue)} records")
    return 0


def prepare_current() -> int:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    queue = []
    for row in records:
        name = row["business_name"]
        query = f"{clean_business_name(name)} {repair_mojibake(row['area'])} Limón Costa Rica"
        queue.append({
            "business_name": name, "search_name": clean_business_name(name), "area": row["area"],
            "category": row["primary_category"], "query": query,
            "search_url": f"https://www.google.com/maps/search/?api=1&query={quote(query)}&hl=en",
        })
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    CURRENT_QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: prepared current evidence-poor queue with {len(queue)} records")
    return 0


async def login(profile: Path) -> int:
    profile.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            str(profile), headless=False, viewport={"width": 1280, "height": 900}, locale="en-US"
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://accounts.google.com/", wait_until="domcontentloaded", timeout=60_000)
        print("SIGN-IN WINDOW READY: authenticate directly, verify Google Maps opens, then close the browser window.", flush=True)
        while context.pages:
            await asyncio.sleep(1)
        return 0


async def extract_links(page) -> list[dict]:
    return await page.locator('a[href*="/maps/place/"]').evaluate_all("""
        els => els.slice(0, 20).map(el => ({
          href: el.href || '',
          label: el.getAttribute('aria-label') || el.textContent || '',
          text: (el.parentElement?.textContent || el.textContent || '').slice(0, 500)
        }))
    """)


async def capture(mode: str, profile: Path | None, delay: float, limit: int, headed: bool,
                  queue_path: Path, run_name: str) -> int:
    sample = json.loads(queue_path.read_text(encoding="utf-8"))
    if limit:
        sample = sample[:limit]
    output = WORKSPACE / run_name
    shots = output / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    results_path = output / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else []
    completed = {item["business_name"] for item in results}
    async with async_playwright() as playwright:
        browser = None
        if mode == "signed":
            if profile is None or not profile.exists():
                raise SystemExit("signed capture requires an initialized --profile")
            context = await playwright.chromium.launch_persistent_context(
                str(profile), executable_path=str(CHROME_EXECUTABLE), headless=not headed,
                viewport={"width": 1440, "height": 1000}, locale="en-US"
            )
        else:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1440, "height": 1000}, locale="en-US")
        page = context.pages[0] if context.pages else await context.new_page()
        for index, item in enumerate(sample, 1):
            if item["business_name"] in completed:
                print(f"[{run_name} {index}/{len(sample)}] SKIP {item['business_name']}", flush=True)
                continue
            error = ""; candidates = []; clicked = False
            try:
                await page.goto(item["search_url"], wait_until="domcontentloaded", timeout=60_000)
                await page.wait_for_timeout(8_000)
                candidates = await extract_links(page)
                for candidate in candidates:
                    candidate["similarity"] = similarity(item["search_name"], candidate["label"] or candidate["text"])
                    candidate["cid"] = cid_from_value(candidate["href"])
                candidates.sort(key=lambda candidate: candidate["similarity"], reverse=True)
                if "/maps/place/" not in page.url and candidates and candidates[0]["similarity"] >= 0.55:
                    best_href = candidates[0]["href"]
                    await page.goto(best_href, wait_until="domcontentloaded", timeout=60_000)
                    await page.wait_for_timeout(6_000)
                    clicked = True
                visible_text = await page.locator("body").inner_text(timeout=15_000)
                title = await page.title()
                headings = await page.locator("h1").all_inner_texts()
                observed_name = headings[0].strip() if headings else title.split(" - ")[0].strip()
                final_url = page.url
                html = await page.content()
                cid = cid_from_value(final_url) or cid_from_value(html)
                if not cid and candidates:
                    cid = next((candidate["cid"] for candidate in candidates if candidate["cid"]), "")
                match_score = similarity(item["search_name"], observed_name)
                wall = any(term in visible_text.casefold() for term in (
                    "before you continue", "sign in to continue", "unusual traffic", "captcha"
                )) or "consent.google" in final_url
                signed_in_visible = "sign in" not in visible_text.casefold()
                if cid and match_score >= 0.72 and not wall:
                    result_class = "exact"
                elif cid and match_score >= 0.5 and not wall:
                    result_class = "probable"
                elif candidates or cid:
                    result_class = "ambiguous"
                else:
                    result_class = "no_result"
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                visible_text = ""; title = ""; headings = []; observed_name = ""; final_url = page.url
                cid = ""; match_score = 0.0; wall = False; result_class = "error"
                signed_in_visible = False
            screenshot = shots / f"{index:02d}-{hashlib.sha256(item['business_name'].encode()).hexdigest()[:10]}.jpg"
            await page.screenshot(path=str(screenshot), type="jpeg", quality=85, full_page=False)
            result = {**item, "mode": mode, "captured_at": datetime.now(timezone.utc).isoformat(),
                      "classification": result_class, "resolved_cid": cid, "observed_name": observed_name,
                      "identity_similarity": match_score, "title": title, "final_url": final_url,
                      "visible_text_length": len(visible_text), "visible_text": visible_text,
                      "candidate_count": len(candidates), "candidates": candidates[:5], "followed_candidate": clicked,
                      "wall_or_challenge": wall, "signed_in_visible": signed_in_visible, "error": error,
                      "screenshot": str(screenshot.relative_to(WORKSPACE)).replace("\\", "/"),
                      "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest()}
            results.append(result)
            results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"[{run_name} {index}/{len(sample)}] {item['business_name']}: {result_class} cid={cid or '-'} sim={match_score:.2f} candidates={len(candidates)}", flush=True)
            if index < len(sample):
                await page.wait_for_timeout(int(delay * 1000))
        await context.close()
        if browser:
            await browser.close()
    return 0


def compare() -> int:
    unsigned = json.loads((WORKSPACE / "unsigned" / "results.json").read_text(encoding="utf-8"))
    signed = json.loads((WORKSPACE / "signed" / "results.json").read_text(encoding="utf-8"))
    signed_by_name = {item["business_name"]: item for item in signed}
    rows = []
    ranks = {"error": 0, "no_result": 1, "ambiguous": 2, "probable": 3, "exact": 4}
    for before in unsigned:
        after = signed_by_name[before["business_name"]]
        rows.append({
            "business_name": before["business_name"], "category": before["category"],
            "unsigned_class": before["classification"], "signed_class": after["classification"],
            "class_delta": ranks[after["classification"]] - ranks[before["classification"]],
            "unsigned_cid": before["resolved_cid"], "signed_cid": after["resolved_cid"],
            "same_cid": bool(before["resolved_cid"]) and before["resolved_cid"] == after["resolved_cid"],
            "unsigned_similarity": before["identity_similarity"], "signed_similarity": after["identity_similarity"],
            "unsigned_text_length": before["visible_text_length"], "signed_text_length": after["visible_text_length"],
            "unsigned_wall": before["wall_or_challenge"], "signed_wall": after["wall_or_challenge"],
        })
    with (WORKSPACE / "comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    signed_wins = sum(row["class_delta"] > 0 for row in rows)
    unsigned_wins = sum(row["class_delta"] < 0 for row in rows)
    report = ["# Missing-CID Discovery: Signed vs Unsigned", "",
              f"- Signed classification wins: {signed_wins}/10",
              f"- Ties: {10-signed_wins-unsigned_wins}/10", f"- Unsigned wins: {unsigned_wins}/10",
              f"- Unsigned exact/probable: {sum(r['unsigned_class'] in {'exact','probable'} for r in rows)}/10",
              f"- Signed exact/probable: {sum(r['signed_class'] in {'exact','probable'} for r in rows)}/10", "",
              "| Business | Unsigned | Signed | Unsigned CID | Signed CID | Same CID |", "|---|---|---|---|---|---|"]
    for row in rows:
        report.append(f"| {row['business_name'].replace('|','/')} | {row['unsigned_class']} | {row['signed_class']} | {row['unsigned_cid'] or '—'} | {row['signed_cid'] or '—'} | {row['same_cid']} |")
    (WORKSPACE / "COMPARISON.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PASS: signed wins={signed_wins}, ties={10-signed_wins-unsigned_wins}, unsigned wins={unsigned_wins}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("prepare-all")
    sub.add_parser("prepare-current")
    login_parser = sub.add_parser("login"); login_parser.add_argument("--profile", type=Path, default=PROFILE)
    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("--mode", choices=("unsigned", "signed"), required=True)
    capture_parser.add_argument("--profile", type=Path, default=CHROME_PROFILE)
    capture_parser.add_argument("--delay", type=float, default=8.0)
    capture_parser.add_argument("--limit", type=int, default=10)
    capture_parser.add_argument("--headed", action="store_true")
    capture_parser.add_argument("--queue", type=Path, default=SAMPLE)
    capture_parser.add_argument("--run-name", default="")
    sub.add_parser("compare")
    args = parser.parse_args()
    if args.command == "prepare": return prepare()
    if args.command == "prepare-all": return prepare_all()
    if args.command == "prepare-current": return prepare_current()
    if args.command == "login": return asyncio.run(login(args.profile))
    if args.command == "capture":
        run_name = args.run_name or args.mode
        return asyncio.run(capture(args.mode, args.profile, args.delay, args.limit, args.headed, args.queue, run_name))
    return compare()


if __name__ == "__main__":
    raise SystemExit(main())
