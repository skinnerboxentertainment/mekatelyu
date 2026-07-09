# Paradisio — Puerto Viejo Business Board

## Purpose

A persistent web directory of ~750 businesses within 5 km of Puerto Viejo
de Talamanca, Costa Rica, with classifieds, QR codes, Maps enrichment,
WhatsApp/Instagram routing, and interactive maps. Built as a static site
on GitHub Pages. Zero infrastructure.

## Canonical files

| File | Purpose |
|------|---------|
| `pv_master_unified.csv` | Master dataset (750 records, 34 cols) |
| `paradisio_app/build.py` | Static app generator |
| `pvscraper/` | Reusable PVS crawl + parse module |
| `codex_bridge.py` | Thin wrapper to delegate tasks to Codex CLI (v2 session-aware) |
| `CODEX_ENDPOINT/` | IPC hub: v2 session-based bidirectional protocol |

## Delegation rules (OpenCode → Codex)

- OpenCode owns planning, decomposition, and integration.
- Codex executes bounded, specialized tasks.
- Delegations write only to assigned output paths — never modify master
  datasets unless explicitly instructed.
- No recursive delegation (Codex must not call OpenCode).
- Verify results by checking for expected artifacts, not prose.

## Protocols

### v1 — One-Shot (fire and forget)

For simple, non-iterative tasks:

```powershell
python codex_bridge.py "task" --json
```

### v2 — Session Bidirectional (ping-pong)

For iterative tasks requiring back-and-forth refinement:

```powershell
# Create a session
python CODEX_ENDPOINT\session_orchestrator.py create --title "My Task" --description "Do X"

# Run the next turn (appends instruction, invokes Codex)
python CODEX_ENDPOINT\session_orchestrator.py next --session-id <id> --message "Now change Y"

# Check status
python CODEX_ENDPOINT\session_orchestrator.py status --session-id <id>

# Retry a failed turn
python CODEX_ENDPOINT\session_orchestrator.py retry --session-id <id>
```

## Codex CLI

- Binary: `~/.codex/.sandbox-bin/codex.exe` (v0.142.5)
- Model: gpt-5.5
- One-shot: `python codex_bridge.py "task"` (defaults to `danger-full-access`)
- Session: `python codex_bridge.py --session <id>` (bridge reads session, spawns Codex, validates post-state)

## Safety

- No paid APIs or commercial datasets.
- No Google login or API key.
- Sandbox helper (`codex-windows-sandbox-setup.exe`) has `CreateProcessWithLogonW` issues on this
  machine — `workspace-write` fails for shell commands. Use `danger-full-access` (safe on single-user
  dev machine).
- Playwright browser automation requires `danger-full-access`.
- Rate limits: 8-10s between Maps page loads, 2s between codex exec calls.
