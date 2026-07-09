# Check what's actually encoded in the QR codes
from generate_qr import get_business_url, BASE_URL
print(f"BASE_URL = {repr(BASE_URL)}")
print(f"Example URL: {get_business_url('black-bamboo-puerto-viejo')}")

# Check a sample QR redirect page
with open('../docs/paradisio_app/qr/black-bamboo-puerto-viejo.html') as f:
    for line in f:
        if 'url=' in line:
            print(f"Redirect page URL: {line.split('url=')[1].split('\"')[0]}")
            break

# The QR image encodes the URL too. Without pyzbar, we read what the generator encoded.
# The generator passes `url` to qrcode.make(data=url)
# url = get_business_url(slug) = "../businesses/{slug}.html" (relative, no BASE_URL)
print()
print("QR codes currently encode RELATIVE paths: ../businesses/{slug}.html")
print("This works when:")
print("  - Scanned from a file:// context (same filesystem)")
print("  - Scanned from the deployed site (they resolve relative to the QR page URL)")
print()
print("To make them PRODUCTION-READY, set PARADISIO_BASE_URL env var and regenerate.")
print("Example:")
print("  $env:PARADISIO_BASE_URL='https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app'")
print("  python paradisio_app/generate_qr.py")
