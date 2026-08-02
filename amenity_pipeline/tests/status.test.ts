import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { ProgressTracker } from "../src/status.js";

const dirs: string[] = [];
async function tempDir(): Promise<string> {
  const dir = await mkdtemp(join(tmpdir(), "amenity-status-"));
  dirs.push(dir);
  return dir;
}

afterEach(async () => {
  while (dirs.length) {
    const d = dirs.pop();
    if (d) await rmrf(d);
  }
});

async function rmrf(dir: string): Promise<void> {
  const { rm } = await import("node:fs/promises");
  await rm(dir, { recursive: true, force: true });
}

const LISTING = { listingId: "a", name: "Test Place", googleCid: "123" };

describe("ProgressTracker", () => {
  it("tracks successes, failures, and skips", async () => {
    const t = new ProgressTracker(3, await tempDir());
    await t.recordDone(LISTING, { status: "success_expanded" }, "done");
    await t.recordDone(LISTING, { status: "navigation_failed" }, "done");
    await t.recordDone(LISTING, null, "skipped");
    const s = t.snapshot();
    expect(s.processed).toBe(3);
    expect(s.succeeded).toBe(1);
    expect(s.failed).toBe(1);
    expect(s.skipped).toBe(1);
  });

  it("counts amenities_not_exposed separately from failures", async () => {
    const t = new ProgressTracker(1, await tempDir());
    await t.recordDone(LISTING, { status: "amenities_not_exposed" }, "done");
    const s = t.snapshot();
    expect(s.noAmenities).toBe(1);
    expect(s.failed).toBe(0);
    expect(s.succeeded).toBe(0);
  });

  it("writes status.json with running=true while active", async () => {
    const dir = await tempDir();
    const t = new ProgressTracker(1, dir);
    await t.recordDone(LISTING, { status: "success_expanded" }, "done");
    const raw = JSON.parse(await readFile(join(dir, "status.json"), "utf8"));
    expect(raw.running).toBe(true);
    expect(raw.processed).toBe(1);
  });

  it("writes running=false after finish()", async () => {
    const dir = await tempDir();
    const t = new ProgressTracker(1, dir);
    await t.recordDone(LISTING, { status: "success_expanded" }, "done");
    await t.finish();
    const raw = JSON.parse(await readFile(join(dir, "status.json"), "utf8"));
    expect(raw.running).toBe(false);
  });

  it("computes ETA from per-record timing", async () => {
    const t = new ProgressTracker(3, await tempDir());
    await t.recordDone(LISTING, { status: "success_expanded" }, "done");
    await new Promise((r) => setTimeout(r, 30));
    await t.recordDone(LISTING, { status: "success_expanded" }, "done");
    const s = t.snapshot();
    expect(s.avgSecondsPerRecord).not.toBeNull();
    expect(s.etaSeconds).toBeGreaterThan(0);
  });
});

