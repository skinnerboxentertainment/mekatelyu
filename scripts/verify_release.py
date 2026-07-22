"""Verify the generated reduced Paradisio release artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path


FORBIDDEN_TEXT = (
    "admin.html",
    "claim.html",
    "classifieds/",
    "dashboard.html",
    "formsubmit",
    "goatcounter",
    "invoices/",
    "modes.js",
    "paradisio@example.com",
    "premium.html",
    "unpkg.com",
    "+506 8888 8888",
)
ALLOWED_ROOT_FILES = {".nojekyll", "404.html", "index.html", "robots.txt", "sitemap.xml"}
ALLOWED_ROOT_DIRS = {"businesses", "invest", "qr", "static"}


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    return struct.unpack(">II", header[16:24])


def verify(root: Path, expected_businesses: int) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"release root does not exist: {root}"]

    if root.parent.name == "release":
        deployment_entries = {path.name for path in root.parent.iterdir()}
        expected_entries = {".nojekyll", "404.html", "index.html", "paradisio_app", "robots.txt"}
        if deployment_entries != expected_entries:
            errors.append(
                f"unexpected deployment-root entries: expected={sorted(expected_entries)} "
                f"actual={sorted(deployment_entries)}"
            )
        wrapper = (root.parent / "index.html").read_text(encoding="utf-8")
        if "url=paradisio_app/" not in wrapper:
            errors.append("deployment root does not preserve the /paradisio_app/ public URL")

    root_entries = {path.name for path in root.iterdir()}
    unexpected = root_entries - ALLOWED_ROOT_FILES - ALLOWED_ROOT_DIRS
    if unexpected:
        errors.append(f"unexpected release-root entries: {sorted(unexpected)}")

    vendor_root = root / "static" / "vendor"
    manifest_path = vendor_root / "manifest.json"
    if not manifest_path.exists():
        errors.append("missing vendored dependency manifest")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for relative, expected_hash in manifest.get("files", {}).items():
            dependency = vendor_root / relative
            if not dependency.exists():
                errors.append(f"missing vendored dependency: {relative}")
                continue
            dependency_bytes = dependency.read_bytes()
            if dependency.suffix in {".css", ".js"}:
                dependency_bytes = dependency_bytes.replace(b"\r\n", b"\n")
            actual_hash = hashlib.sha256(dependency_bytes).hexdigest()
            if actual_hash != expected_hash:
                errors.append(f"vendored dependency hash mismatch: {relative}")

    business_pages = sorted((root / "businesses").glob("*.html"))
    qr_images = sorted((root / "qr").glob("*.png"))
    business_slugs = {path.stem for path in business_pages}
    qr_slugs = {path.stem for path in qr_images}
    if len(business_pages) != expected_businesses:
        errors.append(f"expected {expected_businesses} business pages, found {len(business_pages)}")
    if business_slugs != qr_slugs:
        errors.append(
            f"QR/profile mismatch: missing={sorted(business_slugs - qr_slugs)[:10]} "
            f"orphan={sorted(qr_slugs - business_slugs)[:10]}"
        )

    for path in qr_images:
        try:
            dimensions = png_size(path)
        except (OSError, ValueError) as exc:
            errors.append(f"invalid QR image {path.name}: {exc}")
            continue
        if dimensions != (300, 300):
            errors.append(f"unexpected QR dimensions for {path.name}: {dimensions}")

    html_files = [root / "index.html", *business_pages]
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in FORBIDDEN_TEXT:
            if marker.lower() in lowered:
                errors.append(f"forbidden marker {marker!r} in {path.relative_to(root)}")
        if 'rel="canonical"' not in text:
            errors.append(f"missing canonical: {path.relative_to(root)}")
        if 'property="og:' not in text:
            errors.append(f"missing Open Graph metadata: {path.relative_to(root)}")
        if 'http-equiv="Content-Security-Policy"' not in text:
            errors.append(f"missing Content Security Policy: {path.relative_to(root)}")
        if re.search(r"<script(?![^>]+src=)[^>]*>", text, flags=re.I):
            errors.append(f"inline script present: {path.relative_to(root)}")
        if path.parent.name == "businesses" and f'../qr/{path.stem}.png' not in text:
            errors.append(f"missing profile QR reference: {path.name}")

        for url in re.findall(r"(?:href|src)=[\"']([^\"']+)", text, flags=re.I):
            if url.startswith(("https://", "tel:", "#", "data:")):
                continue
            if url.startswith("http://"):
                errors.append(f"insecure external URL in {path.relative_to(root)}: {url}")
                continue
            local = (path.parent / url.split("#", 1)[0].split("?", 1)[0]).resolve()
            if not local.exists():
                errors.append(f"broken internal reference in {path.relative_to(root)}: {url}")

        for number in re.findall(r"https://wa\.me/(\d+)", text):
            if not re.fullmatch(r"\d{10,15}", number):
                errors.append(f"invalid WhatsApp destination in {path.relative_to(root)}: {number}")
        for number in re.findall(r"tel:\+?(\d+)", text):
            if not re.fullmatch(r"\d{10,15}", number):
                errors.append(f"invalid telephone destination in {path.relative_to(root)}: {number}")

    index_size = (root / "index.html").stat().st_size
    if index_size > 100_000:
        errors.append(f"index.html exceeds 100 KB budget: {index_size} bytes")
    data_size = (root / "static" / "directory-data.js").stat().st_size
    if data_size > 700_000:
        errors.append(f"directory-data.js exceeds 700 KB budget: {data_size} bytes")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("release"))
    parser.add_argument("--expected-businesses", type=int, default=737)
    args = parser.parse_args()

    errors = verify(args.root.resolve(), args.expected_businesses)
    if errors:
        print(f"FAIL: {len(errors)} release verification error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: reduced release verified at {args.root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
