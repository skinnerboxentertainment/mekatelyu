import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_publication_consistency import check_weekly_schedule, check_description_hours, check_taxonomy_type


def business(**kw):
    base = {
        "name": "Test",
        "slug": "test",
        "category": "services",
        "description": "",
        "semantic_tags": [],
        "semantic_attributes": [],
        "weekly_hours": {},
    }
    base.update(kw)
    return base


class PublicationValidatorTests(unittest.TestCase):
    def test_closed_day_with_periods_is_error(self):
        weekly = {"monday": {"closed": True, "open24Hours": False, "periods": [{"opens": "10:00", "closes": "22:00"}]}}
        errors = check_weekly_schedule(weekly)
        self.assertTrue(any("closed but has periods" in e for e in errors))

    def test_closed_and_open24_is_error(self):
        weekly = {"monday": {"closed": True, "open24Hours": True, "periods": []}}
        errors = check_weekly_schedule(weekly)
        self.assertTrue(any("both closed and open24Hours" in e for e in errors))

    def test_invalid_interval_is_error(self):
        weekly = {"monday": {"closed": False, "open24Hours": False, "periods": [{"opens": "banana", "closes": "22:00"}]}}
        errors = check_weekly_schedule(weekly)
        self.assertTrue(any("invalid interval" in e for e in errors))

    def test_overnight_without_flag_is_error(self):
        weekly = {"friday": {"closed": False, "open24Hours": False, "periods": [{"opens": "22:00", "closes": "02:00"}]}}
        errors = check_weekly_schedule(weekly)
        self.assertTrue(any("without closesNextDay" in e for e in errors))

    def test_canonical_open24_is_valid(self):
        weekly = {"monday": {"closed": False, "open24Hours": True, "periods": [{"opens": "00:00", "closes": "24:00", "closesNextDay": False}]}}
        errors = check_weekly_schedule(weekly)
        self.assertEqual(errors, [])

    def test_overlapping_periods_is_error(self):
        weekly = {"monday": {"closed": False, "open24Hours": False, "periods": [
            {"opens": "10:00", "closes": "14:00"},
            {"opens": "13:00", "closes": "18:00"},
        ]}}
        errors = check_weekly_schedule(weekly)
        self.assertTrue(any("overlapping periods" in e for e in errors))

    def test_adjacent_periods_are_not_overlap(self):
        weekly = {"monday": {"closed": False, "open24Hours": False, "periods": [
            {"opens": "10:00", "closes": "12:00"},
            {"opens": "12:00", "closes": "14:00"},
        ]}}
        errors = check_weekly_schedule(weekly)
        self.assertEqual(errors, [])

    def test_description_except_sunday_conflict(self):
        biz = business(
            description="Open daily except Sunday.",
            weekly_hours={"sunday": {"closed": False, "open24Hours": False, "periods": [{"opens": "07:00", "closes": "17:00"}]}},
        )
        warnings = check_description_hours(biz)
        self.assertTrue(any("Sunday described as closed" in w["descriptionClaim"] for w in warnings))

    def test_description_24_7_conflict(self):
        biz = business(
            description="Open 24/7.",
            weekly_hours={"monday": {"closed": False, "open24Hours": False, "periods": [{"opens": "07:00", "closes": "17:00"}]}},
        )
        warnings = check_description_hours(biz)
        self.assertTrue(any("24-7" in w["descriptionClaim"] for w in warnings))

    def test_auto_business_tagged_medical_is_suspicious(self):
        biz = business(
            name="Automotriz Danny",
            description="Car repair and towing.",
            semantic_tags=["local-service", "medical"],
        )
        warnings = check_taxonomy_type(biz)
        self.assertTrue(any(w["issue"] == "suspicious_taxonomy" for w in warnings))

    def test_real_clinic_medical_not_suspicious(self):
        biz = business(
            name="Hone Creek Clinic",
            description="Medical clinic.",
            semantic_tags=["local-service", "medical"],
        )
        warnings = check_taxonomy_type(biz)
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
