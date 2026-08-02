import { describe, expect, it } from "vitest";
import { namesMatch } from "../src/identity.js";

describe("namesMatch", () => {
  it("matches identical names", () => {
    expect(namesMatch("Awa Beach Boutique Hotel", "Awa Beach Boutique Hotel")).toBe(true);
  });

  it("matches case and accent differences", () => {
    expect(namesMatch("Cafe Paradise", "café paradise")).toBe(true);
    expect(namesMatch("Sueño Grande", "SUEÑO GRANDE")).toBe(true);
  });

  it("matches legal suffix differences", () => {
    expect(namesMatch("Paradiso Tours", "Paradiso Tours S.A.")).toBe(true);
    expect(namesMatch("Awa Hotel", "Awa Beach Boutique Hotel LLC")).toBe(true);
  });

  it("matches with the CSV geo suffix stripped", () => {
    expect(
      namesMatch("Banana Azul - Playa Negra, Puerto Viejo, Limón, Costa Rica", "Hotel Banana Azul"),
    ).toBe(true);
    expect(
      namesMatch("Lanna Ban Hotel - Playa Cocles, Puerto Viejo, Limón, Costa Rica", "Lanna Ban Hotel"),
    ).toBe(true);
  });

  it("matches possessive and plural variants", () => {
    expect(namesMatch("Cabinas Mitchaelles", "Cabinas Mitchaelle's")).toBe(true);
    expect(namesMatch("Cabinas Mor", "Cabina Mor")).toBe(true);
  });

  it("matches B&B / Bed and Breakfast variants", () => {
    expect(
      namesMatch("Sueño Grande Bed and Breakfast", "Sueño Grande B&B at the Beach"),
    ).toBe(true);
  });

  it("matches when the detected name adds descriptor words", () => {
    expect(namesMatch("Azania Bungalows - Playa Cocles, Puerto Viejo, Limón, Costa Rica", "Azania Bungalows")).toBe(true);
    expect(namesMatch("La Prometida - Playa Negra, Puerto Viejo, Limón, Costa Rica", "La Prometida Hotel")).toBe(true);
  });

  it("rejects materially different names", () => {
    expect(namesMatch("Estrellas Cabinas", "Banco Nacional")).toBe(false);
    expect(namesMatch("Iguana Lodge - Playa Negra, Puerto Viejo, Limón, Costa Rica", "Iguana Villas")).toBe(false);
    expect(namesMatch("Kaya's Place - Playa Negra, Puerto Viejo, Limón, Costa Rica", "Playa Negra Brewing Beachfront Hotel")).toBe(false);
  });

  it("returns true when names are too short to judge", () => {
    expect(namesMatch("Bar", "Café")).toBe(true);
  });

  it("lenient mode accepts descriptor variations for non-lodging", () => {
    expect(namesMatch("Aloe Boutique", "Aloe Tienda de ropa", true)).toBe(true);
    expect(namesMatch("Automotriz Danny", "Taller y lavacar Danny", true)).toBe(true);
    expect(namesMatch("Gigi O Restaurant", "GigiO Restaurant Puerto Viejo", true)).toBe(true);
    expect(namesMatch("Adobe EasyCar Rent a Car", "Adobe Car Rental Costa Rica - Puerto Viejo", true)).toBe(true);
  });

  it("lenient mode still rejects materially different names", () => {
    expect(namesMatch("Estrellas Cabinas", "Banco Nacional", true)).toBe(false);
    expect(namesMatch("Kaya's Place - Playa Negra, Puerto Viejo, Limón, Costa Rica", "Playa Negra Brewing Beachfront Hotel", true)).toBe(false);
  });
});
