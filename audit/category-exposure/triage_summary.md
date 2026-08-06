# Exposure Triage — First Pass (owner approval pending)

Automated first-pass triage of the 52 identity-level exposure suggestions.
**Decisions are recommendations only — nothing is applied until the owner approves.**

- **ADD (apply multi-category group):** 39
- **REVIEW (owner judgment call):** 8
- **SKIP (false positive):** 5

Source: `exposure_candidates.csv` (tier=identity) → `triage_decisions.csv` (machine-readable).

## nightlife — 7

- ❓ REVIEW **Asante Bistro & Café - Cahuita, Limón, Costa Rica** — Bistro/café with cocktail cuisine — could host evening scene; owner confirms
- ✔ ADD **Colores Restaurant and Beach Lounge - Manzanillo, Limón, Costa Rica** — "Lounge" in name + restaurant = beach lounge venue
- ✔ ADD **Da Lime Beach Club and Restaurant - Playa Chiquita, Puerto Viejo, Limón, Costa Rica** — Beach club + restaurant
- ✔ ADD **El Refugio Grill - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica** — Grill venue
- ✔ ADD **El Sendero Beach Club** — Beach club
- ✔ ADD **Tasty Waves Cantina - Playa Cocles, Puerto Viejo, Limón, Costa Rica** — Cantina venue
- ❓ REVIEW **Vol'Air Dance Studio** — Dance studio — classes vs. dance nights; owner confirms

## eat — 3

- ✔ ADD **Kaya's Place - Playa Negra, Puerto Viejo, Limón, Costa Rica** — Onsite restaurant (cuisine: Restaurante mexicano)
- ✔ ADD **Soda y Cabinas Kaniki - Gandoca, Limón, Costa Rica** — Soda = eatery + cabinas (genuinely both)
- ✔ ADD **Totem Hotel Resort & Restaurant** — Restaurant in name

## stay — 2

- ✖ SKIP **La Casita de Monli** — "Casita" is a diminutive, not lodging evidence
- ❓ REVIEW **The Amazing Treehouse and Nature** — Treehouse nature venue with food — lodging? owner confirms

## things-to-do — 16

- ✔ ADD **Big Tree Wildlife Refuge - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica** — Wildlife refuge
- ✔ ADD **Black Shack Surf School - Playa Cocles, Puerto Viejo, Limón, Costa Rica** — Surf school
- ❓ REVIEW **Cabinas Surf Side - Cahuita, Limón, Costa Rica** — "Surf Side" = location, not activity; owner confirms
- ❓ REVIEW **Cahuita National Park Hotel - Cahuita, Limón, Costa Rica** — Hotel at the park — not itself an activity; owner confirms
- ❓ REVIEW **Casa Canopy** — Canopy may imply zipline/outdoor; owner confirms
- ✔ ADD **La Ceiba Nature Reserve - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica** — Nature reserve
- ❓ REVIEW **Papaya Wildlife Lodge - Cahuita, Limón, Costa Rica** — Lodge named Wildlife — attraction or location? owner confirms
- ✔ ADD **Rico Tico Tours** — Tours in name
- ✔ ADD **Roberto's Restaurant and Tours - Cahuita, Limón, Costa Rica** — Tours in name
- ✔ ADD **Spanish School Pura Vida** — School/classes
- ✔ ADD **Surf Meds Caribe - Playa Cocles, Puerto Viejo, Limón, Costa Rica** — Surf
- ✔ ADD **Surf the Jungle Surf School Adventures** — Surf school
- ✔ ADD **Tarponville Fishing Lodge - Manzanillo, Limón, Costa Rica** — Fishing lodge
- ✔ ADD **Tico Surf and Skate - Playa Cocles, Puerto Viejo, Limón, Costa Rica** — Surf/skate
- ✔ ADD **Vol'Air Dance Studio** — Dance studio = classes
- ❓ REVIEW **Wildlife Lodge Cahuita - Cahuita, Limón, Costa Rica** — Lodge named Wildlife — attraction or location? owner confirms

## shopping — 4

- ✖ SKIP **Casa Firefly Boutique Retreat - Cahuita, Limón, Costa Rica** — "Boutique retreat" = lodging, not a shop
- ✔ ADD **De Gustibus Bakery** — Bakery sells goods
- ✔ ADD **Iriria Specialty Coffee Shop** — Coffee shop = retail + eat
- ✔ ADD **Mendez Barber Shop** — Barber shop retail

## services — 2

- ✔ ADD **Taller Gabriel** — Taller = repair workshop
- ✔ ADD **Tattoo Studio 33** — Tattoo = personal care

## wellness — 14

- ✔ ADD **Aloha Skincare and Wellness** — Skincare + wellness
- ✖ SKIP **Ambar Tattoo Space** — Tattoo = services, not wellness
- ✔ ADD **Blossom Paradise Retreat - Playa Negra, Puerto Viejo, Limón, Costa Rica** — Retreat
- ✖ SKIP **Caribe Love Tattoo** — Tattoo = services, not wellness
- ✔ ADD **Casa Firefly Boutique Retreat - Cahuita, Limón, Costa Rica** — Retreat
- ✔ ADD **Chimuri Beach Retreat - Playa Negra, Puerto Viejo, Limón, Costa Rica** — Retreat
- ✔ ADD **Dragonfly Beach Retreat - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica** — Retreat
- ✔ ADD **Escondido Retreat - Playa Negra, Puerto Viejo, Limón, Costa Rica** — Retreat
- ✔ ADD **FISIOTERAPIA Agustin cuya** — Physiotherapy
- ✔ ADD **Kona Wellness Shala - Playa Cocles, Puerto Viejo, Limón, Costa Rica** — Wellness shala
- ✔ ADD **Shiosai Retreat Cabins - Gandoca, Limón, Costa Rica** — Retreat
- ✔ ADD **Sonora Jungle Retreat - Playa Negra, Puerto Viejo, Limón, Costa Rica** — Retreat
- ✔ ADD **TRIBU functional training** — Fitness
- ✖ SKIP **Tattoo Studio 33** — Tattoo = services, not wellness

## transport — 4

- ✔ ADD **Cahuita Bus Station - Cahuita, Limón, Costa Rica** — Bus station
- ✔ ADD **Main Bus Stop** — Bus stop
- ✔ ADD **Puerto Viejo Golf Carts** — Golf cart rental
- ✔ ADD **Terminal de Buses Sixaola - Sixaola, Limón, Costa Rica** — Bus terminal
