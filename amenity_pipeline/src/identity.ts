/**
 * Conservative normalized similarity check for place identity.
 *
 * We compare the input name with the detected Google place name. The check is
 * deliberately lenient: legitimate punctuation, accents, capitalization, legal
 * entity suffixes, possessive forms, plurals, and area/geo suffixes should not
 * fail. Only a materially different name should produce a mismatch.
 *
 * Our canonical dataset stores many business names with a trailing geo suffix
 * such as " - Playa Negra, Puerto Viejo, Limón, Costa Rica". That suffix is
 * stripped before comparison so it cannot pollute token overlap.
 */

const LEGAL_SUFFIXES = new Set([
  "llc",
  "llp",
  "inc",
  "incorported",
  "incorporated",
  "ltd",
  "limited",
  "s.a",
  "sa",
  "s.r.l",
  "srl",
  "c.a",
  "ca",
  "corp",
  "corporation",
]);

const STOPWORDS = new Set([
  "a",
  "an",
  "and",
  "at",
  "the",
  "of",
  "to",
  "in",
  "on",
  "for",
  "de",
  "del",
  "la",
  "las",
  "el",
  "los",
  "y",
  "e",
  "s",
]);

/** Strip a trailing " - Area, Town, Province, Costa Rica" style geo suffix. */
function stripGeoAffix(s: string): string {
  return s.replace(/\s*[-–—]\s*.+,\s*Costa Rica\s*$/i, "").trim();
}

/** Light singularization: drop a trailing "s" from common plural nouns. */
function singularize(token: string): string {
  if (
    token.length > 3 &&
    token.endsWith("s") &&
    !/(ss|us|is|os)$/.test(token)
  ) {
    return token.slice(0, -1);
  }
  return token;
}

function normalizeForCompare(s: string): string[] {
  const cleaned = stripGeoAffix(s)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "") // strip accents
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/\bb\s+(?:and\s+)?b\b/g, " bed breakfast ") // b&b / b and b
    .replace(/['’]/g, ""); // drop possessive apostrophes: mitchaelle's -> mitchaelle

  return cleaned
    .split(/[^a-z0-9]+/)
    .map((w) => w.trim())
    .filter((w) => w.length > 0)
    .map(singularize)
    .filter((w) => !LEGAL_SUFFIXES.has(w) && !STOPWORDS.has(w));
}

/**
 * Returns true when the detected name is plausibly the same place.
 *
 * Match rules (any of):
 *  - Jaccard overlap of significant tokens >= 0.4 with at least one shared token
 *  - the smaller token set is >= 66% contained in the larger (handles
 *    extra descriptor words on either side)
 *  - in lenient mode: at least one strong token agrees (non-lodging names are
 *    short and the detected name often adds Spanish descriptors, e.g.
 *    "Aloe Boutique" → "Aloe Tienda de ropa"; matching the brand token is enough)
 */
export function namesMatch(
  inputName: string,
  detectedName: string,
  lenient = false,
): boolean {
  const tokensA = normalizeForCompare(inputName);
  const tokensB = normalizeForCompare(detectedName);
  if (tokensA.length === 0 || tokensB.length === 0) return true;

  const setA = new Set(tokensA);
  const setB = new Set(tokensB);

  const intersection = [...setA].filter((t) => setB.has(t)).length;
  const union = new Set([...tokensA, ...tokensB]).size;
  const overlap = intersection / union;

  const smaller = Math.min(tokensA.length, tokensB.length);
  const containment = smaller > 0 ? intersection / smaller : 0;

  // A single significant token on either side is too little to judge on.
  if (smaller <= 1) return true;

  if (lenient && intersection >= 1) return true;

  return (overlap >= 0.4 && intersection >= 1) || containment >= 0.66;
}
