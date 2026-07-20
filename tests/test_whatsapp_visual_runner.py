import unittest

from scripts.run_whatsapp_visual_audit import classify, compare_names


class VisualRunnerTests(unittest.TestCase):
    def test_exact_visible_identity_matches(self):
        self.assertEqual(compare_names("Hotel Pura Vida", "Hotel Pura Vida")[0], "match")

    def test_location_suffix_does_not_break_match(self):
        self.assertEqual(
            compare_names("Cariblue Beach and Jungle Resort - Playa Cocles", "Cariblue Beach and Jungle Resort")[0],
            "match",
        )

    def test_number_only_page_is_unclear(self):
        result = classify({"business_name": "Example"}, ["Chat on WhatsApp with +506 8888 1111"])
        self.assertEqual(result["identity_result"], "unclear")

    def test_different_named_profile_is_mismatch(self):
        result = classify({"business_name": "Example Hotel"}, ["Unrelated Dental Clinic"])
        self.assertEqual(result["identity_result"], "mismatch")


if __name__ == "__main__":
    unittest.main()
