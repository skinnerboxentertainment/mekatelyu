"""Prepare, capture, and summarize paired signed/unsigned Google Maps controls."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
RAW = ROOT / "docs" / "paradisio_app" / "data" / "maps_enrich_v2.json"
WORKSPACE = ROOT / "audit" / "maps-auth-comparison"
SAMPLE = WORKSPACE / "sample.json"


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def prepare() -> int:
    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        master = list(csv.DictReader(handle))
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    raw_by_cid = {str(item.get("cid", "")): item for item in raw if item.get("cid") and item.get("full_text")}
    candidates = defaultdict(list)
    for row in master:
        cid = row.get("google_maps_cid", "").strip()
        capture = raw_by_cid.get(cid)
        if not capture:
            continue
        candidates[row["category"]].append((row, capture))
    sample = []
    for category in sorted(candidates):
        ordered = sorted(candidates[category], key=lambda pair: (
            abs(int(pair[1].get("text_length", 0)) - 4000), pair[0]["business_name"].casefold()
        ))
        row, capture = ordered[0]
        sample.append({
            "business_name": row["business_name"], "area": row["area"], "category": category,
            "cid": row["google_maps_cid"], "url": f"https://www.google.com/maps?cid={row['google_maps_cid']}&hl=en",
            "prior_text_length": capture.get("text_length", 0),
            "sample_reason": "representative positive CID near 4,000 captured characters",
        })
    if len(sample) != 10:
        raise SystemExit(f"expected one positive CID for each of 10 categories, found {len(sample)}")
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    SAMPLE.write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: prepared {len(sample)} positive CID controls across {len(candidates)} categories")
    for item in sample:
        print(f"- {item['category']}: {item['business_name']} ({item['cid']})")
    return 0


def signals(item: dict, text: str, title: str, url: str) -> dict:
    lower = text.casefold()
    name_tokens = [token for token in normalized(item["business_name"]).split() if len(token) >= 4][:3]
    return {
        "identity_visible": bool(name_tokens) and sum(token in normalized(text) for token in name_tokens) >= min(2, len(name_tokens)),
        "nontrivial_text": len(text) >= 1000,
        "category_signal": any(term in lower for term in (
            "hotel", "hostel", "restaurant", "rental", "wellness", "massage", "transport",
            "tour", "shop", "store", "real estate", "servicio", "alojamiento", "restaurante",
        )),
        "address_signal": any(term in lower for term in ("address", "dirección", "puerto viejo", "limón", "cocles")),
        "hours_signal": any(term in lower for term in ("hours", "open", "closed", "horario", "abierto", "cerrado")),
        "phone_signal": bool(re.search(r"(?:\+?506[\s-]?)?\d{4}[\s-]?\d{4}", text)),
        "website_signal": any(term in lower for term in ("website", "sitio web")),
        "rating_signal": bool(re.search(r"\b[1-5][.,]\d\b", text)) or "reviews" in lower or "opiniones" in lower,
        "photo_signal": "photos" in lower or "fotos" in lower,
        "no_wall_or_error": not any(term in lower for term in (
            "before you continue", "sign in to continue", "inicia sesión para continuar", "captcha", "unusual traffic"
        )) and "consent.google" not in url,
    }


async def capture(mode: str, profile: Path | None, delay: float) -> int:
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    output = WORKSPACE / mode
    shots = output / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    results = []
    async with async_playwright() as playwright:
        if mode == "signed":
            if profile is None:
                raise SystemExit("signed capture requires --profile")
            context = await playwright.chromium.launch_persistent_context(
                str(profile), headless=True, viewport={"width": 1440, "height": 1000}, locale="en-US"
            )
            browser = None
        else:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1440, "height": 1000}, locale="en-US")
        page = context.pages[0] if context.pages else await context.new_page()
        for index, item in enumerate(sample, 1):
            error = ""
            try:
                await page.goto(item["url"], wait_until="domcontentloaded", timeout=60_000)
                await page.wait_for_timeout(8_000)
                text = await page.locator("body").inner_text(timeout=15_000)
                title = await page.title()
                final_url = page.url
            except Exception as exc:  # Evidence capture must continue and record the failure.
                error = f"{type(exc).__name__}: {exc}"
                text = ""; title = ""; final_url = page.url
            screenshot = shots / f"{index:02d}-{item['cid']}.jpg"
            await page.screenshot(path=str(screenshot), type="jpeg", quality=85, full_page=False)
            digest = hashlib.sha256(screenshot.read_bytes()).hexdigest()
            result = {**item, "mode": mode, "captured_at": datetime.now(timezone.utc).isoformat(),
                      "title": title, "final_url": final_url, "visible_text_length": len(text),
                      "visible_text": text, "signals": signals(item, text, title, final_url),
                      "signal_score": sum(signals(item, text, title, final_url).values()),
                      "screenshot": str(screenshot.relative_to(WORKSPACE)).replace("\\", "/"),
                      "screenshot_sha256": digest, "error": error}
            results.append(result)
            print(f"[{mode} {index}/10] {item['business_name']}: score={result['signal_score']} text={len(text)} error={bool(error)}")
            if index < len(sample):
                await page.wait_for_timeout(int(delay * 1000))
        (output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        await context.close()
        if browser:
            await browser.close()
    return 0


def summarize() -> int:
    unsigned = json.loads((WORKSPACE / "unsigned" / "results.json").read_text(encoding="utf-8"))
    signed = json.loads((WORKSPACE / "signed" / "results.json").read_text(encoding="utf-8"))
    by_cid = {item["cid"]: item for item in signed}
    rows = []
    for before in unsigned:
        after = by_cid[before["cid"]]
        rows.append({
            "business_name": before["business_name"], "category": before["category"], "cid": before["cid"],
            "unsigned_score": before["signal_score"], "signed_score": after["signal_score"],
            "score_delta": after["signal_score"] - before["signal_score"],
            "unsigned_text_length": before["visible_text_length"], "signed_text_length": after["visible_text_length"],
            "text_delta": after["visible_text_length"] - before["visible_text_length"],
            "unsigned_error": before["error"], "signed_error": after["error"],
        })
    with (WORKSPACE / "comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    wins = sum(row["score_delta"] > 0 for row in rows)
    losses = sum(row["score_delta"] < 0 for row in rows)
    report = ["# Google Maps Authentication Quality Comparison", "",
              f"- Signed score wins: {wins}/10", f"- Ties: {10-wins-losses}/10", f"- Losses: {losses}/10",
              f"- Unsigned total score: {sum(r['unsigned_score'] for r in rows)}/100",
              f"- Signed total score: {sum(r['signed_score'] for r in rows)}/100", "",
              "| Business | Category | Unsigned | Signed | Δ | Unsigned text | Signed text |", "|---|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        report.append(f"| {row['business_name'].replace('|','/')} | {row['category']} | {row['unsigned_score']} | {row['signed_score']} | {row['score_delta']:+d} | {row['unsigned_text_length']} | {row['signed_text_length']} |")
    (WORKSPACE / "REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PASS: signed wins={wins}, ties={10-wins-losses}, losses={losses}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    cap = sub.add_parser("capture"); cap.add_argument("--mode", choices=("unsigned", "signed"), required=True)
    cap.add_argument("--profile", type=Path); cap.add_argument("--delay", type=float, default=8.0)
    sub.add_parser("summarize")
    args = parser.parse_args()
    if args.command == "prepare": return prepare()
    if args.command == "capture": return asyncio.run(capture(args.mode, args.profile, args.delay))
    return summarize()


if __name__ == "__main__":
    raise SystemExit(main())
