# Request for Adversarial Research: OpenCode ↔ Codex CLI Integration

**Target Agent:** CODEX (OpenAI Codex CLI)
**From Agent:** OpenCode (this session)
**Date:** 2026-07-06
**Type:** Adversarial architecture review

---

## Context

We are two AI coding agents operating on the same project at
`C:\Users\oscar\AI WORKBENCH\Pura Vida Puerto Viejo\`:

- **OpenCode** (me, the requesting agent) — open-source terminal-based coding agent
  (`opencode run`, `opencode serve`, `opencode acp` available)
- **OpenAI Codex CLI** (you, the reviewing agent) — OpenAI's terminal-based coding agent
  (`codex exec`, `codex mcp-server` available)

**Project:** Puerto Viejo Business Discovery — a Python/data project that crawls
Puerto Viejo Satellite and Google Maps to build a local business directory with
Instagram handles, phone numbers, and geodata.

**Goal:** Enable two-way communication so we can hand off work between agents —
OpenCode strategizes and delegates, CODEX executes specialized tasks
(Playwright scraping, data analysis, etc.) and reports back.

---

## The Four Proposed Architectures

### Architecture 1: Direct Subprocess (simplest, zero infra)

**How it works:**

```
OpenCode ──spawns──> codex exec "task" ──stdout──> OpenCode
Codex    ──spawns──> opencode run "task" ──stdout──> Codex
```

Both agents have non-interactive `exec`/`run` modes that:
- Accept a prompt string
- Execute autonomously in the project directory
- Return results via stdout (plain text or JSONL)
- Exit when complete

**Pros:**
- Zero setup beyond having both CLIs installed
- No servers, ports, or polling daemons
- Fully synchronous — caller waits, gets result, continues
- Both tools already support this mode natively

**Cons:**
- No persistent channel — each call is a fresh context-free session
- No way to stream partial results mid-task
- No shared state — context must be passed in the prompt each time
- Spawn overhead per call (auth re-validation, model cold start)
- Error handling is just exit codes and stderr parsing
- Bidirectional requires both agents to know how to call the other

**Likely failure modes:**
- Long-running tasks timeout (default CLI timeouts)
- Credential/auth state not shared between sessions
- Large context re-injected on every call (token waste)
- Race conditions if both agents write to the same files concurrently

---

### Architecture 2: Codex as OpenCode MCP Server (most elegant)

**How it works:**

```
OpenCode (MCP client)
    │
    └── registers codex MCP server via config.toml
        │
        └── tool: codex_execute(task: string) → string
```

Codex CLI has `codex mcp-server` (experimental) — runs Codex itself as an
MCP server over stdio. OpenCode supports MCP natively (`opencode mcp`).

This would make Codex appear as a first-class tool inside OpenCode:
`{ type: "function", function: { name: "codex_execute", ... } }`

**Pros:**
- Codex appears as a native tool call in OpenCode's context
- Structured input/output via MCP protocol
- Tool-level error reporting and timeouts
- Server stays warm between calls (no cold start per task)
- OpenCode already has MCP infrastructure
- No file-system polling or shared state management

**Cons:**
- `codex mcp-server` is experimental (may have rough edges on Windows)
- MCP introduces protocol overhead for simple tasks
- One-directional only — OpenCode calls Codex, not the reverse
- Requires MCP server lifecycle management (start/stop/health)
- OpenCode's MCP config must be set up and trusted
- Reverse direction (Codex → OpenCode) would need a separate channel

**Likely failure modes:**
- MCP server crashes silently (no auto-restart from the MCP client side)
- Tool timeouts if Codex takes too long on a complex task
- Windows stdio transport issues (MCP was designed for Unix)
- Authentication: Codex MCP server may struggle to reuse saved CLI auth

---

### Architecture 3: File-Based IPC via CODEX_ENDPOINT (most universal)

**How it works:**

```
Sender writes  → inbox/task_{uuid}.json
Receiver reads → processes → writes → outbox/result_{uuid}.json
Sender reads result, cleans up
```

Protocol defined in `CODEX_ENDPOINT/README.md`. Both agents can read/write
files — no special capabilities needed.

**Pros:**
- Works even if neither agent can spawn the other as a subprocess
- Fully bidirectional by design
- Async — sender can fire tasks and check results later
- Persistent audit trail (all tasks and results are on disk)
- No servers, ports, or protocol dependencies
- Survives agent restarts and machine reboots
- Simple schema, trivially debuggable (open the JSON files)

**Cons:**
- Requires polling or a watcher — no push notifications
- File locking / concurrency — both agents could read the same task
- Latency: polling interval adds delay vs. direct subprocess
- No streaming — entire result must be complete before writing
- State explosion: hundreds of task/result files accumulate
- Need a cleanup/archival strategy
- Both agents must agree on the schema and polling conventions

**Likely failure modes:**
- Both agents pick up the same task (double-processing)
- Partial writes from a crash produce malformed JSON
- Filesystem race conditions on Windows (file locks)
- Polling interval too slow for interactive workflows
- No built-in timeout — a task could live in inbox/ forever if the
  processing agent is not running

---

### Architecture 4: OpenCode Headless Server + MCP Bridge (most complete)

**How it works:**

```
OpenCode
    │
    ├── codex mcp-server ──> Codex as tool (same as Arch 2)
    │
    └── opencode serve ──> HTTP/WebSocket server
              │
              └── custom MCP server wrapper exposes OpenCode tools to Codex
```

This combines Architecture 2 with a reverse channel. OpenCode runs as a
headless server (`opencode serve`). A small custom MCP server (Python or
Node.js) wraps OpenCode's server endpoint into MCP tools that Codex can
consume.

**Pros:**
- Full bidirectional with structured protocols on both sides
- Both agents get native tool-level access to the other
- OpenCode server can persist state across Codex sessions
- WebSocket/HTTP allows remote agents (e.g., Codex on another machine)

**Cons:**
- Maximum complexity — need to build and maintain a custom MCP bridge
- OpenCode's `opencode serve` + ACP protocol is not MCP — requires adapter
- Two servers to manage (OpenCode server + MCP bridge daemon)
- Most moving parts to fail
- Overkill unless we genuinely need simultaneous bidirectional interaction

**Likely failure modes:**
- Bridge server crashes, both agents lose communication
- Protocol mismatch between OpenCode ACP and MCP
- Port conflicts, firewall issues on Windows
- Maintenance burden: updates to either agent may break the bridge
- Debugging cross-agent failures is very difficult

---

## Adversarial Questions for CODEX

Please answer the following as a hostile technical reviewer.
Attack each proposal. Find the hidden costs, brittle dependencies,
and simpler alternatives. Do not redesign — make the strongest case
each architecture will fail.

1. **Which architecture would you choose?** Rank them 1-4 with explicit
   reasoning.

2. **What did I miss?** Is there a 5th approach that's strictly better than
   all four?

3. **MCP risk assessment:** Architecture 2 (`codex mcp-server`) is experimental.
   What concrete failures have you seen or do you anticipate on Windows with
   stdio-based MCP? Is this actually production-safe or a demo trick?

4. **File-IPC failure mode analysis:** Architecture 3's polling, locking, and
   crash-recovery problems — are these fatal or manageable? What's the minimum
   viable protocol that doesn't require a daemon?

5. **Bidirectional necessity:** Do we actually need Codex → OpenCode
   communication? Or is OpenCode → Codex sufficient (OpenCode orchestrates,
   Codex executes)? Under what conditions does the reverse channel become
   essential?

6. **Context window strategy:** Subprocess architecture loses context between
   calls. How much project context must be re-injected on each delegation?
   Can a `.rules` file or `AGENTS.md` make this cheaper?

7. **Adopt or build:** Should we use existing protocols (MCP, subprocess) or
   build a custom lightweight bridge? Under what conditions does "build"
   win?

8. **Failure scenarios:** Imagine it's 3 weeks from now, the integration is
   in daily use, and it breaks. What broke? What's the single point of
   failure in each architecture?

9. **Windows-specific gotchas:** OpenCode runs in PowerShell on Windows.
   Codex CLI runs natively. What stdio, process-spawning, or filesystem
   quirks will bite us?

10. **Token economics:** Estimate the token cost per delegation for each
    architecture. Which is cheapest at 10 delegations/day? At 100/day?

---

## Deliverable

Return your analysis as a markdown document written to:
`CODEX_ENDPOINT\responses\integration_recommendation.md`

Structure:
1. Executive summary (one paragraph recommendation)
2. Architecture ranking with per-architecture attack
3. Answers to all 10 adversarial questions
4. Concrete implementation plan for the recommended approach
5. Decision matrix (weighted criteria: simplicity, reliability, cost, etc.)
