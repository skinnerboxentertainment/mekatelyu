# WHAPPIN × CARIBBEAN GUARD
## Release-Candidate Implementation Brief for Agent Execution

**Document purpose:** Instruct the implementation agent to build a presentation-ready Caribbean Guard flagship experience inside Whappin using only publicly available information from Caribbean Guard’s website and other explicitly public organization-controlled sources.

**Target:** A polished release candidate that can be demonstrated live, on-site, within 1–2 days.

**Repository:** `skinnerboxentertainment/mekatelyu`  
**Production platform:** `https://www.whappin.com/`  
**Organization source:** `https://www.caribbeanguard.org/`

---

# 1. Executive directive

Build a **flagship Community Safety Partner experience** for Caribbean Guard inside Whappin.

Do not treat this as a conventional directory listing. Caribbean Guard is a volunteer aquatic-safety organization, training network, patrol organization, emergency-response network, and public-interest institution serving Costa Rica’s South Caribbean coast.

The release candidate should demonstrate what a formal Whappin–Caribbean Guard collaboration could look like before organizational approval is complete.

The implementation must:

1. Use only public, attributable information.
2. Avoid inventing operational details, response promises, patrol status, emergency contacts, schedules, affiliations, endorsements, or official partnership claims.
3. Present the experience as a **demonstration / proposed community integration** unless and until Caribbean Guard explicitly approves publication as an official collaboration.
4. Be sufficiently complete and polished that stakeholders can understand the proposal by interacting with it on a phone.
5. Make Caribbean Guard look important, credible, useful, and actionable without misrepresenting Whappin as an emergency dispatcher.
6. Be architected as a reusable template for future Whappin community partners.

---

# 2. Product thesis

Whappin should not merely list Caribbean Guard.

Whappin should demonstrate that it can become a public-facing distribution layer for:

- water-safety education;
- organization discovery;
- patrol and program visibility;
- training participation;
- volunteer recruitment;
- donations;
- beach-specific safety information;
- emergency guidance;
- future organization-managed alerts and updates.

This feature should help reposition Whappin from a business directory into a trusted mobile-first community platform.

---

# 3. Public-source research summary

The implementation agent should independently recheck all source pages before committing final copy.

## 3.1 Mission and organizational philosophy

Caribbean Guard states that its mission is to revolutionize aquatic safety in Costa Rica’s South Caribbean and change the pattern of drowning incidents.

Its broader philosophy is that aquatic safety must be community-led and sustainable. The organization seeks to create a community that is strong and safe in the water through swimming, lifesaving, freediving, CPR, first aid, education, and organized beach-safety programs.

Primary source:

- `https://www.caribbeanguard.org/`

## 3.2 Founding and organizational history

Caribbean Guard traces its origin to March 2021, when community members organized patrols during a large Easter swell. Thirty community members reportedly patrolled six beaches. The initiative evolved from “Prevención de ahogamientos,” to “Puerto Viejo Locals,” and then Caribbean Guard.

The organization states that, by September 2024:

- more than 400 people had participated in courses, workshops, and patrols;
- its emergency-alert network had grown to more than 70 members;
- no fatalities had occurred during its organized patrols.

Primary source:

- `https://www.caribbeanguard.org/nuestro-trabajo`

Do not convert these statements into independent Whappin guarantees. Attribute them to Caribbean Guard.

## 3.3 Lifesaving Club

Publicly described functions include:

- continuing education;
- lifeguard courses;
- CPR and first-aid instructor training;
- swimming-instructor training;
- junior lifeguard / Nipper training;
- ELLIS CPR training;
- organized patrols;
- weekly lifesaving training;
- emergency-alert network.

Caribbean Guard states that it patrols Playa Grande and Playa Chiquita on Sundays, with additional patrols during Easter, some holidays, and special dates.

It states that Saturday-morning lifesaving training is open to the community, with location depending on ocean conditions.

Primary source:

- `https://www.caribbeanguard.org/lifesaving-club`

## 3.4 Emergency-alert network

Caribbean Guard publicly describes an emergency group with more than 70 members, including lifeguards, surfers, swimmers, fishers, divers, and freedivers.

The organization says that when an emergency occurs, a protocol is activated and nearby qualified community members may respond.

Primary sources:

- `https://www.caribbeanguard.org/lifesaving-club`
- `https://www.caribbeanguard.org/nuestro-trabajo`

Critical implementation rule:

**Do not expose a “summon Caribbean Guard” button unless the exact approved contact route and wording are supplied by an authorized Caribbean Guard stakeholder.**

The release candidate may visually demonstrate a gated emergency module, but the live action must be one of the following:

1. disabled and labelled “Pending Caribbean Guard approval”;
2. routed only to `911`, using a normal telephone link;
3. routed to a public contact method explicitly identified by Caribbean Guard as suitable for emergencies;
4. implemented as a stakeholder-only demo using non-public test data outside production.

Never imply guaranteed response, real-time monitoring, official dispatch, specific response times, or universal beach coverage.

## 3.5 Swim Club

The Swim Club is publicly described as free and open to the community.

Public schedule listed on the website:

- Punta Uva: Thursdays at 7:15 a.m.
- Playa Negra: Tuesdays and Fridays at 4:00 p.m.

The organization also describes a Swim School providing free swimming instruction to local children.

Primary source:

- `https://www.caribbeanguard.org/swim-club`

Treat schedules as potentially changeable. Add a visible “Confirm with organizer” note and source link.

## 3.6 Programa Playa Organizada

The Organized Beach Program includes publicly described components such as:

- red-and-yellow-flag supervised bathing zones;
- survival lines with rope, buoys, and anchoring;
- drone mapping;
- local business partners;
- rescue stations;
- emergency plans;
- rapid-response groups;
- 911 protocol;
- designated access and extraction points;
- CPR, first-aid, and lifeguard training for local workers.

Primary source:

- `https://www.caribbeanguard.org/programa-playa-organizada`

This program is strategically important to Whappin because it maps directly to future beach pages, local business participation, map layers, safety education, and partner recognition.

## 3.7 Strategic projects

Public projects include:

### Bodega Digna

A secure and dry equipment-storage facility is described as the organization’s top priority.

Equipment referenced includes:

- rescue boards;
- rescue tubes;
- ropes;
- uniforms;
- radios;
- binoculars;
- CPR training mannequins;
- paramedic emergency backpacks;
- AEDs / defibrillators.

### Guardia Móvil

The Mobile Guard concept includes:

- a preventive utility vehicle carrying rescue and safety equipment;
- quads for broad beaches such as Cocles and Playa Negra;
- emergency scooters for reaching congested access points;
- boats, jet skis, and underwater scooters;
- drone capability for patrol, search, and flotation delivery.

### Centro Acuático de Alto Rendimiento / CADAR

The proposed facility includes:

- a 25 m semi-Olympic pool;
- a children’s pool;
- a deep diving tank;
- classrooms;
- changing rooms and bathrooms;
- accommodation for staff and international volunteers;
- parking.

Primary source:

- `https://www.caribbeanguard.org/proyectos`

## 3.8 Governance and funding philosophy

Caribbean Guard presents a “rule of thirds” sustainability model:

- one third community;
- one third local businesses and entrepreneurs;
- one third government.

The organization argues that local associations should organize aquatic safety, local businesses should contribute financially and operationally, and government should support safety through policy and resources.

Primary source:

- `https://www.caribbeanguard.org/involcrate-1`

This aligns strongly with Whappin’s existing business network. The release candidate should show, at least conceptually, how participating local businesses might later receive recognition as Caribbean Guard supporters or Organized Beach Program partners.

Do not create or imply actual sponsorship status without verified data.

## 3.9 Team

Caribbean Guard publicly presents a large multidisciplinary team of local residents and other South Caribbean community members, including:

- lifeguards;
- swim instructors;
- CPR and first-aid instructors;
- surfers;
- fishers;
- divers;
- freedivers;
- drone operators;
- search-and-recovery specialists;
- guides;
- board members;
- founders.

Primary source:

- `https://www.caribbeanguard.org/team`

The Whappin release candidate does not need to reproduce every biography in full. It should support a scalable team module and feature a representative subset with links back to the official team page.

## 3.10 Donations

The official donation page publicly lists donation methods through Banco Nacional, PayPal, and SINPE Móvil.

Primary source:

- `https://www.caribbeanguard.org/donar`

Because financial information is sensitive and can change, Whappin should preferably use a prominent **Donate on Caribbean Guard** link rather than duplicating banking numbers throughout the listing.

If account details are displayed, they must be copied exactly from the current official page and timestamped as source-verified.

---

# 4. Required release-candidate experience

## 4.1 Listing classification

Create a reusable organization type such as:

- `community_partner`
- `community_safety_partner`
- `nonprofit`
- `emergency_support_organization`

Recommended visible badge:

**Community Safety Partner**

Until approved, add a subtle qualifier:

**Proposed Whappin community integration**

Do not say “Official Whappin Partner” before approval.

## 4.2 Page hierarchy

The Caribbean Guard page should contain:

1. Safety-oriented hero
2. Organization summary
3. Emergency guidance module
4. Primary action buttons
5. Impact and credibility metrics
6. Programs
7. Organized Beach Program
8. Patrol and training information
9. Current strategic projects
10. Volunteer / participate
11. Donate
12. Team preview
13. Related beaches
14. Source attribution and verification date

## 4.3 Hero

Recommended structure:

**Eyebrow:** Community Safety Partner  
**Title:** Caribbean Guard  
**Tagline:** Building a stronger, safer community in the water.  
**Summary:** A community-led aquatic-safety organization serving Costa Rica’s South Caribbean through lifesaving training, swimming education, patrols, prevention, and emergency-response coordination.

Primary actions:

- Learn how to help
- Donate
- View programs
- Emergency information

Use organization-controlled imagery only if its use is legally and technically appropriate. Otherwise create a branded layout using public logo assets with source attribution, or request approved media from the stakeholder contact.

Do not hotlink large images from the organization’s server.

## 4.4 Emergency guidance module

This is the highest-sensitivity area.

Recommended visual treatment:

**Water emergency?**

1. Call Costa Rica emergency services: **911**
2. Give the exact beach or landmark.
3. Do not enter dangerous water unless trained and equipped.
4. Caribbean Guard operates a community emergency-alert network.
5. Direct Caribbean Guard activation: **pending approved operational contact**

Required UI states:

- `approved`: show authorized call / WhatsApp / protocol action;
- `pending`: show 911 and “Caribbean Guard contact integration pending approval”;
- `demo`: non-production prototype for stakeholder presentation;
- `disabled`: no action available.

Required warning:

> Whappin does not monitor emergencies or dispatch rescuers.

Never use a fake emergency phone number.

Never route an emergency CTA to a general donation or social-media account.

Never claim 24/7 coverage.

## 4.5 Action bar

Recommended actions:

- Call 911
- Visit official website
- Donate
- Join / volunteer
- Share
- Get directions only if a verified physical destination exists
- WhatsApp only if the number and use case are publicly verified

## 4.6 Impact cards

Use attributed language:

- **400+ people trained or involved**  
  “Reported by Caribbean Guard as of September 2024.”

- **70+ emergency-network members**  
  “Reported by Caribbean Guard.”

- **Patrols at Playa Grande and Playa Chiquita**  
  “See official schedule and current information.”

- **No fatalities during organized patrols**  
  This must be framed explicitly as Caribbean Guard’s own reported record, not a Whappin-certified claim.

## 4.7 Program cards

Create reusable cards for:

- Lifesaving Club
- Swim Club
- Swim School
- Organized Beach Program
- Lifeguard training
- CPR and first aid
- Junior lifeguard / Nipper
- Freediving / apnea education
- Emergency-alert network

Each card should support:

- title;
- summary;
- audience;
- schedule;
- location;
- cost;
- status;
- source URL;
- verification date;
- “confirm with organizer” flag.

## 4.8 Project cards

Create project cards for:

- Bodega Digna
- Guardia Móvil
- CADAR aquatic center

Each should include:

- problem;
- proposed solution;
- why it matters;
- organization’s stated needs;
- donation / learn-more CTA;
- official source link.

## 4.9 Beach integration

At minimum, link Caribbean Guard to:

- Playa Grande;
- Playa Chiquita;
- Punta Uva;
- Playa Negra;
- Cocles.

Do not claim active lifeguard coverage on a beach unless the official source explicitly supports it.

Recommended beach-page component:

**Water Safety in the South Caribbean**

- Learn about local ocean risks
- Check whether organized patrol information is available
- Call 911 in an emergency
- Learn about Caribbean Guard
- View safety programs

Future-ready fields:

- patrol status;
- patrol date;
- safe bathing zone;
- rescue station;
- survival line;
- red-and-yellow flags;
- emergency access point;
- extraction point;
- AED availability;
- current advisory;
- source;
- last verified.

For the release candidate, all dynamic fields should default to `unknown` unless verified.

## 4.10 Donation module

Preferred implementation:

- concise statement of why donations matter;
- link to official donation page;
- optional expandable panel showing public donation methods;
- “Details last verified on [date]”;
- no financial processing inside Whappin for this first release.

## 4.11 Team preview

Feature 4–8 representative public profiles from the official team page.

Recommended roles to showcase:

- founder / president;
- operations lead;
- search and recovery;
- lifeguard / swim instruction;
- local surfer / rescuer;
- drone unit;
- Organized Beach Program leadership.

Do not rewrite biographies in ways that create unsupported credentials.

Link to the official full team page.

---

# 5. Data model

Extend the current listing schema minimally and reuse existing patterns wherever possible.

Illustrative structure:

```json
{
  "id": "caribbean-guard",
  "slug": "caribbean-guard",
  "name": "Caribbean Guard",
  "entityType": "community_organization",
  "partnerTier": "community_safety_partner",
  "partnershipStatus": "proposed",
  "featured": true,
  "verified": {
    "status": "public-source-reviewed",
    "lastReviewed": "YYYY-MM-DD",
    "approvedByOrganization": false
  },
  "summary": {
    "short": "",
    "long": ""
  },
  "actions": {
    "website": "https://www.caribbeanguard.org/",
    "donate": "https://www.caribbeanguard.org/donar",
    "join": null,
    "phone": null,
    "whatsapp": null,
    "emergency": {
      "mode": "pending",
      "primaryNumber": "911",
      "organizationContact": null,
      "disclaimer": "Whappin does not monitor emergencies or dispatch rescuers."
    }
  },
  "programs": [],
  "projects": [],
  "impact": [],
  "team": [],
  "relatedPlaces": [],
  "sources": []
}
```

Do not force the entire schema if the repository already has a better established model. Adapt to the existing data architecture.

---

# 6. Content provenance requirements

Every substantive block must have one or more source URLs.

Recommended source object:

```json
{
  "url": "https://www.caribbeanguard.org/lifesaving-club",
  "publisher": "Caribbean Guard",
  "accessed": "YYYY-MM-DD",
  "supports": [
    "patrol locations",
    "Saturday training",
    "emergency network"
  ]
}
```

At the bottom of the page include:

> Information compiled from Caribbean Guard’s public website. Operational details and schedules may change. Confirm directly with the organization.

For the stakeholder demonstration, include an unobtrusive “Source view” or internal debug panel if convenient.

---

# 7. Language

Caribbean Guard’s public site is primarily Spanish.

The Whappin release candidate should ideally support:

- Spanish as the canonical source language;
- English for visitors;
- clear language switching if Whappin already supports localization.

Do not auto-translate technical emergency terminology without human review.

High-priority bilingual strings:

- Water emergency / Emergencia acuática
- Call 911 / Llame al 911
- Whappin does not monitor emergencies / Whappin no monitorea emergencias
- Confirm with organizer / Confirme con la organización
- Patrol information / Información de guardia
- Donate / Donar
- Volunteer / Ser voluntario
- Learn CPR / Aprender RCP
- Beach safety / Seguridad acuática

---

# 8. UX and visual direction

The experience should feel:

- authoritative;
- calm;
- urgent only where needed;
- community-led;
- ocean-connected;
- trustworthy;
- accessible outdoors on a phone.

Avoid:

- sensational drowning imagery;
- red everywhere;
- fake live-status indicators;
- countdowns;
- unverified maps;
- overloading the page with full biographies;
- presenting the organization as a government agency;
- implying Whappin owns or operates Caribbean Guard.

Emergency red should be reserved for the emergency module and 911 action.

Community and educational areas can use Whappin’s standard visual language with aquatic accents.

Required mobile behaviors:

- primary safety actions visible without hunting;
- large tap targets;
- readable in bright outdoor conditions;
- no horizontal overflow;
- no critical interaction dependent on hover;
- emergency disclaimer directly adjacent to emergency CTA;
- fast loading on weak mobile connections.

---

# 9. Implementation sequence for a 1–2 day release candidate

## Phase 1: Repository reconnaissance

1. Inspect the existing listing schema.
2. Identify the canonical business/profile template.
3. Identify how featured listings, badges, CTA buttons, maps, images, translations, and related entities are currently implemented.
4. Identify build and validation commands.
5. Preserve current static-generation conventions.

## Phase 2: Content object

1. Create Caribbean Guard’s structured data record.
2. Add source metadata.
3. Add organization classification and proposed-partner state.
4. Add programs, projects, impact items, related beaches, and safe emergency state.

## Phase 3: Reusable components

Build or adapt:

- Community Partner badge
- Impact metric cards
- Program cards
- Project cards
- Safety / emergency panel
- Source and verification footer
- Related beach cards

Prefer extending current components over creating a parallel design system.

## Phase 4: Page composition

Assemble the flagship page with:

- hero;
- actions;
- emergency panel;
- organization story;
- impact;
- programs;
- patrol and training;
- Organized Beach Program;
- projects;
- donate;
- team;
- related beaches;
- provenance.

## Phase 5: Discovery and placement

Make the page discoverable through:

- organization / nonprofit category;
- community resources;
- safety;
- beach-related pages;
- site search;
- featured homepage or category placement if appropriate.

Use `proposed` or demo-only language until approved.

## Phase 6: Testing

Test:

- Pixel-class mobile viewport;
- narrow phones;
- desktop;
- keyboard navigation;
- screen-reader labels;
- all CTAs;
- 911 telephone link behavior;
- missing-image fallback;
- no JavaScript failure state if applicable;
- source links;
- Spanish characters;
- performance;
- production build;
- existing CI tests.

---

# 10. Acceptance criteria

The release candidate is complete when:

1. Caribbean Guard has a polished, first-class page in Whappin.
2. It is visibly distinct from a commercial business listing.
3. The page uses only public, attributable facts.
4. The official website and donation page are actionable.
5. Programs and projects are clearly explained.
6. The emergency panel is prominent but does not misrepresent Whappin as a dispatcher.
7. No unapproved Caribbean Guard emergency contact is exposed.
8. 911 is the only live emergency action unless an authorized contact is supplied.
9. Related South Caribbean beaches are linked.
10. The experience is mobile-first and presentation-ready.
11. Existing Whappin functionality and tests remain intact.
12. The implementation can be reused for other community organizations.
13. A stakeholder can understand the collaboration concept in under two minutes.
14. The page contains a visible public-source disclaimer.
15. Partnership status can be changed from `proposed` to `approved` without redesigning the page.

---

# 11. Explicit non-goals for this release

Do not build:

- a real dispatch system;
- a responder location tracker;
- real-time patrol status without a trusted data source;
- user-submitted emergency reports;
- a public emergency-group membership list;
- automated responder notifications;
- medical triage;
- rescue instructions beyond safe, authoritative basics;
- donation processing;
- account access for Caribbean Guard;
- a full organization CMS;
- claims of official partnership;
- fake endorsements;
- live ocean-condition forecasting.

These can become later phases only after operational agreement.

---

# 12. Stakeholder demonstration script

The demo should tell this story:

1. Open Whappin on a phone.
2. Search “Caribbean Guard” or enter through Community Safety.
3. Show that this is not a basic listing.
4. Demonstrate the emergency guidance panel.
5. Clearly explain that 911 remains primary and Whappin is not dispatch.
6. Show programs, patrol information, training, Swim Club, and Organized Beach Program.
7. Show how Caribbean Guard’s projects and donation needs receive visibility.
8. Open a related beach and show the future safety-integration concept.
9. Show the “proposed integration” label.
10. Explain that approval unlocks:
    - official partner status;
    - approved emergency contact route;
    - organization-managed updates;
    - verified schedules;
    - beach alerts;
    - events;
    - partner-business recognition;
    - donation campaigns.

Recommended closing line:

> We did not ask you to imagine what Whappin could do for Caribbean Guard. We built a working version from your public information so you could react to something real.

---

# 13. Questions to resolve with Caribbean Guard after the demo

1. May Whappin identify Caribbean Guard as an official Community Safety Partner?
2. What emergency contact pathway, if any, may Whappin expose?
3. Must users always call 911 before activating the community network?
4. Is the emergency network monitored continuously?
5. Which beaches currently have scheduled patrols?
6. How should Whappin describe patrol hours and limitations?
7. Who is authorized to update operational information?
8. Which WhatsApp, phone, or email contacts are public and for what purpose?
9. May Whappin use the organization’s logo and photographs?
10. Which programs are currently active?
11. Are the Swim Club schedules current?
12. Which projects should receive priority placement?
13. Should donation details be linked or reproduced?
14. May Whappin display team biographies?
15. Can Whappin recognize participating businesses in the Organized Beach Program?
16. Would Caribbean Guard like event and training submissions?
17. What disclaimer language does the organization require?
18. Does Caribbean Guard want Spanish-only content, bilingual content, or both?
19. Who gives final approval?
20. What changes must be made before the demonstration becomes public?

---

# 14. Future collaboration roadmap

## Phase 2: Approved partnership

- official partner badge;
- verified contact details;
- approved media;
- organization review of all copy;
- current program schedules;
- official event feed;
- donation campaigns;
- volunteer form.

## Phase 3: Beach-safety network

- beach-specific safety pages;
- rescue-station mapping;
- safe bathing zones;
- access and extraction points;
- AED locations;
- patrol schedules;
- Organized Beach Program partner recognition.

## Phase 4: Controlled operational integration

Only with formal approval and testing:

- approved emergency activation workflow;
- organization-managed advisories;
- responder-only tools;
- audit trail;
- uptime and escalation procedures;
- multilingual emergency UX;
- legal and operational review.

---

# 15. Source map

Official Caribbean Guard pages:

- Home / mission: `https://www.caribbeanguard.org/`
- Our work / history and impact: `https://www.caribbeanguard.org/nuestro-trabajo`
- Lifesaving Club: `https://www.caribbeanguard.org/lifesaving-club`
- Swim Club: `https://www.caribbeanguard.org/swim-club`
- Organized Beach Program: `https://www.caribbeanguard.org/programa-playa-organizada`
- Projects: `https://www.caribbeanguard.org/proyectos`
- Vision / rule of thirds: `https://www.caribbeanguard.org/involcrate-1`
- Team: `https://www.caribbeanguard.org/team`
- Donate: `https://www.caribbeanguard.org/donar`

Whappin:

- Production: `https://www.whappin.com/`
- Repository: `https://github.com/skinnerboxentertainment/mekatelyu`

---

# 16. Final instruction to the implementation agent

Proceed immediately.

Do not wait for organizational approval to create the release candidate, because the purpose of the release candidate is to make approval concrete and easier.

However:

- keep the partnership state explicitly proposed;
- keep emergency activation gated;
- use public information only;
- do not invent missing details;
- preserve source attribution;
- deliver a polished, mobile-first demonstration;
- run all existing tests;
- report every changed file;
- report any content or technical uncertainty;
- provide the final preview URL or local demonstration path;
- include a short checklist of stakeholder approvals required before public launch.
