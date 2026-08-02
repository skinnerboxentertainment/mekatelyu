import { describe, expect, it } from "vitest";
import { buildMetadataForTest } from "../src/extract.js";

const pageUrl = "https://www.google.com/maps?cid=123&hl=en";

describe("page metadata detection", () => {
  it("detects limited view banner as metadata (not a failure)", () => {
    const md = buildMetadataForTest(
      pageUrl,
      'text: You\'re seeing a limited view of Google Maps.',
    );
    expect(md.limitedView).toBe(true);
  });

  it("detects booking UI as metadata (not a failure)", () => {
    const md = buildMetadataForTest(pageUrl, 'heading "Pricing and availability"');
    expect(md.hasBookingUi).toBe(true);
  });

  it("normal lodging page has tabs and information region", () => {
    const md = buildMetadataForTest(
      pageUrl,
      [
        'tab "Overview of Awa" [selected]',
        'tab "About Awa"',
        'region "Information for Awa"',
      ].join("\n"),
    );
    expect(md.hasOverviewTab).toBe(true);
    expect(md.hasAboutTab).toBe(true);
    expect(md.hasInformationRegion).toBe(true);
    expect(md.limitedView).toBe(false);
    expect(md.hasBookingUi).toBe(false);
  });

  it("a healthy page can coexist with booking UI and limited view", () => {
    // Codex finding: success pages contain booking markers AND limited view.
    const md = buildMetadataForTest(
      pageUrl,
      [
        'heading "Pricing and availability"',
        'button "Check availability"',
        'img "Free Wi-Fi available": Free Wi-Fi',
        'text: You\'re seeing a limited view of Google Maps.',
      ].join("\n"),
    );
    expect(md.hasBookingUi).toBe(true);
    expect(md.limitedView).toBe(true);
    expect(md.amenityPresentation).toBe("inline");
  });
});
