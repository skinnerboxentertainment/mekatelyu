"""Characterisation tests: the build must not change the site by accident.

These are the safety net for structural work on the generator. They assert that a
fresh build reproduces the recorded output exactly — every one of ~1,500 files —
so any refactor that alters a rendered page fails loudly and names the file.

When a change to the output is *intended*, re-record with:

    python scripts/golden_manifest.py write

and review the resulting diff as part of the change.
"""

import difflib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.golden_manifest import (
    FIXTURE_DIR,
    FIXTURES,
    MANIFEST_PATH,
    build_into,
    compare,
    parse_manifest,
    snapshot,
)


class GoldenOutputTest(unittest.TestCase):
    """One build shared by every assertion in this class (a build takes ~7s)."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.release = Path(cls._tmp.name) / "release"
        build_into(cls.release)
        cls.snapshot = snapshot(cls.release)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_manifest_exists(self):
        self.assertTrue(
            MANIFEST_PATH.exists(),
            "golden manifest missing; run: python scripts/golden_manifest.py write",
        )

    def test_every_emitted_file_matches_the_manifest(self):
        expected = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        problems = compare(expected, self.snapshot)
        if problems:
            shown = "\n".join("  " + p for p in problems[:30])
            extra = "" if len(problems) <= 30 else f"\n  ... and {len(problems) - 30} more"
            self.fail(
                f"{len(problems)} file(s) differ from the golden manifest:\n{shown}{extra}\n\n"
                "If this change was intended, re-record with:\n"
                "  python scripts/golden_manifest.py write"
            )

    def test_build_emits_the_expected_file_count(self):
        expected = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            len(self.snapshot), len(expected),
            f"build emitted {len(self.snapshot)} files, manifest records {len(expected)}",
        )

    def test_representative_pages_are_byte_identical(self):
        """Full-text comparison for the page shapes that actually vary.

        The manifest catches any change; these fixtures explain it, by showing
        the offending lines instead of a hash mismatch.
        """
        for slug, description in FIXTURES.items():
            with self.subTest(page=slug, covers=description):
                fixture = FIXTURE_DIR / f"{slug}.html"
                built = self.release / "businesses" / f"{slug}.html"
                self.assertTrue(fixture.exists(), f"missing fixture for {slug}")
                self.assertTrue(built.exists(), f"build did not emit {slug}")
                want = fixture.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
                got = built.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
                if want != got:
                    diff = "\n".join(
                        list(difflib.unified_diff(
                            want.splitlines(), got.splitlines(),
                            fromfile=f"golden/{slug}.html", tofile=f"built/{slug}.html",
                            lineterm="", n=2,
                        ))[:40]
                    )
                    self.fail(f"{slug} changed ({description}):\n{diff}")


class BuildDeterminismTest(unittest.TestCase):
    """The property the golden manifest depends on."""

    def test_two_builds_with_a_pinned_date_are_identical(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first, second = Path(a) / "r", Path(b) / "r"
            build_into(first)
            build_into(second)
            differing = compare(snapshot(first), snapshot(second))
            self.assertEqual(
                differing, [],
                "build is not deterministic; golden comparison cannot be trusted:\n"
                + "\n".join("  " + d for d in differing[:20]),
            )

    def test_build_date_must_be_well_formed(self):
        import os
        import subprocess
        env = dict(os.environ)
        with tempfile.TemporaryDirectory() as tmp:
            env["PARADISIO_OUTPUT_DIR"] = str(Path(tmp) / "r")
            env["PARADISIO_BUILD_DATE"] = "31-08-2026"  # wrong order, must fail closed
            repo = Path(__file__).resolve().parent.parent
            result = subprocess.run(
                [sys.executable, str(repo / "paradisio_app" / "build.py")],
                env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0, "malformed build date was accepted")
            self.assertIn("PARADISIO_BUILD_DATE", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
