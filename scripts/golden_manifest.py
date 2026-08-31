"""Generate and verify the golden manifest of the built release tree.

The manifest pins a SHA-256 for every file the build emits. It is what makes a
structural refactor provable: rebuild, compare, and any unintended change to any
of ~1,500 output files shows up by name.

Two properties make the manifest portable between a Windows workstation and the
Linux CI runner:

* the build date is pinned via PARADISIO_BUILD_DATE, so the date stamped into
  index.html does not drift between days; and
* text files are hashed with line endings normalised to LF, because Python's
  text-mode writes emit CRLF on Windows and LF elsewhere. That is a platform
  artifact, not a content change, and `verify_release.py` already normalises the
  same way for vendored assets.

Usage:
    python scripts/golden_manifest.py write    # capture the current build
    python scripts/golden_manifest.py check    # compare a fresh build to it
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO / "tests" / "golden" / "manifest.sha256"
FIXTURE_DIR = REPO / "tests" / "golden" / "pages"

# The date pinned for every golden build. Changing this invalidates the manifest.
GOLDEN_DATE = "2026-08-01"

# Extensions hashed with normalised line endings.
TEXT_SUFFIXES = {".html", ".js", ".css", ".xml", ".txt", ".json", ".md", ""}

# Pages chosen to cover the shapes that actually vary in the renderer, so a
# failure points at a behaviour rather than at an arbitrary page.
FIXTURES = {
    "beraca-puerto-viejo": "closed business — no contact actions",
    "beach-hut-puerto-viejo": "needs_verification status",
    "boca-chica-bar-restaurante-y-piscina-cahuita-lim-n-costa-rica-cahuita": "no Google Maps CID",
    "7-ice-creams-puerto-viejo": "verified weekly hours, collapsed disclosure",
    "3-bamboo-ecolodge-cahuita-lim-n-costa-rica-cahuita": "Details disclosure collapsed",
    "adobe-easycar-rent-a-car-puerto-viejo": "explicit WhatsApp route",
    "asante-bistro-caf-cahuita-lim-n-costa-rica-cahuita": "unicode and long name",
    "caribbean-guard": "community partner page",
}


def file_digest(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        # Hash decoded pixels, not encoded bytes. PNG encoders differ between
        # Pillow versions (compression level, filter choice), so byte hashing
        # would fail across environments for images that are visually identical.
        # Pixel hashing still catches any real change to a QR code.
        from PIL import Image

        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            payload = f"{rgba.width}x{rgba.height}:".encode() + rgba.tobytes()
        return hashlib.sha256(payload).hexdigest()
    data = path.read_bytes()
    if suffix in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            out[rel] = file_digest(path)
    return out


def build_into(target: Path) -> None:
    env = dict(os.environ)
    env["PARADISIO_OUTPUT_DIR"] = str(target)
    env["PARADISIO_BUILD_DATE"] = GOLDEN_DATE
    result = subprocess.run(
        [sys.executable, str(REPO / "paradisio_app" / "build.py")],
        env=env, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"build failed:\n{result.stdout}\n{result.stderr}")


def render_manifest(snap: dict[str, str]) -> str:
    lines = [
        "# Golden manifest — SHA-256 per emitted file.",
        f"# build date pinned: {GOLDEN_DATE}",
        "# text files hashed with CRLF normalised to LF (platform independence).",
        f"# files: {len(snap)}",
        "",
    ]
    lines += [f"{digest}  {rel}" for rel, digest in sorted(snap.items())]
    return "\n".join(lines) + "\n"


def parse_manifest(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, rel = line.partition("  ")
        out[rel] = digest
    return out


def compare(expected: dict[str, str], actual: dict[str, str]) -> list[str]:
    problems = []
    for rel in sorted(set(expected) - set(actual)):
        problems.append(f"MISSING from build: {rel}")
    for rel in sorted(set(actual) - set(expected)):
        problems.append(f"UNEXPECTED in build: {rel}")
    for rel in sorted(set(expected) & set(actual)):
        if expected[rel] != actual[rel]:
            problems.append(f"CHANGED: {rel}")
    return problems


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "release"
        build_into(target)
        snap = snapshot(target)

        if mode == "write":
            MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
            MANIFEST_PATH.write_text(render_manifest(snap), encoding="utf-8", newline="\n")
            FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
            for slug in FIXTURES:
                src = target / "businesses" / f"{slug}.html"
                if not src.exists():
                    print(f"  WARNING fixture missing from build: {slug}")
                    continue
                body = src.read_bytes().replace(b"\r\n", b"\n")
                (FIXTURE_DIR / f"{slug}.html").write_bytes(body)
            print(f"wrote manifest: {len(snap)} files")
            print(f"wrote {len(list(FIXTURE_DIR.glob('*.html')))} page fixtures")
            return 0

        if not MANIFEST_PATH.exists():
            print("no manifest yet; run: python scripts/golden_manifest.py write")
            return 1
        expected = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        problems = compare(expected, snap)
        if problems:
            print(f"GOLDEN MISMATCH — {len(problems)} difference(s):")
            for p in problems[:40]:
                print("   " + p)
            if len(problems) > 40:
                print(f"   ... and {len(problems) - 40} more")
            return 1
        print(f"golden output OK — {len(snap)} files match")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
