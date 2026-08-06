

```text
Build a production-quality Google Maps amenity enrichment pipeline for our business listings.

Objective
---------
For every listing that has a Google Maps CID:

1. Open its Google Maps page using Playwright.
2. Force the interface to English with `hl=en`.
3. Find and activate the “View more amenities” UI control when present.
4. Verify expansion by detecting “View fewer amenities.”
5. Read the expanded accessibility tree using Playwright `ariaSnapshot()`.
6. Extract amenity labels whose accessible names end in exactly:
   - `available`
   - `unavailable`
7. Store normalized amenity records without guessing from visible text, CSS,
   icons, or screenshots.
8. Preserve the ARIA snapshot as extraction evidence.
9. Make the process resumable, rate-limited, auditable, and safe to rerun.

Use Node.js, TypeScript, and the official `playwright` package.

Do not use computer vision for normal extraction. Screenshots may be captured only
for failed or ambiguous records.

Input
-----
Support JSON or JSONL input containing at least:

{
  "listingId": "awa-beach-boutique-hotel",
  "name": "Awa Beach Boutique Hotel",
  "googleCid": "5579537716284560393"
}

Reject empty or malformed CIDs. Treat CIDs as strings because they can exceed
safe integer handling in other languages or storage systems.

Navigation
----------
Construct the canonical lookup URL as:

https://www.google.com/maps?cid=${encodeURIComponent(cid)}&hl=en

Use a normal Playwright browser context. Reuse the browser between records but
create or clean up pages intentionally.

Do not implement CAPTCHA bypassing, proxy rotation, stealth plugins, login
automation, or mechanisms intended to evade Google controls. If Google presents
a CAPTCHA, consent screen, sign-in requirement, or traffic restriction, mark
the record or run as blocked and stop or back off.

After navigation, wait for a concrete page signal rather than relying only on
`networkidle`, because Google Maps is a continuously running application.

Confirm that a place panel loaded. Capture:

- resolved URL
- detected place name
- CID
- extraction timestamp
- page status

Amenity expansion
-----------------
Use accessibility-first locators:

const more = page.getByRole("button", {
  name: "View more amenities",
  exact: true
});

const fewer = page.getByRole("button", {
  name: "View fewer amenities",
  exact: true
});

Behavior:

1. If “View fewer amenities” is visible, the section is already expanded.
2. Otherwise, if exactly one visible “View more amenities” button exists,
   click it.
3. Wait until “View fewer amenities” becomes visible.
4. If neither button exists, classify the record as `amenities_not_exposed`.
5. If multiple matching controls exist, do not pick one positionally. Scope the
   locator to the place’s main panel.
6. Do not treat extraction as complete unless expansion is verified.

ARIA extraction
---------------
After expansion, obtain an ARIA snapshot from the narrowest stable place panel:

const snapshot = await page.getByRole("main").ariaSnapshot();

Parse accessible image names that end in a complete state token:

- `Free Wi-Fi available`
- `Pool unavailable`

Use a parser equivalent to:

const matches = [
  ...snapshot.matchAll(
    /-\s+img\s+"(.+?)\s+(available|unavailable)"/g
  )
];

const amenities = matches.map(([, rawName, state]) => ({
  rawName: rawName.trim(),
  normalizedName: normalizeAmenityName(rawName),
  available: state === "available",
  sourceState: state
}));

Important: never use `label.includes("available")` because `unavailable` also
contains `available`. Parse the terminal state explicitly.

If YAML quoting or Playwright output escaping makes the regex unreliable, parse
the ARIA YAML structurally or isolate each `img` accessible name safely. Add
unit tests covering quotes, hyphens, Unicode, and the `unavailable` substring
case.

Normalization
-------------
Preserve both the original name and a normalized key.

Examples:

"Free Wi-Fi"       -> "free_wifi"
"Free breakfast"   -> "free_breakfast"
"Air-conditioned"  -> "air_conditioned"
"Business center"  -> "business_center"
"Pet-friendly"     -> "pet_friendly"

Normalization must:

- trim whitespace
- normalize Unicode
- lowercase
- convert `&` to `and`
- replace punctuation and whitespace with underscores
- collapse repeated underscores
- remove leading/trailing underscores

Do not merge semantically different amenities unless there is an explicit,
version-controlled alias map.

Output
------
Write one JSONL result per listing as soon as extraction finishes:

{
  "listingId": "awa-beach-boutique-hotel",
  "sourceName": "Awa Beach Boutique Hotel",
  "detectedGoogleName": "aWà Beach Hotel",
  "googleCid": "5579537716284560393",
  "requestedUrl": "https://www.google.com/maps?cid=5579537716284560393&hl=en",
  "resolvedUrl": "...",
  "capturedAt": "ISO-8601 timestamp",
  "status": "success",
  "amenitiesExpanded": true,
  "amenityCount": 16,
  "amenities": [
    {
      "key": "free_wifi",
      "name": "Free Wi-Fi",
      "available": true
    },
    {
      "key": "pool",
      "name": "Pool",
      "available": false
    }
  ],
  "ariaSnapshotPath": "evidence/<listingId>.aria.yml",
  "screenshotPath": null,
  "extractorVersion": "google-maps-amenities-v1"
}

Statuses must include:

- success
- missing_cid
- place_not_loaded
- place_identity_mismatch
- amenities_not_exposed
- expansion_failed
- no_amenity_states_found
- consent_required
- captcha_or_traffic_block
- navigation_failed
- extraction_failed

Evidence and debugging
----------------------
For every successful record, save the relevant ARIA snapshot.

For failures, save:

- ARIA snapshot when available
- screenshot
- resolved URL
- page title
- concise error
- attempt count

Do not save cookies, authentication data, unrelated page contents, or browser
profile information.

Identity checks
---------------
A CID redirect may resolve to an unexpected or merged place. Compare the input
name with the detected Google place name using a conservative normalized
similarity check.

Do not reject legitimate punctuation, accents, capitalization, or common legal
suffix differences. If identity is materially different, store the extracted
data but mark the record `place_identity_mismatch` so it requires review.

Resumability
------------
The job must be restartable:

- Skip records already completed successfully for the same extractor version.
- Retry transient navigation failures a small, bounded number of times.
- Do not endlessly retry blocked traffic, CAPTCHA, or absent amenity controls.
- Append results atomically or use a small SQLite checkpoint database.
- Never lose completed work if the process stops.

Pacing
------
Use low concurrency and conservative pacing. Begin with one page at a time.
Add bounded jitter between records. Back off on 429 responses, traffic
restriction pages, navigation degradation, or repeated timeouts.

Do not add evasion technology. If the site resists automation, stop and report
the condition.

Validation
----------
Add unit tests for:

1. Parsing `available`.
2. Parsing `unavailable`.
3. Ensuring `unavailable` never becomes true.
4. Unicode names.
5. Duplicate amenities.
6. Conflicting states for the same amenity.
7. Empty snapshots.
8. Expanded snapshots with no amenity labels.
9. Name normalization.
10. Resuming after interruption.

For duplicate amenity labels:

- identical states: deduplicate
- conflicting states: mark the record for review; do not silently choose one

Add an integration command that processes exactly one CID:

npm run amenities:one -- --cid 5579537716284560393

Add a batch command:

npm run amenities:batch -- --input listings.jsonl --output amenities.jsonl

Provide a dry-run or limit option:

npm run amenities:batch -- --input listings.jsonl --limit 5

Deliverables
------------
Implement:

- Playwright browser/extractor module
- ARIA amenity parser
- normalization module
- JSON/JSONL input reader
- resumable batch runner
- evidence writer
- structured logging
- unit tests
- one-record smoke test
- README with commands and output schema

Before declaring completion:

1. Run the parser unit tests.
2. Run one smoke extraction against CID `5579537716284560393`.
3. Confirm “View fewer amenities” was detected.
4. Confirm `Pool` is stored as `available: false`.
5. Confirm `Free Wi-Fi` is stored as `available: true`.
6. Show the generated JSON result and evidence paths.
```

A good core extractor should resemble this:

```ts
import type { Page } from "playwright";

export type Amenity = {
  key: string;
  name: string;
  available: boolean;
};

export async function extractAmenities(page: Page): Promise<{
  expanded: boolean;
  ariaSnapshot: string;
  amenities: Amenity[];
}> {
  const main = page.getByRole("main");

  const fewer = main.getByRole("button", {
    name: "View fewer amenities",
    exact: true,
  });

  if (!(await fewer.isVisible().catch(() => false))) {
    const more = main.getByRole("button", {
      name: "View more amenities",
      exact: true,
    });

    const count = await more.count();

    if (count !== 1 || !(await more.isVisible())) {
      throw new Error("Complete amenities section is not exposed");
    }

    await more.click();
    await fewer.waitFor({ state: "visible" });
  }

  const ariaSnapshot = await main.ariaSnapshot();

  const records = [
    ...ariaSnapshot.matchAll(
      /-\s+img\s+"(.+?)\s+(available|unavailable)"/g,
    ),
  ].map(([, name, state]) => ({
    key: normalizeAmenityName(name),
    name: name.trim(),
    available: state === "available",
  }));

  if (records.length === 0) {
    throw new Error("No explicit amenity states found");
  }

  return {
    expanded: true,
    ariaSnapshot,
    amenities: deduplicateAndValidate(records),
  };
}
```

One architectural recommendation: store amenities as rows rather than permanently flattening them into columns.

```text
listing_id | amenity_key     | amenity_name    | available | captured_at
-----------|-----------------|-----------------|-----------|------------
awa        | free_wifi       | Free Wi-Fi      | true      | ...
awa        | pool            | Pool            | false     | ...
```

That accommodates new Google amenity types without requiring a database migration every time. Also preserve the original ARIA snapshot: it gives you an auditable source artifact when the normalization logic evolves.

For large-scale or commercial collection, review Google Maps’ current terms and the official Places API before running the batch broadly. The pipeline should stop when challenged, not attempt to bypass access controls.