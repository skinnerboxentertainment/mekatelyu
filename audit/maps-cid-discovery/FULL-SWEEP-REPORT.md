# Full Missing-CID Discovery Sweep

## Outcome

- Records searched: 113
- Raw classifications: 88 exact, 15 probable, 10 ambiguous, 0 no result, 0 errors
- Safely applied to the local master: 55
- Safe but not applied (dry run): 0
- Existing/repeated CID collisions quarantined: 33
- Lower-confidence records held for review: 25
- Rejected for failed invariants: 0
- Evidence integrity: every accepted candidate requires a present screenshot whose SHA-256 matches the capture manifest.

## Guardrail

Probable, ambiguous, duplicate-CID, and pre-existing-CID cases are never automatically written. A collision can indicate a legitimate alias/duplicate listing or a legacy CID assigned to the wrong business; both require identity reconciliation.

## Review queues

| Business | Class | Observed Maps name | CID | Decision | Collision / reason |
|---|---|---|---|---|---|
| Casitas Mar y Luz - Playa Chiquita, Puerto Viejo, Limón, Costa Rica | exact | Hotel Casitas Mar y Luz | 8515965990195848246 | collision_review | Hidden Jungle Beach House - Playa Negra, Puerto Viejo, Limón, Costa Rica |
| La Ceiba Nature Reserve - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica | probable | La Ceiba Reserva Natural | 1693592634910607224 | review | classifier=probable |
| Samasati Yoga and Wellness Retreat - Hone Creek, Limón, Costa Rica | probable | Samasati Retreat Center | 2378802529330389577 | review | classifier=probable |
| Estrellas Cabinas | ambiguous | Results | 10951227846186482107 | review | Cabinas Monte Sol |
| Las Casitas de Playa Negra - Playa Negra, Puerto Viejo, Limón, Costa Rica | exact | Las Casitas de Playa Negra | 8689012956679917112 | collision_review | Douglasville Guesthouse |
| Uva Blue Jungle Villas - Playa Chiquita, Puerto Viejo, Limón, Costa Rica | exact | Uva Blue Villas | 9838950680602433731 | collision_review | Villa Laurel - Playa Cocles, Puerto Viejo, Limón, Costa Rica |
| Ginger and Cacao - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica | probable | Cabinas Ginger & Cacao | 1074114199983889358 | review | classifier=probable |
| El Sol del Caribe - Playa Cocles, Puerto Viejo, Limón, Costa Rica | exact | Sol del Caribe | 1216870082731283437 | collision_review | Flor del Caribe - Playa Cocles, Puerto Viejo, Limón, Costa Rica |
| Playa Negra Brewing - Playa Negra, Puerto Viejo, Limón, Costa Rica | exact | Playa Negra Brewing Beachfront Hotel | 8816532573875491055 | collision_review | Kaya's Place - Playa Negra, Puerto Viejo, Limón, Costa Rica |
| We Do Laundry - Hone Creek, Limón, Costa Rica | probable | WeDOlaundry - Caribe | 7766901451570548014 | review | classifier=probable |
| Centro Educativo Playa Chiquita Punta Uva - Playa Chiquita, Puerto Viejo, Limón, Costa Rica | probable | Playa Chiquita Education Center Punta Uva | 15763192850089670329 | review | classifier=probable |
| Proyecto Educativo Semillas de Paz - Playa Chiquita, Puerto Viejo, Limón, Costa Rica | ambiguous | Jardin Infantil Las Semillas | 938478883870584374 | review | classifier=ambiguous |
| Ceibo Adventure - Playa Chiquita, Puerto Viejo, Limón, Costa Rica | ambiguous | Jungle Green House | 10566257576749882719 | review | Green Jungle House - Playa Chiquita, Puerto Viejo, Limón, Costa Rica |
| Talamanca Chocolate - Playa Negra, Puerto Viejo, Limón, Costa Rica | probable | Cacao Huasi - chocolate classes, restaurant and sunset cocktails | 1242408439996904931 | review | Cacao Huasi |
| Servicentro Hone Creek - Hone Creek, Limón, Costa Rica | probable | Hone Creek Gas Station | 11028453782334017200 | review | classifier=probable |
| Hotel Cariblue | probable | Cariblue Beach and Jungle Resort | 14658668036585456092 | review | Cariblue Beach and Jungle Resort - Playa Cocles, Puerto Viejo, Limón, Costa Rica |
| Hotel Posada Nena | probable | Posada Nena Caribe, Puerto Viejo de Talamanca - Deluxe Double Room with Balcony | 11698915664369749164 | review | classifier=probable |
| Hotel Sunshine Caribe | exact | SUNSHINE CARIBE | 2012278593659589679 | collision_review | Sunshine Caribe - Playa Negra, Puerto Viejo, Limón, Costa Rica |
| Le Cameleon Boutique Hotel | exact | Le Cameleon Hotel Puerto Viejo | 4837747133838124638 | collision_review | Le Caméléon - Playa Cocles, Puerto Viejo, Limón, Costa Rica |
| Paula's and Daniel's Homestay | ambiguous | Results | 1261667056997797786 | review | La Casa de Rolando |
| Café Rico | exact | Cafe Rico | 5741623948918730601 | collision_review | Cafe Rico |
| Chili Rojo | probable | Umi Rojo | 2449275981368445735 | review | Chile Rojo |
| Panadería Francés | ambiguous | De Gustibus Bakery - Puerto Viejo | 9034432070677152199 | review | De Gustibus Bakery |
| Ecotourism and Conservation Association of Talamanca | exact | ATEC Talamanca Association of Ecotourism and Conservation | 11890875733593568965 | collision_review | ATEC |
| Refugio de animales Jaguar | ambiguous | Jaguar Rescue Center | 9435208628058025334 | review | Jaguar Rescue Center - Playa Chiquita, Puerto Viejo, Limón, Costa Rica |
| Cabinas KiAMiMi | exact | Cabinas KiaMiMi | 1705549831231309538 | collision_review | Cabañas KiaMiMi |
| Cabinas KiMiMi | exact | Cabinas KiaMiMi | 1705549831231309538 | collision_review | Cabañas KiaMiMi |
| Cabinas KlaMiMi | exact | Cabinas KiaMiMi | 1705549831231309538 | collision_review | Cabañas KiaMiMi |
| Casa Alegre | probable | Casa Rio | 4666775397025577928 | review | Casa Rio Restaurant & Bar - Playa Cocles, Puerto Viejo, Limón, Costa Rica |
| Casa Miluca | probable | Casa Maryluz | 18072482811082707755 | review | classifier=probable |
| Casa Pallalita | exact | Casa Palliata | 3067085546718993771 | collision_review | Casa Palliata |
| Casa Pallita | exact | Casa Palliata | 3067085546718993771 | collision_review | Casa Palliata |
| Da Lime Beach Club & Restaurant at Hotel Aguas Claras | exact | Da Lime Beach Club & Restaurant at Hotel Aguas Claras | 5875257995302760665 | collision_review | Da Lime Beach Club and Restaurant - Playa Chiquita, Puerto Viejo, Limón, Costa Rica |
| El Chilamate | exact | El Chilamate Holiday House | 9842399411646961220 | collision_review | Casa Chilamate Day House |
| El Chilamate Holiday House | exact | El Chilamate Holiday House | 9842399411646961220 | collision_review | Casa Chilamate Day House |
| Finca la Isla Permaculture Farm | exact | Finca la Isla Permaculture Farm, Plant Nursery and Botanical Garden | 7972003479335139796 | collision_review | Finca La Isla Botanical Garden - Playa Negra, Puerto Viejo, Limón, Costa Rica |
| La Isla Permaculture Farm | exact | Finca la Isla Permaculture Farm, Plant Nursery and Botanical Garden | 7972003479335139796 | collision_review | Finca La Isla Botanical Garden - Playa Negra, Puerto Viejo, Limón, Costa Rica |
| La Pecora Nera Ristorante | exact | La Pecora Nera Ristorante | 16671506007035121722 | collision_review | Pecora Nera - Playa Cocles, Puerto Viejo, Limón, Costa Rica |
| La Selva PV Events | exact | La Selva PV Events | 8923069820182897353 | collision_review | Sea Breeze Events |
| Morpho Casitas | exact | Caribbean Blue Morpho Casitas | 15075381955885778012 | collision_review | Caribbean Blue Morpho Casitas |
| Namu Garden Hotel & Spa | exact | Namu Garden Hotel & Spa | 18141110668997261824 | collision_review | Namu Garden Hotel and Spa |
| Paloma Studio | exact | La Paloma Studio en Coclès con cocina à 800 m de la playa | 3738318817422763383 | collision_review | La Paloma Studio en Coclès con cocina a |
| Paragliding CR | exact | Cirrus Sky Paragliding CR | 906367207779863842 | collision_review | Cirrus Sky Paragliding CR |
| Repazul | exact | Repazul Puerto Viejo Limón Costa Rica | 2898935241958549311 | collision_review | Azul Bar and Grill - Playa Negra, Puerto Viejo, Limón, Costa Rica |
| Rustika Lodge | exact | Hotel Rustika Lodge | 17548818634857466246 | collision_review | Hotel Rustika Lodge |
| Sloth Crossing | exact | Buddy's Sloth Crossing | 7100005996183210934 | collision_review | Buddy's Sloth Crossing |
| Soda Shekina | exact | Soda Shekina | 11963087103971381770 | collision_review | Soda Shekiná |
| The Bush | exact | The Bush Doctah Herbalist | 7437765293747491582 | collision_review | Doctah Herbalist |
| The Bush Doctah Herbalist | exact | The Bush Doctah Herbalist | 7437765293747491582 | collision_review | Doctah Herbalist |
| Villas Kandulu | exact | Villas Kandulu | 13333726585970395954 | collision_review | Villa Kandulu |
| Boca Chica Bar Restaurante y Piscina - Cahuita, Limón, Costa Rica | probable | KOKi Beach Restaurant & Bar | 94575443808973745 | review | KOKi Beach |
| El Colibri Rojo - Cahuita, Limón, Costa Rica | probable | Le Colibri Rouge Hotel Cabinas | 903286394928674373 | review | classifier=probable |
| La Fundación Cahuita Playing for Change - Cahuita, Limón, Costa Rica | probable | Playing for Change Cahuita | 14444699894257942648 | review | classifier=probable |
| Se Ua Bed and Breakfast - Manzanillo, Limón, Costa Rica | ambiguous | Se Ua | 15469928124041183357 | review | classifier=ambiguous |
| TKD Caribe - Cahuita, Limón, Costa Rica | ambiguous | Sport Body Gym | 7364638263800075443 | review | Sport Body Gym - Cahuita, Limón, Costa Rica |
| Kinawe Cabinas | ambiguous | Results | 1064329827366942288 | review | classifier=ambiguous |
| Geckoes Lodge | exact | Geckoes Lodge | 11623096819320863549 | collision_review | Geckoes Lodge - Playa Cocles, Puerto Viejo, Limón, Costa Rica |
| Puerto Viejo de Talamanca | ambiguous | Playa Negra | 1386465364860297778 | review | classifier=ambiguous |
