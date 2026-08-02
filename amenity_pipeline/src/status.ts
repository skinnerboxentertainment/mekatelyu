import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";
import { join } from "node:path";
import { EXTRACTOR_VERSION, type PageStatus } from "./extract.js";
import type { Listing } from "./input.js";

export type StatusCounts = Record<PageStatus, number>;

export type StatusSnapshot = {
  extractorVersion: string;
  startedAt: string;
  updatedAt: string;
  total: number;
  processed: number;
  remaining: number;
  succeeded: number;
  failed: number;
  noAmenities: number;
  notApplicable: number;
  skipped: number;
  statuses: StatusCounts;
  current: string | null;
  lastError: string | null;
  avgSecondsPerRecord: number | null;
  elapsedSeconds: number;
  etaSeconds: number | null;
  running: boolean;
  outputDir: string;
};

const ALL_STATUSES: PageStatus[] = [
  "success_expanded",
  "success_inline",
  "success_attributes",
  "amenities_not_applicable",
  "amenities_not_exposed",
  "attributes_not_exposed",
  "page_inconclusive",
  "business_closed",
  "place_identity_mismatch",
  "place_not_loaded",
  "consent_required",
  "captcha_or_traffic_block",
  "navigation_failed",
  "extraction_failed",
];

const FAIL_STATUSES: PageStatus[] = [
  "place_not_loaded",
  "place_identity_mismatch",
  "consent_required",
  "captcha_or_traffic_block",
  "navigation_failed",
  "extraction_failed",
];

/** Expected outcomes: business reached, but no amenity/attribute data exposed. */
const NO_AMENITY_STATUSES: PageStatus[] = [
  "amenities_not_exposed",
  "attributes_not_exposed",
  "page_inconclusive",
];

/** Out of scope for this extractor version (non-lodging categories). */
const NOT_APPLICABLE_STATUSES: PageStatus[] = ["amenities_not_applicable"];

export class ProgressTracker {
  private counts: StatusCounts = Object.fromEntries(
    ALL_STATUSES.map((s) => [s, 0]),
  ) as StatusCounts;
  private skipped = 0;
  private current: string | null = null;
  private lastError: string | null = null;
  private timings: number[] = [];
  private readonly startedAt = Date.now();
  private lastLineLen = 0;
  private isTty: boolean;

  constructor(
    private readonly total: number,
    private readonly outputDir: string,
    extractorVersion: string = EXTRACTOR_VERSION,
  ) {
    this.version = extractorVersion;
    this.isTty = Boolean(process.stdout.isTTY);
    if (this.isTty) {
      process.stdout.write("\n");
    }
  }

  private version: string;

  /** Called when a record is completed (a terminal result or a retry-requeue). */
  async recordDone(
    listing: Listing,
    record: { status: PageStatus } | null,
    mode: "done" | "skipped" | "retry",
  ): Promise<void> {
    if (mode === "skipped") {
      this.skipped += 1;
    } else if (record) {
      this.counts[record.status] += 1;
      const elapsed = (Date.now() - this.startedAt) / 1000;
      this.timings.push(elapsed);
    }
    await this.emit();
  }

  setCurrent(listing: Listing): void {
    this.current = listing.name;
  }

  setLastError(err: string): void {
    this.lastError = err;
  }

  private avgSecondsPerRecord(): number | null {
    if (this.timings.length < 2) return null;
    const last = this.timings[this.timings.length - 1];
    const first = this.timings[0];
    if (last === undefined || first === undefined) return null;
    const span = last - first;
    const spanSeconds = Math.max(1, span);
    return spanSeconds / Math.max(1, this.timings.length - 1);
  }

  private processed(): number {
    return ALL_STATUSES.reduce((sum, s) => sum + this.counts[s], 0) + this.skipped;
  }

  snapshot(running = true): StatusSnapshot {
    const processed = this.processed();
    const elapsedSeconds = (Date.now() - this.startedAt) / 1000;
    const avg = this.avgSecondsPerRecord();
    const remaining = Math.max(0, this.total - processed);
    const etaSeconds =
      avg !== null && remaining > 0 ? Math.round(remaining * avg) : null;
    const failed = FAIL_STATUSES.reduce((sum, s) => sum + this.counts[s], 0);
    const noAmenities = NO_AMENITY_STATUSES.reduce(
      (sum, s) => sum + this.counts[s],
      0,
    );
    const notApplicable = NOT_APPLICABLE_STATUSES.reduce(
      (sum, s) => sum + this.counts[s],
      0,
    );
    const succeeded =
      this.counts.success_expanded + this.counts.success_inline + this.counts.success_attributes;

    return {
      extractorVersion: this.version,
      startedAt: new Date(this.startedAt).toISOString(),
      updatedAt: new Date().toISOString(),
      total: this.total,
      processed,
      remaining,
      succeeded,
      failed,
      noAmenities,
      notApplicable,
      skipped: this.skipped,
      statuses: { ...this.counts },
      current: this.current,
      lastError: this.lastError,
      avgSecondsPerRecord: avg !== null ? Math.round(avg * 10) / 10 : null,
      elapsedSeconds: Math.round(elapsedSeconds),
      etaSeconds,
      running,
      outputDir: this.outputDir,
    };
  }

  private render(): string {
    const s = this.snapshot();
    const pct = s.total > 0 ? Math.round((s.processed / s.total) * 100) : 0;
    const eta = s.etaSeconds !== null ? fmtDuration(s.etaSeconds) : "--:--";
    const elapsed = fmtDuration(s.elapsedSeconds);
    const now = s.current ?? "-";

    return (
      `▸ ${s.processed}/${s.total} (${pct}%) · ` +
      `✓${s.succeeded} ✗${s.failed} ${s.noAmenities > 0 ? `∅${s.noAmenities} ` : ""}` +
      `${s.notApplicable > 0 ? `−${s.notApplicable} ` : ""}⏭${s.skipped} · ` +
      `elapsed ${elapsed} · ETA ${eta}` +
      (s.avgSecondsPerRecord !== null ? ` · ${s.avgSecondsPerRecord}s/rec` : "") +
      ` · now: ${truncate(now, 28)}`
    );
  }

  async emit(): Promise<void> {
    if (this.isTty) {
      process.stdout.write(`\r\x1b[2K${this.render()}`);
    } else {
      process.stdout.write(`${new Date().toISOString()} ${this.render()}\n`);
    }
    await this.writeStatusFile();
  }

  async writeStatusFile(): Promise<void> {
    try {
      const path = join(this.outputDir, "status.json");
      await writeFile(path, JSON.stringify(this.snapshot(), null, 2), "utf8");
    } catch {
      // Status file is best-effort; never fail the run over it.
    }
  }

  async writeRaw(snapshot: StatusSnapshot): Promise<void> {
    try {
      const path = join(this.outputDir, "status.json");
      await writeFile(path, JSON.stringify(snapshot, null, 2), "utf8");
    } catch {
      // Status file is best-effort; never fail the run over it.
    }
  }

  async finish(): Promise<void> {
    if (this.isTty) {
      process.stdout.write("\r\x1b[2K");
    }
    const s = this.snapshot(false);
    await this.writeRaw(s);
    const line = [
      `Finished: ${s.processed}/${s.total}`,
      `✓${s.succeeded} ✗${s.failed}`,
      ...(s.noAmenities > 0 ? [`∅${s.noAmenities} (no amenities exposed)`] : []),
      ...(s.notApplicable > 0 ? [`−${s.notApplicable} (not applicable)`] : []),
      `⏭${s.skipped}`,
      `elapsed ${fmtDuration(s.elapsedSeconds)}`,
    ].join(" · ");
    process.stdout.write(line + "\n");
  }

  errorRate(): number {
    const processed = this.processed();
    if (processed === 0) return 0;
    return this.snapshot().failed / processed;
  }
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

export function fmtDuration(totalSeconds: number): string {
  const total = Math.max(0, Math.round(totalSeconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

/**
 * Desktop notification on completion/failure.
 * Tries BurntToast (if installed); falls back to a `msg` popup; always beeps.
 * Never throws. Await it before the process exits.
 */
export async function notifyCompletion(title: string, message: string): Promise<void> {
  await beep(3);
  await runToast(title, message);
}

function runToast(title: string, message: string): Promise<void> {
  return new Promise((resolve) => {
    const ps = spawn(
      "powershell",
      [
        "-NoProfile",
        "-Command",
        `$script:args = '${escapeForShell(title)}', '${escapeForShell(message)}'; try { New-BurntToastNotification -Text $script:args -UniqueIdentifier 'whappin-run' | Out-Null; exit 0 } catch { & msg * '${escapeForShell(title + " — " + message)}' }`,
      ],
      { windowsHide: true },
    );
    ps.on("error", () => resolve());
    ps.on("exit", () => resolve());
  });
}

function beep(times: number): Promise<void> {
  return new Promise((resolve) => {
    let done = 0;
    for (let i = 0; i < times; i++) {
      const p = spawn("powershell", ["-NoProfile", "-Command", "[console]::beep(880, 220)"], {
        windowsHide: true,
      });
      p.on("error", () => {
        done += 1;
        if (done === times) resolve();
      });
      p.on("exit", () => {
        done += 1;
        if (done === times) resolve();
      });
      if (i < times - 1) {
        // Space beeps slightly without blocking the loop.
        Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 220);
      }
    }
  });
}

function escapeForShell(s: string): string {
  return s.replace(/'/g, "''").replace(/[^\x20-\x7E]/g, "?");
}
