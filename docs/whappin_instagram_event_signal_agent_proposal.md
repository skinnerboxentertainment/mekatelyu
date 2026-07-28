# Proposal for Adversarial Review and Implementation Planning  
## Whappin Instagram Event Signal and Calendar Enrichment System

**Prepared for:** Implementation / Stakeholder Agent  
**Project:** Whappin — Puerto Viejo Community Directory  
**Status:** Request for impartial review, challenge, alignment, and implementation recommendation  
**Date:** July 26, 2026

---

# 1. Purpose of This Request

Whappin maintains a structured registry of businesses, organizations, venues, and service providers in Puerto Viejo and the surrounding South Caribbean region of Costa Rica.

A large portion of these entities maintain public-facing Instagram accounts. A smaller but operationally important subset uses Instagram to announce:

- Live music
- Ladies nights
- DJ sets
- After-hours parties
- Yoga classes
- Workshops
- Markets
- Pop-ups
- Food specials tied to a specific date or time
- Community meetings
- Tours and excursions
- Wellness sessions
- Dance classes
- Fundraisers
- Temporary openings
- Holiday programming
- Recurring weekly activities
- One-time events

This information is fragmented, temporary, difficult to search, and often appears only in Stories, image flyers, captions, or short-form video.

Whappin is considering a system that observes the public activity of businesses already present in its registry, detects event-related announcements, and converts verified facts into a structured community calendar.

The purpose of this document is **not** to instruct the agent to approve a predetermined solution.

The agent is being asked to conduct a:

- Thorough review
- Impartial review
- Adversarial review
- Technical feasibility review
- Legal and platform-policy review
- Ethical review
- Cost review
- Operational review
- Product-value review

The agent should challenge assumptions, identify hidden risks, compare alternatives, and recommend whether and how this capability should be implemented.

---

# 2. Core Concept

The proposed system is better understood as a **local social signal reception system** than as a broad Instagram scraper.

Whappin already has:

1. A registry of local businesses and organizations.
2. Known or discoverable Instagram handles for many registry records.
3. A community-facing directory where events and activities could be published.
4. A geographically limited scope.
5. A legitimate interest in helping residents and visitors discover public activities.

The intended workflow is:

```text
Whappin business registry
        ↓
Known public Instagram accounts
        ↓
Observation of new public activity
        ↓
Detection of event-shaped announcements
        ↓
Human or automated extraction of event facts
        ↓
Verification
        ↓
Structured Whappin calendar entry
        ↓
Attribution and source link
```

The system is **not intended to republish complete Instagram feeds**.

The system should primarily extract and publish factual event information, such as:

- Event title
- Venue
- Date
- Start time
- End time
- Recurrence
- Admission price
- Reservation method
- Age restrictions
- Short factual description
- Original Instagram account
- Original post URL
- Verification timestamp

---

# 3. The Business and Community Problem

Puerto Viejo does not have a single, consistently maintained, comprehensive event calendar.

Event information is scattered across:

- Instagram posts
- Instagram Stories
- Reels
- WhatsApp groups
- Facebook pages
- Posters
- Flyers
- Word of mouth
- Individual venue websites
- Tourism accounts
- Community organization accounts

This creates several problems:

## 3.1 For residents and visitors

People cannot easily answer questions such as:

- What is happening tonight?
- Where is live music this week?
- Are there yoga classes tomorrow?
- Which venues have recurring weekly events?
- What family-friendly activities are available?
- What events are happening in Cocles, Punta Uva, Cahuita, Manzanillo, or Puerto Viejo?

## 3.2 For businesses

Businesses repeatedly create event announcements but depend on their existing followers seeing them.

Their announcements are often:

- Short-lived
- Poorly indexed
- Difficult to discover outside Instagram
- Lost after a Story expires
- Not visible to people who do not follow the account
- Not searchable by date, category, neighborhood, or activity type

## 3.3 For Whappin

Whappin has an opportunity to create a high-value calendar layer using businesses already present in the directory.

The strategic value may include:

- Increased daily utility
- More repeat visits
- Timely local information
- Stronger business relationships
- Improved tourism usefulness
- Better discovery of recurring activities
- A reason for businesses to claim and maintain listings
- A foundation for notifications, newsletters, and “what is happening today” features

The agent should independently determine whether these benefits justify the operational and technical burden.

---

# 4. Scope Boundaries

The proposed system should be geographically and operationally narrow.

## 4.1 Primary scope

Monitor public Instagram activity from businesses and organizations already represented in the Whappin registry.

## 4.2 Secondary scope

Potentially discover additional relevant local event-producing accounts that are not yet in the registry.

## 4.3 Out of scope by default

Unless the agent identifies a compelling, lawful, ethical reason otherwise, the system should not collect:

- Follower lists
- Following lists
- Lists of people who liked posts
- Lists of commenters
- Personal social graphs
- Private-account content
- Close Friends content
- Personal messages without consent
- Facial recognition data
- Biometric data
- Inferred sensitive personal traits
- Complete historical feeds
- Full-resolution media archives
- Unrelated personal lifestyle content
- Contact databases for marketing
- Data gathered by bypassing access controls

---

# 5. Core Ethical Position

The intended distinction is:

> Instagram provides evidence that a public event exists. Whappin publishes a structured factual calendar record.

Whappin should avoid presenting copied creative content as its own.

The proposed system should favor:

- Factual extraction
- Minimal collection
- Clear attribution
- Source linking
- Human verification
- Correction procedures
- Removal procedures
- Limited retention
- Respect for access controls
- No anti-detection circumvention
- No account farming
- No proxy rotation intended to evade enforcement
- No CAPTCHA bypass
- No stolen session cookies
- No fake engagement
- No automated unsolicited messaging

The agent should challenge whether this distinction is sufficient under:

- Meta platform terms
- Applicable contract law
- Copyright law
- Database rights, if relevant
- Privacy law
- Costa Rican law
- Any other jurisdiction reasonably implicated by the implementation

The agent should not assume that “publicly visible” automatically means “authorized for automated collection.”

---

# 6. Candidate Implementation Models

The agent should evaluate at least the following models.

---

## 6.1 Model A — Human Signal Desk

Create a dedicated Whappin Instagram account that follows known local businesses.

A human reviewer checks the account once or twice per day and records relevant events.

### Potential workflow

```text
Open Whappin observer account
        ↓
Review new Stories, posts, and Reels
        ↓
Identify likely events
        ↓
Enter structured event candidate
        ↓
Verify date, time, venue, recurrence, and source
        ↓
Publish to Whappin
```

### Potential advantages

- Low technical complexity
- Low direct infrastructure cost
- Visibility into Stories
- Uses normal Instagram interfaces
- Human judgment handles ambiguous flyers
- Easy to pilot
- No dependency on unofficial scraping infrastructure

### Potential disadvantages

- Ongoing labor requirement
- Reviewer fatigue
- Risk of missed announcements
- Difficult to scale
- Inconsistent processing
- Stories may disappear before review
- Harder to guarantee complete coverage

The agent should estimate realistic daily labor for:

- 25 accounts
- 50 accounts
- 100 accounts
- 200 accounts

---

## 6.2 Model B — Official Meta API Monitoring

Use Meta’s authorized Instagram APIs where available.

Potential use cases include:

- Identifying new feed posts
- Identifying new Reels
- Retrieving permitted media metadata
- Comparing current media IDs with previously seen media IDs
- Detecting captions that appear event-related
- Obtaining permalinks and timestamps
- Receiving authorized mentions or other webhook events

### Questions the agent must verify

- Which current Meta APIs are available as of implementation time?
- Is Business Discovery still available?
- What account types can be observed?
- What permissions are required?
- What App Review requirements apply?
- Can the system access media belonging to unrelated professional accounts?
- What data fields are available?
- Are captions available?
- Are Reels available?
- Are Stories available?
- Are hashtag endpoints available?
- Are mentions available?
- Are webhooks useful?
- What rate limits apply?
- Are there rolling limits on account discovery?
- Are there limitations based on the authenticated account?
- Does Meta charge for API usage?
- Are there indirect costs for app review, hosting, or business verification?
- Can an app of this nature reasonably receive approval?

The agent must use current official documentation and should not rely on obsolete third-party tutorials.

### Potential advantages

- Authorized integration path
- Reliable identifiers and timestamps
- Lower manual burden for permanent media
- Easier deduplication
- Easier scheduling and logging
- Better foundation for a production system

### Potential disadvantages

- Limited account coverage
- Professional accounts only
- Potential App Review friction
- Permission constraints
- No complete solution for Stories
- Platform changes
- Rate limits
- API deprecations
- Technical maintenance

---

## 6.3 Model C — Business Opt-In Signal Network

Invite businesses to actively send or signal events to Whappin.

Possible intake methods:

- Tag or mention the Whappin Instagram account
- Send a direct message
- Send a flyer through WhatsApp
- Submit a Whappin event form
- Claim a Whappin listing and submit events
- Email an event announcement
- Connect an eligible Instagram professional account
- Add Whappin as a collaborator where appropriate
- Use a standardized hashtag or submission convention

### Value proposition to businesses

Whappin can convert an event announcement into:

- A searchable calendar entry
- A listing attached to the business profile
- A “happening today” result
- A category-specific event result
- A neighborhood-specific event result
- A direct link back to the original business account
- Additional reach beyond existing followers

### Potential advantages

- Strong consent posture
- Better source accuracy
- Direct relationship with businesses
- Lower monitoring burden
- Better cancellation and update handling
- Encourages listing claims
- Creates a cooperative community system

### Potential disadvantages

- Requires adoption
- Inconsistent business participation
- Businesses may forget to submit
- Some businesses may prefer Instagram-only workflows
- Onboarding and education cost
- May not provide complete town coverage

---

## 6.4 Model D — Unofficial Browser Automation or Scraping

Use a third-party scraper, headless browser, hosted scraping service, or custom browser automation.

The agent must evaluate this option adversarially rather than assuming it is acceptable.

### Questions to examine

- Does it violate Meta’s current terms?
- What is the enforcement risk?
- Would it require login sessions?
- Would it require account rotation?
- Would it require residential proxies?
- Would it break frequently?
- Can it access Stories reliably?
- What are the monthly costs?
- What are the account-ban risks?
- Could it expose Whappin to claims of circumvention?
- Would it create a fragile dependency?
- Can the implementation be maintained by the current team?
- Is the data quality materially better than the safer alternatives?

### Presumptive position

Unofficial scraping should not be recommended merely because it is technically possible.

It should only be considered if the agent can articulate:

- A legitimate necessity
- A defensible legal and ethical position
- A bounded implementation
- No circumvention of access controls
- Acceptable platform and business risk
- A clear failure and shutdown policy

---

## 6.5 Model E — Hybrid System

A hybrid model may combine:

- Human review for Stories and image flyers
- Official API checks for permanent posts and Reels
- Business opt-in for direct submissions
- WhatsApp or web forms
- Human verification before publication
- AI-assisted extraction and classification
- Limited discovery through hashtags or public search

The agent should determine whether this is the strongest practical architecture.

---

# 7. Proposed Watchlist Strategy

The full Whappin registry should not automatically receive equal monitoring frequency.

The agent should evaluate a tiered watchlist.

## Tier A — High-frequency event producers

Potential daily monitoring:

- Bars
- Nightclubs
- Live music venues
- Restaurants with scheduled entertainment
- Hostels with social programming
- Yoga studios
- Gyms
- Wellness centers
- Dance teachers
- Art spaces
- Community centers
- Markets
- Tour operators
- DJs and promoters
- Cultural organizations

## Tier B — Occasional event producers

Potential monitoring several times per week:

- Hotels
- Cafés
- Surf schools
- Spas
- Retail stores
- Galleries
- Schools
- Nonprofits
- Retreat centers
- Restaurants without frequent programming

## Tier C — Low-frequency event producers

Potential weekly, monthly, or passive monitoring:

- Hardware stores
- Mechanics
- Accountants
- Contractors
- Pharmacies
- Routine professional services
- Businesses that rarely announce scheduled activities

The agent should recommend:

- Account classification rules
- Monitoring frequency
- Automatic promotion or demotion between tiers
- How to identify dormant accounts
- How to handle renamed accounts
- How to handle deleted accounts
- How to handle duplicate business accounts
- How to handle promoter accounts not tied to a venue
- How to handle events announced by multiple accounts

---

# 8. Proposed Event Candidate Schema

The implementation should distinguish between an observed media item and a verified public event.

## 8.1 Event candidate

```json
{
  "candidate_id": "unique-candidate-id",
  "business_id": "whappin-business-id",
  "instagram_handle": "@example",
  "source_type": "story|post|reel|mention|dm|whatsapp|form",
  "source_url": "https://www.instagram.com/p/example/",
  "observed_at": "2026-07-26T08:15:00-06:00",
  "published_at": "2026-07-25T18:30:00-06:00",
  "event_likelihood": 0.91,
  "detected_fields": {
    "title": "Ladies Night",
    "date_text": "Friday",
    "time_text": "8 PM",
    "venue_text": "Example Bar",
    "price_text": "Free entry",
    "recurrence_text": "Every Friday"
  },
  "review_status": "pending",
  "source_retention": {
    "store_media": false,
    "store_caption": "temporary_review_only",
    "preserve_permalink": true
  }
}
```

## 8.2 Verified public event

```json
{
  "event_id": "unique-event-id",
  "title": "Ladies Night",
  "business_id": "whappin-business-id",
  "venue_name": "Example Bar",
  "starts_at": "2026-07-31T20:00:00-06:00",
  "ends_at": null,
  "timezone": "America/Costa_Rica",
  "recurrence": "FREQ=WEEKLY;BYDAY=FR",
  "admission": "Free entry",
  "description": "Weekly Friday evening event.",
  "categories": [
    "nightlife",
    "social"
  ],
  "source": {
    "platform": "instagram",
    "account": "@example",
    "url": "https://www.instagram.com/p/example/"
  },
  "verification": {
    "status": "human_verified",
    "verified_at": "2026-07-26T08:25:00-06:00"
  }
}
```

The agent should review this schema and propose improvements.

---

# 9. Event Detection Requirements

The system should identify event-shaped signals without treating every promotional post as an event.

Potential indicators include:

- Day names
- Calendar dates
- Times
- “Tonight”
- “Tomorrow”
- “This weekend”
- “Every Friday”
- “Weekly”
- “Doors open”
- “Live music”
- “DJ”
- “Class”
- “Workshop”
- “Market”
- “Ceremony”
- “Retreat”
- “Ladies night”
- “Happy hour” tied to a schedule
- “Movie night”
- “Open mic”
- “Karaoke”
- “Fundraiser”
- “Registration”
- “Reserve your spot”
- “Limited spaces”
- “Cover”
- “Free entry”
- “Starts at”
- “From 6 PM”
- “Until late”

The agent should examine:

- Spanish-language announcements
- English-language announcements
- Bilingual announcements
- Informal local phrasing
- Time-zone handling
- Relative dates
- Date ambiguity
- Missing years
- Events announced shortly before they occur
- Recurring events
- Cancellations
- Postponements
- Weather changes
- Venue changes
- Sold-out notices

---

# 10. Human Review Requirements

The agent should not assume that AI extraction is sufficiently reliable for automatic publication.

A reviewer should verify:

- Correct business
- Correct venue
- Correct Puerto Viejo-area location
- Event date
- Start time
- End time, if known
- Whether the date refers to the current or following week
- Whether the event is recurring
- Whether a recurring event is still active
- Admission price
- Reservation requirements
- Age restrictions
- Cancellation or postponement notices
- Duplicate announcements
- Conflicting source information

The agent should recommend:

- Review interface
- Review cards
- Confidence thresholds
- Auto-rejection rules
- Auto-expiration rules
- Escalation rules
- Audit trail
- Reviewer permissions
- Correction workflow
- Business-owner claim workflow

---

# 11. Story and Image-Flyer Handling

Stories and image flyers are likely to contain the highest-value information and the greatest technical difficulty.

The agent should evaluate:

- Whether Stories are available through any official API path
- Whether Stories can be observed through a normal human-operated account
- Whether screenshots are necessary
- Whether screenshots can be retained temporarily
- Whether OCR should be used
- Whether multimodal AI extraction is appropriate
- Whether temporary media storage introduces copyright or privacy risk
- How long review evidence should be retained
- Whether the original media should ever be displayed publicly
- Whether permission should be requested before reusing flyers
- How to attribute image-derived facts

A conservative default might be:

```text
Reviewer sees flyer
        ↓
Reviewer or AI extracts event facts
        ↓
Human verifies details
        ↓
Whappin stores the structured facts
        ↓
Whappin stores source account and permalink when available
        ↓
Whappin does not publicly rehost the flyer without permission
        ↓
Temporary internal review evidence is deleted on schedule
```

The agent should propose a defensible retention period.

---

# 12. Cost Analysis Requested

The agent should produce realistic costs for at least three implementation levels.

## 12.1 Manual pilot

Include:

- Reviewer time
- Number of monitored accounts
- Daily frequency
- Event entry time
- Monthly labor estimate
- Any software cost
- Any account setup cost

## 12.2 Lightweight hybrid

Include:

- Meta app setup
- Hosting
- Database
- Scheduled jobs
- AI classification
- AI image extraction
- Review dashboard
- Logging
- Maintenance
- Human verification

## 12.3 Larger production system

Include:

- Multiple reviewers
- Business onboarding
- Notifications
- Webhooks
- Analytics
- Event deduplication
- Archival policies
- Support and correction handling
- Monitoring and uptime
- Security
- Ongoing engineering

The agent should distinguish:

- Direct cash cost
- Labor cost
- Opportunity cost
- Maintenance burden
- Platform dependency risk
- Cost of failure
- Cost of inaccurate events

All estimates should be expressed in USD unless there is a reason to include Costa Rican colones separately.

---

# 13. Legal, Policy, and Ethical Review Requested

The agent must verify and cite current sources.

At minimum, review:

- Instagram Terms of Use
- Meta automated data collection terms
- Instagram Platform Terms
- Instagram API documentation
- Business Discovery documentation
- Mentions and webhook documentation
- Meta App Review requirements
- Meta Business Verification requirements
- Applicable copyright principles
- Applicable privacy considerations
- Costa Rican legal considerations
- Any relevant computer access or anti-circumvention concerns
- Any applicable database or unfair competition concerns

The review should clearly separate:

1. What is technically possible.
2. What Meta officially permits.
3. What may violate platform terms.
4. What may create legal exposure.
5. What may be ethically defensible but contractually prohibited.
6. What is operationally practical.
7. What is advisable for Whappin.

The agent should not rely on generic claims such as:

- “Public data is free to scrape.”
- “Facts cannot be copyrighted.”
- “Everyone does it.”
- “It is fine because the accounts are businesses.”
- “It is harmless because Whappin links back.”

Each claim should be tested.

---

# 14. Adversarial Questions the Agent Must Answer

The agent should explicitly challenge the proposal using questions such as:

1. Is this solving a real problem or creating a labor-intensive feature users may not value?
2. How many local accounts actually produce usable event information?
3. What percentage of posts would become calendar entries?
4. Would businesses view this as useful distribution or unauthorized extraction?
5. How often would events be published incorrectly?
6. Who is responsible when a canceled event remains listed?
7. Can Whappin maintain daily review during weekends, holidays, and staff absences?
8. Would a submission-first model outperform monitoring?
9. Is Instagram too unstable as a foundation?
10. Are Stories too difficult to capture reliably?
11. Could Meta block or restrict the observer account?
12. Could API approval be denied?
13. Could a dedicated account become overwhelmed by unrelated feed content?
14. Would a browser automation system become a maintenance trap?
15. Does the calendar create enough recurring value to justify the workflow?
16. Would a weekly digest be more achievable than a real-time calendar?
17. Should Whappin begin with recurring events only?
18. Should the system initially cover only nightlife and wellness?
19. Should businesses be required to opt in?
20. Should Whappin publish only events explicitly submitted or tagged?
21. What is the minimum viable coverage that still feels useful?
22. What are the reputational consequences of missing major events?
23. What are the reputational consequences of publishing incorrect events?
24. Could businesses manipulate the calendar with excessive promotions?
25. How should Whappin distinguish events from ordinary sales promotions?
26. Could the system unintentionally privilege Instagram-active businesses?
27. How should non-Instagram businesses participate?
28. How should the system handle events promoted by individuals rather than registered businesses?
29. How should it handle unsafe, illegal, discriminatory, or age-restricted events?
30. What moderation policy is necessary?

The final recommendation should address these questions rather than merely listing them.

---

# 15. Pilot Proposal to Evaluate

The agent should assess the following pilot, modify it if necessary, and either recommend or reject it.

## Pilot size

- 30 to 50 high-signal accounts
- Primarily nightlife, live music, wellness, classes, markets, and community organizations
- Four-week observation period

## Pilot workflow

1. Create or designate a Whappin observer account.
2. Follow the selected accounts.
3. Record all event-shaped announcements.
4. Log where each announcement appeared:
   - Story
   - Post
   - Reel
   - Bio
   - External link
5. Enter event candidates into a structured review sheet or lightweight dashboard.
6. Verify before publication.
7. Track corrections and cancellations.
8. Measure reviewer time.
9. Measure useful event yield.
10. Interview participating businesses where possible.

## Pilot metrics

- Number of accounts monitored
- Number of media items reviewed
- Number of event candidates
- Number of verified events
- Number of duplicates
- Number of false positives
- Number of cancellations or changes
- Number of events missed
- Average review time per account
- Average processing time per event
- Percentage of events originating in Stories
- Percentage originating in permanent posts
- Percentage of businesses willing to opt in
- User engagement with calendar listings
- Business click-throughs
- Calendar return visits
- Operational cost per verified event

## Pilot decision thresholds

The agent should propose objective thresholds for:

- Continue
- Expand
- Modify
- Pause
- Abandon

---

# 16. Product and User Experience Review

The agent should consider how the calendar should appear in Whappin.

Potential features include:

- Happening today
- Happening tonight
- Tomorrow
- This weekend
- Live music
- Nightlife
- Yoga and wellness
- Classes
- Family-friendly
- Markets
- Community events
- Free events
- Recurring weekly events
- Neighborhood filters
- Venue pages with upcoming events
- Calendar view
- List view
- Map view
- WhatsApp share
- Add to calendar
- Source link
- Last verified label
- Report incorrect information
- Business claim and correction

The agent should recommend a minimum viable interface rather than assuming all features should be built.

---

# 17. Proposed Business Participation Message

The agent should review and improve this concept:

> Whappin is building a town-wide calendar for Puerto Viejo. Whenever you announce live music, classes, workshops, specials, parties, markets, tours, or other scheduled activities, tag Whappin or send us the announcement. We will convert it into a searchable calendar listing and link visitors back to your business and original post. We will not republish your media without permission.

The agent should determine:

- Whether businesses should explicitly opt in
- Whether silence can reasonably be treated as permission to publish factual event data
- Whether businesses should receive a claim link
- Whether a standardized submission format is useful
- Whether WhatsApp is likely to outperform Instagram tagging
- Whether incentives are needed
- Whether premium placement creates fairness concerns

---

# 18. Technical Architecture Questions

The agent should recommend a technical architecture appropriate to the existing Whappin stack.

Questions include:

- Where are Instagram handles stored?
- How are handles validated?
- How are renamed handles detected?
- How are media IDs stored?
- How are new media items detected?
- How are candidates deduplicated?
- How are recurring events represented?
- How are dates normalized to America/Costa_Rica?
- How are relative dates resolved?
- How are expired events removed?
- How are corrections propagated?
- How are sources preserved?
- How is temporary media evidence deleted?
- How are API tokens protected?
- How are reviewer actions audited?
- How does the system degrade if the Meta API is unavailable?
- How does the system support manual-only operation?
- How are business-submitted events prioritized?
- How are duplicate venue and promoter announcements merged?

The agent should compare:

- Static JSON generation
- GitHub-based workflow
- Lightweight database
- Serverless functions
- Scheduled GitHub Actions
- Supabase
- Firebase
- Cloudflare
- Other low-cost options

The recommendation should align with Whappin’s actual architecture rather than introducing unnecessary infrastructure.

---

# 19. Security and Abuse Review

The agent should evaluate:

- Token storage
- Credential rotation
- Reviewer account security
- Observer-account compromise
- Malicious event submissions
- Spam
- Fake events
- Impersonation
- Venue disputes
- Unsafe links
- Phishing
- Adult-only events
- Illegal events
- Harassment
- Political events
- Religious events
- Discriminatory listings
- Defamatory descriptions
- Business takedown requests
- Moderator abuse
- Auditability

The agent should recommend minimum moderation and security policies.

---

# 20. Required Deliverables From the Agent

The agent’s response should include all of the following.

## 20.1 Executive recommendation

Choose one:

- Proceed
- Proceed with restrictions
- Pilot only
- Defer
- Reject

Explain why.

## 20.2 Current-state verification

Verify current Meta and Instagram capabilities using official documentation.

## 20.3 Option comparison

Compare:

- Manual
- Official API
- Business opt-in
- Unofficial automation
- Hybrid

Include benefits, limitations, risks, costs, and dependencies.

## 20.4 Adversarial critique

Present the strongest case against implementing the system.

## 20.5 Counterargument

Present the strongest case for implementing the system.

## 20.6 Recommended operating model

Specify:

- Monitoring method
- Account tiers
- Review frequency
- Human roles
- Automation boundaries
- Publication rules
- Retention rules
- Attribution rules
- Correction rules

## 20.7 Technical architecture

Provide:

- Components
- Data flow
- Data schema
- Integration points
- Failure handling
- Security model
- Estimated engineering effort

## 20.8 Pilot plan

Provide:

- Scope
- Duration
- Account selection criteria
- Workflow
- Metrics
- Success thresholds
- Stop conditions

## 20.9 Cost model

Provide:

- One-time cost
- Monthly direct cost
- Labor requirement
- Maintenance burden
- Scaling cost

## 20.10 Risk register

Include:

- Risk
- Probability
- Impact
- Mitigation
- Owner
- Trigger
- Response

## 20.11 Decision log

List:

- Assumptions accepted
- Assumptions rejected
- Open questions
- Required stakeholder decisions

## 20.12 Implementation backlog

If the recommendation is to proceed, provide a phased backlog:

- Phase 0: validation
- Phase 1: manual pilot
- Phase 2: lightweight automation
- Phase 3: business participation
- Phase 4: production calendar
- Phase 5: optimization

---

# 21. Research Standards

The agent must:

- Prefer official Meta and Instagram documentation
- Cite all current platform-policy claims
- Include document dates where available
- Identify deprecated or obsolete APIs
- Distinguish facts from assumptions
- Mark uncertain conclusions
- Avoid relying on SEO articles as primary authority
- Verify rate limits and permission requirements
- Confirm whether quoted documentation is current
- Note any regional limitations
- Note any requirements tied to professional accounts
- Note any Meta App Review uncertainty
- Identify information that requires legal counsel

The agent should use external sources only as supporting material when official sources are incomplete.

---

# 22. Decision Principles

The final recommendation should optimize for:

1. Community usefulness
2. Accuracy
3. Low operating cost
4. Low legal and platform risk
5. Respect for business content
6. Business participation
7. Maintainability
8. Graceful degradation
9. Human accountability
10. Incremental implementation

The system should not be selected merely because it is technologically interesting.

---

# 23. Preliminary Working Hypothesis

The current working hypothesis, which the agent is expected to challenge, is:

> Whappin should begin with a small human-operated signal desk focused on 30 to 50 high-frequency event-producing Instagram accounts. It should publish only structured factual event information with attribution. It should simultaneously develop a business opt-in workflow. Official Meta API automation should be added only where it materially reduces labor and can be implemented within current permissions. Unofficial scraping should not be foundational.

This is a hypothesis, not a decision.

The agent should reject or modify it where the evidence supports doing so.

---

# 24. Final Instruction to the Agent

Conduct a rigorous, impartial, and adversarial review of this proposal.

Do not simply validate the concept.

Challenge:

- The necessity
- The data assumptions
- The platform assumptions
- The legal assumptions
- The ethical assumptions
- The cost assumptions
- The operational assumptions
- The expected user value
- The proposed architecture
- The likelihood of business participation
- The ability of Whappin to maintain the system

Then return a concrete recommendation that Whappin can act upon.

The response should be specific enough to guide an implementation decision and, if approved, become the basis for an engineering plan.

