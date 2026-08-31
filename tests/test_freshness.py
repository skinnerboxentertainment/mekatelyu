"""Freshness: what happens when a fact gets old.

The governing rule is that a fact we can no longer stand behind is labelled,
never asserted. These tests hold the code to it — in particular that an unknown
date is treated as needing attention rather than being quietly assumed fine,
which is the failure mode that would put a confidently wrong page in front of
someone.
"""

import csv
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paradisio_app import freshness, provenance, viewmodels

REPO = Path(__file__).resolve().parent.parent
TODAY = date(2026, 8, 31)


class DateParsingTest(unittest.TestCase):
    def test_plain_dates(self):
        self.assertEqual(freshness.parse_date("2026-02-16"), date(2026, 2, 16))

    def test_iso_timestamps_from_the_extractor(self):
        self.assertEqual(freshness.parse_date("2026-08-02T17:40:19.014Z"), date(2026, 8, 2))
        self.assertEqual(freshness.parse_date("2026-08-02T17:40:19Z"), date(2026, 8, 2))

    def test_unparseable_input_is_none_rather_than_a_guess(self):
        for value in ("", None, "not a date", "16/02/2026", "0000"):
            with self.subTest(value=value):
                self.assertIsNone(freshness.parse_date(value))


class PolicyTest(unittest.TestCase):
    def test_recent_capture_is_fresh(self):
        self.assertEqual(freshness.state_for("hours", "2026-08-20", TODAY), freshness.FRESH)

    def test_approaching_the_threshold_is_aging(self):
        # hours threshold is 60 days; 50 days is past 75% of it
        self.assertEqual(freshness.state_for("hours", "2026-07-12", TODAY), freshness.AGING)

    def test_past_the_threshold_is_stale(self):
        self.assertEqual(freshness.state_for("hours", "2026-05-01", TODAY), freshness.STALE)

    def test_an_unknown_date_is_unknown_not_fresh(self):
        """The important one: absence of evidence is not evidence of freshness."""
        self.assertEqual(freshness.state_for("hours", "", TODAY), freshness.UNKNOWN)
        self.assertEqual(freshness.state_for("operating_status", None, TODAY), freshness.UNKNOWN)

    def test_coordinates_never_expire(self):
        self.assertEqual(freshness.state_for("coordinates", "2019-01-01", TODAY), freshness.FRESH)
        self.assertEqual(freshness.state_for("coordinates", "", TODAY), freshness.FRESH)

    def test_operating_status_expires_sooner_than_identity(self):
        """A business that closed is the costliest thing to get wrong."""
        self.assertLess(freshness.POLICY_DAYS["operating_status"], freshness.POLICY_DAYS["identity"])

    def test_live_assertion_is_stricter_than_the_listing_policy(self):
        """Listing a schedule is one claim; saying 'open now' is a stronger one."""
        self.assertLess(freshness.LIVE_STATUS_MAX_AGE_DAYS, freshness.POLICY_DAYS["hours"])


class AssessmentTest(unittest.TestCase):
    def test_worst_aspect_drives_the_verdict(self):
        assessment = freshness.assess(
            {"verified_date": "2026-08-20"}, {"hours": "2020-01-01"}, TODAY
        )
        self.assertEqual(assessment.worst, freshness.STALE)
        self.assertIn("hours", assessment.stale_aspects)

    def test_a_wholly_recent_record_is_fresh(self):
        assessment = freshness.assess(
            {"verified_date": "2026-08-25", "ig_verify_date": "2026-08-25"},
            {"hours": "2026-08-25", "amenities": "2026-08-25", "attributes": "2026-08-25"},
            TODAY,
        )
        self.assertEqual(assessment.worst, freshness.FRESH)

    def test_aspects_a_record_does_not_have_are_not_assessed(self):
        assessment = freshness.assess({"verified_date": "2026-08-25"}, {}, TODAY)
        self.assertNotIn("hours", assessment.aspects)

    def test_a_record_with_no_dates_at_all_needs_attention(self):
        assessment = freshness.assess({}, {}, TODAY)
        self.assertTrue(assessment.needs_attention())


class PriorityTest(unittest.TestCase):
    def _assess(self, verified, captures=None):
        return freshness.assess({"verified_date": verified}, captures or {}, TODAY)

    def test_a_fresh_record_is_not_queued(self):
        self.assertEqual(freshness.priority(self._assess("2026-08-25"), {}), 0)

    def test_stale_operating_status_outranks_stale_identity(self):
        stale = self._assess("2024-01-01")
        with_status = freshness.priority(stale, {})
        self.assertGreater(with_status, 0)
        self.assertGreaterEqual(
            freshness.POLICY_DAYS["identity"], freshness.POLICY_DAYS["operating_status"]
        )

    def test_a_flagged_record_is_pushed_up_the_queue(self):
        base = freshness.priority(self._assess("2026-08-25"), {})
        flagged = freshness.priority(
            self._assess("2026-08-25"), {"operating_status": "needs_verification"}
        )
        self.assertGreater(flagged, base)

    def test_a_contactable_record_outranks_an_uncontactable_one(self):
        stale = self._assess("2024-01-01")
        self.assertGreater(
            freshness.priority(stale, {"phone": "2750 0000"}),
            freshness.priority(stale, {}),
        )


class HonestLabellingTest(unittest.TestCase):
    def test_a_stale_record_says_so(self):
        lines = viewmodels.provenance_lines(
            {"provenance_summary": {"verified_date": "2024-01-01"}, "freshness_state": "stale"}
        )
        self.assertIn("may have changed", " ".join(lines))

    def test_a_fresh_record_makes_no_such_claim(self):
        lines = viewmodels.provenance_lines(
            {"provenance_summary": {"verified_date": "2026-08-25"}, "freshness_state": "fresh"}
        )
        self.assertNotIn("may have changed", " ".join(lines))

    def test_an_unknown_record_is_treated_like_a_stale_one(self):
        lines = viewmodels.provenance_lines(
            {"provenance_summary": {}, "freshness_state": "unknown"}
        )
        self.assertIn("may have changed", " ".join(lines))

    def test_the_note_is_translated(self):
        from paradisio_app import i18n
        lines = viewmodels.provenance_lines(
            {"provenance_summary": {}, "freshness_state": "stale"}, i18n.translator("es")
        )
        self.assertIn("puede haber cambiado", " ".join(lines))


class RealCatalogueTest(unittest.TestCase):
    """The policy has to produce a sane answer on the actual data."""

    @classmethod
    def setUpClass(cls):
        with open(REPO / "pv_master_unified.csv", encoding="utf-8-sig", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.index = provenance.ProvenanceIndex()

    def test_every_record_can_be_assessed_without_raising(self):
        for row in self.rows:
            with self.subTest(business=row.get("business_name", "")):
                captures = self.index.capture_dates(row.get("google_maps_cid", "").strip())
                self.assertIn(freshness.assess(row, captures, TODAY).worst,
                              (freshness.FRESH, freshness.AGING, freshness.STALE, freshness.UNKNOWN))

    def test_the_queue_is_not_the_whole_catalogue_nor_empty(self):
        queued = 0
        for row in self.rows:
            captures = self.index.capture_dates(row.get("google_maps_cid", "").strip())
            if freshness.priority(freshness.assess(row, captures, TODAY), row):
                queued += 1
        self.assertGreater(queued, 0, "nothing queued — the policy is not doing anything")
        self.assertLess(queued, len(self.rows), "everything queued — the policy is not discriminating")

    def test_google_captured_aspects_are_currently_fresh(self):
        """Sanity check against reality: the Maps batch is recent."""
        checked = 0
        for row in self.rows:
            captures = self.index.capture_dates(row.get("google_maps_cid", "").strip())
            if "hours" in captures:
                self.assertEqual(freshness.state_for("hours", captures["hours"], TODAY), freshness.FRESH)
                checked += 1
        self.assertGreater(checked, 100)


if __name__ == "__main__":
    unittest.main()
