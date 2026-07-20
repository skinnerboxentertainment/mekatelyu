# Findings Register

No findings are accepted solely from historical project reports. New entries require evidence reproduced during this audit.

| ID | Severity | Area | Summary | Status | Evidence |
|---|---|---|---|---|---|
| PAY-001 | Blocker | Payment | Premium page requests SINPE payment to a documented placeholder number | Removed from local candidate | Browser + source |
| PRIV-001 | Blocker | Privacy/authorization | Public static admin and invoice artifacts expose commercial records without authentication | Candidate clean; legacy repo open | Browser + generated files |
| PRIV-002 | High | Privacy | Claim submissions send personal data to a third party without disclosure or privacy terms | Removed from local candidate | Form/source inventory |
| FUNC-001 | High | Classifieds/contact | All Post links use `paradisio@example.com` | Removed from local candidate | Browser + source |
| DATA-001 | High | Contact routing | 99 generated WhatsApp routes are not valid Costa Rica routes | Verified locally | Generated-data profile |
| DATA-002 | High | Trust/safety | Closed businesses retain active contact CTAs | Verified locally | Generated-data profile |
| I18N-001 | High | Localization | Language buttons update document language but do not translate visible content | Unsupported controls removed | Browser interaction |
| MOB-001 | High | Mobile UX | Mode selector overlaps the primary fixed WhatsApp action | Verified locally | 390×844 browser inspection |
| AUTH-001 | High | Product/security | Public mode selector exposes Admin and owner dashboard modes with no trust boundary | Removed from local candidate | Browser + source |
| PUB-001 | High | Publication boundary | Pages publishes raw data, working artifacts, internal documents, and the app as one 53.66 MiB tree | Candidate clean; deployment pending | Pages config + file inventory |
| DATA-003 | High | Data quality | Catalog contains malformed contacts, stale records, duplicates, and scope/distance inconsistencies | Open | Generated-data deep profile |
| CLASS-001 | High | Classifieds integrity | Public classifieds are active seed/demo records with placeholder numbers and no expiry lifecycle | Removed from local candidate | Classifieds-data profile |
| QA-001 | Medium | Quality engineering | No executable automated test suite or CI gate is present | Implemented locally; CI pending | Repository/runtime inspection |
| A11Y-001 | Medium | Accessibility | Primary page lacks `main`; filters lack programmatic labels; language state is not conveyed | Improved; manual audit pending | DOM inspection |
| PERF-001 | Medium | Performance | Homepage ships ~1.39 MB HTML and duplicates business data also present in a ~1.75 MB JSON asset | Verified locally | File-size/source inspection |
| SEO-001 | Medium | Discoverability | Primary pages lack canonical/social metadata and no robots/sitemap artifact is present | Verified locally | DOM/source scan |
| SEC-001 | Medium | Browser security | Generated pages define no CSP or referrer policy; privileged page uses unsanitized HTML assembly | Verified locally | Source scan |
| SEC-002 | Medium | Supply chain | CDN assets have no SRI; Python dependencies are ranged without a lockfile or hashes | Verified locally | Source/dependency scan |
| REPO-001 | Medium | Repository hygiene | Tracked agent sessions, logs, and working artifacts are retained in the public repository | Open | Tracked-file/history inventory |
| EXT-001 | Medium | External links | 95 unique HTTP links remain in the HTTPS product | Verified locally | Generated-link inventory |
| OPS-001 | Medium | Release operations | Production deploys directly from `master:/docs` without CI/staging/rollback verification | Open | GitHub Pages configuration |
| DOC-001 | Low | Documentation | Public business-count claims drift among 750, 771, and historical 772 | Verified locally | README/build/historical QA |

### `PAY-001` — Placeholder SINPE destination is presented as live payment instruction

- Severity: Blocker
- Status: Open
- Affected surface: `premium.html` and generated invoices
- Reproduction: Open the Premium page and inspect payment instructions.
- Expected: A verified production payment destination, owner, bank, support path, refund/activation terms, and prelaunch validation.
- Actual: `SINPE_PHONE` is `+506 8888 8888` with a source comment stating it must be replaced. The page asks users to send money and promises activation.
- Impact: Direct financial loss, severe trust damage, and inability to fulfil purchases.
- Root cause: Development placeholder emitted into production output.
- Recommended initiative: INIT-001.
- Acceptance criterion: Payment remains disabled until production details and operational fulfilment are independently verified; then an end-to-end test transaction is documented.

### `PRIV-001` — Public static payload exposes administrative invoice data

- Severity: Blocker
- Status: Open pending classification of current records as test or real data
- Affected surface: `admin.html`, `data/invoices.json`, and generated invoice pages
- Reproduction: Navigate directly to the public admin page or invoice JSON; no authentication is requested.
- Expected: Commercial/payment records are private, access-controlled, minimized, and absent from the public deployment artifact.
- Actual: Three invoice objects are committed with business, amount, status, payment/reference, validity, and notes fields. Admin fetches and renders them client-side.
- Impact: Commercial confidentiality and privacy exposure; architecture cannot provide authorization because it is entirely static.
- Root cause: Operational/admin data stored under the GitHub Pages publish root.
- Recommended initiative: INIT-002.
- Acceptance criterion: No invoice/admin operational data is present in the public artifact or Git history intended for publication; any administrative workflow uses an appropriate private system.

### `PRIV-002` — Personal claim data is transmitted without privacy disclosure

- Severity: High
- Status: Open
- Affected surface: Business claim/correction form and site-wide analytics
- Evidence: The claim form requests claimant name, email, optional phone, relationship, and business updates, then posts to FormSubmit. No privacy, consent, retention, controller/contact, or third-party processing disclosure appears on the form. No privacy/legal artifact was found. GoatCounter is included on 1,692 generated pages without a visible policy in the inspected output.
- Impact: Visitors cannot make an informed decision about how their personal information is handled; launch creates avoidable privacy and trust risk.
- Root cause: Third-party form and analytics services were integrated without a corresponding data-handling policy and user-facing disclosure.
- Recommended initiative: INIT-013.
- Acceptance criterion: Data collection is minimized; purpose, processor, retention, contact, and user rights are documented and linked at collection points; the chosen analytics posture is reviewed for the launch jurisdictions.

### `FUNC-001` — Classified and global Post actions use a placeholder address

- Severity: High
- Status: Open
- Reproduction: Select Post from navigation or “Post a free ad” on Classifieds.
- Actual: Links target `paradisio@example.com`.
- Impact: User submissions are undeliverable and a promoted launch journey is broken.
- Recommended initiative: INIT-003.
- Acceptance criterion: Every posting CTA reaches a monitored production channel and a test submission is received and processed.

### `DATA-001` — Invalid inferred WhatsApp routes are promoted as verified contact

- Severity: High
- Status: Open
- Evidence: The CSV has 106 explicit WhatsApp values, while the generated product advertises 629. Of those 629 generated routes, 99 do not match Costa Rica `506` plus eight digits. Examples include `+83601553` and `+27500258`.
- Impact: Failed or misdirected contact attempts and misleading “WhatsApp”/“Fully Online” badges.
- Root cause: Build-time inference treats normalized/ordinary phone values as WhatsApp without adequate country-code validation.
- Recommended initiative: INIT-004.
- Acceptance criterion: WhatsApp is displayed only for explicitly verified or safely normalized routes; all generated `wa.me` numbers pass country-aware validation.

### `DATA-002` — Closed listings still invite users to contact the business

- Severity: High
- Status: Open
- Evidence: All three records with `status=closed` generate WhatsApp as their primary CTA.
- Impact: Users are directed toward permanently closed businesses, undermining directory trust.
- Recommended initiative: INIT-004.
- Acceptance criterion: Closed records are excluded or prominently marked and never present booking/contact as the primary action.

### `I18N-001` — Language selection does not translate visible UI

- Severity: High
- Status: Open
- Reproduction: Open the directory and select Español.
- Expected: Navigation, tagline, placeholder, filters, results, and status controls translate, with selection state exposed accessibly.
- Actual: `<html lang>` changes to `es`, but observed navigation, tagline, and search placeholder remain English; no active or `aria-pressed` state appears on language buttons.
- Recommended initiative: INIT-005.
- Acceptance criterion: Representative home, detail, and classifieds strings switch correctly in all advertised languages and persist across navigation.

### `MOB-001` — Fixed controls collide on business pages

- Severity: High
- Status: Open
- Reproduction: Open a business page at 390×844.
- Actual: `.sticky-bar` occupies the bottom 76 px at z-index 100; `#mode-switcher` overlays it at z-index 9999 and obscures the primary WhatsApp CTA.
- Recommended initiative: INIT-006.
- Acceptance criterion: No fixed element overlaps another actionable element at supported mobile widths, including safe-area insets.

### `AUTH-001` — Development viewing modes are exposed as product authorization

- Severity: High
- Status: Open
- Evidence: A fixed selector offers Tourist, Business Owner, Premium Owner, and Admin to every visitor; admin and dashboard pages are direct public URLs.
- Impact: Implies privileges that are neither authenticated nor enforceable and exposes internal product/admin concepts.
- Recommended initiative: INIT-002.
- Acceptance criterion: Production visitor UI contains no unenforceable privileged modes; owner/admin capabilities have a real authorization boundary or are removed.

### `PUB-001` — Production publishes the working tree instead of a minimal release artifact

- Severity: High
- Evidence: Pages serves `master:/docs`; that tree contains 2,538 files/53.66 MiB, including raw datasets, enrichment checkpoints, audit material, CID samples, internal planning documents, and privileged artifacts.
- Impact: Unnecessary data exposure, information leakage, larger attack/review surface, and no reliable boundary between internal work and public product.
- Recommended initiative: INIT-016.
- Acceptance criterion: Deployment contains an allowlisted, reproducible product artifact only; internal and intermediate files return 404 and are checked automatically.

### `DATA-003` — Catalog quality is not launch-governed

- Severity: High
- Evidence: 70 malformed email fields; one malformed website; 44 duplicate-phone groups; 14 exact-coordinate duplicate groups; 70 coordinate-bearing records beyond the stated 5 km scope; eight material distance inconsistencies; 99 verification dates older than a year at launch; 130 unknown and 29 needs-verification statuses.
- Impact: Misrouting, misleading coverage claims, duplicate/confusing results, stale information, and erosion of directory trust.
- Recommended initiative: INIT-017.
- Acceptance criterion: Launch rules define geographic scope, freshness, deduplication, category vocabulary, status handling, and contact validity; a release invariant report passes with reviewed exceptions.

### `CLASS-001` — Classifieds ship as undifferentiated demo content

- Severity: High
- Evidence: All 16 ads are active; 14 use `5555` placeholder contacts; no expiry field exists; July date-specific listings remain active for an August 1 launch.
- Impact: Visitors may act on fictional, unreachable, or expired housing, jobs, ride, sale, lost-property, and event listings.
- Recommended initiative: INIT-018.
- Acceptance criterion: Demo content is removed or unmistakably labeled and isolated; real ads have verified intake, moderation, expiry, renewal, reporting, and privacy rules.

### `QA-001` — No automated release gate

- Severity: Medium
- Status: Open
- Evidence: `.github` contains issue templates but no workflow; `requirements.txt` declares pytest, neither available runtime has it installed, and no conventionally discoverable test suite exists.
- Impact: Generator, data, and 1,700-page output can regress without detection.
- Recommended initiative: INIT-007.
- Acceptance criterion: CI builds from clean checkout and runs unit, data-invariant, link, and smoke-browser checks before deployment.

### `A11Y-001` — Core semantics and control naming are incomplete

- Severity: Medium
- Status: Open
- Evidence: Home/detail pages contain no `main`; search, filters, and mode select lack programmatic labels; language buttons do not expose selected state; no `:focus-visible` or reduced-motion rule was found. Sample token contrasts include faint-on-sand `2.54:1` and coral-on-white `3.74:1`.
- Impact: Screen-reader and keyboard users receive weaker navigation/context and ambiguous controls.
- Recommended initiative: INIT-008.
- Acceptance criterion: Semantic landmarks, labels, focus behavior, state, and representative keyboard journeys pass automated and manual checks.

### `PERF-001` — Initial directory payload duplicates the full catalog

- Severity: Medium
- Status: Open
- Evidence: `index.html` is approximately 1.39 MB and `data/businesses.json` is approximately 1.75 MB; the page embeds catalog data while also publishing the JSON asset.
- Impact: Slow parsing/download on constrained mobile connections and expensive rebuild/review diffs.
- Recommended initiative: INIT-009.
- Acceptance criterion: A measured performance budget is met on a representative constrained mobile profile without duplicating the complete catalog payload.

### `SEO-001` — Primary product pages lack launch metadata controls

- Severity: Medium
- Status: Open
- Evidence: Sample business page had a description but no canonical or Open Graph title; canonical tags found by repository scan belong to QR redirect pages; no robots/sitemap artifact found.
- Recommended initiative: INIT-010.
- Acceptance criterion: Intentional canonical, indexation, sitemap, and social-sharing metadata are verified on home, business, classified, and non-public utility pages.

### `SEC-001` — Browser security policy and unsafe admin rendering require hardening

- Severity: Medium
- Status: Open
- Evidence: No generated HTML contains a CSP or referrer policy. Admin assembles invoice-derived values into `innerHTML` without escaping.
- Impact: Weaker defense in depth and a stored-injection path if invoice content becomes externally influenced.
- Recommended initiative: INIT-002 and INIT-011.
- Acceptance criterion: Public pages have an intentional hosting-compatible policy; untrusted values are rendered as text or escaped; security checks cover the deployment artifact.

### `SEC-002` — Third-party and Python dependency integrity is not reproducible

- Severity: Medium
- Evidence: Leaflet/MarkerCluster assets are CDN-loaded without SRI. Python requirements use ranges without a lockfile or hashes. A missing CDN asset leaves unguarded `L.map(...)` initialization paths.
- Impact: Builds can resolve differently over time; CDN compromise or outage has no integrity/fallback control and may break maps.
- Recommended initiative: INIT-019.
- Acceptance criterion: Build dependencies are locked/reproducible; browser assets are self-hosted or integrity-pinned with an intentional failure state; dependency updates are tested.

### `REPO-001` — Public repository retains development-session artifacts

- Severity: Medium
- Evidence: Eight tracked agent-session JSON files, a 94.5 KB session log, a 464 KB results JSONL file, and multiple checkpoints are present. A limited strong-token/private-key history scan found no confirmed credential, but was not exhaustive.
- Impact: Internal context and metadata are unnecessarily public and increase future secret/privacy leakage risk.
- Recommended initiative: INIT-020.
- Acceptance criterion: Repository retention rules and ignore patterns are defined; tracked artifacts are reviewed and removed where appropriate; a proper secret scan passes before release.

### `EXT-001` — HTTPS product contains legacy HTTP destinations

- Severity: Medium
- Status: Open
- Evidence: Generated HTML contains 109 `http://` references representing 95 unique URLs. Sampling found redirects to HTTPS, two HTTP-only destinations, and an affiliate endpoint returning `403` to HEAD; the set therefore cannot be treated as uniformly safe or live.
- Impact: Depending on the destination, users may receive insecure transport, failed navigation, browser warnings, or tracking through legacy affiliate chains.
- Root cause: Source data preserves unnormalized historical URLs.
- Recommended initiative: INIT-014.
- Acceptance criterion: Every external destination is normalized to a verified HTTPS endpoint where supported; failures and unavoidable HTTP-only destinations are explicitly reviewed.

### `OPS-001` — Production release has no automated quality gate or verified rollback

- Severity: Medium
- Status: Open
- Evidence: GitHub Pages is public and built directly from `master:/docs` using the legacy Pages mechanism. The inspected latest deployment at `6f40dd80` succeeded, HTTPS is enforced, `master` is unprotected, and no custom 404 exists. No CI workflow, staging environment, release approval, artifact provenance check, or tested rollback record was found.
- Impact: Any push affecting `docs/` can become production without the audit checks; recovery depends on manual Git operations.
- Root cause: Deployment predates a controlled release pipeline.
- Recommended initiative: INIT-007 and INIT-015.
- Acceptance criterion: A protected release workflow validates the exact artifact, supports preview/staging, records provenance, and demonstrates rollback to a known-good version.

### `DOC-001` — Record-count claims are inconsistent

- Severity: Low
- Status: Open
- Evidence: README headline says 750, current dataset/build says 771, and the 2026-07-11 historical QA report says 772.
- Recommended initiative: INIT-012.
- Acceptance criterion: Public and operator documentation derives the count from the same canonical build and includes an as-of date.

## Finding template

### `AREA-NNN` — Title

- Severity:
- Status: Open / Remediation planned / Implemented / Verified / Risk accepted / Deferred
- Affected surface:
- Baseline:
- Reproduction:
- Expected:
- Actual:
- Impact:
- Root cause:
- Evidence:
- Recommended initiative:
- Acceptance criterion:
- Verification:
