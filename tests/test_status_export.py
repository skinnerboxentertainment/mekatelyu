"""Operating status and identity: export, wiring, and the freshness policy.

These cover the change that makes P1 measurable at all. Before it, `identity`
and `operating_status` had no capture date of their own and fell back to a CSV
column nothing writes, so their age only ever grew and no sweep could move them.
"""

import sys
import unittest
from datetime import date
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paradisio_app import freshness
from scripts.export_verified_status import CONCLUSIVE, build_index


def record(**over):
    """A conclusive pipeline record, overridable per test."""
    base = {
        "listingId": "black-bamboo",
        "sourceName": "Black Bamboo",
        "detectedGoogleName": "Black Bamboo",
        "googleCid": "111",
        "capturedAt": "2026-09-05T10:00:00Z",
        "status": "success_expanded",
        "operatingStatus": "open",
        "extractorVersion": "google-maps-amenities-v2",
    }
    base.update(over)
    return base


class BuildIndex(unittest.TestCase):
    def test_a_clean_read_is_kept(self):
        store, counts = build_index([record()])
        self.assertIn("111", store)
        self.assertEqual(store["111"]["operatingStatus"], "open")
        self.assertEqual(store["111"]["capturedAt"], "2026-09-05T10:00:00Z")
        self.assertEqual(counts["kept"], 1)

    def test_a_closed_business_is_recorded_not_dropped(self):
        store, _ = build_index([record(status="business_permanently_closed",
                                       operatingStatus="permanently_closed")])
        self.assertEqual(store["111"]["operatingStatus"], "permanently_closed")

    def test_a_blocked_page_records_nothing(self):
        """A failed check must never look like a fresh one."""
        for blocked in ("captcha_or_traffic_block", "consent_required", "navigation_failed"):
            store, counts = build_index([record(status=blocked)])
            self.assertEqual(store, {}, f"{blocked} was recorded as a capture")
            self.assertEqual(counts["inconclusive"], 1)

    def test_an_identity_mismatch_records_nothing_and_is_counted(self):
        store, counts = build_index([record(status="place_identity_mismatch")])
        self.assertEqual(store, {})
        self.assertEqual(counts["identity_mismatch"], 1)

    def test_a_record_with_no_cid_is_skipped(self):
        store, counts = build_index([record(googleCid="")])
        self.assertEqual(store, {})
        self.assertEqual(counts["no_cid"], 1)

    def test_a_capture_with_no_timestamp_is_not_trusted(self):
        store, _ = build_index([record(capturedAt="")])
        self.assertEqual(store, {})

    def test_an_unrecognised_status_becomes_no_assertion(self):
        """A pipeline change must not silently introduce a status we misread."""
        store, _ = build_index([record(operatingStatus="probably_fine")])
        self.assertIsNone(store["111"]["operatingStatus"])

    def test_later_records_win(self):
        store, _ = build_index([
            record(capturedAt="2026-01-01T00:00:00Z", operatingStatus="open"),
            record(capturedAt="2026-09-05T00:00:00Z", operatingStatus="permanently_closed"),
        ])
        self.assertEqual(store["111"]["operatingStatus"], "permanently_closed")


class ProvenanceWiring(unittest.TestCase):
    def test_status_store_dates_identity_and_operating_status(self):
        from paradisio_app import provenance

        index = provenance.ProvenanceIndex()
        index.status = {"999": {"capturedAt": "2026-09-05T10:00:00Z"}}
        dates = index.capture_dates("999")
        self.assertEqual(dates.get("identity"), "2026-09-05T10:00:00Z")
        self.assertEqual(dates.get("operating_status"), "2026-09-05T10:00:00Z")

    def test_without_the_store_those_aspects_have_no_capture_date(self):
        """The defect this change fixes: no capture date, so no way to refresh."""
        from paradisio_app import provenance

        index = provenance.ProvenanceIndex()
        index.status = {}
        dates = index.capture_dates("999")
        self.assertNotIn("identity", dates)
        self.assertNotIn("operating_status", dates)


class FreshnessPolicy(unittest.TestCase):
    """Contact and Instagram are label-only by owner decision, 2026-09-05."""

    def test_label_only_aspects_do_not_age(self):
        ancient = "2019-01-01"
        today = date(2026, 9, 5)
        for aspect in ("contact", "instagram"):
            self.assertEqual(
                freshness.state_for(aspect, ancient, today), freshness.FRESH,
                f"{aspect} is label-only and must not drive the staleness verdict",
            )

    def test_refreshable_aspects_still_age(self):
        """The policy must not have gone slack everywhere."""
        today = date(2026, 9, 5)
        self.assertEqual(freshness.state_for("operating_status", "2019-01-01", today), freshness.STALE)
        self.assertEqual(freshness.state_for("hours", "2019-01-01", today), freshness.STALE)
        self.assertEqual(freshness.state_for("identity", "2019-01-01", today), freshness.STALE)

    def test_a_refreshed_capture_reads_fresh(self):
        today = date(2026, 9, 5)
        self.assertEqual(freshness.state_for("operating_status", "2026-09-05", today), freshness.FRESH)
        self.assertEqual(freshness.state_for("identity", "2026-09-05", today), freshness.FRESH)

    def test_the_ceiling_is_reachable_when_the_sweep_runs(self):
        """P1's 95% bar must be meetable, or the gate it guards never opens.

        With every ageing aspect captured today, a record must read fresh. If
        this fails, some aspect is un-refreshable and the bar is unreachable by
        construction — which is the exact defect that prompted this change.
        """
        today = date(2026, 9, 5)
        for aspect, threshold in freshness.POLICY_DAYS.items():
            if threshold is None:
                continue
            self.assertEqual(
                freshness.state_for(aspect, today.isoformat(), today), freshness.FRESH,
                f"{aspect} cannot read fresh even when captured today",
            )



class SweepActuallyRefreshes(unittest.TestCase):
    """The whole point of leg 4b: a sweep must move a record from stale to fresh.

    The first wiring attempt failed silently here. `capture_dates` supplied
    identity and operating_status correctly, but `assess` hardcoded both to the
    CSV's `verified_date` and never looked at the captures — so a sweep could
    re-read a place, store the evidence, and change nothing. Nothing failed; the
    number simply did not move. These tests fail if that returns.
    """

    STALE_ROW: ClassVar[dict[str, str]] = {
        "business_name": "Test Place",
        "google_maps_cid": "424242",
        "verified_date": "2019-01-01",
        "operating_status": "active",
    }

    def test_a_fresh_capture_makes_a_stale_record_fresh(self):
        today = date(2026, 9, 5)
        before = freshness.assess(self.STALE_ROW, {}, today)
        self.assertEqual(before.worst, freshness.STALE)
        self.assertIn("operating_status", before.stale_aspects)

        captured = {"identity": "2026-09-05T10:00:00Z", "operating_status": "2026-09-05T10:00:00Z"}
        after = freshness.assess(self.STALE_ROW, captured, today)
        self.assertEqual(
            after.worst, freshness.FRESH,
            "a sweep re-read this place and the freshness verdict did not move",
        )

    def test_a_record_never_swept_still_reports_its_real_age(self):
        """The fallback must survive: no capture means old, not unknown."""
        today = date(2026, 9, 5)
        assessment = freshness.assess(self.STALE_ROW, {}, today)
        self.assertEqual(assessment.aspects["identity"], freshness.STALE)
        self.assertEqual(assessment.aspects["operating_status"], freshness.STALE)

    def test_a_stale_capture_does_not_launder_a_record_fresh(self):
        """Storing an old capture must not make a record look recently checked."""
        today = date(2026, 9, 5)
        captured = {"identity": "2019-01-01T00:00:00Z", "operating_status": "2019-01-01T00:00:00Z"}
        assessment = freshness.assess(self.STALE_ROW, captured, today)
        self.assertEqual(assessment.worst, freshness.STALE)

class SectionAbsentIsStillAGoodRead(unittest.TestCase):
    """A missing amenities section is not a failed check.

    Measured in CI on 2026-09-05: of ten records, four returned
    `success_attributes` and six `attributes_not_exposed` — and every one of the
    six still carried a detected name and an operating status. Treating them as
    failures threw away 60% of a sweep's usable yield for no safety benefit.
    """

    def test_a_missing_section_still_dates_status_and_identity(self):
        for status in ("attributes_not_exposed", "amenities_not_exposed",
                       "hours_not_exposed", "amenities_not_applicable"):
            store, _ = build_index([record(status=status)])
            self.assertIn("111", store, f"{status} was discarded despite a clean read")
            self.assertEqual(store["111"]["operatingStatus"], "open")

    def test_a_read_with_neither_name_nor_status_is_not_stored(self):
        """Belt and braces: never date an aspect we did not actually read."""
        store, counts = build_index([
            record(status="attributes_not_exposed", detectedGoogleName=None, operatingStatus=None),
        ])
        self.assertEqual(store, {})
        self.assertEqual(counts["inconclusive"], 1)

    def test_being_turned_away_is_still_never_a_read(self):
        """Widening the conclusive set must not have let a block through."""
        for blocked in ("consent_required", "captcha_or_traffic_block",
                        "navigation_failed", "place_not_loaded",
                        "place_identity_mismatch", "extraction_failed"):
            store, _ = build_index([record(status=blocked)])
            self.assertEqual(store, {}, f"{blocked} was treated as a successful read")


class TheTwoConclusiveSetsAgree(unittest.TestCase):
    """The sweep reporter and the exporter must classify identically.

    They live in different files and are easy to update singly. If they drift,
    the sweep reports success while the exporter silently stores nothing — a
    green run that refreshed no data, which is the failure mode hardest to
    notice from the outside.
    """

    def test_they_are_the_same_set(self):
        from scripts.sweep_outcome import CONCLUSIVE as REPORTER

        self.assertEqual(
            CONCLUSIVE, REPORTER,
            "sweep_outcome.py and export_verified_status.py disagree about what "
            "counts as a successful read",
        )


class TheReportSeesEveryAspect(unittest.TestCase):
    """The quality report must not keep its own list of evidence stores.

    It did, and the list was stale: after a sweep refreshed eleven records the
    report still showed the old numbers, because `captures_for` named amenities,
    attributes and hours explicitly and knew nothing about the status store. The
    sweep worked; the instrument measuring it did not.
    """

    def test_report_lookup_matches_the_provenance_index(self):
        from paradisio_app.provenance import ProvenanceIndex
        from scripts.quality_report import captures_for

        index = ProvenanceIndex()
        index.status = {"777": {"capturedAt": "2026-09-05T10:00:00Z"}}
        self.assertEqual(captures_for(index, "777"), index.capture_dates("777"))

    def test_a_status_capture_reaches_the_report(self):
        from paradisio_app.provenance import ProvenanceIndex
        from scripts.quality_report import captures_for

        index = ProvenanceIndex()
        index.status = {"777": {"capturedAt": "2026-09-05T10:00:00Z"}}
        captures = captures_for(index, "777")
        self.assertIn("operating_status", captures)
        self.assertIn("identity", captures)


if __name__ == "__main__":
    unittest.main()
