"""Local queue, ledger, and dashboard for visual WhatsApp route review.

This utility does not automate WhatsApp, send messages, or edit source data. It
prepares review queues and records observations made through a visible browser.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

try:
    from .audit_whatsapp_routes import normalize_whatsapp
except ImportError:  # Direct script execution.
    from audit_whatsapp_routes import normalize_whatsapp


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE = ROOT / "audit" / "whatsapp-checkifier"
TERMINAL_RESULTS = {"match", "probable_match", "mismatch", "unclear", "unavailable"}
RENDER_STATES = {
    "target_visible", "business_target_visible", "invalid_or_unavailable",
    "login_required", "native_app_handoff", "consent_or_interstitial",
    "rate_limited_or_challenged", "generic_send_page", "unexpected_page",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_id(name: str, area: str) -> str:
    return hashlib.sha256(f"{name.strip()}|{area.strip()}".encode()).hexdigest()[:16]


def safe_route(number: str) -> str:
    normalized = normalize_whatsapp(number)
    if normalized != number or not re.fullmatch(r"\+\d{10,15}", normalized):
        raise ValueError("number must already be normalized E.164")
    route = f"https://wa.me/{normalized[1:]}"
    parsed = urlsplit(route)
    if parsed.scheme != "https" or parsed.netloc != "wa.me" or parsed.query or parsed.fragment:
        raise ValueError("unsafe WhatsApp route")
    return route


def load_master(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def queue_item(row: dict[str, str], number: str, source_class: str) -> dict[str, object]:
    return {
        "record_id": record_id(row.get("business_name", ""), row.get("area", "")),
        "business_name": row.get("business_name", "").strip(),
        "area": row.get("area", "").strip(),
        "whatsapp_normalized": number,
        "route": safe_route(number),
        "phone": row.get("phone", "").strip(),
        "website": row.get("website", "").strip(),
        "source_url": row.get("url", "").strip(),
        "source_class": source_class,
        "operating_status": row.get("operating_status", "").strip(),
    }


def build_queues(master: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    preservation, candidates = [], []
    for row in master:
        explicit = normalize_whatsapp(row.get("whatsapp", ""))
        phone = normalize_whatsapp(row.get("normalized_phone", "") or row.get("phone", ""))
        if explicit:
            preservation.append(queue_item(row, explicit, "master_explicit"))
        elif phone:
            candidates.append(queue_item(row, phone, "phone_candidate"))
    return preservation, candidates


def select_pilot(preservation: list[dict]) -> list[dict]:
    unique = [item for item in preservation if sum(x["whatsapp_normalized"] == item["whatsapp_normalized"] for x in preservation) == 1]
    shared = [item for item in preservation if item not in unique]
    international = [item for item in unique if not str(item["whatsapp_normalized"]).startswith("+506")]
    selected = unique[:3]
    if shared:
        selected.append(shared[0])
    selected.append((international or unique[3:4] or preservation)[0])
    control = {
        "record_id": "control-50600000000", "business_name": "IMPOSSIBLE CONTROL",
        "area": "", "whatsapp_normalized": "+50600000000",
        "route": safe_route("+50600000000"), "phone": "", "website": "",
        "source_url": "", "source_class": "negative_control", "operating_status": "control",
    }
    selected.append(control)
    return selected[:6]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(master_path: Path, workspace: Path) -> dict[str, int]:
    preservation, candidates = build_queues(load_master(master_path))
    pilot = select_pilot(preservation)
    write_json(workspace / "queues" / "preservation.json", preservation)
    write_json(workspace / "queues" / "candidates.json", candidates)
    write_json(workspace / "queues" / "pilot.json", pilot)
    metadata = {
        "generated_at": utc_now(), "master": str(master_path),
        "preservation_count": len(preservation), "candidate_count": len(candidates),
        "pilot_count": len(pilot), "messages_sent": 0,
    }
    write_json(workspace / "metadata.json", metadata)
    (workspace / "screenshots").mkdir(parents=True, exist_ok=True)
    return metadata


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def validate_attempt(payload: dict, queue: list[dict]) -> dict:
    by_id = {item["record_id"]: item for item in queue}
    item = by_id.get(payload.get("record_id"))
    if not item:
        raise ValueError("record_id is not in the selected queue")
    if payload.get("route") != item["route"] or urlsplit(item["route"]).netloc != "wa.me":
        raise ValueError("route does not match the safe queue route")
    if payload.get("identity_result") not in TERMINAL_RESULTS:
        raise ValueError("invalid identity_result")
    if payload.get("render_state") not in RENDER_STATES:
        raise ValueError("invalid render_state")
    if payload["identity_result"] in {"match", "probable_match"} and not str(payload.get("display_name", "")).strip():
        raise ValueError("a match requires a visible displayed identity")
    if payload["render_state"] in {"generic_send_page", "invalid_or_unavailable"} and payload["identity_result"] in {"match", "probable_match"}:
        raise ValueError("generic or unavailable pages cannot be classified as a match")
    confidence = float(payload.get("confidence", 0))
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if item["source_class"] == "negative_control" and payload["identity_result"] in {"match", "probable_match"}:
        raise ValueError("negative control cannot be classified as a match")
    return {
        "attempt_id": hashlib.sha256(f"{item['record_id']}|{utc_now()}".encode()).hexdigest()[:16],
        "record_id": item["record_id"], "business_name": item["business_name"],
        "route": item["route"], "source_class": item["source_class"],
        "started_at": payload.get("started_at") or utc_now(), "completed_at": utc_now(),
        "render_state": payload["render_state"], "display_name": str(payload.get("display_name", ""))[:200],
        "business_label": str(payload.get("business_label", ""))[:200],
        "visible_number": str(payload.get("visible_number", ""))[:40],
        "identity_result": payload["identity_result"], "confidence": confidence,
        "evidence_summary": str(payload.get("evidence_summary", ""))[:1000],
        "screenshot_path": str(payload.get("screenshot_path", ""))[:500],
        "review_state": "human_required" if payload["identity_result"] in {"probable_match", "mismatch", "unclear"} else "auto_complete",
        "messages_sent": 0, "tool_version": "0.2.0",
    }


def attach_screenshot(entry: dict, workspace: Path, screenshot_path: str) -> dict:
    relative = Path(screenshot_path)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("screenshots",):
        raise ValueError("screenshot must be inside the local screenshots directory")
    absolute = (workspace / relative).resolve()
    screenshots_root = (workspace / "screenshots").resolve()
    if absolute.parent != screenshots_root or absolute.suffix.lower() not in {".png", ".jpg", ".jpeg"} or not absolute.is_file():
        raise ValueError("a PNG or JPEG screenshot is required for every attempt")
    data = absolute.read_bytes()
    valid_png = absolute.suffix.lower() == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n")
    valid_jpeg = absolute.suffix.lower() in {".jpg", ".jpeg"} and data.startswith(b"\xff\xd8\xff")
    if not (valid_png or valid_jpeg):
        raise ValueError("screenshot content does not match its file extension")
    entry["screenshot_path"] = relative.as_posix()
    entry["screenshot_sha256"] = hashlib.sha256(data).hexdigest()
    entry["screenshot_bytes"] = len(data)
    return entry


def review_html(workspace: Path) -> bytes:
    cards = []
    for entry in reversed(read_ledger(workspace / "ledger.jsonl")):
        path = entry.get("screenshot_path", "")
        evidence = f'<img loading="lazy" src="/evidence/{html.escape(Path(path).name)}" alt="Evidence for {html.escape(entry["business_name"])}">' if path else '<p class="missing">No screenshot attached</p>'
        cards.append(f'''<article><h2>{html.escape(entry["business_name"])}</h2>
<p><strong>{html.escape(entry["identity_result"])}</strong> · {html.escape(entry["display_name"] or "No displayed identity")} · confidence {entry["confidence"]}</p>
{evidence}<p>{html.escape(entry["evidence_summary"])}</p>
<small>{html.escape(entry["completed_at"])} · {html.escape(entry.get("screenshot_sha256", "no hash"))}</small></article>''')
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WhatsApp visual evidence review</title><style>body{{max-width:1100px;margin:auto;padding:24px;font:16px/1.45 system-ui;background:#f4f7f5;color:#17332d}}article{{background:white;border:1px solid #d7e2de;border-radius:14px;padding:18px;margin:16px 0}}img{{display:block;max-width:100%;max-height:650px;margin:12px auto;border:1px solid #d7e2de}}small{{overflow-wrap:anywhere;color:#60716c}}.missing{{color:#a33}}</style>
<h1>WhatsApp visual evidence review</h1><p>Local-only evidence. Newest attempts appear first.</p>{''.join(cards)}</html>'''
    return page.encode("utf-8")


class ReviewHandler(BaseHTTPRequestHandler):
    workspace: Path
    dashboard: Path

    def _json(self, status: int, body: object) -> None:
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            data = self.dashboard.read_bytes(); self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data); return
        if self.path == "/review":
            data = review_html(self.workspace); self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data); return
        if self.path.startswith("/evidence/"):
            name = Path(self.path.removeprefix("/evidence/")).name
            path = self.workspace / "screenshots" / name
            suffix = Path(name).suffix.lower()
            if suffix not in {".png", ".jpg", ".jpeg"} or not path.is_file(): return self._json(404, {"error": "not found"})
            data = path.read_bytes(); self.send_response(200); self.send_header("Content-Type", "image/png" if suffix == ".png" else "image/jpeg")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        if self.path.startswith("/api/queue"):
            queue_name = "pilot"
            if "?name=" in self.path: queue_name = self.path.split("?name=", 1)[1].split("&", 1)[0]
            if queue_name not in {"pilot", "preservation", "candidates"}: return self._json(400, {"error": "invalid queue"})
            queue = json.loads((self.workspace / "queues" / f"{queue_name}.json").read_text(encoding="utf-8"))
            ledger = read_ledger(self.workspace / "ledger.jsonl")
            return self._json(200, {"name": queue_name, "items": queue, "attempts": ledger})
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/attempt": return self._json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            queue_name = payload.pop("queue_name", "pilot")
            if queue_name not in {"pilot", "preservation", "candidates"}: raise ValueError("invalid queue")
            queue = json.loads((self.workspace / "queues" / f"{queue_name}.json").read_text(encoding="utf-8"))
            entry = validate_attempt(payload, queue)
            entry = attach_screenshot(entry, self.workspace, str(payload.get("screenshot_path", "")))
            with (self.workspace / "ledger.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self._json(201, entry)
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        print(f"dashboard: {format % args}")


def serve(workspace: Path, port: int) -> None:
    if not (workspace / "queues" / "pilot.json").exists():
        prepare(ROOT / "pv_master_unified.csv", workspace)
    handler = type("ConfiguredReviewHandler", (ReviewHandler,), {
        "workspace": workspace, "dashboard": ROOT / "tools" / "autovisualwhatsappcheckifier" / "dashboard.html"
    })
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"AutoVisualWhatsAppCheckifier: http://127.0.0.1:{port}")
    server.serve_forever()


def record_batch(workspace: Path, queue_name: str, input_path: Path) -> list[dict]:
    if queue_name not in {"pilot", "preservation", "candidates"}:
        raise ValueError("invalid queue")
    queue = json.loads((workspace / "queues" / f"{queue_name}.json").read_text(encoding="utf-8"))
    payloads = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payloads, list) or not payloads:
        raise ValueError("input must be a non-empty JSON array")
    entries = []
    for payload in payloads:
        entry = validate_attempt(payload, queue)
        entries.append(attach_screenshot(entry, workspace, str(payload.get("screenshot_path", ""))))
    with (workspace / "ledger.jsonl").open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    write_review_markdown(workspace)
    return entries


def write_review_markdown(workspace: Path) -> None:
    entries = [entry for entry in read_ledger(workspace / "ledger.jsonl") if entry.get("screenshot_sha256")]
    lines = ["# WhatsApp visual evidence review", "", "Local-only evidence; newest image-backed attempts appear first.", ""]
    for entry in reversed(entries):
        lines.extend([
            f"## {entry['business_name']}", "",
            f"- Result: `{entry['identity_result']}`",
            f"- Displayed identity: {entry['display_name'] or 'None; number-only page'}",
            f"- Confidence: {entry['confidence']}",
            f"- SHA-256: `{entry['screenshot_sha256']}`",
            f"- Evidence: {entry['evidence_summary']}", "",
            f"![{entry['business_name']}]({entry['screenshot_path']})", "",
        ])
    (workspace / "REVIEW.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare"); prep.add_argument("--master", type=Path, default=ROOT / "pv_master_unified.csv")
    prep.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    run = sub.add_parser("serve"); run.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    run.add_argument("--port", type=int, default=8771)
    record = sub.add_parser("record-batch"); record.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    record.add_argument("--queue", choices=("pilot", "preservation", "candidates"), required=True)
    record.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        print(json.dumps(prepare(args.master, args.workspace), indent=2)); return 0
    if args.command == "record-batch":
        print(json.dumps(record_batch(args.workspace, args.queue, args.input), ensure_ascii=False, indent=2)); return 0
    serve(args.workspace, args.port); return 0


if __name__ == "__main__":
    raise SystemExit(main())
