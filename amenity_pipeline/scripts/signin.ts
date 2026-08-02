/**
 * Sign in to Google Maps with a persistent profile.
 *
 * Opens a headed browser pointed at Google Maps with the given user-data-dir.
 * Sign in manually (throwaway account), then close the window. The profile
 * (cookies/session) is saved for reuse by the amenity pipeline via --profile.
 *
 * Run from amenity_pipeline/:
 *   npx tsx scripts/signin.ts profiles/throwaway
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";

const profileDir = process.argv[2];
if (!profileDir) {
  console.error("usage: npx tsx scripts/signin.ts <profileDir>");
  process.exit(1);
}

await mkdir(profileDir, { recursive: true });
console.log(`Profile: ${profileDir}`);
console.log("Sign in with a throwaway Google account, then CLOSE this window.");
console.log("(The session is saved on exit.)");

const context = await chromium.launchPersistentContext(profileDir, {
  headless: false,
  channel: "chrome",
  ignoreDefaultArgs: ["--enable-automation"],
  args: ["--disable-blink-features=AutomationControlled"],
  viewport: { width: 1400, height: 900 },
  locale: "en-US",
});
await context.addInitScript(() => {
  // @ts-expect-error remove automation flag
  delete window.navigator.webdriver;
});

const page = await context.newPage();
await page.goto("https://www.google.com/maps?hl=en", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(500);

// Keep the browser open until the user closes the window, then exit cleanly.
page.on("close", async () => {
  console.log("Window closed — profile saved.");
  await context.close().catch(() => {});
  process.exit(0);
});
page.on("crash", async () => {
  console.log("Window crashed — profile saved.");
  await context.close().catch(() => {});
  process.exit(0);
});
process.on("SIGINT", async () => {
  await context.close().catch(() => {});
  process.exit(0);
});
