import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

from .schema import BusinessListing

PARSER_VERSION = "0.2"

# ----- Helpers -----

def _get_content_area(soup: BeautifulSoup) -> BeautifulSoup:
    """Scope parsing to the main content area by removing nav, footer, and sidebar."""
    body = soup.find("body") or soup
    # Only strip elements that are clearly outside the main content
    for tag in body.find_all(["nav", "footer", "header", "aside"]):
        tag.decompose()
    return body


def _clean_title(title: str) -> str:
    """Remove site suffix from page title to get business name."""
    for suffix in [
        " - Puerto Viejo de Talamanca, Limón, Costa Rica",
        " - Puerto Viejo de Talamanca, Limon, Costa Rica",
        " - Puerto Viejo and Area",
        " - Puerto Viejo, Talamanca, Limon, Costa Rica",
        " - Puerto Viejo, Talamanca, Limón, Costa Rica",
    ]:
        if title.endswith(suffix):
            title = title[: -len(suffix)]
            break
    return title.strip()


# ----- Parser -----

class ListingParser:
    def parse(self, url: str, html: str, http_status: int = 200) -> BusinessListing:
        warnings: list[str] = []
        soup = BeautifulSoup(html, "html.parser")
        content = _get_content_area(soup)

        listing = BusinessListing(
            url=url,
            http_status=http_status,
            retrieved_at=datetime.utcnow().isoformat(),
            parser_version=PARSER_VERSION,
        )

        # --- Business name from <title> (most reliable on this site) ---
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            cleaned = _clean_title(raw)
            if cleaned:
                listing.business_name = cleaned
            else:
                warnings.append(f"Title tag empty after cleaning: {raw}")
        else:
            warnings.append("Title tag not found")

        # --- Fallback: H1 text after logo ---
        if not listing.business_name:
            h1 = soup.find("h1")
            if h1:
                # Skip the logo image; get direct text nodes
                txt = "".join(
                    h1.find_all(string=True, recursive=False)
                ).strip()
                if txt:
                    listing.business_name = txt

        # --- Category from page breadcrumb ---
        cat = self._extract_category(soup)
        if cat:
            listing.category = cat

        # --- Area from breadcrumb ---
        area = self._extract_area(soup)
        if area:
            listing.area = area

        # --- Category/Area fallback from URL ---
        if not listing.category:
            warnings.append("Category not found")
        if not listing.area:
            fallback = self._area_from_url(url)
            if fallback:
                listing.area = fallback
                warnings.append(f"Area inferred from URL: {fallback}")

        # --- Phone ---
        phone = self._extract_phone(content)
        if phone:
            listing.phone = phone

        # --- Website ---
        website = self._extract_website(content)
        if website:
            listing.website = website

        # --- Google Maps CID ---
        cid = self._extract_google_maps_cid(content)
        if cid:
            listing.google_maps_cid = cid

        # --- Instagram ---
        instagram = self._extract_instagram(content)
        if instagram:
            listing.instagram_handle = instagram.get("handle")
            listing.instagram_url = instagram.get("url")

        # --- Facebook ---
        facebook = self._extract_facebook(content)
        if facebook:
            listing.facebook_url = facebook

        # --- Description ---
        desc = self._extract_description(content)
        if desc:
            listing.description = desc

        # --- Rating ---
        rating = self._extract_rating(content)
        if rating is not None:
            listing.rating = rating

        # --- Price range / room rate ---
        price = self._extract_price(content)
        if price:
            listing.price_range = price

        # --- Verified date ---
        verified = self._extract_verified_date(content)
        if verified:
            listing.verified_date = verified

        # --- Operating status ---
        status = self._extract_status(soup)
        if status:
            listing.operating_status = status

        # --- Alternate names ---
        alt = self._extract_alternate_names(content)
        if alt:
            listing.alternate_names = alt

        if warnings:
            listing.extraction_warnings = "; ".join(warnings)

        return listing

    # ---- Extraction helpers ----

    def _extract_breadcrumb_links(self, soup: BeautifulSoup) -> list[tuple[str, str]]:
        """Find breadcrumb links: <a> inside a <p> that contains '>'."""
        links = []
        for p in soup.find_all("p"):
            text = p.get_text()
            if ">" not in text:
                continue
            for a in p.find_all("a", href=True):
                href = a["href"]
                txt = a.get_text(strip=True)
                if href.startswith("/en/") or href.startswith("en/"):
                    links.append((href, txt))
        return links

    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract category from breadcrumb links."""
        crumbs = self._extract_breadcrumb_links(soup)
        for href, txt in crumbs:
            h = href.lower()
            if "/en/hotels/" in h or txt.lower() in ("hotels", "accommodations"):
                return "hotel"
            if "/en/hostels/" in h:
                return "hostel"
            if "/en/vacation-rentals/" in h:
                return "vacation_rental"
            if "/en/restaurants/" in h or "restaurant" in txt.lower():
                return "restaurant"
            if "/en/shopping/" in h:
                return "shopping"
            if "/en/services/" in h:
                return "services"
            if "/en/tour-companies/" in h or "tour" in txt.lower():
                return "tour_company"
            if "/en/real-estate/" in h:
                return "real_estate"
        return None

    def _extract_area(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract area from breadcrumb or page content."""
        known_areas = {
            "puerto-viejo": "Puerto Viejo",
            "playa-negra": "Playa Negra",
            "cocles": "Cocles",
            "playa-chiquita": "Playa Chiquita",
            "punta-uva": "Punta Uva",
            "manzanillo": "Manzanillo",
            "cahuita": "Cahuita",
            "hone-creek": "Hone Creek",
            "bribri": "Bribri",
            "gandoca": "Gandoca",
            "sixaola": "Sixaola",
        }
        crumbs = self._extract_breadcrumb_links(soup)
        for href, txt in crumbs:
            for slug, name in known_areas.items():
                if f"/en/{slug}/" in href and not txt.lower().startswith("en/"):
                    return name
        return None

    def _area_from_url(self, url: str) -> Optional[str]:
        path = urlparse(url).path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            slug = parts[1]
            return " ".join(word.capitalize() for word in slug.split("-"))
        return None

    def _extract_phone(self, content: BeautifulSoup) -> Optional[str]:
        """Phone number from page text."""
        text = content.get_text()

        # Try different CR phone patterns
        patterns = [
            r"\+506\s*\d{4}\s*\d{4}",
            r"\+506[\s\-]*\d{3,4}[\s\-]*\d{4}",
            r"\(\+506\)[\s\-]*\d{4}[\s\-]*\d{4}",
        ]
        for pattern in patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0].strip()
        return None

    def _extract_website(self, content: BeautifulSoup) -> Optional[str]:
        """Website link from the listing details area."""
        for a in content.find_all("a", href=True):
            h = a["href"]
            if h.startswith(("http://", "https://")) and "puertoviejosatellite" not in h:
                # Exclude booking.com, instagram, facebook, maps
                if any(s in h for s in ["booking.com", "instagram", "facebook", "maps.google"]):
                    continue
                # Exclude common non-business links
                if any(s in h for s in [
                    "wa.me", "whatsapp", "mailto", "javascript",
                ]):
                    continue
                # Check if the link text or nearby has a website icon
                img_before = a.find_previous("img", src=lambda s: s and "website" in s.lower()) if a.find_previous else None
                if img_before:
                    return h
                # Also check if link text contains a URL
                txt = a.get_text(strip=True)
                if txt and ("." in txt) and not txt.startswith("View"):
                    return h
        return None

    def _extract_google_maps_cid(self, content: BeautifulSoup) -> Optional[str]:
        """Extract Google Maps CID from 'Get directions' link."""
        for a in content.find_all("a", href=True):
            h = a["href"]
            # Direct CID in query
            cid_match = re.search(r"[?&]cid=(\d+)", h)
            if cid_match:
                return cid_match.group(1)
            # Google Maps URL with CID
            if "maps.google.com" in h or "maps.googleapis.com" in h:
                parsed = urlparse(h)
                qs = parse_qs(parsed.query)
                if "cid" in qs:
                    return qs["cid"][0]
        return None

    def _extract_instagram(self, content: BeautifulSoup) -> Optional[dict]:
        """Extract Instagram handle+URL from Listing Details area."""
        # Find instagram.com links
        for a in content.find_all("a", href=True):
            h = a["href"]
            if "instagram.com" in h.lower():
                # Skip the site-wide Instagram in the footer (already excluded by using content area)
                handle = a.get_text(strip=True)
                if not handle or "@" in handle:
                    # Extract handle from URL
                    match = re.search(r"instagram\.com/([^/?\s]+)", h)
                    if match:
                        handle = match.group(1)
                return {"handle": handle, "url": h}
        return None

    def _extract_facebook(self, content: BeautifulSoup) -> Optional[str]:
        for a in content.find_all("a", href=True):
            h = a["href"]
            if "facebook.com" in h.lower() and "sharer" not in h.lower():
                return h
        return None

    def _extract_description(self, content: BeautifulSoup) -> Optional[str]:
        # Look for paragraph text after the H1/business name
        # On PVS, the short description is often between the H1 and "Listing Details"
        heading = content.find(["h2", "h3"], string=re.compile(r"Listing Details", re.I))
        if heading:
            # Get text between business name and Listing Details
            prev = heading.find_previous("p")
            if prev:
                txt = prev.get_text(strip=True)
                if len(txt) > 10:
                    return txt[:2000]
        return None

    def _extract_rating(self, content: BeautifulSoup) -> Optional[float]:
        rating_text = content.find(string=re.compile(r"Average rating[: ]\d+", re.I))
        if rating_text:
            match = re.search(r"(\d+\.?\d*)", str(rating_text))
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None

    def _extract_price(self, content: BeautifulSoup) -> Optional[str]:
        price_img = content.find(
            "img", src=lambda s: s and "green-dollar" in s.lower()
        )
        if price_img:
            parent = price_img.parent
            txt = parent.get_text(strip=True) if parent else ""
            if "$" in txt:
                return txt
        return None

    def _extract_verified_date(self, content: BeautifulSoup) -> Optional[str]:
        verified_text = content.find(
            string=re.compile(r"Verified\s*\d{4}-\d{2}-\d{2}", re.I)
        )
        if verified_text:
            match = re.search(r"(\d{4}-\d{2}-\d{2})", str(verified_text))
            if match:
                return match.group(1)
        return None

    def _extract_status(self, soup: BeautifulSoup) -> str:
        # Check for Closed/Temporarily closed/Needs verification
        for img in soup.find_all("img", src=True):
            s = img.get("src", "")
            if "caution" in s.lower():
                alt = img.get("alt", "")
                if "temporarily" in alt.lower():
                    return "temporarily_closed"
            if "closed" in s.lower():
                return "closed"
            if "warning" in s.lower():
                return "needs_verification"
        # Check for "Closed" text in the listing area
        if soup.find(string=re.compile(r"^\s*Closed\s*$", re.M)):
            return "closed"
        return "active"

    def _extract_alternate_names(self, content: BeautifulSoup) -> Optional[str]:
        text = content.get_text()
        patterns = [
            r"previously\s+called\s+([^\.]+)",
            r"(?:formerly|aka)\s+([^\.]+)",
            r"also\s+known\s+as\s+([^\.]+)",
            r"previously\s+named\s+([^\.]+)",
            r"also\s+called\s+([^\.]+)",
        ]
        names = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.I)
            names.extend(m.strip() for m in matches)
        return "; ".join(names) if names else None
