# Second-Pass Evidence — 2026-07-20

Baseline commit: `6f40dd80`
Scope: accessibility structure, external-reference inventory, live deployment, release configuration, analytics/privacy, and payload sanity check

## Accessibility structure

- Homepage landmarks: 0 `main`, 0 `header`, 1 `nav`, 1 `footer`.
- Search input has placeholder-only naming and no explicit label/ARIA label.
- Category, area, channel, sort, and mode selects have no explicit label/ARIA label.
- Language buttons have visible names but no selected-state semantics.
- No duplicate IDs, unnamed links, or unnamed buttons were detected on the sampled home page.
- Full keyboard, contrast, zoom, reduced-motion, and assistive-technology checks remain pending.

## External references

- Total external references across generated HTML: 11,045.
- Unique external URLs: 3,392.
- HTTP references: 109.
- Unique HTTP URLs: 95.
- High-volume domains are expected because shared libraries and contact links repeat across generated pages; counts do not imply unique endpoints.
- FormSubmit's published documentation confirms first use requires email confirmation and that submitted form fields are emailed through its service. The audit did not submit the project form.

## Live deployment

- URL: `https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app/`
- Browser result: loaded successfully without observed console errors.
- Visible build timestamp: 2026-07-14 13:50.
- Placeholder `paradisio@example.com` Post route confirmed live.
- Public Admin mode option confirmed live.
- GitHub Pages source: `master`, `/docs`.
- Build type: legacy.
- Status: built.
- HTTPS enforced: yes.
- Custom domain: none.
- Custom 404: no.
- Latest build commit: `6f40dd803c55d8d99f548aa496018934cef5ebfe`.
- Latest build duration: 24.05 seconds.

## Privacy and analytics

- GoatCounter script appears on 1,692 generated pages.
- Claim form action sends data to FormSubmit.
- Personal fields include name, email, optional phone, relationship, and free-text business corrections.
- Claim page contains no detected privacy, consent, retention, or third-party disclosure language.
- No privacy/terms/legal/cookie artifact was found by filename/content routing scan.

## Payload sanity check

Local uncompressed HTTP measurements:

- Directory HTML: 1,393,240 bytes; localhost transfer completed in 260 ms.
- Businesses JSON: 1,754,727 bytes; localhost transfer completed in 38 ms.

These timings reflect loopback I/O only. They do not represent mobile latency, compression behavior on GitHub Pages, parse/render cost, or Core Web Vitals.

## Safety

- No external form was submitted.
- No payment, email, call, WhatsApp, login, or administrative mutation was performed.
- GitHub configuration inspection was read-only.
