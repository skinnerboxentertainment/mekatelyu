import unittest

from paradisio_app.semantic_taxonomy import classify_record


def row(name, category, description="", cid=""):
    return {"business_name": name, "area": "Cocles", "category": category,
            "description_full": description, "google_maps_cid": cid}


class SemanticTaxonomyTests(unittest.TestCase):
    def test_all_lodging_types_surface_under_stay(self):
        for category in ("hotel", "hostel", "vacation_rental"):
            with self.subTest(category=category):
                self.assertIn("stay", classify_record(row("Example", category))["groups"])

    def test_hostel_has_specific_tag_and_lodging_synonyms(self):
        result = classify_record(row("Example Hostel", "hostel"))
        self.assertIn("hostel", result["tags"])
        self.assertIn("places to stay", result["search_synonyms"])
        self.assertIn("accommodation", result["search_synonyms"])

    def test_multi_label_business_can_surface_in_multiple_groups(self):
        result = classify_record(row("Beach Rooms Café & Yoga", "hotel", "A small hotel with a café and yoga studio."))
        self.assertIn("stay", result["groups"])
        self.assertIn("eat", result["groups"])
        self.assertIn("wellness", result["groups"])

    def test_amenity_does_not_redefine_business_identity(self):
        result = classify_record(row("Beach Rooms", "hotel", "A small hotel with a gym and bar."))
        self.assertEqual(["stay"], result["groups"])
        self.assertIn("gym", result["attributes"])
        self.assertIn("bar", result["attributes"])

    def test_maps_navigation_noise_is_not_classified(self):
        parsed = {"fields": {"address": {"value": "Near Hotels, Restaurants and Bars"}}}
        result = classify_record(row("Accounting Office", "services"), parsed)
        self.assertEqual(["services"], result["groups"])

    def test_assertions_retain_provenance(self):
        result = classify_record(row("Caribe Surf School", "tour_company"))
        self.assertEqual("master.name", result["assertions"]["surf"]["source"])
        self.assertGreaterEqual(result["assertions"]["surf"]["confidence"], 0.95)

    def test_missing_category_is_review_only(self):
        result = classify_record(row("Mystery Place", ""))
        self.assertEqual("review", result["review_state"])
        self.assertIn("no_discovery_group", result["conflicts"])

    def test_obvious_primary_category_contradiction_is_queued(self):
        result = classify_record(row("ALMA Masajes", "restaurant"))
        self.assertEqual("review", result["review_state"])
        self.assertIn("restaurant_with_non_food_identity", result["conflicts"])

    def test_lodging_identity_can_recover_misclassified_record(self):
        result = classify_record(row("Namu Garden Hotel & Spa", "restaurant"))
        self.assertIn("stay", result["groups"])
        self.assertIn("hotel", result["tags"])
        self.assertEqual("review", result["review_state"])

    def test_restaurant_named_casita_is_not_assumed_to_be_lodging(self):
        result = classify_record(row("La Casita de Monli", "restaurant", "Fresh seafood restaurant."))
        self.assertEqual(["eat"], result["groups"])


if __name__ == "__main__":
    unittest.main()
