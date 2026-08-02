import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { MapsBrowser, processListing, EXTRACTOR_VERSION, EXTRACTOR_VERSION_ABOUT, EXTRACTOR_VERSION_HOURS, isLodgingCategory } from "./extract.js";
import type { Listing } from "./input.js";
import { EvidenceWriter } from "./evidence.js";
import { ProgressTracker, type StatusSnapshot } from "./status.js";

export type BatchOptions = {
  inputPath: string;
  outputDir: string;
  limit?: number;
  headless?: boolean;
  concurrency?: number;
  jitterMs?: [number, number];
  retries?: number;
  /** Extraction mode: "amenities" (default), "about", or "hours". */
  mode?: "amenities" | "about" | "hours";
  /** Persistent browser profile dir (signed-in session) to reuse. */
  profileDir?: string;
  /** Called after every record for live status. */
  onProgress?: (snapshot: StatusSnapshot) => void;
};

export type BatchStats = {
  total: number;
  attempted: number;
  skipped: number;
  succeeded: number;
  failed: number;
  notApplicable: number;
  resultsPath: string;
};

/**
 * Resumable batch runner.
 *
 * - Records completed for the current EXTRACTOR_VERSION in a checkpoint file,
 *   so a restart skips them.
 * - Non-lodging categories short-circuit to `amenities_not_applicable`.
 * - Retries transient navigation/extraction failures a bounded number of times.
 * - Never retries blocked traffic or CAPTCHA.
 * - Results are appended to JSONL as soon as each listing finishes.
 */
export async function runBatch(opts: BatchOptions): Promise<BatchStats> {
  const {
    inputPath,
    outputDir,
    limit,
    headless = true,
    concurrency = 1,
    jitterMs = [1500, 4000],
    retries = 2,
    mode,
    profileDir,
  } = opts;

  const raw = await readFile(inputPath, "utf8");
  const { readListings } = await import("./input.js");
  let listings: Listing[] = readListings(raw);
  if (limit !== undefined && limit > 0) listings = listings.slice(0, limit);

  const checkpointPath = join(outputDir, "checkpoint.json");
  const writer = new EvidenceWriter(outputDir);
  await writer.init();

  const checkpoint = await loadCheckpoint(checkpointPath);
  const retryCounts = new Map<string, number>();
  const extractorVersion =
    mode === "about" ? EXTRACTOR_VERSION_ABOUT : mode === "hours" ? EXTRACTOR_VERSION_HOURS : EXTRACTOR_VERSION;

  const tracker = new ProgressTracker(listings.length, outputDir, extractorVersion);

  const browser = new MapsBrowser();
  await browser.start(headless, profileDir);

  const stats: BatchStats = {
    total: listings.length,
    attempted: 0,
    skipped: 0,
    succeeded: 0,
    failed: 0,
    notApplicable: 0,
    resultsPath: writer.getResultsPath(),
  };

  const randomJitter = () => {
    const [min, max] = jitterMs;
    return Math.floor(min + Math.random() * (max - min));
  };

  const emitProgress = () => {
    const snap = tracker.snapshot();
    opts.onProgress?.(snap);
  };

  try {
    const queue = [...listings];
    while (queue.length > 0) {
      const batch = queue.splice(0, Math.max(1, concurrency));

      const results = await Promise.all(
        batch.map(async (listing) => {
          tracker.setCurrent(listing);
          emitProgress();

          const done = checkpoint[listing.listingId];
          if (done === extractorVersion) {
            await tracker.recordDone(listing, null, "skipped");
            return { listing, skipped: true as const, record: null };
          }

          stats.attempted += 1;
          const context = await browser.newContext();
          try {
            const record = await processListing(context, listing, writer.getEvidenceDir(), {
              headless,
              mode,
              minDelayMs: randomJitter(),
            });
            await writer.appendResult(record);

            if (record.error) tracker.setLastError(record.error);

            const attempts = retryCounts.get(listing.listingId) ?? 1;
            const transient = isTransient(record.status);

            if (transient && attempts < retries) {
              retryCounts.set(listing.listingId, attempts + 1);
              queue.push(listing); // re-queue for a bounded retry
              await tracker.recordDone(listing, null, "retry");
              return { listing, skipped: false as const, record: null };
            }

            if (
              record.status === "success_expanded" ||
              record.status === "success_inline" ||
              record.status === "success_attributes" ||
              record.status === "success_hours" ||
              record.status === "amenities_not_applicable"
            ) {
              checkpoint[listing.listingId] = extractorVersion;
            }

            await tracker.recordDone(listing, record, "done");
            return { listing, skipped: false as const, record };
          } finally {
            // Never close a shared persistent context — it's reused across records.
            if (!browser.isPersistent()) {
              await context.close().catch(() => {});
            }
          }
        }),
      );

      for (const r of results) {
        if (r.skipped) stats.skipped += 1;
        else if (r.record) {
          if (
            r.record.status === "success_expanded" ||
            r.record.status === "success_inline" ||
            r.record.status === "success_attributes" ||
            r.record.status === "success_hours"
          ) {
            stats.succeeded += 1;
          } else if (r.record.status === "amenities_not_applicable") {
            stats.notApplicable += 1;
          } else if (!isNoAmenity(r.record.status) && r.record.status !== "business_closed") {
            stats.failed += 1;
          }
        }
      }

      await saveCheckpoint(checkpointPath, checkpoint);
    }
  } finally {
    await browser.stop();
  }

  await tracker.finish();
  return stats;
}

function isTransient(status: string): boolean {
  return status === "navigation_failed" || status === "extraction_failed";
}

function isNoAmenity(status: string): boolean {
  return (
    status === "amenities_not_exposed" ||
    status === "attributes_not_exposed" ||
    status === "hours_not_exposed" ||
    status === "page_inconclusive"
  );
}

async function loadCheckpoint(path: string): Promise<Record<string, string>> {
  try {
    const text = await readFile(path, "utf8");
    const parsed = JSON.parse(text) as Record<string, string>;
    return typeof parsed === "object" && parsed !== null ? parsed : {};
  } catch {
    return {};
  }
}

async function saveCheckpoint(path: string, checkpoint: Record<string, string>): Promise<void> {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, JSON.stringify(checkpoint, null, 2), "utf8");
}

