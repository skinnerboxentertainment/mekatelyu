import csv
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class EntityResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "pv_master_unified.csv").open(encoding="utf-8-sig", newline="") as handle:
            cls.master = list(csv.DictReader(handle))
        with (ROOT / "audit" / "entity-resolution" / "pair-decisions.csv").open(encoding="utf-8", newline="") as handle:
            cls.decisions = list(csv.DictReader(handle))
        with (ROOT / "audit" / "entity-resolution" / "merge-manifest.csv").open(encoding="utf-8", newline="") as handle:
            cls.merges = list(csv.DictReader(handle))
        cls.archive = [json.loads(line) for line in (ROOT / "audit" / "entity-resolution" / "merged-row-archive.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_every_candidate_pair_has_a_disposition(self):
        self.assertEqual(142, len(self.decisions))
        counts = Counter(item["decision"] for item in self.decisions)
        self.assertEqual({"deterministic_merge": 4, "distinct_cids": 121,
                          "related_or_shared_contact": 8, "not_duplicate_single_signal": 9}, dict(counts))

    def test_four_merges_are_archived_and_aliases_absent(self):
        self.assertEqual(4, len(self.merges))
        self.assertEqual(12, len(self.archive))
        names = {row["business_name"] for row in self.master}
        self.assertTrue({item["removed_alias"] for item in self.merges}.isdisjoint(names))
        self.assertTrue({item["canonical"] for item in self.merges}.issubset(names))

    def test_master_is_entity_resolved_and_cids_unique(self):
        self.assertEqual(737, len(self.master))
        cids = [row["google_maps_cid"] for row in self.master if row["google_maps_cid"]]
        self.assertEqual(len(cids), len(set(cids)))


if __name__ == "__main__":
    unittest.main()
