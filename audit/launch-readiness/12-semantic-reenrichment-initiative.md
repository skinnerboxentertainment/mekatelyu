# Semantic Re-enrichment and Discovery Initiative

## Intent

Re-evaluate how all 771 establishments are represented in discovery. A record is not adequately
served merely because it exists: its supported qualities must survive the path from source evidence
to canonical classification, parent discovery groups, specific tags, search terms, filters, and the
generated visitor experience.

This initiative replaces the brittle assumption that one category can represent the full meaning of
an establishment. It preserves a primary type while allowing multiple evidence-backed discovery
groups and specific qualities.

## Local evidence available

- `pv_master_unified.csv`: 771 canonical records, including primary category and descriptions.
- `docs/paradisio_app/data/maps_enrich_v2.json`: 715 CID captures with full visible text and
  structured extraction data.
- `paradisio_app/data/maps_parsed_v3.json`: 715 parsed CID records with fields, confidence,
  inferred categories, and warnings.
- Existing website crawl and enrichment datasets for source coverage and future corroboration.

The first pass uses only these local artifacts. Fresh CID navigation or external source retrieval is
deferred until local evidence coverage and contradictions are measured.

## Classification model

Each establishment receives a versioned semantic record containing:

1. Stable record key and source identifiers.
2. Primary type from the canonical master.
3. One or more broad discovery groups such as Stay, Eat & Drink, Things to Do, Shopping,
   Wellness, Services, Nightlife, and Transport.
4. Specific tags such as Hostel, Bed & Breakfast, Café, Bakery, Surf School, Spa, or Pharmacy.
5. Search synonyms derived from the accepted groups and tags.
6. Provenance and confidence for every inferred assertion.
7. Evidence coverage, conflicts, and a review state.

## Safety boundaries

- Work only in the cloned local launch branch and local release artifact.
- Never delete, merge, exclude, or rename a business automatically.
- Never replace the canonical primary category from unreviewed inference.
- Automatically surface only deterministic parent groups and high-precision explicit type matches.
- Keep weak, conflicting, and multi-meaning evidence in a separate review queue.
- Do not fetch external pages, contact businesses, push, commit, or deploy during the autonomous pass.

## Acceptance criteria

- All 771 master records receive a semantic record and visibility matrix row.
- Every supported primary category maps to at least one visitor-facing discovery group.
- Hostel, hotel, and vacation-rental records all appear under Stay.
- Generated search indexes accepted tags and synonyms, not only name/category/description.
- Every accepted inferred tag includes source provenance and deterministic rule identity.
- Orphaned, conflicting, and evidence-poor records are reported rather than silently guessed.
- Unit tests protect group membership, tag derivation, search visibility, and no-record-loss rules.
- The reduced release continues to contain 771 profiles and 771 establishment-specific QR codes.

## Authority tail

- Review ambiguous semantic classifications and proposed primary-category changes.
- Approve any record merge, exclusion, or canonical category rewrite.
- Approve a fresh rate-limited CID/source sweep for records whose local evidence is inadequate.
- Approve commit, push, CI execution, deployment, and production verification.

## Status

Completed locally on 2026-07-20 after owner authorization. All 23 initially flagged taxonomy
decisions were resolved through 19 corrections and four documented retentions; the unresolved queue
is zero. Implementation and results are recorded in the audit log, change log, verification register,
and generated taxonomy evidence directory.
