import csv
import json
import unittest
from pathlib import Path

from paradisio_app.semantic_taxonomy import semantic_key


ROOT = Path(__file__).resolve().parent.parent


class SemanticArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "pv_master_unified.csv").open(encoding="utf-8-sig", newline="") as handle:
            cls.master = list(csv.DictReader(handle))
        cls.index = json.loads(
            (ROOT / "paradisio_app" / "data" / "semantic_taxonomy.json").read_text(encoding="utf-8")
        )

    def test_index_has_one_record_per_business(self):
        records = self.index["records"]
        self.assertEqual(738, self.index["record_count"])
        self.assertEqual(738, len(records))
        self.assertEqual({semantic_key(row) for row in self.master}, set(records))

    def test_primary_categories_are_preserved(self):
        for row in self.master:
            record = self.index["records"][semantic_key(row)]
            self.assertEqual(row["category"], record["primary_category"])

    def test_every_record_has_a_discovery_group(self):
        for record in self.index["records"].values():
            self.assertTrue(record["groups"], record["business_name"])

    def test_all_canonical_lodging_is_discoverable_as_stay(self):
        lodging = {"hotel", "hostel", "vacation_rental"}
        for record in self.index["records"].values():
            if record["primary_category"] in lodging:
                self.assertIn("stay", record["groups"], record["business_name"])

    def test_authorized_taxonomy_decisions_are_fully_resolved(self):
        with (ROOT / "audit" / "semantic-taxonomy" / "resolved-primary-categories.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            decisions = list(csv.DictReader(handle))
        self.assertEqual(23, len(decisions))
        self.assertEqual(19, sum(item["old_category"] != item["resolved_category"] for item in decisions))
        self.assertEqual(4, sum(item["disposition"].startswith("retained_") for item in decisions))
        unresolved = json.loads(
            (ROOT / "audit" / "semantic-taxonomy" / "review-queue.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], unresolved)


if __name__ == "__main__":
    unittest.main()
