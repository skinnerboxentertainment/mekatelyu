# Google Maps Amenity Extraction Pipeline

Extracts Google Maps amenity availability for business listings using Playwright
accessibility trees — no computer vision, no API keys.

For every listing with a Google Maps CID it:

1. Opens `https://www.google.com/maps?cid=<cid>&hl=en`.
2. Expands the amenities section ("View more amenities" → "View fewer amenities").
3. Reads the expanded ARIA snapshot (`page.getByRole("main").ariaSnapshot()`).
4. Parses `img` accessible names ending in exactly `available` or `unavailable`.
5. Normalizes names to stable snake_case keys, preserving the original.
6. Writes one JSONL result per listing plus the ARIA snapshot as evidence.

It stops (and reports) rather than evading CAPTCHA, consent, or traffic controls.

## Requirements

- Node.js 20+
- Playwright Chromium: `npx playwright install chromium`

## Install

```powershell
npm install
npx playwright install chromium
```

## Commands

### Smoke test one CID

```powershell
npm run amenities:one -- --cid 5579537716284560393 --name "Awa Beach Boutique Hotel"
```

Optional: `--headed` for a visible browser, `--out <dir>` (default `./output`).

### Batch run

```powershell
npm run amenities:batch -- --input amenities-listings.jsonl --out ./output
```

Optional flags:

| Flag | Meaning |
|---|---|
| `--limit <n>` | Process at most N records (dry-run / limited run) |
| `--concurrency <n>` | Parallel pages (default 1; keep low to be polite) |
| `--headed` | Visible browser |

### Live progress

A long batch gives you three signals so you never have to stare at it:

1. **Terminal progress line** — updates in place on a real terminal:
   `▸ 42/726 (6%) · ✓38 ✗3 ∅7 ⏭1 · elapsed 00:08 · ETA 00:31 · 4.7s/rec · now: Black Bamboo`
   (bucket legend: ✓ extracted · ✗ genuine failure · ∅ no amenity UI on page ·
   ⏭ already completed in a previous run). When piped/non-TTY it falls back to
   one line per record instead.
2. **`output/status.json`** — rewritten after every record. Open a second
   terminal and check it any time without touching the running job:
   ```powershell
   Get-Content output\status.json | ConvertFrom-Json | Select processed,total,succeeded,failed,noAmenities,skipped,etaSeconds
   ```
   `running: false` appears once the batch finishes.
3. **Completion notification** — three beeps plus a Windows toast (BurntToast
   if installed, otherwise a `msg` popup) when the run completes, so you can
   walk away entirely.

### Input format (JSON or JSONL)

```json
{ "listingId": "awa-beach-boutique-hotel", "name": "Awa Beach Boutique Hotel", "googleCid": "5579537716284560393" }
```

CIDs are treated as strings and must be numeric. Empty/malformed CIDs are rejected.

## Output schema

`<out>/amenities.jsonl` — one line per listing:

```json
{
  "listingId": "awa-beach-boutique-hotel",
  "sourceName": "Awa Beach Boutique Hotel",
  "detectedGoogleName": "aWà Beach Hotel",
  "googleCid": "5579537716284560393",
  "requestedUrl": "https://www.google.com/maps?cid=...&hl=en",
  "resolvedUrl": "...",
  "capturedAt": "ISO-8601",
  "status": "success",
  "amenitiesExpanded": true,
  "amenityCount": 16,
  "amenities": [
    { "key": "free_wifi", "name": "Free Wi-Fi", "available": true },
    { "key": "pool", "name": "Pool", "available": false }
  ],
  "ariaSnapshotPath": "output/evidence/<id>.aria.yml",
  "screenshotPath": null,
  "extractorVersion": "google-maps-amenities-v1"
}
```

`available` may be `null` when Google exposes conflicting states for the same
amenity; the record is flagged for review rather than silently resolved.

### Statuses

`success`, `missing_cid`, `place_not_loaded`, `place_identity_mismatch`,
`amenities_not_exposed`, `expansion_failed`, `no_amenity_states_found`,
`consent_required`, `captcha_or_traffic_block`, `navigation_failed`,
`extraction_failed`.

## Outputs

- `<out>/amenities.jsonl` — results (appended as each listing finishes)
- `<out>/evidence/<id>.aria.yml` — ARIA snapshot per listing
- `<out>/evidence/<id>.<run>.png` — screenshots for failed/ambiguous records only
- `<out>/checkpoint.json` — resumability state keyed by extractor version
- `<out>/status.json` — live progress snapshot (rewritten per record)

## Resumability & pacing

- Completed records are skipped on restart (same `extractorVersion`).
- Transient navigation/extraction failures retry a bounded number of times.
- Blocked traffic, CAPTCHA, and missing amenity controls are never retried.
- Default pacing: 1 page at a time with 1.5–4s jitter between records.

## Testing

```powershell
npm test          # 36 unit tests
npm run typecheck
```

Tests cover `available`/`unavailable` parsing, the `unavailable`-contains-
`available` trap, Unicode, duplicates, conflicting states, empty snapshots,
normalization, and evidence writing.

## Security / privacy

- Never saves cookies, auth data, unrelated page content, or browser profiles.
- No CAPTCHA bypass, proxy rotation, stealth plugins, or login automation.
- Screenshots only for failed or ambiguous records.
- For large-scale collection, review Google Maps' current terms and the official
  Places API before running broad batches.
