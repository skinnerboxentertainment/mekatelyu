"""Compare two HTML documents for semantic equivalence, ignoring formatting.

The golden manifest compares bytes, which is the right oracle for a change that
should alter nothing. It is the wrong oracle for moving markup into a template
engine: indentation and line breaks shift even when the document does not.

This module supplies the oracle for that migration. Two documents are equivalent
when they have the same element tree, the same attributes on each element, and
the same text once runs of whitespace are collapsed. Everything that determines
what a reader sees, or where a link goes, is compared exactly; only formatting
is forgiven.

Used by the template-migration tests, and runnable directly:

    python scripts/html_equivalence.py before.html after.html
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# Tags that never have a closing tag; the parser must not expect one.
VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})


@dataclass
class Node:
    tag: str
    attrs: tuple[tuple[str, str], ...]
    children: list = field(default_factory=list)
    text: str = ""

    def signature(self) -> str:
        rendered = " ".join(f'{k}="{v}"' for k, v in self.attrs)
        return f"<{self.tag}{' ' + rendered if rendered else ''}>"


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", ())
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        # Attribute order is not meaningful in HTML, so sort for comparison.
        # Class lists are order-sensitive to nobody but are compared as written,
        # because a reordered class list is still worth noticing in a refactor.
        node = Node(tag, tuple(sorted((k, v if v is not None else "") for k, v in attrs)))
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, tuple(sorted((k, v if v is not None else "") for k, v in attrs)))
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        collapsed = re.sub(r"\s+", " ", data)
        if collapsed.strip():
            self.stack[-1].text += collapsed


def parse(markup: str) -> Node:
    builder = _TreeBuilder()
    builder.feed(markup)
    builder.close()
    return builder.root


def _walk(node: Node, path: str, out: list[tuple[str, str, str]]) -> None:
    here = f"{path}/{node.tag}"
    out.append((here, node.signature(), node.text.strip()))
    counts: dict[str, int] = {}
    for child in node.children:
        counts[child.tag] = counts.get(child.tag, 0) + 1
        _walk(child, f"{here}[{child.tag}:{counts[child.tag]}]", out)


def flatten(markup: str) -> list[tuple[str, str, str]]:
    flat: list[tuple[str, str, str]] = []
    _walk(parse(markup), "", flat)
    return flat


def differences(before: str, after: str, limit: int = 12) -> list[str]:
    """Return human-readable differences; empty means the documents match."""
    left, right = flatten(before), flatten(after)
    problems: list[str] = []

    if len(left) != len(right):
        problems.append(f"element count differs: {len(left)} vs {len(right)}")

    for index in range(min(len(left), len(right))):
        lpath, lsig, ltext = left[index]
        rpath, rsig, rtext = right[index]
        if lsig != rsig:
            problems.append(f"element {index} at {lpath}:\n      before: {lsig}\n      after:  {rsig}")
        elif ltext != rtext:
            problems.append(
                f"text at {lpath}:\n      before: {ltext[:120]!r}\n      after:  {rtext[:120]!r}"
            )
        if len(problems) >= limit:
            problems.append("... further differences suppressed")
            break

    if len(left) != len(right) and len(problems) < limit:
        extra = left[len(right):] if len(left) > len(right) else right[len(left):]
        side = "only before" if len(left) > len(right) else "only after"
        for path, sig, _ in extra[:5]:
            problems.append(f"{side}: {sig} at {path}")

    return problems


def equivalent(before: str, after: str) -> bool:
    return not differences(before, after)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    before = Path(sys.argv[1]).read_text(encoding="utf-8")
    after = Path(sys.argv[2]).read_text(encoding="utf-8")
    problems = differences(before, after)
    if not problems:
        print("documents are semantically equivalent")
        return 0
    print(f"{len(problems)} difference(s):")
    for problem in problems:
        print("   " + problem)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
