"""Language support.

The directory lists every business in a Spanish-speaking town by default. That
premise is only honest if those businesses can read their own listing, so these
tests assert the chrome is genuinely translated — not merely that a translation
file exists.

What is deliberately *not* translated, and why:

* **Business names.** Proper nouns.
* **Descriptions a business wrote.** Shown as written; translating them would be
  putting words in someone's mouth.
* **Amenities and attributes captured from Google Maps.** Shown in the language
  they were captured in. Translating captured evidence would make it no longer
  the evidence, which is the opposite of what this project claims about its data.

Descriptions this generator composes itself *are* translated, because we wrote
them.
"""

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paradisio_app import i18n, viewmodels


class TranslatorTest(unittest.TestCase):
    def test_every_language_has_the_same_keys(self):
        reference = set(i18n.load_strings("en"))
        for language in i18n.available_languages():
            with self.subTest(language=language):
                self.assertEqual(
                    set(i18n.load_strings(language)), reference,
                    f"{language}.json has drifted from en.json",
                )

    def test_no_translation_is_blank(self):
        for language in i18n.available_languages():
            blanks = [k for k, v in i18n.load_strings(language).items() if not str(v).strip()]
            self.assertEqual(blanks, [], f"{language} has empty values: {blanks[:5]}")

    def test_a_missing_key_returns_the_key_rather_than_nothing(self):
        """A gap must be visible, not silently blank out a control."""
        t = i18n.translator("es")
        self.assertEqual(t("no.such.key"), "no.such.key")

    def test_english_falls_back_for_a_language_specific_gap(self):
        t = i18n.Translator("xx", {}, {"a.key": "English text"})
        self.assertEqual(t("a.key"), "English text")

    def test_parameters_are_substituted(self):
        t = i18n.translator("es")
        self.assertIn("5", t("biz.details_view_all", n=5))

    def test_a_bad_parameter_does_not_raise(self):
        t = i18n.translator("en")
        self.assertIsInstance(t("biz.details_view_all"), str)


class UrlLayoutTest(unittest.TestCase):
    def test_english_is_unprefixed(self):
        """736 printed QR codes point at /businesses/<slug>.html."""
        self.assertEqual(i18n.translator("en").path_prefix, "")

    def test_other_languages_are_prefixed(self):
        self.assertEqual(i18n.translator("es").path_prefix, "es/")

    def test_alternates_cover_every_language_plus_a_default(self):
        links = i18n.alternate_links("businesses/x.html", "https://example.test")
        langs = [link["lang"] for link in links]
        for language in i18n.available_languages():
            self.assertIn(language, langs)
        self.assertIn("x-default", langs)

    def test_the_default_alternate_points_at_the_unprefixed_url(self):
        links = i18n.alternate_links("businesses/x.html", "https://example.test")
        default = next(link for link in links if link["lang"] == "x-default")
        self.assertEqual(default["url"], "https://example.test/businesses/x.html")

    def test_switch_links_are_root_absolute(self):
        links = i18n.language_switch_links("businesses/x.html", "es")
        by_lang = {link["lang"]: link["url"] for link in links}
        self.assertEqual(by_lang["en"], "/businesses/x.html")
        self.assertEqual(by_lang["es"], "/es/businesses/x.html")

    def test_the_current_language_is_marked(self):
        links = i18n.language_switch_links("index.html", "es")
        current = [link["lang"] for link in links if link["current"]]
        self.assertEqual(current, ["es"])


class TranslatedPresentationTest(unittest.TestCase):
    """The view model must render its text in the requested language."""

    def setUp(self):
        self.es = i18n.translator("es")

    def test_category_is_translated(self):
        self.assertEqual(viewmodels.category_label("restaurant", self.es), "Restaurante")
        self.assertEqual(viewmodels.category_label("vacation_rental", self.es), "Alquiler vacacional")

    def test_status_is_translated(self):
        self.assertEqual(viewmodels.status_label("closed", self.es), "Cerrado")
        self.assertEqual(viewmodels.status_label("active", self.es), "")

    def test_day_schedule_is_translated(self):
        self.assertEqual(viewmodels.format_day_schedule({"closed": True}, self.es), "Cerrado")
        self.assertEqual(viewmodels.format_day_schedule({"open24Hours": True}, self.es), "Abierto 24 horas")

    def test_hours_provenance_is_translated(self):
        model = viewmodels.weekly_hours(
            {"weekly_hours": {"monday": {"periods": []}}, "hours_meta": {"capturedAt": "2026-08-02T00:00:00Z"}},
            self.es,
        )
        self.assertIn("Según Google Maps", model["provenance"])

    def test_a_generated_description_is_composed_in_spanish(self):
        biz = {"description_facts": [
            ("desc.category_in_area", {"category_key": "restaurant", "area": "Cocles"}),
            ("desc.phone", {}),
        ]}
        text = viewmodels.describe(biz, self.es)
        self.assertIn("Restaurante en Cocles.", text)
        self.assertIn("Teléfono disponible.", text)

    def test_a_business_written_description_is_left_alone(self):
        """We do not translate what a business wrote about itself."""
        original = "We serve the best gallo pinto on the Caribbean coast, since 1998."
        biz = {"description_facts": None, "description": original}
        self.assertEqual(viewmodels.describe(biz, self.es), original)

    def test_contact_label_is_translated_without_altering_the_target(self):
        contact = {"type": "WhatsApp", "label": "Message on WhatsApp", "url": "https://wa.me/50688888888"}
        localised = viewmodels.localise_contact(contact, self.es)
        self.assertEqual(localised["label"], "Enviar WhatsApp")
        self.assertEqual(localised["url"], contact["url"], "translation must never change where a link goes")

    def test_semantic_chips_are_translated(self):
        chips = viewmodels.semantic_facets(
            {"category": "hotel", "semantic_tags": ["cabins"], "semantic_attributes": []}, self.es
        )
        self.assertIn("Cabinas", chips)


class BuiltSiteTest(unittest.TestCase):
    """Assertions against a real build, covering the page chrome end to end."""

    @classmethod
    def setUpClass(cls):
        import tempfile

        from scripts.golden_manifest import build_into

        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name) / "release"
        build_into(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _read(self, relative):
        return (self.root / relative).read_text(encoding="utf-8")

    def test_english_pages_keep_their_original_urls(self):
        """The constraint that outranks everything else here: printed QR codes."""
        self.assertTrue((self.root / "index.html").exists())
        self.assertTrue((self.root / "businesses" / "7-ice-creams-puerto-viejo.html").exists())

    def test_each_language_has_a_full_page_tree(self):
        english = len(list((self.root / "businesses").glob("*.html")))
        for language in i18n.available_languages():
            if language == i18n.DEFAULT_LANGUAGE:
                continue
            with self.subTest(language=language):
                pages = list((self.root / language / "businesses").glob("*.html"))
                # The community-partner page is English-only for now.
                self.assertGreaterEqual(len(pages), english - 1)

    def test_lang_attribute_matches_the_tree(self):
        for language in i18n.available_languages():
            prefix = "" if language == i18n.DEFAULT_LANGUAGE else f"{language}/"
            with self.subTest(language=language):
                markup = self._read(f"{prefix}index.html")
                self.assertIn(f'<html lang="{language}">', markup)

    def test_spanish_chrome_is_actually_spanish(self):
        markup = self._read("es/businesses/7-ice-creams-puerto-viejo.html")
        for expected in ["Directorio", "Horario", "Hora de Costa Rica", "Copiar", "Comparte este lugar"]:
            with self.subTest(string=expected):
                self.assertIn(expected, markup)

    def test_spanish_home_chrome_is_actually_spanish(self):
        markup = self._read("es/index.html")
        for expected in ["Todas las Categorías", "Todas las Zonas", "Cargando directorio"]:
            with self.subTest(string=expected):
                self.assertIn(expected, markup)

    def test_pages_declare_their_alternates(self):
        markup = self._read("es/businesses/7-ice-creams-puerto-viejo.html")
        self.assertGreaterEqual(markup.count('rel="alternate" hreflang'), len(i18n.available_languages()))

    def test_canonical_points_at_the_language_that_rendered_it(self):
        markup = self._read("es/businesses/7-ice-creams-puerto-viejo.html")
        canonical = re.search(r'rel="canonical" href="([^"]+)"', markup).group(1)
        self.assertIn("/es/businesses/", canonical)

    def test_every_language_gets_its_own_client_strings(self):
        for language in i18n.available_languages():
            with self.subTest(language=language):
                self.assertTrue((self.root / "static" / f"ui-{language}.js").exists())
                self.assertTrue((self.root / "static" / f"directory-data-{language}.js").exists())

    def test_asset_references_resolve_in_every_language(self):
        """A prefixed tree sits one level deeper; a wrong prefix silently
        strips the stylesheet and every script from those pages."""
        broken = []
        pages = [self.root / "index.html"]
        for language in i18n.available_languages():
            prefix = "" if language == i18n.DEFAULT_LANGUAGE else f"{language}/"
            pages.append(self.root / f"{prefix}index.html")
            pages.extend(sorted((self.root / f"{prefix}businesses").glob("*.html"))[:5])
        for page in pages:
            for ref in re.findall(r'(?:href|src)="([^"#:]+?)(?:\?[^"]*)?"', page.read_text(encoding="utf-8")):
                if ref.startswith(("http", "//", "mailto", "tel", "data:", "/")):
                    continue
                if not (page.parent / ref).resolve().exists():
                    broken.append(f"{page.relative_to(self.root)} -> {ref}")
        self.assertEqual(broken, [], f"broken asset references: {broken[:10]}")


if __name__ == "__main__":
    unittest.main()
