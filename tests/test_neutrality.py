"""The neutrality guarantee, and proof that each part of it can fail.

Payment may buy presentation. It may never buy position or inclusion. That
promise is only worth something if the check enforcing it is capable of
rejecting a violation — and one of these checks shipped briefly unable to match
anything at all, because a shell heredoc replaced its `\\b` escapes with literal
backspace characters. It passed every run and would have passed a real breach.

So every check here is tested by planting the violation it exists to catch.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import verify_neutrality as neutrality

SAMPLE = {
    "business_name": "Test Place",
    "category": "restaurant",
    "area": "Puerto Viejo",
    "latitude": "9.65",
    "phone": "27500000",
    "whatsapp": "+50688889999",
    "website": "https://example.com",
    "instagram_handle": "testplace",
    "google_maps_cid": "123",
    "description_full": "A place.",
    "operating_status": "active",
    "verified_date": "2026-08-01",
}


class OrderingReadsOnlyCompleteness(unittest.TestCase):
    def test_the_fields_ordering_touches_are_all_declared(self):
        touched = neutrality.fields_ordering_reads(SAMPLE)
        undeclared = touched - neutrality.ORDERING_MAY_READ
        self.assertEqual(undeclared, set(), f"ordering reads undeclared fields: {sorted(undeclared)}")

    def test_no_ordering_field_is_payment_shaped(self):
        self.assertEqual(neutrality.check_ordering_inputs(SAMPLE), [])

    def test_the_recorder_actually_records(self):
        """If RecordingRow stopped recording, every check above would pass vacuously."""
        touched = neutrality.fields_ordering_reads(SAMPLE)
        self.assertIn("phone", touched)
        self.assertIn("website", touched)
        self.assertGreater(len(touched), 10)

    def test_a_payment_field_in_the_ordering_path_is_caught(self):
        """Plant the violation: make a score read a sponsorship field."""
        original = neutrality.build.visibility_score

        def bribed(row):
            if row.get("sponsorship_level"):
                return 100
            return original(row)

        neutrality.build.visibility_score = bribed
        try:
            errors = neutrality.check_ordering_inputs(SAMPLE)
        finally:
            neutrality.build.visibility_score = original
        self.assertTrue(errors, "a score reading `sponsorship_level` was not caught")
        self.assertTrue(any("sponsorship_level" in e for e in errors), errors)


class PayingChangesNothing(unittest.TestCase):
    def test_scores_are_identical_with_and_without_payment_fields(self):
        self.assertEqual(neutrality.check_payment_cannot_change_a_score(SAMPLE), [])

    def test_a_score_that_rewards_payment_is_caught(self):
        original = neutrality.build.contactability_score

        def bribed(row):
            return original(row) + (50 if row.get("premium") else 0)

        neutrality.build.contactability_score = bribed
        try:
            errors = neutrality.check_payment_cannot_change_a_score(SAMPLE)
        finally:
            neutrality.build.contactability_score = original
        self.assertTrue(errors, "a score that pays out for `premium` was not caught")


class ThePayloadCheckCanActuallyFail(unittest.TestCase):
    """The check that once could not match anything.

    A word-boundary regex built from an escaped string is easy to break in a way
    that leaves it silently permissive, so this asserts the mechanism works
    rather than trusting that it looks right.
    """

    def test_it_flags_a_planted_payment_word(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            static = Path(tmp) / "static"
            static.mkdir()
            (static / "directory-data-en.js").write_text(
                'const BUSINESSES=[{"name":"A Place","sponsor":true}];', encoding="utf-8"
            )
            original = neutrality.RELEASE
            neutrality.RELEASE = Path(tmp)
            try:
                errors = neutrality.check_payload_is_clean()
            finally:
                neutrality.RELEASE = original
        self.assertTrue(errors, "a payload containing 'sponsor' was not flagged")
        self.assertTrue(any("sponsor" in e for e in errors), errors)

    def test_it_does_not_fire_on_an_innocent_substring(self):
        """`tier` must not match inside `frontier`, or the check cries wolf."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            static = Path(tmp) / "static"
            static.mkdir()
            (static / "directory-data-en.js").write_text(
                'const BUSINESSES=[{"name":"Frontier Cabinas"}];', encoding="utf-8"
            )
            original = neutrality.RELEASE
            neutrality.RELEASE = Path(tmp)
            try:
                errors = neutrality.check_payload_is_clean()
            finally:
                neutrality.RELEASE = original
        self.assertEqual(errors, [], "the word-boundary match is not working")

    def test_a_missing_payload_is_reported_rather_than_passing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            original = neutrality.RELEASE
            neutrality.RELEASE = Path(tmp)
            try:
                errors = neutrality.check_payload_is_clean()
            finally:
                neutrality.RELEASE = original
        self.assertTrue(errors, "an absent payload passed silently")


if __name__ == "__main__":
    unittest.main()
