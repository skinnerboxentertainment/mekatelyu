import { mkdtemp, readFile, readdir, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { EvidenceWriter } from "../src/evidence.js";

const dirs: string[] = [];
async function tempDir(): Promise<string> {
  const dir = await mkdtemp(join(tmpdir(), "amenity-evidence-"));
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

describe("EvidenceWriter", () => {
  it("initializes output directories", async () => {
    const dir = await tempDir();
    const writer = new EvidenceWriter(dir);
    await writer.init();
    const entries = await readdir(dir);
    expect(entries).toContain("evidence");
  });

  it("appends results as JSONL", async () => {
    const dir = await tempDir();
    const writer = new EvidenceWriter(dir);
    await writer.init();
    await writer.appendResult({ listingId: "a", status: "success" });
    await writer.appendResult({ listingId: "b", status: "fail" });

    const lines = (await readFile(writer.getResultsPath(), "utf8")).trim().split("\n");
    expect(lines).toHaveLength(2);
    expect(JSON.parse(lines[0]!).listingId).toBe("a");
  });

  it("writes ARIA snapshots and returns the path", async () => {
    const dir = await tempDir();
    const writer = new EvidenceWriter(dir);
    await writer.init();
    const path = await writer.writeAriaSnapshot("awa-beach-boutique-hotel", "application\n");
    expect(path).toContain("awa-beach-boutique-hotel.aria.yml");
    expect(await readFile(path, "utf8")).toBe("application\n");
  });

  it("sanitizes unsafe listing ids in evidence filenames", async () => {
    const dir = await tempDir();
    const writer = new EvidenceWriter(dir);
    await writer.init();
    const path = await writer.writeAriaSnapshot("bad / name", "x");
    expect(path).toContain("bad___name.aria.yml");
  });
});
