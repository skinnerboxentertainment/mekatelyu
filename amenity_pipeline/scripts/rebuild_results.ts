/**
 * Recover amenity results from saved ARIA evidence files.
 *
 * The current Google Maps session serves lodging pages in several layouts. Some
 * layouts expose amenity states inline without any "View more amenities"
 * expander, and prior runs classified those as `amenities_not_exposed` and
 * threw the states away. This script re-reads every saved `.aria.yml`, parses
 * any terminal `available`/`unavailable` states, and rebuilds the results
 * JSONL — recovering records without hitting Google again.
 *
 * Run from amenity_pipeline/:
 *   npx tsx scripts/rebuild_results.ts output/evidence output/amenities.jsonl amenities-listings.jsonl
 */
import { readFile, readdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { parseAmenities } from "../src/parse.js";
import { EXTRACTOR_VERSION, isLodgingCategory } from "../src/extract.js";
import { readListings } from "../src/input.js";

const [evidenceDir, outResults, listingsPath] = process.argv.slice(2);
if (!evidenceDir || !outResults || !listingsPath) {
  console.error(
    "usage: npx tsx scripts/rebuild_results.ts <evidenceDir> <outResults> <listingsJsonl>",
  );
  process.exit(1);
}

const listings = readListings(await readFile(listingsPath, "utf8"));
const byId = new Map(listings.map((l) => [l.listingId, l]));

const files = await readdir(evidenceDir);
const ariaFiles = files.filter((f) => f.endsWith(".aria.yml"));

const recovered = new Map<string, {
  snapshot: string;
  amenities: { key: string; name: string; available: boolean | null }[];
  file: string;
  expanded: boolean;
}>();

for (const f of ariaFiles) {
  const listingId = f.replace(/\.aria\.yml$/, "");
  // Clean success files end `<id>.aria.yml`; failure evidence is `<id>.<run>.aria.yml`.
  const baseId = f.split(".")[0];
  const key = /^[^.]+\.aria\.yml$/.test(f) ? listingId : baseId;

  const listing = byId.get(key);
  if (!listing) continue;

  const snapshot = await readFile(join(evidenceDir, f), "utf8");
  const { amenities } = parseAmenities(snapshot);
  if (amenities.length === 0) continue;

  // Prefer the clean (success-run) snapshot over a failure-run snapshot.
  const expanded = /^[^.]+\.aria\.yml$/.test(f);
  const existing = recovered.get(key);
  if (!existing || (expanded && !existing.expanded)) {
    recovered.set(key, { snapshot, amenities, file: f, expanded });
  }
}

const results: unknown[] = [];
let recoveredCount = 0;

for (const [listingId, data] of recovered) {
  const listing = byId.get(listingId);
  if (!listing) continue;
  recoveredCount += 1;

  const category = listing.category ?? "";
  const lodging = isLodgingCategory(category);
  const closed = /permanently closed/i.test(data.snapshot.slice(0, 4000));

  results.push({
    listingId,
    sourceName: listing.name,
    category,
    detectedGoogleName: null,
    googleCid: listing.googleCid,
    requestedUrl: `https://www.google.com/maps?cid=${encodeURIComponent(listing.googleCid)}&hl=en`,
    resolvedUrl: null,
    capturedAt: new Date().toISOString(),
    status: closed
      ? "business_closed"
      : data.expanded
        ? "success_expanded"
        : "success_inline",
    operatingStatus: closed ? "permanently_closed" : "open",
    amenitiesExpanded: data.expanded,
    amenityCount: data.amenities.length,
    amenities: data.amenities,
    metadata: {
      limitedView: /limited view of google maps/i.test(data.snapshot),
      hasBookingUi: /(Pricing and availability|Compare prices|Check availability|See rooms|per night for)/i.test(
        data.snapshot,
      ),
      hasOverviewTab: /tab "Overview of /i.test(data.snapshot),
      hasAboutTab: /tab "About of /i.test(data.snapshot),
      hasInformationRegion: /region "Information for /.test(data.snapshot),
      amenityPresentation: data.expanded ? "expanded" : "inline",
      completeness: data.expanded ? "expanded_complete" : "inline_exposed",
    },
    ariaSnapshotPath: join("evidence", data.file),
    screenshotPath: null,
    extractorVersion: EXTRACTOR_VERSION,
    recoveredFromEvidence: true,
  });
}

await writeFile(
  outResults,
  results.map((r) => JSON.stringify(r)).join("\n") + "\n",
  "utf8",
);
console.log(
  `recovered ${recoveredCount} listings with parseable amenity states from ${ariaFiles.length} aria files`,
);
