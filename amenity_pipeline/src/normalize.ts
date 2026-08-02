/**
 * Normalize an amenity name to a stable lowercase snake_case key.
 *
 * Rules:
 *  - trim whitespace
 *  - normalize Unicode (NFKC)
 *  - lowercase
 *  - convert `&` to `and`
 *  - replace punctuation and whitespace with underscores
 *  - collapse repeated underscores
 *  - remove leading/trailing underscores
 *
 * No semantic merging happens here. An explicit, version-controlled alias map
 * is the only place where distinct amenities may be merged.
 */

const PUNCT_RE = /[^\p{L}\p{N}]+/gu;

/**
 * Versioned alias map for known orthographic variants that are the *same*
 * amenity. Semantically distinct amenities must never be merged here.
 */
const ALIASES: Record<string, string> = {};

const PRE_SUBSTITUTIONS: Array<[RegExp, string]> = [
  // Wi-Fi / wi-fi -> wifi (single canonical token)
  [/wi\s*[-–—]\s*fi/gi, "wifi"],
];

export function normalizeAmenityName(name: string): string {
  let prepped = name;
  for (const [re, replacement] of PRE_SUBSTITUTIONS) {
    prepped = prepped.replace(re, replacement);
  }

  const key = prepped
    .trim()
    .normalize("NFKC")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(PUNCT_RE, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");

  return ALIASES[key] ?? key;
}
