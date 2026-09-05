"""
Decide, honestly, whether a sweep actually read anything.

A sweep can "succeed" in the sense that the process exits zero while every
single page was a consent wall or a CAPTCHA. Folding that into the evidence
store would refresh capture dates without refreshing any facts — the worst
possible outcome, because it would make stale data look freshly confirmed.

So the pipeline's own exit code is not the signal. This is: it classifies what
the sweep came back with, writes a summary for the pull request, and sets
`usable=true` only when at least one record was genuinely read.

Emits GitHub Actions outputs (`usable`, `summary`) when running in CI, and
prints the same summary either way.

Usage:
  python scripts/sweep_outcome.py --results amenity_pipeline/output-sweep/amenities.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

# Outcomes that mean we reached the place and read it. Kept in step with
# CONCLUSIVE in export_verified_status.py — if they drift, the sweep could
# report success while the exporter stores nothing.
CONCLUSIVE = frozenset({
    # Read cleanly, section present.
    "success_expanded",
    "success_inline",
    "success_attributes",
    "success_hours",
    # The place told us it is shut. That is a reading, not a failure.
    "business_closed",
    "business_permanently_closed",
    "business_temporarily_closed",
    # The page loaded and we identified the place, but the amenities, attributes
    # or hours section was absent or would not parse. Irrelevant here: we are
    # capturing operating status and identity, both of which were read. Measured
    # on 2026-09-05, treating these as failures threw away 6 of 10 usable reads.
    "amenities_not_applicable",
    "amenities_not_exposed",
    "attributes_not_exposed",
    "hours_not_exposed",
    "hours_expansion_failed",
    "hours_parse_failed",
})

# Outcomes that specifically indicate we were turned away rather than that the
# place was odd. These are the ones that would signal a datacenter-IP problem.
BLOCKED = frozenset({
    "consent_required",
    "captcha_or_traffic_block",
    "navigation_failed",
})


def emit(name: str, value: str) -> None:
    """Write a GitHub Actions output, if we are running in one."""
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        if "\n" in value:
            handle.write(f"{name}<<__EOF__\n{value}\n__EOF__\n")
        else:
            handle.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()

    if not args.results.exists():
        summary = "The sweep produced no results file at all — the pipeline did not run."
        print(summary)
        emit("usable", "false")
        emit("summary", summary)
        return 0

    statuses: Counter[str] = Counter()
    for line in args.results.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            statuses[json.loads(line).get("status", "unparseable")] += 1
        except json.JSONDecodeError:
            statuses["unparseable"] += 1

    total = sum(statuses.values())
    read = sum(n for s, n in statuses.items() if s in CONCLUSIVE)
    blocked = sum(n for s, n in statuses.items() if s in BLOCKED)

    lines = [f"Attempted {total} records: {read} read, {blocked} blocked."]
    for status, n in statuses.most_common():
        lines.append(f"  {n:>4}  {status}")
    if blocked and not read:
        lines.append("")
        lines.append("Every attempt was turned away. This is the datacenter-IP failure "
                     "mode: Google is far stricter with CI ranges than with a "
                     "residential connection.")
    summary = "\n".join(lines)

    print(summary)
    emit("usable", "true" if read else "false")
    emit("summary", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
