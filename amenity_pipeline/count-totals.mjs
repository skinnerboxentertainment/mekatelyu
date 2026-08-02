import { readFileSync } from "node:fs";

// Attributes (about run)
const about = readFileSync("output-about/amenities.jsonl", "utf8")
  .trim()
  .split("\n")
  .filter(Boolean)
  .map((l) => JSON.parse(l));
const aboutLatest = new Map();
for (const r of about) {
  const cur = aboutLatest.get(r.listingId);
  if (!cur || r.capturedAt >= cur.capturedAt) aboutLatest.set(r.listingId, r);
}
const withAttrs = [...aboutLatest.values()].filter((r) => r.attributeCount > 0);
const attrTotal = withAttrs.reduce((s, r) => s + r.attributeCount, 0);
const attrGroups = new Set();
for (const r of withAttrs) for (const g of r.attributes || []) attrGroups.add(g.group);
console.log("=== ATTRIBUTES (about run) ===");
console.log("records with attributes:", withAttrs.length);
console.log("total attribute entries:", attrTotal);
console.log("distinct group names:", attrGroups.size);

// Amenities (verified file consumed by the site)
const v = JSON.parse(readFileSync("../paradisio_app/data/verified_amenities.json", "utf8"));
let amenRecords = 0, amenTotal = 0;
for (const rec of Object.values(v)) {
  if (rec.availableNames && rec.availableNames.length) {
    amenRecords++;
    amenTotal += rec.availableNames.length;
  }
}
console.log("\n=== AMENITIES (verified, in site) ===");
console.log("records with amenities:", amenRecords);
console.log("total amenity entries:", amenTotal);

// Combined coverage across 737/738
console.log("\n=== COVERAGE ===");
console.log("with amenities:", amenRecords);
console.log("with attributes:", withAttrs.length);
const both = new Set();
for (const r of withAttrs) both.add(r.listingId);
for (const cid of Object.keys(v)) {
  // need listingId -> but verified file is keyed by cid; count overlap by cid via about googleCid
}
const aboutCids = new Set(withAttrs.map((r) => r.googleCid));
const amenCids = new Set(Object.keys(v));
const overlap = [...amenCids].filter((c) => aboutCids.has(c)).length;
console.log("records with BOTH amenities and attributes:", overlap);
