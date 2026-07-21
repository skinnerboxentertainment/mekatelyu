import unittest

from scripts.autovisual_whatsapp_checkifier import record_id


class WhatsAppIntegrationTests(unittest.TestCase):
    def test_record_id_is_stable(self):
        self.assertEqual(record_id("Example", "Puerto Viejo"), record_id("Example", "Puerto Viejo"))

    def test_area_disambiguates_same_business_name(self):
        self.assertNotEqual(record_id("Example", "Cocles"), record_id("Example", "Manzanillo"))


if __name__ == "__main__":
    unittest.main()
