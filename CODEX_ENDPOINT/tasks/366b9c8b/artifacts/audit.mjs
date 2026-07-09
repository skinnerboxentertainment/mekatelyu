import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const root = path.resolve('../../../..');
const app = path.join(root, 'docs', 'paradisio_app');
const out = process.cwd();
const shotDir = path.join(out, 'screenshots');
await fs.mkdir(shotDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1366, height: 900 }, deviceScaleFactor: 1 });
const page = await context.newPage();
const consoleErrors = [];
const pageErrors = [];
page.on('console', msg => {
  if (['error', 'warning'].includes(msg.type())) consoleErrors.push(`${msg.type()}: ${msg.text()}`);
});
page.on('pageerror', err => pageErrors.push(err.message));

const url = p => pathToFileURL(path.join(app, p)).href;
const countVisible = async (sel) => page.locator(sel).evaluateAll(els => els.filter(el => {
  const s = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
}).length);
const text = async (sel) => (await page.locator(sel).first().textContent().catch(() => '') || '').trim();
const shot = async (name) => {
  const p = path.join(shotDir, name);
  await page.screenshot({ path: p, fullPage: true });
  return path.relative(out, p).replaceAll('\\', '/');
};

const result = { screenshots: [], homepage: {}, business: {}, classifieds: {}, qr: {}, consoleErrors, pageErrors };

await page.goto(url('index.html'), { waitUntil: 'networkidle' });
await page.waitForSelector('.result-card', { timeout: 10000 });
result.homepage.initialCards = await countVisible('.result-card');
result.homepage.initialStats = await text('#stats-line');
result.screenshots.push(await shot('homepage-desktop.png'));
await page.fill('#search', 'cacao');
await page.waitForTimeout(300);
result.homepage.searchCacaoCards = await countVisible('.result-card');
result.homepage.searchCacaoStats = await text('#stats-line');
await page.fill('#search', '');
await page.selectOption('#category-filter', { index: 1 });
await page.waitForTimeout(250);
result.homepage.categoryValue = await page.locator('#category-filter').inputValue();
result.homepage.categoryCards = await countVisible('.result-card');
await page.selectOption('#category-filter', '');
await page.selectOption('#area-filter', { index: 1 });
await page.waitForTimeout(250);
result.homepage.areaValue = await page.locator('#area-filter').inputValue();
result.homepage.areaCards = await countVisible('.result-card');
await page.selectOption('#area-filter', '');
await page.selectOption('#channel-filter', 'whatsapp');
await page.waitForTimeout(250);
result.homepage.channelCards = await countVisible('.result-card');
await page.selectOption('#channel-filter', '');
const beforeLoadMore = await countVisible('.result-card');
const loadMoreButton = page.locator('#load-more button').first();
result.homepage.loadMoreButtonVisible = await loadMoreButton.isVisible().catch(() => false);
if (result.homepage.loadMoreButtonVisible) {
  await loadMoreButton.click();
  await page.waitForTimeout(300);
}
result.homepage.beforeLoadMore = beforeLoadMore;
result.homepage.afterLoadMore = await countVisible('.result-card');
await page.click('#view-map');
await page.waitForTimeout(1500);
result.homepage.mapVisible = await page.locator('#map-container').isVisible();
result.homepage.leafletLoaded = await page.evaluate(() => !!window.L);
result.homepage.markerCount = await page.locator('.leaflet-marker-icon').count();
result.screenshots.push(await shot('homepage-map.png'));

await page.setViewportSize({ width: 375, height: 812 });
await page.goto(url('index.html'), { waitUntil: 'networkidle' });
await page.waitForSelector('.result-card', { timeout: 10000 });
result.screenshots.push(await shot('homepage-mobile.png'));

await page.setViewportSize({ width: 1366, height: 900 });
await page.goto(url('businesses/black-bamboo-puerto-viejo.html'), { waitUntil: 'networkidle' });
await page.waitForSelector('h1', { timeout: 10000 });
await page.waitForTimeout(1200);
result.business.name = await text('h1');
result.business.category = await text('.biz-category');
result.business.rating = await text('.biz-rating');
result.business.badges = await countVisible('.badge');
result.business.scores = await countVisible('.score-bar');
result.business.mapVisible = await page.locator('.biz-map').isVisible();
result.business.leafletLoaded = await page.evaluate(() => !!window.L).catch(() => false);
result.business.markerCount = await page.locator('.leaflet-marker-icon').count();
result.business.qrVisible = await page.locator('.biz-qr img').isVisible();
result.business.claimHref = await page.locator('.claim-link').first().getAttribute('href');
result.business.whatsappHref = await page.locator('.primary-cta').first().getAttribute('href');
result.business.instagramHref = await page.locator('a[data-plausible-channel="Instagram"]').first().getAttribute('href');
result.business.facebookHref = await page.locator('a[data-plausible-channel="Facebook"]').first().getAttribute('href');
result.screenshots.push(await shot('business-black-bamboo-desktop.png'));
await page.setViewportSize({ width: 375, height: 812 });
await page.screenshot({ path: path.join(shotDir, 'business-black-bamboo-mobile.png'), fullPage: true });
result.screenshots.push('screenshots/business-black-bamboo-mobile.png');

await page.setViewportSize({ width: 1366, height: 900 });
await page.goto(url('classifieds/index.html'), { waitUntil: 'networkidle' });
await page.waitForSelector('.cl-card', { timeout: 10000 });
result.classifieds.categories = await countVisible('.cat-link');
result.classifieds.initialCards = await countVisible('.cl-card');
await page.fill('#cl-search', 'surf');
await page.waitForTimeout(300);
result.classifieds.searchSurfCards = await countVisible('.cl-card');
result.classifieds.searchSurfCount = await text('#cl-count');
const firstListingHref = await page.locator('.cl-card').first().getAttribute('href');
result.classifieds.firstListingHref = firstListingHref;
await page.locator('.cl-card').first().click();
await page.waitForLoadState('domcontentloaded');
result.classifieds.detailTitle = await text('h1');
result.classifieds.detailUrl = page.url();
result.screenshots.push(await shot('classifieds-detail.png'));
await page.goto(url('classifieds/index.html'), { waitUntil: 'networkidle' });
result.screenshots.push(await shot('classifieds-index.png'));
await page.setViewportSize({ width: 375, height: 812 });
await page.goto(url('classifieds/index.html'), { waitUntil: 'networkidle' });
result.screenshots.push(await shot('classifieds-mobile.png'));

await page.setViewportSize({ width: 1366, height: 900 });
await page.goto(url('qr/black-bamboo-puerto-viejo.html'), { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2500);
result.qr.finalUrl = page.url();
result.qr.redirectedToBusiness = page.url().includes('/businesses/black-bamboo-puerto-viejo.html');
result.screenshots.push(await shot('qr-redirect-final.png'));

await browser.close();
await fs.writeFile(path.join(out, 'audit_results.json'), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
