# CODEX_ENDPOINT — IPC Hub

This directory is the shared communication channel between **OpenCode** (this session)
and **OpenAI Codex CLI** (subprocess / MCP server).

## Directory layout

```
CODEX_ENDPOINT/
├── README.md              ← This file: protocol, layout, conventions
├── inbox/                 ← Tasks from one agent to the other
│   └── *.json
├── outbox/                ← Results from the processing agent
│   └── *.json
└── requests/              ← Long-form adversarial research requests
    └── *.md
```

## IPC Protocol (File-based)

When subprocess / MCP channels are unavailable, agents fall back to file-based IPC:

1. **Sender** writes a JSON task into `inbox/` with a unique ID.
   Schema: `{ "id": "str", "from": "opencode"|"codex", "type": "str", "payload": {} }`

2. **Receiver** polls or watches `inbox/`, processes the task, writes the result
   to `outbox/{id}.json`.
   Schema: `{ "id": "str", "status": "ok"|"error", "result": {} }`

3. **Sender** reads the result from `outbox/` and cleans up both files.

No locking — tasks are designed to be idempotent and collision-resistant via UUID IDs.
