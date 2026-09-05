"""What the published site is allowed to contain, declared rather than forbidden.

The launch audit removed payments, claims, classifieds and an admin dashboard
because they were unfinished and unbounded, and the control left behind was a
list of forbidden strings — `admin.html`, `goatcounter`, `formsubmit` and so on.
That list can only catch surfaces somebody thought to forbid. It says nothing
about a surface nobody anticipated, which is precisely the one that would hurt.

This inverts it. Every surface declares the files it owns, the data it reads,
whether it accepts anything from a visitor, and where that input goes. The
release verifier then requires that every emitted file is claimed by exactly one
surface, so anything undeclared fails the build **by name** rather than passing
because it did not match a keyword.

The practical effect: re-adding a removed surface stops being a risk and becomes
a reviewable act. You cannot ship it without writing down what it does.

Adding a surface means adding an entry here. That is the point — the declaration
is the review.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

# Authorization boundaries, from least to most dangerous.
PUBLIC_READ = "public-read"      # a visitor can only look
PUBLIC_WRITE = "public-write"    # a visitor can send something
OWNER_ONLY = "owner-only"        # requires an authenticated owner — none exist today

BOUNDARIES = frozenset({PUBLIC_READ, PUBLIC_WRITE, OWNER_ONLY})


@dataclass(frozen=True)
class Surface:
    """One published surface and the promises it makes."""

    name: str
    why: str
    paths: tuple[str, ...]
    reads: tuple[str, ...] = ()
    authorization: str = PUBLIC_READ
    # Where a visitor's input lands. Required when the boundary is public-write,
    # and forbidden otherwise, so a surface cannot quietly start accepting input
    # without saying where it goes.
    input_goes_to: str = ""
    notes: str = ""

    def claims(self, relative_path: str) -> bool:
        return any(fnmatch(relative_path, pattern) for pattern in self.paths)


SURFACES: tuple[Surface, ...] = (
    Surface(
        name="directory",
        why="The English directory: the home page, one page per establishment, "
            "and the crawler files that let people find them.",
        paths=(
            "index.html",
            "404.html",
            "robots.txt",
            "sitemap.xml",
            "favicon.ico",
            ".nojekyll",
            "CNAME",
            "businesses/*.html",
        ),
        reads=("pv_master_unified.csv", "semantic_taxonomy.json", "verified_*.json", "organizations.json"),
        authorization=PUBLIC_READ,
        notes="Contact routes are outbound links only. The site never brokers a "
              "message; tapping WhatsApp opens WhatsApp.",
    ),
    Surface(
        name="directory-es",
        why="The Spanish tree. The premise is that every business in town is "
            "listed by default, which is only honest if they can read it.",
        paths=("es/index.html", "es/404.html", "es/businesses/*.html"),
        reads=("locales/es.json",),
        authorization=PUBLIC_READ,
    ),
    Surface(
        name="directory-de",
        why="The German tree, for the other large visitor group.",
        paths=("de/index.html", "de/404.html", "de/businesses/*.html"),
        reads=("locales/de.json",),
        authorization=PUBLIC_READ,
    ),
    Surface(
        name="qr-codes",
        why="One printable QR per establishment, pointing at its own profile. "
            "These are on doors and menus around town, so the URLs they encode "
            "must never change.",
        paths=("qr/*.png",),
        authorization=PUBLIC_READ,
        notes="English URLs are deliberately un-prefixed so previously printed "
              "codes keep resolving.",
    ),
    Surface(
        name="static-assets",
        why="Stylesheets, client scripts, fonts, icons, and the vendored map "
            "library. Self-hosted so the page depends on no third party.",
        paths=("static/*", "static/**/*"),
        authorization=PUBLIC_READ,
    ),
    Surface(
        name="invest",
        why="A single page describing the project and inviting enquiries.",
        paths=("invest/index.html",),
        authorization=PUBLIC_READ,
        notes="Links out to email and a GitHub issue template. Collects nothing "
              "itself — there is no form on the page.",
    ),
)


def find_surface(relative_path: str) -> Surface | None:
    """Which surface claims this file, if any."""
    for surface in SURFACES:
        if surface.claims(relative_path):
            return surface
    return None


def declaration_problems() -> list[str]:
    """Check the declaration is coherent before trusting it to police anything.

    A manifest that contradicts itself is worse than none, because it looks like
    a control while permitting whatever its author mistyped.
    """
    problems: list[str] = []
    seen: set[str] = set()

    for surface in SURFACES:
        if surface.name in seen:
            problems.append(f"duplicate surface name: {surface.name}")
        seen.add(surface.name)

        if surface.authorization not in BOUNDARIES:
            problems.append(
                f"{surface.name}: unknown authorization boundary "
                f"{surface.authorization!r} (expected one of {sorted(BOUNDARIES)})"
            )
        if surface.authorization == PUBLIC_WRITE and not surface.input_goes_to:
            problems.append(
                f"{surface.name}: accepts input from the public but does not say "
                f"where it goes"
            )
        if surface.authorization != PUBLIC_WRITE and surface.input_goes_to:
            problems.append(
                f"{surface.name}: names an input destination but is not declared "
                f"public-write, so the declaration disagrees with itself"
            )
        if not surface.paths:
            problems.append(f"{surface.name}: claims no files")
        if not surface.why.strip():
            problems.append(f"{surface.name}: no stated purpose")

    return problems


def summary() -> str:
    """A short human-readable account of what the release is allowed to be."""
    lines = [f"{len(SURFACES)} declared surfaces:"]
    for surface in SURFACES:
        marker = "" if surface.authorization == PUBLIC_READ else f"  [{surface.authorization}]"
        lines.append(f"  {surface.name}{marker}")
    writable = [s.name for s in SURFACES if s.authorization != PUBLIC_READ]
    lines.append("")
    lines.append(
        f"accepting input from visitors: {', '.join(writable) if writable else 'none'}"
    )
    return "\n".join(lines)
