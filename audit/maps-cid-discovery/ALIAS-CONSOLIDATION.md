# Field-Preserving CID Alias Consolidation

## Outcome

- Same-CID clusters consolidated: 23
- Redundant alias rows removed: 29
- Canonical rows retained: 23
- Master rows after consolidation: 742
- Original alias rows and canonical before/after states: archived verbatim in `alias-row-archive.jsonl`.
- Conflicting values: retained in the archive and summarized in `alias-consolidation.csv`.

| CID | Canonical record | Removed aliases | Merged fields |
|---|---|---|---|
| 11623096819320863549 | Geckoes Lodge - Playa Cocles, Puerto Viejo, Limón, Costa Rica | Geckoes Lodge | Geckoes Lodge:whatsapp:filled |
| 11890875733593568965 | ATEC | Ecotourism and Conservation Association of Talamanca | Ecotourism and Conservation Association of Talamanca:email:filled / Ecotourism and Conservation Association of Talamanca:website:official-promoted |
| 11963087103971381770 | Soda Shekiná | Soda Shekina | No canonical field change |
| 13333726585970395954 | Villa Kandulu | Villas Kandulu | Villas Kandulu:whatsapp:filled |
| 15075381955885778012 | Caribbean Blue Morpho Casitas | Morpho Casitas | No canonical field change |
| 16671506007035121722 | Pecora Nera - Playa Cocles, Puerto Viejo, Limón, Costa Rica | La Pecora Nera Ristorante | La Pecora Nera Ristorante:website:filled / La Pecora Nera Ristorante:facebook:filled |
| 1705549831231309538 | Cabañas KiaMiMi | Cabinas KiAMiMi / Cabinas KiMiMi / Cabinas KlaMiMi | Cabinas KiAMiMi:instagram:filled |
| 17548818634857466246 | Hotel Rustika Lodge | Rustika Lodge | No canonical field change |
| 18141110668997261824 | Namu Garden Hotel and Spa | Namu Garden Hotel & Spa | No canonical field change |
| 2012278593659589679 | Sunshine Caribe - Playa Negra, Puerto Viejo, Limón, Costa Rica | Hotel Sunshine Caribe | No canonical field change |
| 2898935241958549311 | Azul Bar and Grill - Playa Negra, Puerto Viejo, Limón, Costa Rica | Repazul | Repazul:website:official-promoted |
| 3067085546718993771 | Casa Palliata | Casa Pallalita / Casa Pallita | Casa Pallita:email:filled |
| 3738318817422763383 | La Paloma Studio en Coclès con cocina a | Paloma Studio | Paloma Studio:instagram:filled |
| 4837747133838124638 | Le Caméléon - Playa Cocles, Puerto Viejo, Limón, Costa Rica | Le Cameleon Boutique Hotel | Le Cameleon Boutique Hotel:email:filled / Le Cameleon Boutique Hotel:youtube_url:filled / Le Cameleon Boutique Hotel:website:official-promoted |
| 5741623948918730601 | Cafe Rico | Café Rico | Café Rico:email:filled / Café Rico:youtube_url:filled / Café Rico:website:official-promoted |
| 5875257995302760665 | Da Lime Beach Club and Restaurant - Playa Chiquita, Puerto Viejo, Limón, Costa Rica | Da Lime Beach Club & Restaurant at Hotel Aguas Claras | Da Lime Beach Club & Restaurant at Hotel Aguas Claras:website:filled / Da Lime Beach Club & Restaurant at Hotel Aguas Claras:facebook:filled |
| 7100005996183210934 | Buddy's Sloth Crossing | Sloth Crossing | No canonical field change |
| 7437765293747491582 | Doctah Herbalist | The Bush / The Bush Doctah Herbalist | No canonical field change |
| 7972003479335139796 | Finca La Isla Botanical Garden - Playa Negra, Puerto Viejo, Limón, Costa Rica | Finca la Isla Permaculture Farm / La Isla Permaculture Farm | No canonical field change |
| 8816532573875491055 | Kaya's Place - Playa Negra, Puerto Viejo, Limón, Costa Rica | Playa Negra Brewing - Playa Negra, Puerto Viejo, Limón, Costa Rica | No canonical field change |
| 8923069820182897353 | Sea Breeze Events | La Selva PV Events | No canonical field change |
| 906367207779863842 | Cirrus Sky Paragliding CR | Paragliding CR | No canonical field change |
| 9842399411646961220 | Casa Chilamate Day House | El Chilamate / El Chilamate Holiday House | El Chilamate:phone:filled / El Chilamate:normalized_phone:filled |
