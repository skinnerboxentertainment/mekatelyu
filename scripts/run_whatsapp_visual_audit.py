"""Run the visual WhatsApp audit in a dedicated local Chromium instance.

One public wa.me target is rendered at a time. The runner never clicks, types,
sends a message, enters WhatsApp Web, or modifies directory source data.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

try:
    from .autovisual_whatsapp_checkifier import (
        DEFAULT_WORKSPACE, ROOT, attach_screenshot, read_ledger, validate_attempt, write_review_markdown,
    )
except ImportError:  # Direct script execution.
    from autovisual_whatsapp_checkifier import (
        DEFAULT_WORKSPACE, ROOT, attach_screenshot, read_ledger, validate_attempt, write_review_markdown,
    )


STOP_WORDS = {"puerto", "viejo", "playa", "costa", "rica", "limon", "de", "la", "the", "and"}


def normalized_name(value: str) -> str:
    value = unicodedata.normalize("NFD", value)
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def compare_names(expected: str, displayed: str) -> tuple[str, float]:
    expected_norm, displayed_norm = normalized_name(expected), normalized_name(displayed)
    if len(displayed_norm) >= 4 and (displayed_norm in expected_norm or expected_norm in displayed_norm):
        return "match", 0.95
    expected_tokens = {token for token in expected_norm.split() if len(token) > 2 and token not in STOP_WORDS}
    displayed_tokens = {token for token in displayed_norm.split() if len(token) > 2 and token not in STOP_WORDS}
    union = expected_tokens | displayed_tokens
    similarity = len(expected_tokens & displayed_tokens) / len(union) if union else 0
    return ("probable_match", 0.75) if similarity >= 0.5 else ("mismatch", 0.8)


def classify(item: dict, headings: list[str]) -> dict:
    named = [text.strip() for text in headings if text.strip() and not text.startswith("Chat on WhatsApp with")]
    if named:
        result, confidence = compare_names(item["business_name"], named[0])
        return {
            "render_state": "business_target_visible", "identity_result": result,
            "display_name": named[0], "confidence": confidence,
            "evidence_summary": f"WhatsApp rendered the visible profile identity {named[0]}.",
        }
    if any(text.startswith("Chat on WhatsApp with") for text in headings):
        return {
            "render_state": "target_visible", "identity_result": "unclear", "display_name": "",
            "confidence": 0.25,
            "evidence_summary": "WhatsApp rendered only the formatted telephone number; no profile identity was visible.",
        }
    return {
        "render_state": "unexpected_page", "identity_result": "unclear", "display_name": "",
        "confidence": 0.1, "evidence_summary": "WhatsApp did not render an allowlisted target state.",
    }


def append_entry(workspace: Path, queue: list[dict], payload: dict) -> dict:
    entry = attach_screenshot(validate_attempt(payload, queue), workspace, payload["screenshot_path"])
    with (workspace / "ledger.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def write_progress(workspace: Path, queue_name: str, progress: dict) -> None:
    path = workspace / f"{queue_name}-progress.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


async def capture(page, item: dict, screenshot: Path) -> tuple[list[str], str]:
    await page.goto(item["route"], wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(1_000)
    headings = [text.strip() for text in await page.locator("h2, h3").all_inner_texts()]
    title = await page.title()
    await page.screenshot(path=str(screenshot), type="jpeg", quality=85, full_page=False, timeout=45_000)
    return headings, title


async def run(args) -> int:
    workspace = args.workspace.resolve()
    queue = json.loads((workspace / "queues" / f"{args.queue}.json").read_text(encoding="utf-8"))
    completed = {
        entry["record_id"] for entry in read_ledger(workspace / "ledger.jsonl")
        if entry.get("screenshot_sha256")
    }
    all_pending = [item for item in queue if item["record_id"] not in completed]
    pending = all_pending
    if args.limit:
        pending = pending[:args.limit]
    progress = {
        "queue": args.queue, "total": len(queue), "already_complete": len(queue) - len(all_pending),
        "pending_at_start": len(pending), "captured": 0, "errors": 0, "messages_sent": 0,
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    write_progress(workspace, args.queue, progress)
    errors_path = workspace / f"{args.queue}-errors.jsonl"

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1265, "height": 710}, locale="en-US")
        page = await context.new_page()
        for index, item in enumerate(pending, start=1):
            screenshot = workspace / "screenshots" / f"{item['record_id']}.jpg"
            last_error = None
            for attempt in range(2):
                try:
                    headings, title = await capture(page, item, screenshot)
                    payload = classify(item, headings)
                    payload.update({
                        "record_id": item["record_id"], "route": item["route"],
                        "screenshot_path": f"screenshots/{screenshot.name}",
                        "evidence_summary": payload["evidence_summary"] + f" Page title: {title}.",
                    })
                    append_entry(workspace, queue, payload)
                    progress["captured"] += 1
                    last_error = None
                    break
                except Exception as exc:  # Browser failures are evidence failures, never business results.
                    last_error = str(exc)
                    if attempt == 0:
                        await asyncio.sleep(args.retry_delay)
                        await page.close()
                        page = await context.new_page()
            if last_error:
                progress["errors"] += 1
                with errors_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps({"record_id": item["record_id"], "route": item["route"], "error": last_error}) + "\n")
            progress["processed"] = index
            progress["last_record_id"] = item["record_id"]
            progress["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            write_progress(workspace, args.queue, progress)
            if index < len(pending):
                await asyncio.sleep(random.uniform(args.delay, args.delay + 2))
        await browser.close()

    progress["completed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_progress(workspace, args.queue, progress)
    write_review_markdown(workspace)
    print(json.dumps(progress, indent=2))
    return 1 if progress["errors"] else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", choices=("preservation", "candidates"), required=True)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--delay", type=float, default=8.0)
    parser.add_argument("--retry-delay", type=float, default=60.0)
    parser.add_argument("--limit", type=int, default=0, help="Process at most this many pending records; 0 means all")
    args = parser.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
