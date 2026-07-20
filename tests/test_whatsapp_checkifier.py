import json
import tempfile
import unittest
from pathlib import Path

from scripts.autovisual_whatsapp_checkifier import (
    attach_screenshot, build_queues, prepare, record_batch, safe_route, select_pilot, validate_attempt,
)


class CheckifierTests(unittest.TestCase):
    def test_route_has_no_message_or_query(self):
        self.assertEqual(safe_route("+50687903340"), "https://wa.me/50687903340")
        with self.assertRaises(ValueError):
            safe_route("87903340")

    def test_explicit_and_phone_candidate_are_separate(self):
        rows = [
            {"business_name":"A","area":"PV","whatsapp":"8790 3340","phone":"8790 3340"},
            {"business_name":"B","area":"PV","whatsapp":"","phone":"6186 1852"},
        ]
        preservation, candidates = build_queues(rows)
        self.assertEqual(len(preservation), 1)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["source_class"], "phone_candidate")

    def test_control_cannot_be_match(self):
        preservation, _ = build_queues([
            {"business_name":f"Biz {n}","area":"PV","whatsapp":f"+5068{n:07d}","phone":""}
            for n in range(1, 7)
        ])
        pilot = select_pilot(preservation)
        control = pilot[-1]
        with self.assertRaises(ValueError):
            validate_attempt({"record_id":control["record_id"],"route":control["route"],
                "render_state":"target_visible","identity_result":"match","display_name":"Control",
                "confidence":1}, pilot)

    def test_number_only_target_cannot_be_match(self):
        preservation, _ = build_queues([
            {"business_name":"Biz","area":"PV","whatsapp":"+50687903340","phone":""}
        ])
        item = preservation[0]
        with self.assertRaises(ValueError):
            validate_attempt({"record_id":item["record_id"],"route":item["route"],
                "render_state":"target_visible","identity_result":"match","display_name":"",
                "confidence":1}, preservation)

    def test_prepare_writes_three_queues(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); master = base / "master.csv"
            master.write_text("business_name,area,whatsapp,phone,normalized_phone,website,url,operating_status\nA,PV,87903340,87903340,,,,active\nB,PV,,61861852,,,,active\n", encoding="utf-8")
            metadata = prepare(master, base / "work")
            self.assertEqual(metadata["preservation_count"], 1)
            self.assertEqual(metadata["candidate_count"], 1)
            self.assertTrue(json.loads((base/"work/queues/pilot.json").read_text()))

    def test_screenshot_is_required_and_hashed(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp); (workspace / "screenshots").mkdir()
            screenshot = workspace / "screenshots" / "attempt.png"
            screenshot.write_bytes(b"\x89PNG\r\n\x1a\nvisual evidence")
            entry = attach_screenshot({}, workspace, "screenshots/attempt.png")
            self.assertEqual(entry["screenshot_path"], "screenshots/attempt.png")
            self.assertEqual(len(entry["screenshot_sha256"]), 64)
            with self.assertRaises(ValueError):
                attach_screenshot({}, workspace, "../outside.png")

    def test_record_batch_appends_hash_backed_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp); (workspace / "queues").mkdir(); (workspace / "screenshots").mkdir()
            item = {"record_id":"one","business_name":"One","route":"https://wa.me/50687903340","source_class":"master_explicit"}
            (workspace / "queues" / "pilot.json").write_text(json.dumps([item]), encoding="utf-8")
            (workspace / "screenshots" / "one.png").write_bytes(b"\x89PNG\r\n\x1a\nvisual evidence")
            payload = [{"record_id":"one","route":item["route"],"render_state":"business_target_visible",
                "identity_result":"match","display_name":"One","confidence":1,
                "screenshot_path":"screenshots/one.png"}]
            source = workspace / "batch.json"; source.write_text(json.dumps(payload), encoding="utf-8")
            entries = record_batch(workspace, "pilot", source)
            self.assertEqual(entries[0]["screenshot_bytes"], 23)
            self.assertIn("screenshot_sha256", json.loads((workspace / "ledger.jsonl").read_text()))


if __name__ == "__main__":
    unittest.main()
