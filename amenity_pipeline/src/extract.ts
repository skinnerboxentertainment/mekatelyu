import { randomUUID } from "node:crypto";
import { chromium, type Browser, type BrowserContext, type Page } from "playwright";
import { namesMatch } from "./identity.js";
import { parseAmenities, type Amenity } from "./parse.js";
import type { Listing } from "./input.js";

export const EXTRACTOR_VERSION = "google-maps-amenities-v2";
export const EXTRACTOR_VERSION_ABOUT = "google-maps-about-attributes-v1";

export type PageStatus =
  | "success_expanded"
  | "success_inline"
  | "success_attributes"
  | "amenities_not_applicable"
  | "amenities_not_exposed"
  | "attributes_not_exposed"
  | "page_inconclusive"
  | "business_closed"
  | "place_identity_mismatch"
  | "place_not_loaded"
  | "consent_required"
  | "captcha_or_traffic_block"
  | "navigation_failed"
  | "extraction_failed";

export type AmenityPresentation =
  | "expanded"
  | "inline"
  | "collapsed"
  | "absent";

export type Completeness = "expanded_complete" | "inline_exposed" | "unknown";

export type PageMetadata = {
  limitedView: boolean;
  hasBookingUi: boolean;
  hasOverviewTab: boolean;
  hasAboutTab: boolean;
  hasInformationRegion: boolean;
  amenityPresentation: AmenityPresentation;
  completeness: Completeness;
};

export type ExtractedRecord = {
  listingId: string;
  sourceName: string;
  category: string;
  detectedGoogleName: string | null;
  googleCid: string;
  requestedUrl: string;
  resolvedUrl: string;
  capturedAt: string;
  status: PageStatus;
  operatingStatus: "open" | "permanently_closed" | "unknown" | null;
  amenitiesExpanded: boolean;
  amenityCount: number;
  amenities: Amenity[];
  attributes: AboutGroup[];
  attributeCount: number;
  metadata: PageMetadata;
  ariaSnapshotPath: string | null;
  screenshotPath: string | null;
  extractorVersion: string;
  error?: string;
  attempts: number;
};

export type ExtractOptions = {
  headless?: boolean;
  minDelayMs?: number;
  /** "amenities" (lodging hotel matrix) or "about" (non-lodging attributes). */
  mode?: "amenities" | "about";
};

export type AboutGroup = {
  group: string;
  attributes: string[];
};

export type AboutAttributes = {
  groups: AboutGroup[];
  /** Total attribute count across all groups. */
  attributeCount: number;
};

export type ExtractedAboutRecord = {
  listingId: string;
  sourceName: string;
  category: string;
  detectedGoogleName: string | null;
  googleCid: string;
  requestedUrl: string;
  resolvedUrl: string;
  capturedAt: string;
  status: PageStatus;
  operatingStatus: "open" | "permanently_closed" | "unknown" | null;
  attributes: AboutGroup[];
  attributeCount: number;
  metadata: PageMetadata;
  ariaSnapshotPath: string | null;
  screenshotPath: string | null;
  extractorVersion: string;
  error?: string;
  attempts: number;
};

/**
 * Parse About-tab attribute groups from an ARIA snapshot.
 *
 * Structure: a `region "About <name>"` containing repeated
 * `- heading "<Group>" [level=2]` followed by `- list: - listitem: <attr>`.
 * Attribute lists are fully expanded in the snapshot (no expander).
 */
export function parseAboutAttributes(snapshot: string): AboutGroup[] {
  const groups: AboutGroup[] = [];
  const lines = snapshot.split("\n");

  let current: AboutGroup | null = null;
  let inList = false;

  for (const line of lines) {
    const trimmed = line.trim();
    const headingMatch = trimmed.match(/^-\s+heading\s+"([^"]+)"\s+\[level=2\]$/);
    if (headingMatch) {
      // "About this data" and similar non-attribute headings are skipped.
      const name = headingMatch[1] ?? "";
      if (name === "About this data" || name === "Pricing and availability") {
        current = null;
        inList = false;
        continue;
      }
      current = { group: name, attributes: [] };
      groups.push(current);
      inList = false;
      continue;
    }

    const listOpenMatch = trimmed.match(/^-\s+list:$/);
    if (listOpenMatch && current) {
      inList = true;
      continue;
    }

    const listItemMatch = trimmed.match(/^-\s+listitem:\s*(.+)$/);
    if (listItemMatch && current && inList) {
      const attr = (listItemMatch[1] ?? "").trim();
      if (attr) current.attributes.push(attr);
      continue;
    }

    // Anything else (button, link, text) ends the current list.
    if (!/^-/.test(trimmed) || /^-\s+(button|link|text|region|img|tab)/.test(trimmed)) {
      inList = false;
    }
  }

  return groups.filter((g) => g.attributes.length > 0);
}

const TRAFFIC_PATTERNS = [
  /unusual traffic/i,
  /captcha/i,
  /prove you are not a robot/i,
  /our systems have detected/i,
];

async function waitForPlacePanel(page: Page, timeoutMs: number): Promise<boolean> {
  try {
    await page.getByRole("heading", { level: 1 }).first().waitFor({
      state: "visible",
      timeout: timeoutMs,
    });
    return true;
  } catch {
    return false;
  }
}

function detectBlocked(pageUrl: string, bodyText: string): PageStatus | null {
  if (TRAFFIC_PATTERNS.some((re) => re.test(pageUrl + " " + bodyText))) {
    return "captcha_or_traffic_block";
  }
  return null;
}

async function extractPlaceName(page: Page): Promise<string | null> {
  try {
    const heading = page.getByRole("heading", { level: 1 }).first();
    const name = await heading.textContent({ timeout: 3000 });
    return name?.trim() || null;
  } catch {
    return null;
  }
}

/** Detect the anonymous "limited view" banner. Metadata only — not a status. */
function detectLimitedView(pageUrl: string, snapshot: string): boolean {
  return /limited view of google maps/i.test(pageUrl + " " + snapshot);
}

/** Detect the presence of ordinary lodging booking widgets. Metadata only. */
function detectBookingUi(snapshot: string): boolean {
  return [
    "Pricing and availability",
    "Compare prices",
    "Check availability",
    "All options",
    "See rooms",
    "per night for",
  ].some((m) => snapshot.toLowerCase().includes(m.toLowerCase()));
}

function detectTab(snapshot: string, name: string): boolean {
  return new RegExp(`tab "${name}(?: of | )`, "i").test(snapshot);
}

function buildMetadata(
  pageUrl: string,
  snapshot: string,
  presentation: AmenityPresentation,
  completeness: Completeness,
): PageMetadata {
  return {
    limitedView: detectLimitedView(pageUrl, snapshot),
    hasBookingUi: detectBookingUi(snapshot),
    hasOverviewTab: detectTab(snapshot, "Overview"),
    hasAboutTab: detectTab(snapshot, "About"),
    hasInformationRegion: /region "Information for /.test(snapshot),
    amenityPresentation: presentation,
    completeness,
  };
}

/** Testable wrapper for metadata detection without a real Page. */
export function buildMetadataForTest(
  pageUrl: string,
  snapshot: string,
  presentation: AmenityPresentation = "inline",
  completeness: Completeness = "inline_exposed",
): PageMetadata {
  return buildMetadata(pageUrl, snapshot, presentation, completeness);
}

export type ExtractResult = {
  status: "success_expanded" | "success_inline";
  expanded: boolean;
  completeness: Completeness;
  ariaSnapshot: string;
  amenities: Amenity[];
  metadata: PageMetadata;
};

/**
 * Extract amenity states from a place panel.
 *
 * Order of operations (critical):
 *  1. Snapshot + parse FIRST — states may already be exposed inline.
 *  2. Use the expander only to reveal more states when present.
 *  3. Accept inline states even when no expander exists (Casa Lucas case).
 *  4. Fall back to the About tab, which can expose inline amenity states the
 *     default (Overview/Prices) view omits.
 *  5. Only if no amenity states at all, classify the absence.
 */
export async function extractAmenitiesFromPage(page: Page): Promise<ExtractResult> {
  const main = page.getByRole("main");

  let snapshot = await main.ariaSnapshot();
  let parsed = parseAmenities(snapshot);

  const fewer = main.getByRole("button", {
    name: "View fewer amenities",
    exact: true,
  });

  if (await fewer.isVisible().catch(() => false)) {
    // Already expanded; states already parsed from the first snapshot.
    if (parsed.amenities.length === 0) {
      throw new NoAmenityStatesError(snapshot);
    }
    return {
      status: "success_expanded",
      expanded: true,
      completeness: "expanded_complete",
      ariaSnapshot: snapshot,
      amenities: parsed.amenities,
      metadata: buildMetadata(page.url(), snapshot, "expanded", "expanded_complete"),
    };
  }

  const more = main.getByRole("button", {
    name: "View more amenities",
    exact: true,
  });

  const moreCount = await more.count();

  if (moreCount === 1 && (await more.isVisible().catch(() => false))) {
    await more.click();
    try {
      await fewer.waitFor({ state: "visible", timeout: 8000 });
    } catch {
      // Expansion attempted but not confirmed; fall through to inline/About.
    }

    snapshot = await main.ariaSnapshot();
    parsed = parseAmenities(snapshot);

    if (parsed.amenities.length === 0) {
      throw new NoAmenityStatesError(snapshot);
    }
    return {
      status: "success_expanded",
      expanded: true,
      completeness: "expanded_complete",
      ariaSnapshot: snapshot,
      amenities: parsed.amenities,
      metadata: buildMetadata(page.url(), snapshot, "expanded", "expanded_complete"),
    };
  }

  // No expander (or ambiguous). If states are already exposed inline, keep them.
  if (parsed.amenities.length > 0) {
    return {
      status: "success_inline",
      expanded: false,
      completeness: "inline_exposed",
      ariaSnapshot: snapshot,
      amenities: parsed.amenities,
      metadata: buildMetadata(page.url(), snapshot, "inline", "inline_exposed"),
    };
  }

  // Fall back to the About tab: it can expose inline states the default view omits.
  const aboutTab = main.getByRole("tab", { name: /About/ }).first();
  const aboutCount = await aboutTab.count().catch(() => 0);
  if (aboutCount === 1 && (await aboutTab.isVisible().catch(() => false))) {
    const currentUrl = page.url();
    await aboutTab.click().catch(() => {});
    await page.waitForTimeout(1500);

    const aboutSnapshot = await main.ariaSnapshot();
    const aboutParsed = parseAmenities(aboutSnapshot);

    if (aboutParsed.amenities.length > 0) {
      return {
        status: "success_inline",
        expanded: false,
        completeness: "inline_exposed",
        ariaSnapshot: aboutSnapshot,
        amenities: aboutParsed.amenities,
        metadata: buildMetadata(currentUrl, aboutSnapshot, "inline", "inline_exposed"),
      };
    }

    // No states on About either — restore the original snapshot for evidence.
    snapshot = await main.ariaSnapshot();
  }

  // No states, no expander, no About fallback. Only now classify the absence.
  throw new AmenitiesNotExposedError(snapshot);
}

export class AmenitiesNotExposedError extends Error {
  constructor(public readonly ariaSnapshot: string) {
    super("Place panel loaded but exposed no amenity states or controls");
  }
}
export class NoAmenityStatesError extends Error {
  constructor(public readonly ariaSnapshot: string) {
    super("No explicit amenity states found");
  }
}

/**
 * Extract About-tab attribute groups from a place panel.
 *
 * Clicks the About tab if present, snapshots, and parses `heading [level=2]`
 * + `list/listitem` attribute groups. Returns the groups and the snapshot used
 * as evidence.
 */
export async function extractAboutAttributesFromPage(page: Page): Promise<{
  attributes: AboutGroup[];
  attributeCount: number;
  ariaSnapshot: string;
  metadata: PageMetadata;
}> {
  const main = page.getByRole("main");

  let snapshot = await main.ariaSnapshot();

  const aboutTab = main.getByRole("tab", { name: /^About/ }).first();
  const aboutCount = await aboutTab.count().catch(() => 0);

  if (aboutCount === 1 && (await aboutTab.isVisible().catch(() => false))) {
    await aboutTab.click().catch(() => {});
    await page.waitForTimeout(2500);
    snapshot = await main.ariaSnapshot();
  }

  const groups = parseAboutAttributes(snapshot);

  if (groups.length === 0) {
    throw new AmenitiesNotExposedError(snapshot);
  }

  const attributeCount = groups.reduce((s, g) => s + g.attributes.length, 0);
  return {
    attributes: groups,
    attributeCount,
    ariaSnapshot: snapshot,
    metadata: buildMetadata(page.url(), snapshot, "absent", "unknown"),
  };
}

export class MapsBrowser {
  private browser: Browser | null = null;
  private persistentContext: BrowserContext | null = null;
  private profileDir: string | null = null;

  /**
   * Start the browser.
   *
   * When `profileDir` is set, a persistent context (user-data-dir) is launched
   * so an authenticated/signed-in profile is reused across records. Otherwise
   * a normal anonymous browser is used with a fresh context per record.
   */
  async start(headless = true, profileDir?: string): Promise<void> {
    this.profileDir = profileDir ?? null;
    if (profileDir) {
      // Signed-in profiles require a HEADED browser: Chrome's headless modes
      // (legacy and new) do not propagate the profile's authenticated Maps
      // session, so the page renders anonymous ("limited view"). Headed is
      // required for the signed-in session to take effect.
      this.persistentContext = await chromium.launchPersistentContext(profileDir, {
        headless: false,
        channel: "chrome",
        ignoreDefaultArgs: ["--enable-automation"],
        args: ["--disable-blink-features=AutomationControlled"],
        viewport: { width: 1400, height: 900 },
        locale: "en-US",
      });
      await this.persistentContext.addInitScript(() => {
        // @ts-expect-error remove automation flag
        delete window.navigator.webdriver;
      });
    } else {
      this.browser = await chromium.launch({ headless });
    }
  }

  async newContext(): Promise<BrowserContext> {
    if (this.persistentContext) return this.persistentContext;
    if (!this.browser) throw new Error("Browser not started");
    return this.browser.newContext({
      viewport: { width: 1400, height: 900 },
      locale: "en-US",
    });
  }

  /** True when running against a shared signed-in persistent profile. */
  isPersistent(): boolean {
    return this.persistentContext !== null;
  }

  async stop(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
    if (this.persistentContext) {
      await this.persistentContext.close();
      this.persistentContext = null;
    }
  }
}

const LODGING = new Set(["hotel", "hostel", "vacation_rental"]);

export function isLodgingCategory(category: string): boolean {
  return LODGING.has(category);
}

/**
 * Process a single listing end-to-end.
 */
export async function processListing(
  context: BrowserContext,
  listing: Listing,
  evidenceDir: string,
  opts: ExtractOptions = {},
): Promise<ExtractedRecord> {
  const mode = opts.mode ?? (isLodgingCategory(listing.category ?? "") ? "amenities" : "about");
  const listingId = listing.listingId;
  const requestedUrl = `https://www.google.com/maps?cid=${encodeURIComponent(
    listing.googleCid,
  )}&hl=en`;

  const base: ExtractedRecord = {
    listingId,
    sourceName: listing.name,
    category: listing.category ?? "",
    detectedGoogleName: null,
    googleCid: listing.googleCid,
    requestedUrl,
    resolvedUrl: requestedUrl,
    capturedAt: new Date().toISOString(),
    status: "page_inconclusive",
    operatingStatus: null,
    amenitiesExpanded: false,
    amenityCount: 0,
    amenities: [],
    attributes: [],
    attributeCount: 0,
    metadata: {
      limitedView: false,
      hasBookingUi: false,
      hasOverviewTab: false,
      hasAboutTab: false,
      hasInformationRegion: false,
      amenityPresentation: "absent",
      completeness: "unknown",
    },
    ariaSnapshotPath: null,
    screenshotPath: null,
    extractorVersion: EXTRACTOR_VERSION,
    attempts: 1,
  };

  // In "amenities" mode, non-lodging categories are out of scope.
  if (mode === "amenities" && listing.category && !isLodgingCategory(listing.category)) {
    base.status = "amenities_not_applicable";
    base.operatingStatus = "unknown";
    return base;
  }

  const page = await context.newPage();
  const record: ExtractedRecord = { ...base, attempts: 1 };

  try {
    await page.goto(requestedUrl, { waitUntil: "domcontentloaded", timeout: 30000 });

    const placeLoaded = await waitForPlacePanel(page, 15000);
    const bodyText = await page.evaluate(() => document.body?.innerText ?? "").catch(() => "");
    const blocked = detectBlocked(page.url(), bodyText);

    record.resolvedUrl = page.url();

    if (blocked) {
      record.status = blocked;
      record.error = "Traffic or CAPTCHA restriction detected";
      return record;
    }

    if (!placeLoaded) {
      const title = await page.title().catch(() => "");
      if (/consent/i.test(title + " " + bodyText.slice(0, 500))) {
        record.status = "consent_required";
        record.error = "Consent screen presented";
      } else {
        record.status = "place_not_loaded";
        record.error = "Place panel did not load";
      }
      await captureFailureEvidence(page, record, evidenceDir);
      return record;
    }

    // Closed-business short-circuit: preserve any surviving data, but never
    // treat a closed listing as "no amenities/attributes".
    const closed = /permanently closed/i.test(bodyText.slice(0, 2000));
    if (closed) {
      record.status = "business_closed";
      record.operatingStatus = "permanently_closed";
    } else {
      record.operatingStatus = "open";
    }

    const detectedGoogleName = await extractPlaceName(page);
    record.detectedGoogleName = detectedGoogleName;

    if (
      detectedGoogleName !== null &&
      !namesMatch(listing.name, detectedGoogleName, mode === "about")
    ) {
      record.status = "place_identity_mismatch";
      record.error = `Detected name "${detectedGoogleName}" does not match "${listing.name}"`;
    }

    try {
      if (mode === "about") {
        const result = await extractAboutAttributesFromPage(page);
        record.attributes = result.attributes;
        record.attributeCount = result.attributeCount;
        record.metadata = result.metadata;

        const ariaPath = await writeEvidence(evidenceDir, listingId, "aria", result.ariaSnapshot);
        record.ariaSnapshotPath = ariaPath;

        if (record.status !== "business_closed" && record.status !== "place_identity_mismatch") {
          record.status = "success_attributes";
        }
      } else {
        const result = await extractAmenitiesFromPage(page);
        record.amenitiesExpanded = result.expanded;
        record.amenities = result.amenities;
        record.amenityCount = result.amenities.length;
        record.metadata = result.metadata;

        const ariaPath = await writeEvidence(evidenceDir, listingId, "aria", result.ariaSnapshot);
        record.ariaSnapshotPath = ariaPath;

        if (record.status !== "business_closed" && record.status !== "place_identity_mismatch") {
          record.status = result.status;
        }
      }
    } catch (err) {
      record.error = err instanceof Error ? err.message : String(err);

      if (record.status === "business_closed") {
        // Closed + nothing extractable → business_closed (already set).
      } else if (err instanceof AmenitiesNotExposedError) {
        record.status = mode === "about" ? "attributes_not_exposed" : "amenities_not_exposed";
        record.metadata = buildMetadata(
          page.url(),
          (err as AmenitiesNotExposedError).ariaSnapshot,
          "absent",
          "unknown",
        );
      } else if (err instanceof NoAmenityStatesError) {
        record.status = mode === "about" ? "attributes_not_exposed" : "amenities_not_exposed";
        record.metadata = buildMetadata(
          page.url(),
          (err as NoAmenityStatesError).ariaSnapshot,
          "absent",
          "unknown",
        );
      } else if (record.status !== "place_identity_mismatch") {
        record.status = "extraction_failed";
      }
      await captureFailureEvidence(page, record, evidenceDir);
    }
  } catch (err) {
    record.status = "navigation_failed";
    record.error = err instanceof Error ? err.message : String(err);
    await captureFailureEvidence(page, record, evidenceDir);
  } finally {
    await page.close().catch(() => {});
    if (opts.minDelayMs) {
      await new Promise((r) => setTimeout(r, opts.minDelayMs));
    }
  }

  return record;
}

async function writeEvidence(
  evidenceDir: string,
  listingId: string,
  kind: string,
  content: string,
): Promise<string> {
  const { mkdir, writeFile } = await import("node:fs/promises");
  const { join } = await import("node:path");
  await mkdir(evidenceDir, { recursive: true });
  const safeId = listingId.replace(/[^a-zA-Z0-9._-]/g, "_");
  const path = join(evidenceDir, `${safeId}.${kind}.yml`);
  await writeFile(path, content, "utf8");
  return path;
}

async function captureFailureEvidence(
  page: Page,
  record: ExtractedRecord,
  evidenceDir: string,
): Promise<void> {
  try {
    const { mkdir, writeFile } = await import("node:fs/promises");
    const { join } = await import("node:path");
    await mkdir(evidenceDir, { recursive: true });
    const safeId = record.listingId.replace(/[^a-zA-Z0-9._-]/g, "_");
    const runId = randomUUID().slice(0, 8);

    const screenshotPath = join(evidenceDir, `${safeId}.${runId}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false }).catch(() => {});
    record.screenshotPath = screenshotPath;

    const ariaSnapshot = await page.getByRole("main").ariaSnapshot().catch(() => "");
    if (ariaSnapshot) {
      const ariaPath = join(evidenceDir, `${safeId}.${runId}.aria.yml`);
      await writeFile(ariaPath, ariaSnapshot, "utf8");
      record.ariaSnapshotPath = ariaPath;
    }
  } catch {
    // Evidence capture is best-effort; never fail the record for it.
  }
}
