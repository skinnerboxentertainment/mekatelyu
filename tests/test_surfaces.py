"""The surface declaration, and the control it replaced.

The old control was a list of forbidden strings. It could only catch surfaces
somebody had thought to forbid, which is the opposite of the property you want
from a release gate: the dangerous surface is the one nobody anticipated.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paradisio_app import surfaces


class TheDeclarationIsCoherent(unittest.TestCase):
    """A manifest that contradicts itself looks like a control and is not one."""

    def test_no_problems(self):
        self.assertEqual(surfaces.declaration_problems(), [])

    def test_every_surface_says_why_it_exists(self):
        for surface in surfaces.SURFACES:
            self.assertTrue(surface.why.strip(), f"{surface.name} has no stated purpose")

    def test_nothing_currently_accepts_input_from_visitors(self):
        """A true statement today, and the test that makes changing it deliberate.

        If a surface ever starts accepting input, this fails and whoever added it
        has to come here and say so.
        """
        writable = [s.name for s in surfaces.SURFACES if s.authorization != surfaces.PUBLIC_READ]
        self.assertEqual(
            writable, [],
            f"these surfaces now accept visitor input: {writable}. That may be "
            f"correct, but it is a change in what the site does and belongs in a "
            f"review, not in a passing test.",
        )


class TheDeclarationCatchesWhatTheBlocklistMissed(unittest.TestCase):
    def test_an_undeclared_file_is_claimed_by_nobody(self):
        self.assertIsNone(surfaces.find_surface("dashboard/index.html"))
        self.assertIsNone(surfaces.find_surface("admin/panel.html"))
        self.assertIsNone(surfaces.find_surface("classifieds/index.html"))
        self.assertIsNone(surfaces.find_surface("invoices/00001.html"))

    def test_the_real_release_shapes_are_all_claimed(self):
        for path in (
            "index.html", "404.html", "robots.txt", "sitemap.xml", "favicon.ico",
            ".nojekyll", "CNAME",
            "businesses/black-bamboo-puerto-viejo.html",
            "es/index.html", "es/businesses/black-bamboo-puerto-viejo.html",
            "de/index.html", "de/businesses/black-bamboo-puerto-viejo.html",
            "qr/black-bamboo-puerto-viejo.png",
            "static/app.js", "static/tokens.css",
            "static/vendor/leaflet/leaflet.js",
            "invest/index.html",
        ):
            self.assertIsNotNone(
                surfaces.find_surface(path),
                f"{path} is emitted by the build but claimed by no surface",
            )

    def test_a_near_miss_the_keyword_list_would_have_shipped(self):
        """The concrete case, kept because it is the whole argument.

        The forbidden list contains `dashboard.html`. A file at
        `dashboard/index.html` does not contain that string, so the old control
        passed it. The declaration rejects it for the only reason that matters:
        nothing claims it.
        """
        forbidden_keywords = (
            "admin.html", "claim.html", "classifieds/", "dashboard.html",
            "formsubmit", "goatcounter", "invoices/", "modes.js",
            "premium.html", "unpkg.com",
        )
        sneaky = "dashboard/index.html"
        self.assertFalse(
            any(keyword in sneaky for keyword in forbidden_keywords),
            "this path was supposed to slip past the keyword list",
        )
        self.assertIsNone(surfaces.find_surface(sneaky))


class BoundariesAreEnforcedNotAdvisory(unittest.TestCase):
    """`declaration_problems` has to actually reject bad declarations."""

    def test_public_write_without_a_destination_is_rejected(self):
        bad = surfaces.Surface(
            name="corrections", why="Accept owner corrections.",
            paths=("corrections/*.html",), authorization=surfaces.PUBLIC_WRITE,
        )
        problems = self._problems_for(bad)
        self.assertTrue(any("where it goes" in p for p in problems), problems)

    def test_naming_a_destination_without_declaring_write_is_rejected(self):
        bad = surfaces.Surface(
            name="sneaky", why="Looks read-only, is not.",
            paths=("sneaky/*.html",), input_goes_to="a database somewhere",
        )
        problems = self._problems_for(bad)
        self.assertTrue(any("disagrees with itself" in p for p in problems), problems)

    def test_an_unknown_boundary_is_rejected(self):
        bad = surfaces.Surface(
            name="vague", why="Unclear.", paths=("vague/*",), authorization="probably-fine",
        )
        problems = self._problems_for(bad)
        self.assertTrue(any("unknown authorization boundary" in p for p in problems), problems)

    def test_a_surface_claiming_nothing_is_rejected(self):
        bad = surfaces.Surface(name="empty", why="Claims no files.", paths=())
        problems = self._problems_for(bad)
        self.assertTrue(any("claims no files" in p for p in problems), problems)

    def _problems_for(self, surface):
        original = surfaces.SURFACES
        try:
            surfaces.SURFACES = (*original, surface)
            return surfaces.declaration_problems()
        finally:
            surfaces.SURFACES = original


if __name__ == "__main__":
    unittest.main()
