import { describe, expect, it } from "vitest";
import { normalizeAmenityName } from "../src/normalize.js";

describe("normalizeAmenityName", () => {
  it("trims whitespace", () => {
    expect(normalizeAmenityName("  Free Wi-Fi  ")).toBe("free_wifi");
  });

  it("normalizes unicode", () => {
    expect(normalizeAmenityName("Wifi \u{1F1E8}")).toBe("wifi"); // regional indicator decomposes away
  });

  it("lowercases", () => {
    expect(normalizeAmenityName("BREAKFAST")).toBe("breakfast");
  });

  it("converts ampersand to and", () => {
    expect(normalizeAmenityName("Bikes & Breakfast")).toBe("bikes_and_breakfast");
  });

  it("replaces punctuation and whitespace with underscores", () => {
    expect(normalizeAmenityName("Air-conditioned")).toBe("air_conditioned");
    expect(normalizeAmenityName("Business Center")).toBe("business_center");
  });

  it("collapses repeated underscores", () => {
    expect(normalizeAmenityName("Pet  --  friendly")).toBe("pet_friendly");
  });

  it("removes leading/trailing underscores", () => {
    expect(normalizeAmenityName("--Pool--")).toBe("pool");
  });

  it("handles accented names", () => {
    expect(normalizeAmenityName("Café con Leche")).toBe("café_con_leche");
  });

  it("keeps digits", () => {
    expect(normalizeAmenityName("Wheelchair access 24h")).toBe("wheelchair_access_24h");
  });
});
