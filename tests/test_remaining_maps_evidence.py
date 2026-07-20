import csv
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class RemainingMapsEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "pv_master_unified.csv").open(encoding="utf-8-sig", newline="") as handle:
            cls.master = list(csv.DictReader(handle))
        with (ROOT / "audit" / "maps-cid-discovery" / "remaining-evidence-decisions.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.decisions = list(csv.DictReader(handle))

    def test_all_25_records_have_final_decisions(self):
        self.assertEqual(25, len(self.decisions))
        self.assertEqual({"accepted": 13, "rejected_wrong_target": 12},
                         dict(Counter(item["decision"] for item in self.decisions)))

    def test_accepted_cids_are_present_and_rejected_cids_not_injected(self):
        by_name = {row["business_name"]: row for row in self.master}
        for item in self.decisions:
            if item["decision"] == "accepted":
                self.assertEqual(item["resolved_cid"], by_name[item["business_name"]]["google_maps_cid"])
            else:
                self.assertNotEqual(item["resolved_cid"], by_name[item["business_name"]]["google_maps_cid"])

    def test_master_cids_remain_unique(self):
        cids = [row["google_maps_cid"] for row in self.master if row["google_maps_cid"]]
        self.assertEqual(len(cids), len(set(cids)))


if __name__ == "__main__":
    unittest.main()
