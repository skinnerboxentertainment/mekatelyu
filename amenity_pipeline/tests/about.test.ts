import { describe, expect, it } from "vitest";
import { parseAboutAttributes } from "../src/extract.js";

describe("parseAboutAttributes", () => {
  it("parses heading + list groups from a restaurant About tab", () => {
    const snapshot = [
      '- main "GigiO Restaurant"',
      '- region "About GigiO Restaurant"',
      '- heading "Service options" [level=2]',
      "- list:",
      "- listitem: Outdoor seating",
      "- listitem: Delivery",
      "- listitem: Dine-in",
      '- heading "Offerings" [level=2]',
      "- list:",
      "- listitem: Alcohol",
      "- listitem: Coffee",
      '- heading "Payments" [level=2]',
      "- list:",
      "- listitem: Credit cards",
    ].join("\n");

    const groups = parseAboutAttributes(snapshot);
    expect(groups).toHaveLength(3);
    expect(groups[0]).toEqual({
      group: "Service options",
      attributes: ["Outdoor seating", "Delivery", "Dine-in"],
    });
    expect(groups[1]).toEqual({ group: "Offerings", attributes: ["Alcohol", "Coffee"] });
    expect(groups[2]).toEqual({ group: "Payments", attributes: ["Credit cards"] });
  });

  it("stops a group at a non-listitem element", () => {
    const snapshot = [
      '- heading "Service options" [level=2]',
      "- list:",
      "- listitem: Dine-in",
      '- button "More info"',
      '- heading "Payments" [level=2]',
      "- list:",
      "- listitem: Cash",
    ].join("\n");
    const groups = parseAboutAttributes(snapshot);
    expect(groups[0]).toEqual({ group: "Service options", attributes: ["Dine-in"] });
    expect(groups[1]).toEqual({ group: "Payments", attributes: ["Cash"] });
  });

  it("ignores non-attribute headings", () => {
    const snapshot = [
      '- heading "About this data" [level=2]',
      "- list:",
      "- listitem: something irrelevant",
      '- heading "Pricing and availability" [level=2]',
      "- list:",
      "- listitem: CRC 100",
    ].join("\n");
    expect(parseAboutAttributes(snapshot)).toEqual([]);
  });

  it("returns empty for a snapshot with no groups", () => {
    const snapshot = ['- main "X"', '- heading "About X" [level=1]'].join("\n");
    expect(parseAboutAttributes(snapshot)).toEqual([]);
  });

  it("drops empty groups", () => {
    const snapshot = [
      '- heading "Service options" [level=2]',
      "- list:",
      "- listitem: Dine-in",
      '- heading "Atmosphere" [level=2]',
      "- list:",
      "- listitem:   ",
    ].join("\n");
    const groups = parseAboutAttributes(snapshot);
    expect(groups).toHaveLength(1);
    expect(groups[0]?.group).toBe("Service options");
  });
});
