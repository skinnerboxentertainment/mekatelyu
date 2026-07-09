Use this as the initial challenge prompt:

---

## Research challenge: autonomous local-business discovery

Design a zero-cost or effectively free agentic system that discovers the largest practically obtainable set of businesses operating within a 5 km straight-line radius of central Puerto Viejo de Talamanca, Costa Rica, and identifies each business’s likely Instagram account.

### Objective

Acquire the main tranches of data automatically through some combination of:

- Browser control
- Search-engine queries
- Google Maps interaction
- Extraction of publicly visible listing information
- OpenStreetMap/Overpass
- Public directories and tourism platforms
- Business websites
- Instagram and other social-platform discovery

The system should minimize manual labor while producing traceable, reviewable evidence.

### Constraints

- No paid APIs or commercial datasets.
- Do not assume one source is complete.
- Google Maps has result limits, personalization, interface instability, bot detection, and contractual restrictions.
- Instagram may restrict unauthenticated access and automated collection.
- The workflow must survive interruptions, throttling, CAPTCHAs, layout changes, and partial failures.
- Every record must retain its source, acquisition date, and supporting URLs.
- The system must distinguish confirmed facts, inferred matches, and uncertain candidates.
- Do not claim absolute completeness.
- Avoid collecting sensitive personal information.
- Prefer compliant and low-risk methods, but analyze technically possible alternatives and their tradeoffs honestly.

### Required fields

For each candidate business, attempt to obtain:

- Canonical business name
- Alternate names
- Business category
- Address or locality
- Latitude and longitude
- Phone number
- Website
- Google Maps URL or identifier
- Instagram handle and URL
- Other social profiles
- Operating status
- Discovery sources
- Social-match confidence
- Evidence supporting the match
- First-seen and last-verified dates

### Your assignment

Do not implement anything yet. Propose at least three materially different acquisition architectures, including:

1. A conservative, terms-conscious approach
2. A browser-agent approach using Google Maps interactively
3. A hybrid, maximum-coverage approach

For each architecture, provide:

- Components and data flow
- Exact acquisition strategy
- Geographic coverage method
- Search categories and query generation
- Extraction method
- Deduplication method
- Instagram-discovery method
- Match-confidence model
- Failure recovery and resumability
- Expected coverage
- Expected runtime
- Manual-review burden
- Legal/contractual and technical risks
- Likely failure modes
- Maintenance requirements

Then compare the architectures in a decision matrix.

### Adversarial requirements

Act as both architect and critic.

For every proposed solution:

- Identify how it could silently miss businesses.
- Identify how its completeness estimate could be misleading.
- Explain how Google or Instagram could defeat it.
- Describe how duplicate or renamed businesses would corrupt results.
- Challenge whether the proposed automation is genuinely free.
- Propose tests that could falsify its coverage claims.
- State what evidence would cause you to abandon that architecture.

Finally, recommend:

- One pilot architecture
- One fallback architecture
- A small proof-of-concept covering a limited geographic cell
- Quantitative success criteria for deciding whether to scale
- The unresolved questions that require human judgment

The output should be concrete enough that another engineering agent could implement it without inventing the core methodology.

---

For the adversarial process, give a second agent the proposal and ask:

> Attack this proposal as a hostile technical reviewer. Find hidden costs, prohibited assumptions, coverage gaps, brittle dependencies, false-confidence mechanisms, and simpler alternatives. Do not redesign it until you have made the strongest possible case that it will fail.