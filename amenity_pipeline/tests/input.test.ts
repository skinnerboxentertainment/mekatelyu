import { describe, expect, it } from "vitest";
import { readListings, parseListing } from "../src/input.js";

describe("readListings", () => {
  it("reads a JSON array", () => {
    const listings = readListings(
      JSON.stringify([
        { listingId: "a", name: "Awa", googleCid: "123" },
        { listingId: "b", name: "Pool Place", googleCid: "456" },
      ]),
    );
    expect(listings).toHaveLength(2);
    expect(listings[0]).toEqual({ listingId: "a", name: "Awa", googleCid: "123" });
  });

  it("reads JSONL", () => {
    const listings = readListings(
      ['{"listingId":"a","name":"Awa","googleCid":"123"}', '{"listingId":"b","name":"P","googleCid":"456"}'].join("\n"),
    );
    expect(listings).toHaveLength(2);
  });

  it("rejects empty input", () => {
    expect(() => readListings("   ")).toThrow("Input is empty");
  });

  it("rejects missing fields", () => {
    expect(() => parseListing({ name: "X", googleCid: "1" })).toThrow("listingId");
    expect(() => parseListing({ listingId: "a", googleCid: "1" })).toThrow("name");
    expect(() => parseListing({ listingId: "a", name: "X" })).toThrow("googleCid");
  });

  it("rejects malformed CIDs", () => {
    expect(() => parseListing({ listingId: "a", name: "X", googleCid: "" })).toThrow("googleCid");
    expect(() => parseListing({ listingId: "a", name: "X", googleCid: "abc" })).toThrow("malformed");
  });

  it("treats large CIDs as strings", () => {
    const listing = parseListing({
      listingId: "a",
      name: "X",
      googleCid: "5579537716284560393",
    });
    expect(listing.googleCid).toBe("5579537716284560393");
  });
});
