import { describe, expect, it } from "vitest";
import { parseAmenities } from "../src/parse.js";

function snapshot(imgs: string[]): string {
  return [
    "application",
    `heading "Awa Beach Boutique Hotel"`,
    'banner "Top bar"',
    ...imgs.map((img) => `- img "${img}"`),
  ].join("\n");
}

describe("parseAmenities", () => {
  it("parses an available amenity", () => {
    const { amenities } = parseAmenities(snapshot(["Free Wi-Fi available"]));
    expect(amenities).toEqual([
      { key: "free_wifi", name: "Free Wi-Fi", available: true },
    ]);
  });

  it("parses an unavailable amenity", () => {
    const { amenities } = parseAmenities(snapshot(["Pool unavailable"]));
    expect(amenities).toEqual([
      { key: "pool", name: "Pool", available: false },
    ]);
  });

  it("never turns unavailable into available", () => {
    const { amenities } = parseAmenities(snapshot(["Pool unavailable"]));
    expect(amenities[0]?.available).toBe(false);
    // The substring "available" must not falsely match inside "unavailable".
    const { amenities: noMatch } = parseAmenities(snapshot(["Free Wi-Fi unavailable"]));
    expect(noMatch[0]?.available).toBe(false);
  });

  it("handles Unicode names", () => {
    const { amenities } = parseAmenities(snapshot(["Café y té available"]));
    // Accented chars survive normalization; spaces become underscores.
    expect(amenities[0]?.key).toBe("café_y_té");
    expect(amenities[0]?.available).toBe(true);
  });
  it("deduplicates identical states", () => {
    const { amenities, duplicates } = parseAmenities(
      snapshot(["Free Wi-Fi available", "Free Wi-Fi available"]),
    );
    expect(duplicates).toEqual(["free_wifi"]);
    expect(amenities).toHaveLength(1);
    expect(amenities[0]?.available).toBe(true);
  });

  it("flags conflicting states without choosing one", () => {
    const { amenities, conflicts } = parseAmenities(
      snapshot(["Pool available", "Pool unavailable"]),
    );
    expect(conflicts).toEqual([{ key: "pool", states: [true, false] }]);
    expect(amenities[0]?.available).toBeNull();
  });

  it("returns empty for an empty snapshot", () => {
    const { amenities } = parseAmenities("");
    expect(amenities).toEqual([]);
  });

  it("returns empty for expanded snapshot with no amenity labels", () => {
    const { amenities } = parseAmenities(
      ["application", 'button "View fewer amenities"', 'link "Directions"'].join("\n"),
    );
    expect(amenities).toEqual([]);
  });

  it("handles hyphens and punctuation in names", () => {
    const { amenities } = parseAmenities(snapshot(["Air-conditioned available"]));
    expect(amenities[0]?.key).toBe("air_conditioned");
    expect(amenities[0]?.available).toBe(true);
  });

  it("handles ampersands and quotes", () => {
    const { amenities } = parseAmenities(snapshot(["Bikes & breakfast available"]));
    expect(amenities[0]?.key).toBe("bikes_and_breakfast");

    const quoted = parseAmenities(snapshot(['Pool \\"shallow\\" unavailable']));
    expect(quoted.amenities[0]?.name).toBe('Pool "shallow"');
    expect(quoted.amenities[0]?.available).toBe(false);
  });

  it("normalizes free wifi, free breakfast, pet-friendly, business center", () => {
    const { amenities } = parseAmenities(
      snapshot([
        "Free Wi-Fi available",
        "Free breakfast available",
        "Pet-friendly available",
        "Business center unavailable",
      ]),
    );
    const keys = amenities.map((a) => a.key).sort();
    expect(keys).toEqual([
      "business_center",
      "free_breakfast",
      "free_wifi",
      "pet_friendly",
    ]);
  });
});
