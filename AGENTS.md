# Puerto Viejo Business Discovery — Agent Context

## Purpose

Build and maintain a business directory of ~450 businesses within 5 km of
Puerto Viejo de Talamanca, Costa Rica, enriched with Instagram handles,
phone, WhatsApp, Booking.com, and Facebook data.

## Canonical files

| File | Purpose |
|------|---------|
| `pv_within_5km_enriched_b.csv` | Master dataset (450 records, 32 cols) |
| `pvscraper/` | Reusable PVS crawl + parse module |
| `codex_bridge.py` | Thin wrapper to delegate tasks to Codex CLI |
| `CODEX_ENDPOINT/` | IPC hub: requests in `requests/`, results in `responses/` |

## Delegation rules (OpenCode → Codex)

- OpenCode owns planning, decomposition, and integration.
- Codex executes bounded, specialized tasks.
- Delegations write only to assigned output paths — never modify master
  datasets unless explicitly instructed.
- No recursive delegation (Codex must not call OpenCode).
- Verify results by checking for expected artifacts, not prose.

## Codex CLI

- Binary: `~/.codex/.sandbox-bin/codex.exe` (v0.142.5)
- Non-interactive: `codex exec --ephemeral --sandbox danger-full-access "task"`
- Bridge: `python codex_bridge.py "task"` (defaults to `danger-full-access`)
- Bridge JSON output: `python codex_bridge.py --json "task"`
- Model: gpt-5.5

## Safety

- No paid APIs or commercial datasets.
- No Google login or API key.
- Sandbox helper (`codex-windows-sandbox-setup.exe`) has `CreateProcessWithLogonW` issues on this
  machine — `workspace-write` fails for shell commands. Use `danger-full-access` (safe on single-user
  dev machine).
- Playwright browser automation requires `danger-full-access`.
- Rate limits: 8-10s between Maps page loads, 2s between codex exec calls.
