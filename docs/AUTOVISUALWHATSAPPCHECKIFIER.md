# AutoVisualWhatsAppCheckifier

## Status

Proposed pre-launch verification tool. This specification does not authorize messaging,
bulk account enumeration, master-dataset mutation, or publishing results.

## Purpose

Review proposed `wa.me` routes one at a time in a visible browser, inspect the rendered
WhatsApp target, compare visible identity evidence with the corresponding directory
listing, and create a resumable audit record. The tool is deliberately semi-automated:
navigation, capture, comparison, and logging can be autonomous; ambiguous identity and
final dataset promotion remain review decisions.

## Non-goals

- Sending test messages, calls, reactions, or contact requests.
- Scraping WhatsApp contacts or discovering unlisted numbers.
- Treating HTTP 200, a redirect, or merely opening WhatsApp as proof of a working account.
- Reading chats, contact lists, browser storage, cookies, or unrelated account data.
- Modifying `pv_master_unified.csv` directly.
- Removing the establishment QR system or changing profile QR destinations.

## Inputs

The checker accepts a UTF-8 CSV queue with these fields:

| Field | Required | Meaning |
|---|---:|---|
| `record_id` | yes | Stable directory identifier |
| `business_name` | yes | Expected establishment name |
| `whatsapp_normalized` | yes | E.164 number, stored with leading `+` |
| `phone` | no | Published telephone number for comparison |
| `area` | no | Location disambiguator |
| `website` | no | First-party evidence source |
| `source_url` | no | URL where WhatsApp evidence was observed |
| `source_class` | yes | `master_explicit`, `first_party_link`, or `phone_candidate` |
| `prior_status` | no | Previous review outcome |

Numbers must pass local normalization before entering the browser queue. A route is
constructed as `https://wa.me/<international digits>` with no prefilled message.

## Outputs

The append-only review ledger is CSV or JSON Lines and contains:

| Field | Meaning |
|---|---|
| `run_id`, `attempt_id`, `record_id` | Stable trace identifiers |
| `started_at`, `completed_at` | ISO-8601 timestamps |
| `route` | Opened `wa.me` route |
| `render_state` | Observed page-state classification |
| `display_name` | Visible target name, if any |
| `business_label` | Visible WhatsApp business label, if any |
| `visible_number` | Visible number, if rendered |
| `identity_result` | `match`, `probable_match`, `mismatch`, `unclear`, `unavailable` |
| `confidence` | Numeric 0–1 assessment confidence |
| `evidence_summary` | Short factual description of visible evidence |
| `screenshot_path` | Redacted, review-scoped screenshot path |
| `review_state` | `auto_complete`, `human_required`, `human_confirmed` |
| `error_code` | Stable failure code, if applicable |
| `tool_version` | Checker version used for the attempt |

Screenshots must contain only the target surface needed for verification. If unrelated
chats, notifications, or personal information are visible, the capture must be cropped
or discarded. Screenshots remain local and are excluded from the public release.

## Observable render states

1. `target_visible`: a target header or profile surface is rendered.
2. `business_target_visible`: WhatsApp explicitly presents a business identity.
3. `invalid_or_unavailable`: the UI explicitly says the number is invalid or unavailable.
4. `login_required`: inspection cannot continue without authentication.
5. `native_app_handoff`: the browser delegates to an app the checker cannot observe.
6. `consent_or_interstitial`: a safe interstitial blocks target inspection.
7. `rate_limited_or_challenged`: WhatsApp presents throttling or an anti-automation check.
8. `generic_send_page`: no target identity is visible; this is inconclusive.
9. `unexpected_page`: any state outside the allowlisted patterns.

## Identity comparison

Vision extracts only visible target identity fields. Comparison uses normalized tokens,
business aliases already present in the directory, area, website domain, and visible
business category. Logos and avatars are supporting evidence only and cannot establish
identity by themselves.

Suggested scoring:

- Exact or near-exact establishment name: strong positive evidence.
- Known alias plus matching location/category: strong positive evidence.
- Same visible telephone number: positive routing evidence, not ownership proof.
- Generic personal name with no corroboration: unclear.
- Clearly different business name: mismatch.
- Missing identity or generic send page: unavailable/unclear, never match.

Automatic `match` requires at least two independent visible signals and confidence of
0.90 or higher. `probable_match`, all mismatches, and all unclear states enter the human
review queue. Neither automatic class modifies production data.

## State machine

```text
queued
  -> validating_input
  -> opening_route
  -> waiting_for_stable_render
  -> classifying_render_state
  -> extracting_visible_identity
  -> comparing_identity
  -> capturing_scoped_evidence
  -> writing_ledger
  -> complete | human_required | retryable_error | halted
```

The ledger entry is written before advancing. Restarting the tool resumes from the first
record without a terminal attempt and never repeats a completed route unless explicitly
requested.

## Browser interaction boundary

Allowed:

- Open one `wa.me` route in a dedicated review tab.
- Follow WhatsApp-owned redirects generated by that navigation.
- Wait for a stable visible state.
- Inspect visible text and pixels in the dedicated target surface.
- Capture a tightly scoped screenshot.
- Close or reuse the dedicated tab after the ledger is durable.

Forbidden:

- Typing into a message box.
- Clicking Send, Call, Add Contact, Share, attachment, microphone, or reaction controls.
- Opening chat history or unrelated navigation elements.
- Bypassing login, challenges, consent, or rate limits.
- Running multiple target tabs concurrently.
- DOM injection, private endpoints, contact-upload APIs, or browser-profile inspection.

The implementation should fail closed: if control identification is uncertain, it takes
no click and records `unexpected_page` or `human_required`.

## Pacing and intrusion controls

- Concurrency: exactly one route.
- Default delay: randomized 8–15 seconds between completed routes.
- Maximum autonomous batch: 25 routes, followed by a five-minute cool-down and health check.
- Stop immediately on the first challenge or explicit rate-limit page.
- Stop after three consecutive unexpected or generic states.
- Retry transient navigation failures once after at least 60 seconds.
- Never retry invalid/unavailable, mismatch, login-required, or native-handoff states.
- Configurable daily ceiling; initial pilot ceiling is six routes including one control.

These defaults are intentionally conservative and may be reduced after the pilot. They
must not be increased automatically.

## Two queues

### Preservation queue

The 106 existing explicit WhatsApp routes. Results confirm or flag current routes; an
inconclusive check never removes a route automatically.

### Candidate queue

Normalized mobile numbers lacking explicit WhatsApp evidence. Candidate results are kept
separate and cannot create a public WhatsApp button without `human_confirmed` review.

## Safety controls

- No message text is included in the URL.
- A pre-navigation assertion verifies that the route host is exactly `wa.me`.
- A page guard detects message-composer focus; if focused, the run halts without input.
- The tool records every navigation and attempted action locally.
- Screenshots and logs are ignored by public build/export steps.
- Production updates require a separately generated review patch and explicit approval.
- Original evidence and prior values are retained so every change is reversible.

## Pilot protocol

The first run contains six cases:

1. Three established routes previously observed to open correctly on mobile.
2. One shared-number route.
3. One route expected to be ambiguous.
4. The impossible control `+50600000000`.

The pilot is successful only if the visible browser exposes meaningful target identity,
the control is not classified as a match, no message is sent, screenshots exclude
unrelated account data, and the run resumes correctly after interruption.

If WhatsApp exposes only generic pages, native-app handoff, or login-gated UI, the pilot
ends and the mobile human-review dashboard becomes the supported verification surface.

## Acceptance criteria

- Zero outbound messages or calls.
- Zero reads of unrelated chats, contacts, storage, or session secrets.
- Every attempted route has a durable ledger entry.
- The impossible control cannot receive `match` or `probable_match`.
- All screenshots are review-scoped and remain local.
- Interruption and restart do not duplicate completed checks.
- Human-review exports contain the evidence and prior value needed for a decision.
- No master or release dataset changes without an explicitly approved second-stage patch.

## Implementation stages

1. Queue and ledger schemas, normalization, resume logic, and unit tests.
2. Local dashboard showing progress, evidence, and human-review controls.
3. Six-route browser/vision pilot under the interaction boundary above.
4. Evaluate pilot evidence and tune only classifiers—not safety limits.
5. Preservation-queue review in bounded batches.
6. Candidate review after the preservation queue is complete.
7. Generate a proposed data patch for explicit human approval.

## Launch decision

This tool is quality-assurance infrastructure, not a launch dependency. The August 1
directory release can ship with the 106 explicit routes while verification continues.
Only confirmed additions or corrections should flow into later release candidates.
