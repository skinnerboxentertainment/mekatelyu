import re
from typing import Optional
from .schema import BusinessListing


class Normalizer:
    def normalize(self, listing: BusinessListing) -> BusinessListing:
        self._normalize_phone(listing)
        self._normalize_instagram(listing)
        self._normalize_urls(listing)
        self._normalize_name(listing)
        return listing

    def _normalize_phone(self, listing: BusinessListing):
        if not listing.phone:
            return
        raw = listing.phone.strip()

        # Remove prefixes like "Phone:", "Tel:", etc
        raw = re.sub(r"^(phone|tel|call|whatsapp)\s*:?\s*", "", raw, flags=re.I)

        # Remove labels after phone number
        raw = re.sub(r"\s+(whatsapp|phone).*$", "", raw, flags=re.I)

        # Remove whitespace, dashes, parens
        cleaned = re.sub(r"[\s\-\(\)]", "", raw)

        # Normalize Costa Rica format
        if cleaned.startswith("506") and len(cleaned) >= 11:
            listing.normalized_phone = "+" + cleaned
        elif cleaned.startswith("+506"):
            listing.normalized_phone = cleaned
        elif cleaned.startswith("00"):
            listing.normalized_phone = "+" + cleaned[2:]
        elif cleaned.startswith("0"):
            listing.normalized_phone = "+506" + cleaned[1:]
        else:
            # Already a number with digits only
            digits = re.sub(r"[^\d]", "", raw)
            if len(digits) == 8:
                listing.normalized_phone = "+506" + digits
            elif len(digits) > 8:
                if not digits.startswith("506"):
                    listing.normalized_phone = "+506" + digits
                else:
                    listing.normalized_phone = "+" + digits
            else:
                listing.normalized_phone = listing.phone

        # Store normalized
        listing.normalized_phone = listing.normalized_phone.strip()

    def _normalize_instagram(self, listing: BusinessListing):
        if listing.instagram_handle:
            handle = listing.instagram_handle.strip().strip("@")
            handle = re.sub(r"[^a-zA-Z0-9_.]", "", handle)
            if handle:
                listing.normalized_instagram = handle
                if not listing.instagram_url:
                    listing.instagram_url = f"https://www.instagram.com/{handle}/"

    def _normalize_urls(self, listing: BusinessListing):
        if listing.website:
            if not listing.website.startswith(("http://", "https://")):
                listing.website = "https://" + listing.website

        if listing.instagram_url and not listing.instagram_url.startswith(("http://", "https://")):
            listing.instagram_url = "https://" + listing.instagram_url.lstrip(":/")

        if listing.facebook_url and not listing.facebook_url.startswith(("http://", "https://")):
            listing.facebook_url = "https://" + listing.facebook_url.lstrip(":/")

    def _normalize_name(self, listing: BusinessListing):
        if listing.business_name:
            listing.business_name = listing.business_name.strip()
            # Collapse multiple spaces
            listing.business_name = re.sub(r"\s+", " ", listing.business_name)
