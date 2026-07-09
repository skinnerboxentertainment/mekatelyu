"""
Generate print-ready QR codes for every Paradisio business listing.

Output structure:
  docs/paradisio_app/qr/
    index.html              — QR gallery page for batch printing
    {slug}.png              — QR code image (300x300, 300 DPI)
    {slug}.html             — Redirect/landing page (QR scans go here)
"""

import json
import os
import sys
from pathlib import Path

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
except ImportError:
    print("ERROR: qrcode not installed. Run: pip install qrcode[pil]")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "docs" / "paradisio_app"
BUSINESSES_JSON = APP_DIR / "data" / "businesses.json"
QR_DIR = APP_DIR / "qr"

# Production GitHub Pages URL. QR codes encode absolute URLs so phone scanners work.
# Override with PARADISIO_BASE_URL env var for custom domains or local testing.
DEFAULT_BASE_URL = "https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app"
BASE_URL = os.environ.get("PARADISIO_BASE_URL", DEFAULT_BASE_URL)

QR_SIZE = 300  # pixels at 300 DPI = 1 inch
FILL_COLOR = "#1a3a2a"
BACK_COLOR = "#ffffff"


def get_landing_url(slug):
    """Get the QR landing page URL (scans go through this for tracking)."""
    if BASE_URL:
        return f"{BASE_URL.rstrip('/')}/qr/{slug}.html"
    return f"../qr/{slug}.html"


def get_business_url(slug):
    """Get the direct business page URL."""
    if BASE_URL:
        return f"{BASE_URL.rstrip('/')}/businesses/{slug}.html"
    return f"../businesses/{slug}.html"


def generate_qr(data, path):
    """Generate a QR code PNG image."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=FILL_COLOR, back_color=BACK_COLOR)
    img = img.resize((QR_SIZE, QR_SIZE), Image.NEAREST)
    img.save(path, "PNG", dpi=(300, 300))
    return path


def generate_redirect_page(slug, business_name, area):
    """Generate a minimal landing page for QR scans (with future tracking hook)."""
    biz_url = get_business_url(slug)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{business_name} — Paradisio</title>
<meta http-equiv="refresh" content="0; url={biz_url}">
<link rel="canonical" href="{biz_url}">
</head>
<body>
<p><a href="{biz_url}">Open {business_name} on Paradisio &rarr;</a></p>
</body>
</html>"""


def generate_index_html(qr_codes):
    """Generate a QR gallery page for batch printing."""
    rows = []
    for slug, name, area, qr_path in qr_codes:
        qr_rel = qr_path.name
        biz_url = get_business_url(slug)
        rows.append(f"""<div class="qr-card">
<img src="{qr_rel}" alt="QR for {name}" width="200" height="200" loading="lazy">
<div class="qr-label">{name}</div>
<div class="qr-meta">{area}</div>
<a href="{biz_url}" class="qr-link">View page &rarr;</a>
</div>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Paradisio QR Codes — Print Ready</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f3ef; padding: 20px; }}
h1 {{ font-size: 1.5rem; color: #1a3a2a; margin-bottom: 4px; }}
.screen-only {{ color: #666; font-size: 0.9rem; margin-bottom: 20px; }}
.qr-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }}
.qr-card {{ background: #fff; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
.qr-card img {{ display: block; margin: 0 auto 8px; border-radius: 4px; }}
.qr-label {{ font-size: 0.88rem; font-weight: 600; color: #1a1a1a; line-height: 1.3; word-break: break-word; }}
.qr-meta {{ font-size: 0.78rem; color: #888; margin-top: 2px; }}
.qr-link {{ display: inline-block; margin-top: 6px; font-size: 0.8rem; color: #1a3a2a; }}
@page {{ size: letter; margin: 0.35in; }}
@media print {{
  body {{ background: #fff; padding: 0; }}
  h1, .screen-only, .qr-link {{ display: none; }}
  .qr-grid {{ grid-template-columns: repeat(4, 1.55in); gap: 0.12in; justify-content: start; }}
  .qr-card {{ width: 1.55in; min-height: 1.9in; padding: 0.12in; border: 0.5pt dashed #bbb; border-radius: 0; break-inside: avoid; page-break-inside: avoid; box-shadow: none; }}
  .qr-card img {{ width: 1in; height: 1in; margin-bottom: 0.06in; }}
  .qr-label {{ font-size: 7pt; line-height: 1.15; }}
  .qr-meta {{ font-size: 6pt; }}
}}
</style>
</head>
<body>
<h1>Paradisio QR Codes</h1>
<p class="screen-only">{len(qr_codes)} businesses &middot; Print &amp; cut &middot; 1 inch QR &middot; 4 per row &middot; Letter paper</p>
<div class="qr-grid">
{"".join(rows)}
</div>
</body>
</html>"""


def main():
    if not BUSINESSES_JSON.exists():
        print(f"ERROR: businesses.json not found at {BUSINESSES_JSON}")
        print("Run paradisio_app/build.py first.")
        sys.exit(1)

    with open(BUSINESSES_JSON, encoding="utf-8") as f:
        businesses = json.load(f)

    QR_DIR.mkdir(parents=True, exist_ok=True)
    qr_codes = []
    generated = 0
    errors = 0

    for biz in businesses:
        slug = biz["slug"]
        name = biz["name"]
        area = biz["area"] or "Unknown"

        if not slug:
            errors += 1
            continue

        url = get_landing_url(slug)
        qr_path = QR_DIR / f"{slug}.png"
        html_path = QR_DIR / f"{slug}.html"

        try:
            generate_qr(url, qr_path)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(generate_redirect_page(slug, name, area))
            qr_codes.append((slug, name, area, qr_path))
            generated += 1

            if generated <= 3 or generated % 100 == 0:
                print(f"  [{generated}/{len(businesses)}] {name[:50]}")

        except Exception as e:
            print(f"  ERROR {slug}: {e}", file=sys.stderr)
            errors += 1

    # Generate index page
    index_html = generate_index_html(qr_codes)
    with open(QR_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"\nDone. {generated} QR codes generated in {QR_DIR}")
    print(f"  QR images:    {QR_DIR}/*.png")
    print(f"  QR landing:   {QR_DIR}/*.html")
    print(f"  Print page:   {QR_DIR}/index.html")
    if errors:
        print(f"  Errors:       {errors}")
    if not BASE_URL:
        print(f"\nNOTE: No BASE_URL set. QR codes use relative paths.")
        print(f"      Set PARADISIO_BASE_URL env var for production URLs.")
        print(f"      Example: PARADISIO_BASE_URL=https://example.com/paradisio_app")


if __name__ == "__main__":
    main()
