"""Provenance: the join between a published field and the evidence behind it.

The project's claim is that its data is evidence-backed. These tests hold that
claim to something checkable — that a field can name its source, that a source
which is known to be corrupt is reported as unknown rather than displayed, and
that a record with no evidence says so instead of implying confidence it has not
earned.
"""

import csv
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paradisio_app import i18n, provenance, viewmodels

REPO = Path(__file__).resolve().parent.parent


class CleanSourceTest(unittest.TestCase):
    def test_a_stringified_list_is_not_a_source(self):
        """`coordinate_source` reads 'array' for 448 of 736 records."""
        self.assertEqual(provenance.clean_source("array"), "")
        self.assertEqual(provenance.clean_source("ARRAY"), "")

    def test_blank_is_not_a_source(self):
        for value in ("", None, "   ", "none", "nan"):
            with self.subTest(value=value):
                self.assertEqual(provenance.clean_source(value), "")

    def test_a_real_source_is_given_a_readable_name(self):
        self.assertEqual(provenance.clean_source("osm"), "OpenStreetMap")
        self.assertEqual(provenance.clean_source("maps_stealth"), "Google Maps (manual search)")

    def test_an_unrecognised_but_present_source_is_kept(self):
        self.assertEqual(provenance.clean_source("some_new_pipeline"), "some_new_pipeline")


class ExplainTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = provenance.ProvenanceIndex()
        with open(REPO / "pv_master_unified.csv", encoding="utf-8-sig", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.by_cid = {r["google_maps_cid"].strip(): r for r in cls.rows if r["google_maps_cid"].strip()}

    def test_every_record_can_say_something_about_itself(self):
        for row in self.rows[:120]:
            with self.subTest(business=row["business_name"]):
                self.assertTrue(self.index.explain(row), "record produced no evidence at all")

    def test_identity_names_its_source(self):
        row = self.rows[0]
        identity = self.index.identity(row)[0]
        self.assertEqual(identity.field, "business_name")
        self.assertTrue(identity.source)

    def test_a_record_without_coordinates_claims_no_location_evidence(self):
        row = {"business_name": "X", "latitude": "", "longitude": ""}
        self.assertEqual(self.index.location(row), [])

    def test_corrupt_coordinate_source_is_reported_as_unrecorded(self):
        row = {"latitude": "9.65", "longitude": "-82.75", "coordinate_source": "array"}
        self.assertEqual(self.index.location(row)[0].source, "not recorded")

    def test_whatsapp_evidence_states_it_was_never_inferred(self):
        row = {"whatsapp": "+50688888888"}
        evidence = self.index.whatsapp(row)[0]
        self.assertIn("never inferred", evidence.detail)

    def test_taxonomy_assertions_carry_the_rule_that_fired(self):
        row = next(r for r in self.rows if r["google_maps_cid"].strip())
        semantics = self.index.semantics(row)
        if semantics:
            self.assertTrue(any("rule" in e.detail for e in semantics))

    def test_enrichment_evidence_records_when_it_was_captured(self):
        found = False
        for cid, row in list(self.by_cid.items())[:200]:
            for evidence in self.index.enrichment(row):
                self.assertTrue(evidence.captured, f"{cid} evidence has no capture time")
                found = True
        self.assertTrue(found, "no enrichment evidence found to check")

    def test_evidence_renders_without_raising(self):
        for row in self.rows[:40]:
            for evidence in self.index.explain(row):
                self.assertIsInstance(evidence.describe(), str)


class ProvenanceSurfaceTest(unittest.TestCase):
    """What a reader is told, as opposed to what an operator can query."""

    def test_a_record_with_no_evidence_says_so(self):
        lines = viewmodels.provenance_lines({"provenance_summary": {}})
        self.assertEqual(len(lines), 1)
        self.assertIn("not been re-checked", lines[0])

    def test_a_confirmed_record_reports_its_date(self):
        lines = viewmodels.provenance_lines({"provenance_summary": {"verified_date": "2026-02-16"}})
        self.assertIn("2026-02-16", " ".join(lines))

    def test_maps_capture_is_reported_as_a_readable_month(self):
        lines = viewmodels.provenance_lines(
            {"provenance_summary": {"google_captured": "2026-08-02"}}
        )
        self.assertIn("August 2026", " ".join(lines))

    def test_the_surface_is_translated(self):
        spanish = i18n.translator("es")
        lines = viewmodels.provenance_lines(
            {"provenance_summary": {"google_captured": "2026-08-02"}}, spanish
        )
        joined = " ".join(lines)
        self.assertIn("agosto 2026", joined)
        self.assertNotIn("August", joined)

    def test_unverified_instagram_is_not_claimed_as_verified(self):
        lines = viewmodels.provenance_lines(
            {"provenance_summary": {"instagram_confidence": "handle_guess", "verified_date": "2026-01-01"}}
        )
        self.assertNotIn("checked against the live profile", " ".join(lines))

    def test_verified_instagram_is_reported(self):
        lines = viewmodels.provenance_lines(
            {"provenance_summary": {"instagram_confidence": "verified"}}
        )
        self.assertIn("checked against the live profile", " ".join(lines))


if __name__ == "__main__":
    unittest.main()
