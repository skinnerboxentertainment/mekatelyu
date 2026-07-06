# Request: UI/UX Audit & Redesign Recommendations for Puerto Viejo Business Directory

**Target:** CODEX
**From:** OpenCode
**Date:** 2026-07-06

---

## Task

Visit the GitHub Pages site at:

**https://skinnerboxentertainment.github.io/puerto-viejo-business-discovery/**

Use your in-app browser to visually inspect every page. Then produce a
detailed audit and redesign proposal.

## Pages to audit

| Page | URL | Purpose |
|------|-----|---------|
| Landing | `index.html` | Project overview, stats, entry point |
| Directory | `directory.html` | Interactive business directory with search/filter |
| Report | `report.html` | Analytical report with charts and map |
| Gap Map | `gapmap.html` | Grid-based gap scanner visual |

## What to evaluate

### 1. Landing page (index.html)
- Does it communicate the project scope clearly?
- Is there an interactive map? Should there be?
- Are the stats meaningful at a glance (450 vs 754 records)?
- Does it link clearly to the other pages?

### 2. Directory page (directory.html)
- Search/filter usability
- Map integration quality
- Data table readability
- Mobile responsiveness

### 3. Report page (report.html)
- Chart quality and readability
- Are the metrics still accurate with 754 records?
- What's missing?

### 4. Data architecture
- The site currently pulls from `businesses.json` (754 records)
- The GeoJSON has 481 features (only records with coordinates)
- Are there performance issues with the full dataset?

### 5. Content and messaging
- The dataset has grown from 450 to 754 records
- Should the site reflect this growth / versioning?
- Any missing CTAs or navigation?

## Deliverable

Write your analysis to `CODEX_ENDPOINT/responses/website_audit.md`

Structure:

1. **Executive summary** — overall impression, biggest issues
2. **Per-page audit** — what works, what doesn't, concrete fixes
3. **Landing page redesign** — specific HTML/CSS/JS recommendations
   including whether an interactive map should be on the landing page
   and how to implement it
4. **Data architecture recommendations** — JSON structure, lazy loading,
   search indexing, mobile perf
5. **Priority-ordered action items** — what to fix first, what can wait
6. **Mock layout** — describe (or sketch in markdown) your recommended
   landing page layout

## Constraints

- The site is static HTML/CSS/JS hosted on GitHub Pages
- No server-side code, no database, no API keys
- Data comes from a static `businesses.json` file
- Any JS libraries must be CDN-sourced

Note: I cannot open the live URL for you, so the current page source
is embedded below for your analysis. Read it and evaluate the structure,
not the visual rendering.

## Current landing page (index.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Puerto Viejo Business Discovery</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; color: #2c3e50; max-width: 700px; margin: 60px auto; padding: 0 20px; line-height: 1.7; text-align: center; }
h1 { font-size: 28px; margin-bottom: 8px; }
.sub { color: #7f8c8d; font-size: 14px; margin-bottom: 40px; }
.links { display: flex; flex-direction: column; gap: 12px; }
.links a { display: block; padding: 14px 20px; background: white; border-radius: 8px; text-decoration: none; color: #2c3e50; font-weight: 500; box-shadow: 0 1px 4px rgba(0,0,0,0.08); transition: box-shadow 0.2s; }
.links a:hover { box-shadow: 0 3px 12px rgba(0,0,0,0.15); }
.desc { font-size: 12px; color: #95a5a6; margin-top: 4px; font-weight: normal; }
.badge-new { background: #e74c3c; color: white; font-size: 10px; padding: 1px 6px; border-radius: 8px; margin-left: 6px; vertical-align: super; }
</style>
</head>
<body>
<h1>Puerto Viejo Business Discovery</h1>
<p class="sub">450 businesses within 5 km &mdash; 99.8% Instagram coverage</p>
<div class="links">
<a href="directory.html">Browse Directory <span class="desc">Search, filter by category/area, interactive map</span></a>
<a href="report.html">Interactive Report <span class="desc">Map with 450 markers, Instagram coverage, category breakdown</span></a>
<a href="dataset.csv">Full Dataset (CSV) <span class="desc">450 records with Instagram, phone, coordinates, confidence tags</span></a>
<a href="https://github.com/...">GitHub Repository <span class="desc">Source code, SQLite database, OSM cross-reference</span></a>
</div>
</body>
</html>
```

## Key facts the site should reflect

- Dataset: 754 records (not 450)
- 481 with coordinates, 457 with CIDs, 521 with phones
- 361 Instagram handles, 328 Facebook URLs
- Sources: PVS crawl, OSM, Google Maps grid scan, SQLite cache
- Instagram verified via Playwright browser checks
- 255 screenshot evidence set

Write your recommendations accordingly.
