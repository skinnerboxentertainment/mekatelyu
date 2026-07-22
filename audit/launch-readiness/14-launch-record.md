# Launch Record — August 1, 2026

## Deployed artifact

| Field | Value |
|-------|-------|
| Commit | `01305235` |
| Branch | `master` |
| CI run | 29870632649 |
| Deployed at | 2026-07-21T21:36Z |
| Artifact | `paradisio-reduced-release` |
| Tests passing | 54/54 |
| Businesses | 737 |
| CSV SHA-256 | `ed6fd32d38c345eaf8d44dd202e76929c78390690625dc33dbe53a21d2846ef8` |
| Semantic taxonomy | `2026-07-21.1` |

## Verified gates

- [x] Build reproducible from clean checkout
- [x] 54 unit tests pass
- [x] Source-data invariants pass
- [x] Release artifact verified
- [x] Critical browser journeys pass (search, filter, map, detail, QR, closed-state)
- [x] No CSP console errors
- [x] Self-hosted Leaflet with SHA-256 manifest
- [x] Deployment and rollback rehearsed
- [x] QA feedback template added
- [x] Legacy cleanup committed

## Residual risks (accepted)

- 239 businesses (restaurants/services/shopping) have no amenity data
- `whappin.com` apex SSL pending (auto-resolves, up to 24h)
- `master` branch protection not yet enabled
- Enforce HTTPS not yet activated
- No screen-reader or keyboard audit completed
- No iOS physical device test

## Owner decisions recorded

| Decision | Value |
|----------|-------|
| Catalog risk | 104 blank→active, Casa Alegre merged, Casa Miluca→needs_verification |
| Correction ownership | Oscar AF |
| Legacy cleanup | Authorized and executed |
| Device testing | Pixel 7a (iOS: none) |
| Release ownership | Oscar AF |
