import { parseArgs } from "node:util";
import { mkdir } from "node:fs/promises";
import { MapsBrowser, processListing, EXTRACTOR_VERSION } from "./extract.js";
import type { Listing } from "./input.js";
import { runBatch } from "./runner.js";
import { EvidenceWriter } from "./evidence.js";
import { notifyCompletion } from "./status.js";

function usage(): void {
  console.log(`
Google Maps amenity extraction pipeline (${EXTRACTOR_VERSION})

Usage:
  npm run amenities:one -- --cid <cid> [--name <name>] [--out <dir>] [--headed]
  npm run amenities:batch -- --input <file> [--out <dir>] [--limit <n>] [--concurrency <n>] [--headed]

Options:
  --cid          Google Maps CID to smoke-test (string).
  --name         Source listing name for identity check (default "Test Listing").
  --category     Source category (default "hotel").
  --mode         "amenities" (default), "about" (non-lodging attributes), or "hours".
  --input        Path to JSON or JSONL listings file.
  --out          Output directory (default "./output").
  --limit        Process at most N records from the input (dry-run option).
  --concurrency  Number of parallel pages (default 1).
  --headed       Run with a visible browser window.
  --jitter       Base seconds between records (default 2; add +50% random).
  --profile      Path to a persistent browser profile dir (signed-in session).
                 Required for about mode; runs headed. Sign in once with
                 "npx tsx scripts/signin.ts <dir>" first.

Output:
  <out>/amenities.jsonl        One result JSON per listing.
  <out>/evidence/<id>.aria.yml ARIA snapshot per listing.
  <out>/checkpoint.json        Resumability state.
`);
}

export async function main(argv: string[]): Promise<number> {
  const { values, positionals } = parseArgs({
    args: argv,
    options: {
      cid: { type: "string" },
      name: { type: "string" },
      category: { type: "string" },
      mode: { type: "string" },
      input: { type: "string" },
      out: { type: "string", default: "./output" },
      limit: { type: "string" },
      concurrency: { type: "string" },
      headed: { type: "boolean", default: false },
      jitter: { type: "string" },
      profile: { type: "string" },
    },
    allowPositionals: true,
  });

  const command = positionals[0];

  if (!command || (command !== "one" && command !== "batch")) {
    usage();
    return 1;
  }

  const outDir = values.out;
  await mkdir(outDir, { recursive: true });
  const headless = !values.headed;

  if (command === "one") {
    const cid = values.cid;
    if (!cid) {
      console.error("Missing --cid");
      usage();
      return 1;
    }
    return runOne(
      cid,
      values.name ?? "Test Listing",
      values.category ?? "hotel",
      values.mode ?? "amenities",
      outDir,
      headless,
      values.profile,
    );
  }

  const inputPath = values.input;
  if (!inputPath) {
    console.error("Missing --input");
    usage();
    return 1;
  }
  const limit = values.limit ? parseInt(values.limit, 10) : undefined;
  const concurrency = values.concurrency ? parseInt(values.concurrency, 10) : 1;
  const jitterBase = values.jitter ? parseInt(values.jitter, 10) : undefined;

  const stats = await runBatch({
    inputPath,
    outputDir: outDir,
    limit,
    headless,
    concurrency,
    mode: (values.mode as "amenities" | "about" | "hours" | undefined),
    jitterMs: jitterBase ? [jitterBase * 1000, jitterBase * 1500] : undefined,
    profileDir: values.profile,
    onProgress: () => {}, // runBatch renders + writes status.json itself
  });

  console.log("\n" + JSON.stringify(stats, null, 2));

  const doneMsg =
    `WHAPPIN amenities batch finished · ${stats.succeeded} succeeded, ` +
    `${stats.failed} failed, ${stats.skipped} skipped of ${stats.total}.`;
  if (process.stdout.isTTY) {
    await notifyCompletion("WHAPPIN amenity batch", doneMsg);
  } else {
    console.log(doneMsg);
  }
  return stats.failed > 0 ? 1 : 0;
}

async function runOne(
  cid: string,
  name: string,
  category: string,
  mode: string,
  outDir: string,
  headless: boolean,
  profileDir?: string,
): Promise<number> {
  const listing: Listing = { listingId: "smoke", name, googleCid: cid, category };
  const writer = new EvidenceWriter(outDir);
  await writer.init();

  const browser = new MapsBrowser();
  await browser.start(headless, profileDir);
  try {
    const context = await browser.newContext();
    try {
      const record = await processListing(context, listing, writer.getEvidenceDir(), {
        headless,
        mode: mode as "amenities" | "about" | "hours",
      });
      await writer.appendResult(record);
      console.log(JSON.stringify(record, null, 2));
      return record.status.startsWith("success") ? 0 : 1;
    } finally {
      await context.close().catch(() => {});
    }
  } finally {
    await browser.stop();
  }
}

// Entry point when executed directly (`tsx src/cli.ts one ...`).
if (process.argv[1]?.endsWith("cli.ts")) {
  main(process.argv.slice(2)).then(
    (code) => process.exit(code),
    (err) => {
      console.error(err);
      process.exit(1);
    },
  );
}
