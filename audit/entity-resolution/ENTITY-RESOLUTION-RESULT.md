# Broader Entity-Resolution Result

## Outcome

- Candidate pairs resolved: 142
- Deterministic duplicate merges: 4
- Separate-CID relationships retained: 121
- Related/shared-contact pairs retained: 8
- Single-signal pairs rejected: 9
- Canonical records after applied merges: 738

All removed rows and canonical before/after states are preserved in `merged-row-archive.jsonl`.

| Canonical | Removed alias | Preserved changes |
|---|---|---|
| Cariblue Beach and Jungle Resort - Playa Cocles, Puerto Viejo, Limón, Costa Rica | Hotel Cariblue | No field change |
| Jaguar Rescue Center - Playa Chiquita, Puerto Viejo, Limón, Costa Rica | Refugio de animales Jaguar | email:filled|website:filled|tripadvisor_url:filled|tiktok_url:filled |
| Douglasville Guesthouse | Douglas Ville guest house | google_maps_cid:transferred |
| Chile Rojo | Chili Rojo | instagram_handle:filled|instagram_url:filled |
