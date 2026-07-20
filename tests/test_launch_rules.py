import unittest

from paradisio_app import build


class LaunchContactRulesTest(unittest.TestCase):
    def test_local_phone_is_normalized_for_calling(self):
        self.assertEqual(build.normalize_phone("8888 1111"), "+50688881111")

    def test_invalid_phone_is_rejected(self):
        self.assertEqual(build.normalize_phone("123"), "")

    def test_whatsapp_requires_explicit_source_value(self):
        row = {"phone": "+506 8888 1111", "normalized_phone": "+50688881111", "whatsapp": ""}
        self.assertEqual(build.has_whatsapp(row), "")

    def test_local_explicit_whatsapp_gets_country_code(self):
        self.assertEqual(build.has_whatsapp({"whatsapp": "8888 1111"}), "+50688881111")

    def test_international_explicit_whatsapp_is_preserved(self):
        self.assertEqual(
            build.has_whatsapp({"whatsapp": "https://api.whatsapp.com/send?phone=12133143400"}),
            "+12133143400",
        )

    def test_invalid_explicit_whatsapp_is_rejected(self):
        self.assertEqual(build.has_whatsapp({"whatsapp": "123"}), "")

    def test_closed_business_has_no_primary_or_secondary_contact(self):
        row = {
            "business_name": "Closed Example",
            "operating_status": "closed",
            "phone": "+506 8888 1111",
            "whatsapp": "+50688881111",
            "instagram_handle": "closed-example",
        }
        self.assertEqual(build.get_primary_contact(row)["type"], "None")
        self.assertEqual(build.get_secondary_links(row), [])
        self.assertEqual(build.get_badges(row), [])


class LaunchPresentationRulesTest(unittest.TestCase):
    def test_raw_category_identifiers_are_humanized(self):
        self.assertEqual(build.category_label("tour_company"), "Tours")
        self.assertEqual(build.category_label("vacation_rental"), "Vacation rental")
        self.assertEqual(build.category_label("real_estate"), "Real estate")
        self.assertEqual(build.get_intents("real_estate"), ["services"])

    def test_only_actionable_statuses_are_presented(self):
        self.assertEqual(build.status_html("active"), "")
        self.assertEqual(build.status_html("unknown"), "")
        self.assertIn("Information needs review", build.status_html("needs_verification"))
        self.assertIn("Closed", build.status_html("closed"))

    def test_invalid_external_url_is_removed(self):
        self.assertEqual(build.safe_external_url("https:///broken.example"), "")

    def test_invalid_instagram_handle_is_removed(self):
        self.assertEqual(build.safe_instagram_handle("pcb&b"), "")
        self.assertEqual(build.safe_instagram_handle("@valid.handle"), "valid.handle")

    def test_http_external_url_is_removed_instead_of_guessed(self):
        self.assertEqual(build.safe_external_url("http://example.com/path"), "")

    def test_public_summary_excludes_private_and_operational_fields(self):
        business = {
            "slug": "example-puerto-viejo",
            "name": "Example",
            "category": "services",
            "area": "Puerto Viejo",
            "lat": "9.65",
            "lng": "-82.75",
            "distance_km": "0.1",
            "status": "active",
            "channels": {
                "phone": "+506 8888 1111",
                "whatsapp": "+50688881111",
                "instagram": "example",
                "website": "https://example.com",
                "booking_url": "",
                "google_maps_cid": "123",
                "email": "private@example.com",
            },
            "primary_contact": {"type": "WhatsApp", "label": "Message on WhatsApp", "url": "https://wa.me/50688881111"},
            "scores": {"contactability": 80, "visibility": 60, "completeness": 70},
            "badges": ["WhatsApp"],
            "intents": ["services"],
            "description": "Example description",
            "rating": 4.5,
        }
        summary = build.public_business_summary(business)
        self.assertNotIn("email", summary["channels"])
        self.assertNotIn("url", summary["primary_contact"])


if __name__ == "__main__":
    unittest.main()
