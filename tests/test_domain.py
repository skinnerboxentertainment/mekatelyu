"""Tests for the typed core.

These cover the rules that protect people — a route that is published must be
one that works and one the business actually offers — plus the provenance fields
the renderer historically discarded.
"""

import sys
import unittest
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paradisio_app import domain


class PhoneNormalisationTest(unittest.TestCase):
    def test_local_eight_digit_number_gains_the_country_code(self):
        self.assertEqual(domain.normalize_phone("2750 0000"), "+50627500000")

    def test_international_number_is_preserved(self):
        self.assertEqual(domain.normalize_phone("+1 415 555 0100"), "+14155550100")

    def test_unusable_input_fails_closed(self):
        for bad in ["", None, "abc", "123", "0" * 20, "call us!"]:
            with self.subTest(value=bad):
                self.assertEqual(domain.normalize_phone(bad), "")


class WhatsAppRouteTest(unittest.TestCase):
    """The rule that a phone number is never assumed to be a WhatsApp account."""

    def test_explicit_local_number_is_routed(self):
        self.assertEqual(domain.explicit_whatsapp("8888 8888"), "+50688888888")

    def test_wa_me_link_is_parsed(self):
        self.assertEqual(domain.explicit_whatsapp("https://wa.me/50688888888"), "+50688888888")

    def test_phone_query_form_is_parsed(self):
        self.assertEqual(
            domain.explicit_whatsapp("https://api.whatsapp.com/send?phone=50688888888"),
            "+50688888888",
        )

    def test_absent_source_yields_no_route(self):
        self.assertEqual(domain.explicit_whatsapp(""), "")
        self.assertEqual(domain.explicit_whatsapp(None), "")

    def test_a_plain_phone_column_never_becomes_a_whatsapp_route(self):
        routes = domain.ContactRoutes.from_row({"phone": "2750 0000", "normalized_phone": "+50627500000"})
        self.assertEqual(routes.phone_e164, "+50627500000")
        self.assertEqual(routes.whatsapp, "", "a phone number was silently promoted to WhatsApp")


class ExternalUrlTest(unittest.TestCase):
    def test_https_is_kept(self):
        self.assertEqual(domain.safe_external_url("https://example.com/x"), "https://example.com/x")

    def test_http_is_rejected_rather_than_upgraded(self):
        self.assertEqual(domain.safe_external_url("http://example.com"), "")

    def test_junk_is_rejected(self):
        for bad in ["", None, "javascript:alert(1)", "ftp://example.com", "example.com", "//example.com"]:
            with self.subTest(value=bad):
                self.assertEqual(domain.safe_external_url(bad), "")


class InstagramHandleTest(unittest.TestCase):
    def test_at_prefix_is_stripped(self):
        self.assertEqual(domain.safe_instagram_handle("@cafe_rico"), "cafe_rico")

    def test_invalid_handles_are_rejected(self):
        for bad in ["", None, "has space", "https://instagram.com/x", "a" * 31, "bad/slash"]:
            with self.subTest(value=bad):
                self.assertEqual(domain.safe_instagram_handle(bad), "")


class DisplayNameTest(unittest.TestCase):
    def test_location_suffix_after_dash_is_removed(self):
        self.assertEqual(
            domain.clean_display_name("Cabinas Sol - Playa Cocles, Puerto Viejo, Costa Rica", "Cocles"),
            "Cabinas Sol",
        )

    def test_trailing_country_is_removed(self):
        self.assertEqual(domain.clean_display_name("Hotel Mar, Costa Rica", "Cahuita"), "Hotel Mar")

    def test_a_name_that_is_only_location_is_not_emptied(self):
        self.assertEqual(domain.clean_display_name("Puerto Viejo", "Puerto Viejo"), "Puerto Viejo")


class ClosedBusinessTest(unittest.TestCase):
    """A closed business must expose no way to contact it."""

    def _closed(self, status):
        return domain.Establishment.from_row({
            "business_name": "Former Cafe", "category": "restaurant", "area": "Cocles",
            "operating_status": status, "phone": "2750 0000", "normalized_phone": "+50627500000",
            "whatsapp": "88888888", "website": "https://example.com",
            "instagram_handle": "former_cafe",
        })

    def test_closed_statuses_are_recognised(self):
        for status in ("closed", "permanently_closed", "CLOSED"):
            with self.subTest(status=status):
                self.assertTrue(self._closed(status).is_closed)

    def test_closed_business_publishes_no_route(self):
        for status in ("closed", "permanently_closed"):
            with self.subTest(status=status):
                routes = self._closed(status).contactable_routes()
                self.assertEqual(routes.phone_e164, "")
                self.assertEqual(routes.whatsapp, "")
                self.assertEqual(routes.website, "")
                self.assertEqual(routes.instagram, "")

    def test_open_business_keeps_its_routes(self):
        routes = self._closed("active").contactable_routes()
        self.assertEqual(routes.phone_e164, "+50627500000")
        self.assertEqual(routes.whatsapp, "+50688888888")


class DisplayPhoneTest(unittest.TestCase):
    def test_unusable_phone_is_not_displayed(self):
        """The page must not print a number the Call action would refuse."""
        routes = domain.ContactRoutes.from_row({"phone": "call us", "normalized_phone": ""})
        self.assertEqual(routes.phone_e164, "")
        self.assertEqual(routes.phone_display, "")


class ProvenanceTest(unittest.TestCase):
    """The acquisition record the renderer used to ignore entirely."""

    ROW: ClassVar[dict[str, str]] = {
        "business_name": "Cafe Rico", "category": "restaurant", "area": "Cocles",
        "url": "https://source.example/listing/1",
        "coordinate_source": "maps_stealth",
        "geofilter": "within", "geofilter_reason": "3.1km from origin",
        "instagram_enrich_source": "handle_guess", "instagram_enrich_date": "2026-07-02",
        "instagram_enrich_confidence": "high", "instagram_confidence": "verified",
        "ig_verified": "true", "ig_verify_date": "2026-07-04",
        "verified_date": "2026-07-20",
    }

    def test_every_acquisition_field_is_captured(self):
        p = domain.Establishment.from_row(self.ROW).provenance
        self.assertEqual(p.source_url, "https://source.example/listing/1")
        self.assertEqual(p.coordinate_source, "maps_stealth")
        self.assertEqual(p.geofilter_reason, "3.1km from origin")
        self.assertEqual(p.instagram_source, "handle_guess")
        self.assertEqual(p.instagram_verified_on, "2026-07-04")
        self.assertEqual(p.verified_date, "2026-07-20")

    def test_has_any_reports_whether_anything_is_known(self):
        self.assertTrue(domain.Establishment.from_row(self.ROW).provenance.has_any())
        bare = domain.Establishment.from_row({"business_name": "X", "area": "Y"})
        self.assertFalse(bare.provenance.has_any())


class SecondarySocialChannelTest(unittest.TestCase):
    """Channels the dataset holds but the site does not yet render."""

    def test_channels_are_modelled_and_validated(self):
        routes = domain.ContactRoutes.from_row({
            "tiktok_url": "https://tiktok.com/@rico",
            "youtube_url": "https://youtube.com/@rico",
            "twitter_url": "http://twitter.com/rico",  # insecure, must be dropped
        })
        self.assertEqual(
            routes.social_channels(),
            [("TikTok", "https://tiktok.com/@rico"), ("YouTube", "https://youtube.com/@rico")],
        )


class BuildDelegationTest(unittest.TestCase):
    """build.* must keep behaving identically now that it delegates here."""

    def test_build_helpers_are_the_domain_implementations(self):
        from paradisio_app import build
        self.assertIs(build.normalize_phone, domain.normalize_phone)
        self.assertIs(build.safe_external_url, domain.safe_external_url)
        self.assertIs(build.safe_instagram_handle, domain.safe_instagram_handle)
        self.assertIs(build.clean_display_name, domain.clean_display_name)

    def test_has_whatsapp_still_takes_a_row(self):
        from paradisio_app import build
        self.assertEqual(build.has_whatsapp({"whatsapp": "88888888"}), "+50688888888")
        self.assertEqual(build.has_whatsapp({"whatsapp": ""}), "")


if __name__ == "__main__":
    unittest.main()
