import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class AliasConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "pv_master_unified.csv").open(encoding="utf-8-sig", newline="") as handle:
            cls.master = list(csv.DictReader(handle))
        with (ROOT / "audit" / "maps-cid-discovery" / "alias-consolidation.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.manifest = list(csv.DictReader(handle))
        cls.archive = [
            json.loads(line) for line in
            (ROOT / "audit" / "maps-cid-discovery" / "alias-row-archive.jsonl").read_text(encoding="utf-8").splitlines()
        ]

    def test_all_reviewed_alias_clusters_were_consolidated(self):
        self.assertEqual(23, len(self.manifest))
        self.assertEqual(29, sum(int(item["removed_count"]) for item in self.manifest))
        names = {row["business_name"] for row in self.master}
        removed = {
            name for item in self.manifest for name in item["removed_aliases"].split(" | ") if name
        }
        self.assertTrue(removed.isdisjoint(names))

    def test_archive_preserves_every_alias_and_canonical_state(self):
        alias_records = [item for item in self.archive if item["role"] == "alias"]
        before = [item for item in self.archive if item["role"] == "canonical_before"]
        after = [item for item in self.archive if item["role"] == "canonical_after"]
        self.assertEqual(29, len(alias_records))
        self.assertEqual(23, len(before))
        self.assertEqual(23, len(after))
        self.assertTrue(all(set(item["record"]) == set(self.master[0]) for item in self.archive))

    def test_google_maps_cids_are_unique(self):
        cids = [row["google_maps_cid"] for row in self.master if row["google_maps_cid"]]
        self.assertEqual(len(cids), len(set(cids)))


if __name__ == "__main__":
    unittest.main()
