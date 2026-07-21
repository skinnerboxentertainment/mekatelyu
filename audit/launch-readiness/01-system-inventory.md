# System Inventory

Status: Baseline inventory established; deeper operational inventory in progress

## Confirmed baseline

| Item | Current observation |
|---|---|
| Product | Paradisio — Puerto Viejo Business Board |
| Delivery model | Static site intended for GitHub Pages |
| Default branch | `master` |
| Baseline commit | `6f40dd80` |
| Canonical dataset | `pv_master_unified.csv` |
| Static generator | `paradisio_app/build.py` |
| Published output | `docs/` |
| Application output | `docs/paradisio_app/` |
| Main implementation languages | Python, HTML, CSS, JavaScript |
| Declared infrastructure | Zero server infrastructure for the public static site |
| Clean-build output | 771 business pages, 16 classified listings, 2,500 files |
| Front-end payload | Vanilla HTML/CSS/JS; Leaflet and MarkerCluster from unpkg; GoatCounter analytics |
| Owner submission | FormSubmit endpoint to the configured project email |
| Payment model | Static SINPE instructions plus locally generated invoice records/pages |
| Administrative model | Static, publicly routable admin/dashboard pages; no authentication boundary |
| Automated verification | No CI workflow and no discoverable test suite |

## Repository surfaces requiring assessment

- Data acquisition and enrichment scripts at repository root and in `pvscraper/`
- Static-site generator and operational utilities in `paradisio_app/`
- Generated GitHub Pages payload in `docs/`
- Historical reports, specifications, screenshots, and QA records in `docs/`
- Automation/configuration in `.github/`
- IPC/development tooling in `CODEX_ENDPOINT/` and `codex_bridge.py`
- Large collection of intermediate CSV, JSON, log, screenshot, and report artifacts

## Critical journeys

To be confirmed against the shipped application:

1. Visitor opens the directory and understands its purpose. **Baseline rendered.**
2. Visitor searches and filters businesses. **Search baseline passed; full filter matrix pending.**
3. Visitor opens a business detail page and uses contact/map actions. **Rendering passed; route correctness has high-severity findings.**
4. Visitor browses and searches classifieds. **Browsing rendered; posting is nonfunctional due to placeholder email.**
5. Visitor changes language and/or viewing mode where exposed. **Language behavior failed; viewing modes expose non-production surfaces.**
6. Business owner initiates a claim or premium-listing journey. **Claim form renders; submission was not transmitted; premium payment is blocked by placeholder configuration.**
7. Payment instructions and invoice-related flows communicate safe, correct expectations. **Failed launch safety review.**
8. Administrative/dashboard pages do not expose privileged claims or sensitive information without appropriate controls. **Failed: public static access confirmed.**
9. Direct links and page refreshes work under the GitHub Pages subpath.

## Inventory work remaining

- Build command and deterministic inputs
- Complete dependency inventory
- Generated/source file boundary
- GitHub Pages workflow and deployment source
- Browser storage and client-side trust boundaries
- External services and domains
- Data schema and validation rules
- Authentication/authorization claims of dashboard modes
- Analytics, monitoring, feedback, and recovery mechanisms
