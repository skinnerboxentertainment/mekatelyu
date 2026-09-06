"""Tests for the presentation logic, now that it returns data instead of markup.

Before the template split these rules could only be checked by rendering HTML
and reading it back. They are asserted directly here.

Also covers the HTML equivalence checker itself: it is the oracle the template
migration relied on, so it needs its own evidence that it catches real changes
rather than waving everything through.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paradisio_app import viewmodels as vm
from scripts.html_equivalence import differences, equivalent


class CategoryAndStatusTest(unittest.TestCase):
    def test_raw_identifiers_are_humanised(self):
        self.assertEqual(vm.category_label("tour_company"), "Tours")
        self.assertEqual(vm.category_label("vacation_rental"), "Vacation rental")
        self.assertEqual(vm.category_label(""), "Other")

    def test_only_actionable_statuses_produce_a_label(self):
        self.assertEqual(vm.status_label("active"), "")
        self.assertEqual(vm.status_label("unknown"), "")
        self.assertEqual(vm.status_label("needs_verification"), "Information needs review")
        self.assertEqual(vm.status_label("closed"), "Closed")
        self.assertEqual(vm.status_label("permanently_closed"), "Closed")


class RatingTest(unittest.TestCase):
    def test_absent_rating_yields_nothing(self):
        self.assertIsNone(vm.rating({}))

    def test_half_star_appears_above_the_threshold(self):
        self.assertEqual(vm.rating({"rating": 4.7})["full_stars"], 4)
        self.assertTrue(vm.rating({"rating": 4.7})["half_star"])
        self.assertFalse(vm.rating({"rating": 4.2})["half_star"])


class AddressTest(unittest.TestCase):
    def test_area_is_the_fallback(self):
        self.assertEqual(vm.address({"area": "Cocles"}), "Cocles, Puerto Viejo")

    def test_unknown_area_produces_nothing(self):
        self.assertEqual(vm.address({"area": "Unknown"}), "")

    def test_plus_code_is_appended(self):
        self.assertEqual(
            vm.address({"maps_address": "50m south of the bridge", "plus_code": "8XQ5+2R"}),
            "50m south of the bridge · 8XQ5+2R",
        )


class HoursTest(unittest.TestCase):
    def test_verified_hours_suppress_the_legacy_status(self):
        """Both showing at once produced pages that contradicted themselves."""
        model = vm.hours_header({"weekly_hours": {"monday": {}}, "open_status": "Abierto"})
        self.assertEqual(model["mode"], "verified_placeholder")

    def test_legacy_status_is_read_when_there_is_nothing_better(self):
        model = vm.hours_header({"open_status": "Abierto ahora"})
        self.assertEqual(model["mode"], "legacy")
        self.assertTrue(model["status"]["is_open"])

    def test_nothing_known_yields_no_section(self):
        self.assertEqual(vm.hours_header({})["mode"], "none")

    def test_a_closed_day_reads_as_closed(self):
        self.assertEqual(vm.format_day_schedule({"closed": True}), "Closed")
        self.assertEqual(vm.format_day_schedule({"periods": []}), "Closed")

    def test_twenty_four_hour_day(self):
        self.assertEqual(vm.format_day_schedule({"open24Hours": True}), "Open 24 hours")

    def test_period_formatting(self):
        schedule = {"periods": [{"opens": "10:00", "closes": "22:30", "closesNextDay": False}]}
        self.assertEqual(vm.format_day_schedule(schedule), "10 AM – 10:30 PM")

    def test_overnight_period_is_marked(self):
        schedule = {"periods": [{"opens": "20:00", "closes": "02:00", "closesNextDay": True}]}
        self.assertIn("(next day)", vm.format_day_schedule(schedule))

    def test_missing_day_is_reported_as_not_listed(self):
        model = vm.weekly_hours({
            "weekly_hours": {"monday": {"periods": [{"opens": "09:00", "closes": "17:00"}]}},
            "hours_meta": {"capturedAt": "2026-08-02T00:00:00Z"},
        })
        by_day = {row["day"]: row for row in model["rows"]}
        self.assertEqual(by_day["Tuesday"]["text"], "Not listed")
        self.assertTrue(by_day["Tuesday"]["unknown"])

    def test_payload_is_serialised_for_an_attribute_context(self):
        """Regression: the payload must not contain a raw double quote.

        Emitting it with Jinja's tojson filter terminated the HTML attribute
        early and corrupted the markup on every page with verified hours.
        """
        model = vm.weekly_hours({
            "weekly_hours": {"monday": {"periods": []}},
            "hours_meta": {"timezone": "America/Costa_Rica"},
        })
        self.assertIsInstance(model["payload_json"], str)
        self.assertIn('"timezone"', model["payload_json"])


class AmenityTest(unittest.TestCase):
    def test_none_yields_nothing(self):
        self.assertIsNone(vm.amenities({"amenities": []}))

    def test_short_lists_are_shown_whole(self):
        self.assertFalse(vm.amenities({"amenities": ["a", "b", "c"]})["collapsed"])

    def test_long_lists_collapse(self):
        model = vm.amenities({"amenities": [f"a{i}" for i in range(9)]})
        self.assertTrue(model["collapsed"])
        self.assertEqual(model["total"], 9)


class AttributeSelectionTest(unittest.TestCase):
    def _groups(self, count):
        return [{"group": "Service options", "items": [f"Option {i}" for i in range(count)]}]

    def test_nothing_to_show(self):
        self.assertIsNone(vm.attributes({"attributes": []}))

    def test_small_sets_are_not_collapsed(self):
        model = vm.attributes({"attributes": self._groups(4), "category": "restaurant"})
        self.assertFalse(model["collapsed"])
        self.assertIsNone(model["summary"])

    def test_large_sets_collapse_with_a_summary(self):
        model = vm.attributes({"attributes": self._groups(25), "category": "restaurant"})
        self.assertTrue(model["collapsed"])
        self.assertEqual(len(model["summary"]), vm.DETAILS_LARGE_SUMMARY_LIMIT)

    def test_duplicates_within_a_group_are_removed(self):
        model = vm.attributes({
            "attributes": [{"group": "Offerings", "items": ["Coffee", "coffee", "  Coffee  ", "Tea"]}],
            "category": "restaurant",
        })
        self.assertEqual(model["groups"][0]["items"], ["Coffee", "Tea"])

    def test_alias_pairs_collapse_to_the_richer_wording(self):
        model = vm.attributes({
            "attributes": [{"group": "Amenities", "items": ["Free Wi-Fi", "Wi-Fi"]}],
            "category": "hotel",
        })
        self.assertEqual(model["groups"][0]["items"], ["Free Wi-Fi"])

    def test_decision_relevant_attributes_outrank_universal_ones(self):
        model = vm.attributes({
            "attributes": [
                {"group": "Service options", "items": ["Casual", "Groups", "Delivery", "Takeaway"]},
                {"group": "Accessibility", "items": ["Wheelchair-accessible entrance"]},
                {"group": "Offerings", "items": [f"Dish {i}" for i in range(12)]},
            ],
            "category": "restaurant",
        })
        self.assertTrue(model["collapsed"])
        self.assertIn("Wheelchair-accessible entrance", model["summary"])
        self.assertNotIn("Casual", model["summary"])

    def test_one_group_cannot_crowd_out_the_others(self):
        model = vm.attributes({
            "attributes": [
                {"group": "Offerings", "items": [f"Dish {i}" for i in range(20)]},
                {"group": "Accessibility", "items": ["Wheelchair-accessible entrance"]},
            ],
            "category": "restaurant",
        })
        self.assertIn("Wheelchair-accessible entrance", model["summary"])


class SemanticFacetTest(unittest.TestCase):
    def test_the_category_tag_is_not_repeated_as_a_chip(self):
        facets = vm.semantic_facets({
            "category": "restaurant", "semantic_tags": ["restaurant", "cafe"], "semantic_attributes": [],
        })
        self.assertNotIn("Restaurant", facets)
        self.assertIn("Café", facets)


class StickyActionTest(unittest.TestCase):
    def test_share_is_always_present(self):
        actions = vm.sticky_actions({"channels": {}, "primary_contact": {"type": "None"}})
        self.assertEqual([a["kind"] for a in actions], ["share"])

    def test_call_is_offered_when_it_is_not_already_the_primary_action(self):
        actions = vm.sticky_actions({
            "channels": {"phone_normalized": "+50627500000"}, "primary_contact": {"type": "WhatsApp"},
        })
        self.assertIn("call", [a["kind"] for a in actions])

    def test_call_is_not_duplicated_when_it_is_the_primary_action(self):
        actions = vm.sticky_actions({
            "channels": {"phone_normalized": "+50627500000"}, "primary_contact": {"type": "Call"},
        })
        self.assertEqual([a["kind"] for a in actions], ["share"])

    def test_whatsapp_number_becomes_a_link(self):
        actions = vm.sticky_actions({
            "channels": {"whatsapp": "+50688888888"}, "primary_contact": {"type": "WhatsApp"},
        })
        call = next(a for a in actions if a["kind"] == "call")
        self.assertEqual(call["url"], "https://wa.me/50688888888")


class HtmlEquivalenceCheckerTest(unittest.TestCase):
    """The oracle the template migration was verified against."""

    BASE = '<div class="a"><p>Hello <b>world</b></p><a href="https://x.test">Go</a></div>'

    def test_formatting_differences_are_forgiven(self):
        reformatted = '<div class="a">\n  <p>Hello <b>world</b></p>\n  <a href="https://x.test">Go</a>\n</div>'
        self.assertTrue(equivalent(self.BASE, reformatted))

    def test_changed_text_is_caught(self):
        self.assertTrue(differences(self.BASE, self.BASE.replace("world", "there")))

    def test_changed_link_target_is_caught(self):
        self.assertTrue(differences(self.BASE, self.BASE.replace("https://x.test", "https://evil.test")))

    def test_changed_class_is_caught(self):
        self.assertTrue(differences(self.BASE, self.BASE.replace('class="a"', 'class="b"')))

    def test_missing_element_is_caught(self):
        self.assertTrue(differences(self.BASE, '<div class="a"><p>Hello <b>world</b></p></div>'))

    def test_added_element_is_caught(self):
        self.assertTrue(differences(self.BASE, self.BASE.replace("</div>", "<span>x</span></div>")))


if __name__ == "__main__":
    unittest.main()
