export type Listing = {
  listingId: string;
  name: string;
  googleCid: string;
  category?: string;
  area?: string;
};

/**
 * Read listings from JSON or JSONL.
 *
 * A JSON array of objects is supported, as is a JSONL stream (one object per
 * line). Entries may carry extra fields; only `listingId`, `name`, and
 * `googleCid` are required.
 */
export function readListings(input: string): Listing[] {
  const text = input.trim();
  if (text.length === 0) throw new Error("Input is empty");

  let records: unknown[];
  if (text.startsWith("[")) {
    records = JSON.parse(text) as unknown[];
  } else {
    records = text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .map((line) => JSON.parse(line));
  }

  return records.map((raw, index) => parseListing(raw, index));
}

export function parseListing(raw: unknown, index?: number): Listing {
  if (typeof raw !== "object" || raw === null) {
    throw new Error(`Record ${index ?? "?"} is not an object`);
  }
  const rec = raw as Record<string, unknown>;
  const { listingId, name, googleCid } = rec;

  if (typeof listingId !== "string" || listingId.length === 0) {
    throw new Error(`Record ${index ?? "?"} missing valid listingId`);
  }
  if (typeof name !== "string" || name.length === 0) {
    throw new Error(`Record ${index ?? "?"} missing valid name`);
  }
  if (typeof googleCid !== "string" || googleCid.trim().length === 0) {
    throw new Error(`Record ${index ?? "?"} missing valid googleCid`);
  }
  // CIDs are treated as strings; reject anything non-numeric/blank.
  if (!/^\d+$/.test(googleCid.trim())) {
    throw new Error(`Record ${index ?? "?"} malformed googleCid: ${googleCid}`);
  }

  return {
    listingId,
    name: name.trim(),
    googleCid: googleCid.trim(),
    category: typeof rec.category === "string" ? rec.category : undefined,
    area: typeof rec.area === "string" ? rec.area : undefined,
  };
}
