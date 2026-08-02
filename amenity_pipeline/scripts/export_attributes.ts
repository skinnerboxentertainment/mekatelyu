import { readFile, writeFile } from "node:fs/promises";

/**
 * Export About-attribute results to a reviewable JSON file.
 *
 * Reads the pipeline results JSONL (records with `attributes` groups) and
 * writes one entry per listing, keeping the latest record per listingId.
 * Designed for human review before any site integration.
 *
 * Usage:
 *   npx tsx scripts/export_attributes.ts <resultsJsonl> <outJson>
 */
const [resultsPath, outPath] = process.argv.slice(2);
if (!resultsPath || !outPath) {
  console.error("usage: npx tsx scripts/export_attributes.ts <resultsJsonl> <outJson>");
  process.exit(1);
}

const lines = (await readFile(resultsPath, "utf8"))
  .trim()
  .split("\n")
  .filter(Boolean);
const latest = new Map<string, Record<string, unknown>>();
for (const l of lines) {
  const r = JSON.parse(l) as { listingId: string; capturedAt: string };
  const cur = latest.get(r.listingId);
  if (!cur || r.capturedAt >= (cur.capturedAt as string)) latest.set(r.listingId, r);
}

const out: unknown[] = [];
let withData = 0;
for (const r of latest.values()) {
  const groups = (r.attributes as { group: string; attributes: string[] }[]) ?? [];
  const total = groups.reduce((s, g) => s + g.attributes.length, 0);
  if (total > 0) withData += 1;
  out.push({
    listingId: r.listingId,
    sourceName: r.sourceName,
    category: r.category,
    googleCid: r.googleCid,
    status: r.status,
    detectedGoogleName: r.detectedGoogleName,
    capturedAt: r.capturedAt,
    attributeCount: total,
    attributes: groups,
  });
}

await writeFile(outPath, JSON.stringify(out, null, 2), "utf8");
console.log(`exported ${out.length} listings (${withData} with attributes) → ${outPath}`);
