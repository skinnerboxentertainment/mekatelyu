import unittest

from scripts.audit_whatsapp_routes import normalize_whatsapp


class WhatsAppAuditTests(unittest.TestCase):
    def test_local_number_gets_country_code(self):
        self.assertEqual(normalize_whatsapp("8790 3340"), "+50687903340")

    def test_wa_me_link(self):
        self.assertEqual(normalize_whatsapp("https://wa.me/50687903340"), "+50687903340")

    def test_api_link(self):
        self.assertEqual(
            normalize_whatsapp("https://api.whatsapp.com/send?phone=12133143400"),
            "+12133143400",
        )

    def test_invalid_number(self):
        self.assertEqual(normalize_whatsapp("123"), "")


if __name__ == "__main__":
    unittest.main()
