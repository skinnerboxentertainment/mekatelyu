import { mkdir, writeFile, appendFile } from "node:fs/promises";
import { dirname, join } from "node:path";

/**
 * Evidence writer.
 *
 * - Appends one JSON line per listing result as soon as it finishes (atomic
 *   enough via appendFile on the same writer).
 * - Writes the ARIA snapshot for successful records and failure records when
 *   available.
 * - Never writes cookies, authentication data, unrelated page contents, or
 *   browser profile information.
 */

export class EvidenceWriter {
  private readonly resultsFile: string;
  private readonly evidenceDir: string;

  constructor(outputDir: string) {
    this.resultsFile = join(outputDir, "amenities.jsonl");
    this.evidenceDir = join(outputDir, "evidence");
  }

  async init(): Promise<void> {
    await mkdir(dirname(this.resultsFile), { recursive: true });
    await mkdir(this.evidenceDir, { recursive: true });
  }

  getResultsPath(): string {
    return this.resultsFile;
  }

  getEvidenceDir(): string {
    return this.evidenceDir;
  }

  async appendResult(result: unknown): Promise<void> {
    await appendFile(this.resultsFile, JSON.stringify(result) + "\n", "utf8");
  }

  async writeAriaSnapshot(listingId: string, snapshot: string): Promise<string> {
    const safeId = listingId.replace(/[^a-zA-Z0-9._-]/g, "_");
    const path = join(this.evidenceDir, `${safeId}.aria.yml`);
    await writeFile(path, snapshot, "utf8");
    return path;
  }
}
