import { normalizeAmenityName } from "./normalize.js";

export type Amenity = {
  key: string;
  name: string;
  available: boolean | null;
};

export type ParseResult = {
  amenities: Amenity[];
  duplicates: string[];
  conflicts: Array<{ key: string; states: boolean[] }>;
};

/**
 * Parse an ARIA snapshot string and extract `img` accessible names that end
 * in a complete terminal state token (`available` / `unavailable`).
 *
 * The terminal token is parsed explicitly. We never use
 * `label.includes("available")` because `unavailable` also contains
 * `available`.
 *
 * The regex tolerates quoting variants that Playwright/YAML escaping can
 * produce (double quotes, backslash-escaped quotes, hyphens, Unicode).
 */
const IMG_PATTERN =
  /-\s+img\s+"((?:\\.|[^"\\])*?)\s+(available|unavailable)"/g;

function unescapeToken(raw: string): string {
  return raw.replace(/\\(.)/g, "$1");
}

export function parseAmenities(snapshot: string): ParseResult {
  const matches = [...snapshot.matchAll(IMG_PATTERN)];

  const seen = new Map<
    string,
    { name: string; available: boolean; count: number; states: Set<boolean> }
  >();

  for (const match of matches) {
    const rawName = match[1];
    const state = match[2];
    if (rawName === undefined || state === undefined) continue;

    const name = unescapeToken(rawName).trim();
    if (name.length === 0) continue;

    const key = normalizeAmenityName(name);
    const available = state === "available";

    const existing = seen.get(key);
    if (existing) {
      existing.count += 1;
      existing.states.add(available);
    } else {
      seen.set(key, { name, available, count: 1, states: new Set([available]) });
    }
  }

  const duplicates: string[] = [];
  const conflicts: Array<{ key: string; states: boolean[] }> = [];
  const amenities: Amenity[] = [];

  for (const [key, entry] of seen) {
    if (entry.count > 1) duplicates.push(key);
    let available: boolean | null = entry.available;
    if (entry.states.size > 1) {
      // Conflicting states: do not silently choose one. Mark for review.
      conflicts.push({ key, states: [...entry.states] });
      available = null;
    }
    amenities.push({ key, name: entry.name, available });
  }

  return { amenities, duplicates, conflicts };
}
