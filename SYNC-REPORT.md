# Paradisio — Sync Report for ChatGPT

## Project
Paradisio — static business directory for Puerto Viejo, Costa Rica (~737 businesses).
Repo: `skinnerboxentertainment/mekatelyu`
Domain: `whappin.com` → `www.whappin.com` (recommended canonical)

---

## What was accomplished (July 20-21, 2026)

### Owner decisions resolved (5 items from `11-authority-tail-handoff.md`)
1. **Catalog risk** — 104 blank-status businesses with CIDs set to `active`; Casa Alegre removed (duplicate of Casa Alegra, same coords); Casa Miluca set to `needs_verification` (no CID, CID attempt resolved to wrong target). Canonical count: 738 → 737.
2. **Correction ownership** — Oscar AF
3. **Legacy cleanup** — Deleted 334 files (255 screenshots, 8 agent sessions, 6 request docs, 27 temp scripts, 24 intermediate CSVs, checkpoint logs, opencode session file)
4. **Device testing** — Pixel 7a available; no iOS device
5. **Release ownership** — Oscar AF

### Code/Data changes
- `pv_master_unified.csv`: 737 rows, 0 blank statuses (711 active, 23 needs_verification, 3 closed)
- `tests/test_entity_resolution.py`: count 738→737
- `tests/test_semantic_artifact.py`: count 738→737
- `tests/test_remaining_maps_evidence.py`: handle removed Casa Alegre row
- `scripts/verify_source_data.py`: expected count 738→737
- `scripts/verify_release.py`: default 738→737
- `.github/workflows/launch-readiness.yml`: added deploy job, Pages permissions, `actions/upload-pages-artifact` + `actions/deploy-pages`
- `paradisio_app/generate_qr.py`: `DEFAULT_BASE_URL` → `https://whappin.com/paradisio_app`

### Git history (on `launch/aug1-directory-base`)
```
91a831d8 checkpoint: legacy cleanup
4fe365df checkpoint: catalog cleanup — 104 blank→active, merge Casa Alegre, Casa Miluca→needs_verification, 738→737
480058fb Normalize vendor hashes across platforms
86c8e50b Make Playwright optional in launch CI
8f97c591 Prepare August 1 reduced directory release candidate
6f40dd80 support cash payments alongside SINPE (baseline)
```

### Deployment status
- **Branch:** `master` (PR #1 merged, PR #2 deployed)
- **CI:** Launch readiness workflow passes (54 tests, source verifier, release verifier)
- **GitHub Pages:** switched from legacy `master:/docs` to Actions artifact (`build_type: workflow`)
- **Custom domain:** `whappin.com` configured in Pages settings
- **CNAME:** `www` → `skinnerboxentertainment.github.io.` set at GoDaddy
- **Forwarding:** GoDaddy forwarding `whappin.com` → `https://www.whappin.com` was set but needs to be removed (creates redirect loop with GitHub Pages auto-redirect)

### Remaining DNS work (GoDaddy)
The following changes still need to be made in GoDaddy DNS:

1. **Change Pages custom domain** from `whappin.com` to `www.whappin.com` (in GitHub repo Settings → Pages)
2. **Replace 2 apex A records** pointing to GoDaddy IPs (`15.197.142.173`, `3.33.152.147`) with GitHub's 4 A records:
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
3. **Remove** GoDaddy domain forwarding rule (GitHub auto-redirects apex → www)
4. Keep CNAME `www` → `skinnerboxentertainment.github.io.` ✅ (already correct)
5. Keep NS, SOA, `_domainconnect`, `_dmarc` records as-is

### Verification
- 54/54 tests passing
- Source data verifier: PASS
- Release verifier: PASS
- CI on master: SUCCESS (build + deploy)
- Smoke tests not yet run against live `www.whappin.com` (awaiting DNS)

### Remaining launch steps
- [ ] Fix DNS / Pages config as outlined above
- [ ] Wait for DNS propagation + SSL cert provisioning (up to 24h)
- [ ] Enable "Enforce HTTPS" in Pages settings
- [ ] Run production smoke tests at `https://www.whappin.com/`
   - root redirect, home data load, search, filters, map, active/closed profiles, WhatsApp links, QR download, correction link, sitemap, robots, 404
- [ ] Rollback rehearsal — verify ability to redeploy previous artifact
- [ ] Pixel 7a device test

### Key files to read for context
- `audit/launch-readiness/13-aug1-release-candidate-handover.md` — authoritative handover
- `audit/launch-readiness/11-authority-tail-handoff.md` — owner decisions
- `HANDOVER.md` — entry point
- `TURNOVER.md` — full project turnover
- `AGENTS.md` — agent operation protocols
- `README.md` — public-facing description
