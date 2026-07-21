# Google Maps Signed-vs-Unsigned Evidence Comparison

## Question

Does a signed-in Google Maps browser session materially improve evidence quality or capture
reliability enough to justify using an isolated sockpuppet account for the targeted 113-record
enrichment sweep?

The 113 evidence-poor records do not contain stored CIDs. Therefore, the comparison uses ten known
positive CID controls from the 658 successfully linked records. One representative control is chosen
from each current canonical category. The same CID URLs are inspected unsigned and signed.

## Controls

- Identical ten CIDs, order, locale, viewport, timeout, delay, extraction code, and screenshot size.
- Fresh anonymous browser context for the unsigned run.
- Dedicated local browser profile for the signed run; never reuse a personal browser profile.
- No clicks on contact actions, directions, reviews, calls, websites, or booking links.
- No messages, form submissions, edits, reviews, or business contact.
- Full viewport screenshot plus visible body text, final URL, title, timestamp, and error state.
- Sequential navigation with conservative delay; no concurrency.

## Scoring

Each capture receives machine-readable signals:

1. Target business name visibly resolved.
2. Nontrivial visible-text length.
3. Business-type/category vocabulary present.
4. Address/location signal present.
5. Hours/open-status signal present.
6. Phone signal present.
7. Website signal present.
8. Rating/review signal present.
9. Photo/media signal present.
10. Sign-in wall, consent wall, CAPTCHA, or navigation error absent.

The final recommendation compares paired records, not aggregate page size alone. Signing in is
recommended only if it improves identity/field completeness or capture success on multiple controls,
not merely because the page contains more unrelated interface text.

## Credential boundary

The owner signs into a dedicated isolated browser profile directly. Codex does not request, type,
read, record, or export credentials, cookies, recovery information, or OTPs.
