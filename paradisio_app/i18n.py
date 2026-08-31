"""Language support for the generated site.

The directory lists every business in a Spanish-speaking town by default, which
is only an honest premise if those businesses can read their own listing. This
module is what makes that true.

Approach: **one static page tree per language**, not client-side switching.

* It works with JavaScript disabled and on a slow connection, which matters for
  the audience this site is for.
* Each page carries a correct ``lang`` attribute, so screen readers pronounce it
  properly rather than reading Spanish with an English voice.
* Search engines get real URLs and ``hreflang`` links instead of one page that
  changes under them.

English stays at the existing paths. This is a hard constraint, not a
preference: 736 QR codes are already printed and stuck to doors around town,
and every one of them points at ``/businesses/<slug>.html``. Other languages are
served from a prefix, so nothing already in the physical world breaks.
"""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "data" / "locales"

# English is the default and therefore un-prefixed; see the module docstring.
DEFAULT_LANGUAGE = "en"

# Ordered for the language switcher.
LANGUAGES = ("en", "es", "de")

LANGUAGE_NAMES = {"en": "English", "es": "Español", "de": "Deutsch"}


class Translator:
    """Looks up UI strings for one language, falling back to English.

    A missing key returns the key itself rather than raising or rendering an
    empty element, so a gap in translation shows up plainly in the page instead
    of silently deleting a control.
    """

    def __init__(self, language: str, strings: dict[str, str], fallback: dict[str, str]):
        self.language = language
        self._strings = strings
        self._fallback = fallback

    @property
    def is_default(self) -> bool:
        return self.language == DEFAULT_LANGUAGE

    @property
    def path_prefix(self) -> str:
        """URL prefix for this language: "" for English, "es/" otherwise."""
        return "" if self.is_default else f"{self.language}/"

    def __call__(self, key: str, **params) -> str:
        text = self._strings.get(key) or self._fallback.get(key) or key
        if params:
            try:
                return text.format(**params)
            except (KeyError, IndexError):
                return text
        return text

    def has(self, key: str) -> bool:
        return key in self._strings or key in self._fallback


def load_strings(language: str) -> dict[str, str]:
    path = LOCALES_DIR / f"{language}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def translator(language: str) -> Translator:
    fallback = load_strings(DEFAULT_LANGUAGE)
    return Translator(language, load_strings(language), fallback)


def available_languages() -> tuple[str, ...]:
    """Languages with a locale file present, in display order."""
    return tuple(lang for lang in LANGUAGES if (LOCALES_DIR / f"{lang}.json").exists())


def alternate_links(page_path: str, base_url: str) -> list[dict[str, str]]:
    """hreflang alternates for one page.

    `page_path` is the path within a language tree, e.g. "businesses/x.html" or
    "" for the home page.
    """
    links = []
    for lang in available_languages():
        prefix = "" if lang == DEFAULT_LANGUAGE else f"{lang}/"
        links.append({"lang": lang, "url": f"{base_url}/{prefix}{page_path}"})
    links.append({"lang": "x-default", "url": f"{base_url}/{page_path}"})
    return links


def language_switch_links(page_path: str, current: str) -> list[dict[str, str]]:
    """Links to the same page in each available language.

    Root-absolute rather than relative. The site is served from the domain root,
    and relative paths would have to account for how deep the current page sits,
    which is exactly the kind of arithmetic that produces a broken link on one
    page type and nowhere else.
    """
    return [
        {
            "lang": lang,
            "name": LANGUAGE_NAMES.get(lang, lang),
            "url": "/" + ("" if lang == DEFAULT_LANGUAGE else f"{lang}/") + page_path,
            "current": lang == current,
        }
        for lang in available_languages()
    ]
