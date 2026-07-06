# Adversarial Review: OpenCode ↔ Codex Integration

**Reviewer:** Codex  
**Date:** 2026-07-06  
**Scope:** Architecture review, not implementation approval

## 1. Executive summary

Choose **Architecture 1, one-way direct subprocess delegation from OpenCode to Codex**, but only after a small capability probe proves that the exact OpenCode host process can launch the exact Codex CLI installation non-interactively. Add a thin, versioned wrapper that accepts a task manifest, invokes Codex, captures structured output, enforces timeouts, and writes an append-only audit record. Use `AGENTS.md` for durable repository context and pass only task-specific deltas per call. Do **not** begin with `codex mcp-server`, bidirectional orchestration, or a custom bridge. The premise that both installed applications can mutually spawn one another is currently unproven: from this Codex desktop thread, the packaged `codex.exe` resolves but cannot be launched from the workspace (`Access is denied`), while `opencode` is absent from this process's `PATH`. Keep file IPC as a manual recovery queue, not the primary transport. Reconsider MCP only after subprocess delegation has demonstrated a real need for persistent tool sessions or streaming.

This recommendation is deliberately less ambitious than the proposal. The integration's job is not to make two agents converse. Its job is to hand a bounded task to one executor, obtain a machine-checkable result, and leave a trace a human can audit.

## 2. Architecture ranking and attacks

### Rank 1 — Architecture 1: Direct subprocess

**Why it wins:** It has the fewest independent failure domains and the clearest ownership model. OpenCode calls Codex; Codex returns a result and exits. Process exit, timeout, stdout, stderr, and an output artifact are enough to define success.

**Attack:**

- “Zero infrastructure” is false. A reliable caller still needs executable discovery, quoting, environment isolation, timeout and cancellation, output limits, schema validation, log redaction, and cleanup.
- Mutual spawning invites recursive delegation: A calls B, B calls A, and each believes the other owns completion. One-way ownership must be enforced.
- Windows app-packaged executables may resolve through aliases yet fail when launched from a different security context. That exact failure occurred during this review.
- A model process exiting with code 0 does not mean the task succeeded. Completion must be tied to an expected artifact or validated result schema.
- Passing prompts on the command line leaks them into process inspection and breaks on quoting/length limits. Use stdin or a manifest file.
- Every fresh session pays instruction and repository-discovery cost unless durable context is stored in the repository.
- Unbounded `exec` can mutate the same checkout while the parent agent is also editing it.

**Verdict:** Best starting point, but only behind a disciplined adapter and single-writer policy.

### Rank 2 — Architecture 3: File-based IPC

**Why it is second:** It is transparent, durable, asynchronous, and independent of whether one agent can spawn the other. It is excellent as a dead-letter queue and human-observable handoff mechanism.

**Attack:**

- A directory is not a scheduler. Nothing guarantees a receiver is alive, wakes up, owns a task, or finishes it.
- The current protocol has no atomic publish rule, claim state, lease, attempt count, deadline, cancellation, schema version, checksum, or idempotency key.
- “Sender cleans up” destroys the claimed audit-trail benefit.
- `inbox` and `outbox` alone cannot distinguish queued, running, expired, cancelled, failed-retryable, and permanently failed work.
- A watcher embedded in an interactive agent is not persistent. Once the turn ends, monitoring ends unless a separate scheduler/automation exists.
- Exactly-once processing is not achievable with this design. At best, use at-least-once delivery plus idempotent handlers.
- Antivirus, indexing, cloud sync, and Windows file sharing can delay renames or temporarily lock files.

**Verdict:** Manageable, not fatal, if reduced to an atomic spool protocol. Poor as an interactive primary transport; good as fallback and audit.

### Rank 3 — Architecture 2: Codex as OpenCode MCP server

**Why it ranks below file IPC:** MCP provides a useful tool contract, but the proposal assumes that `codex mcp-server` exposes the desired stable execution semantics, that OpenCode interoperates with its exact transport and lifecycle behavior, and that Windows process/auth handling works. Those are integration tests, not facts established by the request.

**Attack:**

- “Server stays warm” does not imply conversational continuity. Tool calls may still create independent runs unless the server explicitly exposes durable session identifiers.
- MCP standardizes messages, not task correctness, filesystem coordination, authentication reuse, cancellation quality, or recovery after a half-completed edit.
- A stdio child has no independent health endpoint. If it hangs without closing pipes, the client sees a timeout, not a diagnosis.
- Logging anything to stdout can corrupt a stdio protocol stream; all human diagnostics must go to stderr.
- Client and server may disagree about initialization, capability negotiation, progress notifications, cancellation, maximum message size, and tool-result encoding.
- A long agent run is a poor fit for a single synchronous tool call unless the client has generous, configurable timeouts.
- It solves only OpenCode → Codex. Adding another mechanism for reverse calls forfeits much of the alleged elegance.
- Experimental CLI commands can change flags, tool schemas, or lifecycle behavior across upgrades.

OpenAI documents MCP as a Codex customization/integration surface, but documentation of MCP support is not a production guarantee for this particular OpenCode/Codex/Windows combination. Treat it as a candidate transport requiring a compatibility test matrix, not as a stable internal API. See [Codex customization](https://developers.openai.com/codex/concepts/customization) and [Codex documentation](https://developers.openai.com/codex/).

**Verdict:** Pilot later if subprocess startup overhead becomes material or native tool semantics provide measurable value.

### Rank 4 — Architecture 4: OpenCode server plus MCP bridge

**Why it loses:** It adds a custom adapter, two server lifecycles, protocol translation, port management, state ownership, and cross-version maintenance before proving that bidirectionality is needed.

**Attack:**

- The bridge becomes an undocumented distributed system: correlation, retries, cancellation, authentication, backpressure, and trace propagation all become your responsibility.
- Translating ACP/HTTP/WebSocket concepts into MCP tool calls is semantic adaptation, not simple plumbing.
- A persistent server expands the local attack surface and requires binding, authentication, and secret-handling decisions.
- Debugging now spans four logs: OpenCode, bridge, Codex MCP, and the task process.
- Updates on either side can break the bridge even when both products work independently.
- Simultaneous editing remains unsolved. Better communication does not prevent checkout corruption.

**Verdict:** Reject until a measured workload proves that simpler one-way delegation cannot meet requirements.

## 3. Answers to the adversarial questions

### 1. Which architecture would you choose?

Ranking: **1 → 3 → 2 → 4**.

1. **Direct subprocess:** least state and clearest failure boundary.
2. **File IPC:** robust fallback and durable queue if made atomic.
3. **MCP:** attractive interface, but greater compatibility and lifecycle uncertainty than the proposal admits.
4. **Custom bridge:** unjustified distributed-systems cost.

The ranking optimizes for reliable task completion in one local repository, not architectural elegance.

### 2. What was missed? A fifth approach

The best fifth approach is not another agent-to-agent chat channel. It is a **task-runner adapter with artifact-based handoff**:

```text
OpenCode
  -> writes immutable task manifest
  -> invokes codex-adapter once
  -> adapter runs Codex in an isolated worktree or designated output directory
  -> validates result.json + expected artifacts
  -> returns a compact status to OpenCode
```

This is Architecture 1 with the dangerous details pulled into a deterministic boundary. It is strictly better for this use case because it separates:

- orchestration from model prompting;
- transport success from task success;
- agent output from validated artifacts;
- repository context from per-task context;
- execution from integration into the main checkout.

If “strictly better” means zero new code, then no fifth option qualifies. The adapter costs a small amount of code, but far less than an MCP bridge.

### 3. MCP risk assessment on Windows

No honest reviewer should claim production safety without testing the exact version pair. Concrete anticipated failures include:

- executable aliases resolving differently in interactive PowerShell and child-process environments;
- `CreateProcess` access failures for packaged applications;
- `.cmd`/`.ps1` shim invocation requiring the correct shell;
- quoting differences for JSON, backslashes, spaces, and Unicode paths;
- CRLF-sensitive line readers;
- code-page mismatches when a process does not use UTF-8;
- stdout contamination by banners, update notices, or debug logs;
- inherited proxy/auth/environment variables differing from the user's terminal;
- pipe-buffer deadlock when a parent reads stdout but not stderr concurrently;
- orphaned grandchildren after timeout;
- client timeout while the server continues mutating files;
- antivirus scanning or file locks delaying startup and artifact publication.

During this review, `codex.exe` was discoverable at a WindowsApps path but the current host process received `Access is denied` when launching it. This is direct evidence that “installed” and “spawnable from the orchestrator” are different properties.

MCP itself is not a demo trick. Treating an experimental CLI server plus a different client implementation as production-safe without soak tests would be.

### 4. File-IPC failure analysis and minimum viable protocol

The problems are manageable if the protocol accepts **at-least-once**, not exactly-once, processing.

Minimum viable protocol:

1. Sender writes `tmp/{uuid}.json`, flushes and closes it.
2. Sender atomically renames it to `queued/{uuid}.json`.
3. Receiver atomically renames it to `running/{uuid}.{worker}.json` to claim it.
4. Receiver periodically updates a separate lease file with `lease_expires_at`.
5. Receiver writes the result to a temporary file, then atomically renames it into `completed/` or `failed/`.
6. Tasks contain `schema_version`, `id`, `created_at`, `deadline`, `attempt`, `max_attempts`, `idempotency_key`, `cwd`, `requested_outputs`, and a content hash.
7. Results contain `status`, `started_at`, `finished_at`, `exit_code`, `summary`, `artifacts`, and error classification.
8. Never delete automatically. Move old records to date-partitioned archives.

No daemon is required if the sender launches a receiver once after publishing or if a human/automation periodically drains the queue. Without either, it is a mailbox, not active IPC.

### 5. Is bidirectional communication necessary?

No. **OpenCode → Codex is sufficient** while OpenCode owns planning, decomposition, retries, and integration.

Reverse communication becomes essential only when Codex must:

- ask a blocking question during execution and suspend safely;
- delegate a specialized operation available only through OpenCode;
- stream progress for an interactive human decision;
- negotiate shared resources or locks;
- initiate unsolicited work based on an event it monitors.

Even then, a reverse agent invocation is usually the wrong abstraction. Codex should return `needs_input` with a structured question, or call a narrow purpose-built tool. Agent A calling agent B, which then calls A, creates cycles, ambiguous authority, and unpredictable token multiplication.

### 6. Context-window strategy

Do not re-inject the whole project history. Split context into three layers:

1. **Durable repository context:** `AGENTS.md` with purpose, canonical dataset, safety boundaries, commands, output conventions, and verification requirements.
2. **Task manifest:** objective, inputs, allowed write locations, expected artifacts, acceptance tests, and budget.
3. **References on demand:** paths to relevant briefs, schemas, and datasets.

Codex supports repository guidance through `AGENTS.md`; nested files can narrow instructions by subtree. This makes durable context cheaper and less error-prone than repeating it in every prompt. See [Codex customization](https://developers.openai.com/codex/concepts/customization).

For this repository, a delegation usually needs 300–1,000 tokens of task-specific text once durable guidance exists. Sending the previous conversation or README on every task is waste.

### 7. Adopt or build?

Adopt subprocess execution first. Build only the thinnest adapter needed to make it reliable.

“Build” wins when at least one is true:

- more than one caller needs the same execution contract;
- retries and idempotency are recurring operational needs;
- structured artifacts must be validated automatically;
- tasks need isolation in worktrees;
- observability is required for daily use;
- measured startup/context overhead materially dominates task cost.

Do not build a protocol translator merely because both products expose different protocols. A custom bridge is justified only after workload traces show that subprocess plus manifests cannot meet latency, continuity, or interaction requirements.

### 8. Three-weeks-later failure scenarios

| Architecture | Most likely break | Single point of failure |
|---|---|---|
| Subprocess | CLI update changes flags/output; executable alias or auth differs under child process | launcher adapter/executable resolution |
| MCP | client/server version mismatch, hung stdio session, timeout during mutation | MCP child process and its stdio pipe |
| File IPC | no receiver is alive, stale claim never recovered, partial/non-atomic publication | queue-draining/lease logic |
| Custom bridge | protocol update or bridge crash causes silent translation failures | custom bridge service |

Across all four, the hidden common failure is **concurrent writes to one checkout**. Transport reliability cannot compensate for unclear file ownership.

### 9. Windows-specific gotchas

- Prefer an absolute executable path verified by a startup probe; do not rely on a GUI app alias.
- Determine whether the command is a native `.exe`, `.cmd`, or PowerShell script. Spawn it accordingly.
- Avoid prompt text in command arguments. Use UTF-8 stdin or a UTF-8 manifest file.
- Set UTF-8 explicitly and tolerate CRLF.
- Drain stdout and stderr concurrently.
- Kill the process tree on timeout, not only the immediate child.
- Use atomic rename within the same volume; cross-volume moves are not atomic.
- Expect transient sharing violations from antivirus/indexers; retry renames with bounded backoff.
- Use `-LiteralPath` in PowerShell for paths containing brackets or wildcard characters.
- Normalize path comparisons case-insensitively but preserve original casing.
- Keep secrets out of manifests, logs, command lines, and inherited environments where possible.
- Test paths with spaces—the current project path contains several.

### 10. Token economics

Transport does not determine most token cost; **context policy and model behavior do**. The following estimates are engineering ranges, not OpenAI billing quotes:

| Architecture | Typical input overhead per delegation | Hidden duplication |
|---|---:|---|
| Subprocess + `AGENTS.md` + compact manifest | 0.5k–2k tokens | fresh session still reads durable guidance |
| MCP tool call | 0.3k–1.5k tokens | parent pays tool schema/result; child may still be a fresh run |
| File IPC | 0.5k–2k tokens | same as subprocess if a fresh worker processes it |
| Custom bridge | 0.5k–2.5k tokens | protocol summaries and two-agent state can multiply context |

At **10 delegations/day**, operational simplicity matters more than small token differences. Subprocess plus compact manifests is cheapest overall.

At **100 delegations/day**, prompt caching, batching related work, smaller models for mechanical tasks, and avoiding duplicate agent deliberation dominate. MCP may reduce process latency, but it is not inherently token-cheaper. A persistent session can become *more* expensive if history grows without compaction. The worst pattern is bidirectional recursive delegation: each side restates context and critiques the other.

Use actual telemetry: input tokens, cached tokens, output tokens, wall time, retries, and successful-artifact rate. Do not choose a transport based on speculative token savings.

## 4. Concrete implementation plan

### Phase 0 — Capability probe

Before integration work:

1. From the actual OpenCode process environment, resolve the absolute Codex executable.
2. Run a harmless non-interactive command in a temporary directory.
3. Verify authentication, stdin handling, UTF-8, stdout/stderr capture, timeout, and exit code.
4. Run a task in a path containing spaces.
5. Confirm whether the executable can be launched without an interactive desktop token.

If this fails, fix executable installation/path/security context first. Do not paper over it with MCP; MCP also requires spawning the server.

### Phase 1 — Repository contract

Create a root `AGENTS.md` containing:

- project purpose and canonical files;
- read/write boundaries;
- rule that delegated tasks write only to an assigned directory or worktree;
- verification expectations;
- prohibition on recursive agent delegation;
- result schema location.

Create a JSON Schema for task and result manifests.

### Phase 2 — Thin adapter

Build one wrapper, owned by OpenCode, with:

```text
codex-adapter run task.json
```

Responsibilities:

- validate the manifest;
- acquire a repository/task lock;
- choose an isolated output directory or worktree;
- invoke Codex using stdin;
- set a hard deadline and output-size limits;
- capture stdout/stderr separately;
- validate `result.json` and expected artifacts;
- emit one compact JSON status;
- append a redacted audit record.

The adapter must never infer success from prose alone.

### Phase 3 — Five-task pilot

Test five bounded task classes:

1. read-only repository analysis;
2. CSV analysis with a required report;
3. code change with tests;
4. intentionally failing task;
5. timed-out task.

Acceptance targets:

- 100% correct status classification;
- no writes outside assigned scope;
- deterministic artifact discovery;
- clean recovery after timeout;
- no orphaned process;
- enough logs to diagnose failure without replaying it.

### Phase 4 — File fallback

Retain `CODEX_ENDPOINT` as an observable fallback queue using `queued/running/completed/failed/archive`, atomic renames, and leases. A scheduled automation or explicit drain command may process it. Do not claim it is being “actively monitored” unless such a runner is actually alive.

### Phase 5 — MCP gate

Pilot MCP only if 30–50 real subprocess delegations show one of:

- startup latency is a material share of wall time;
- task interaction genuinely needs progress/cancellation;
- MCP exposes stable, useful session semantics unavailable to the wrapper.

Pin tested versions and run compatibility tests before upgrades. Keep the subprocess adapter as the recovery path.

## 5. Decision matrix

Scores are 1 (poor) to 5 (strong). Weighted total is out of 5.

| Criterion | Weight | Subprocess | File IPC | MCP | Custom bridge |
|---|---:|---:|---:|---:|---:|
| Simplicity | 20% | 5 | 4 | 3 | 1 |
| Reliability/recovery | 25% | 4 | 4 | 3 | 2 |
| Observability/audit | 15% | 4 | 5 | 3 | 3 |
| Windows compatibility confidence | 15% | 3 | 4 | 2 | 2 |
| Latency | 10% | 3 | 2 | 4 | 4 |
| Bidirectional capability | 5% | 1 | 4 | 1 | 5 |
| Maintenance cost | 10% | 5 | 4 | 3 | 1 |
| **Weighted total** | **100%** | **4.10** | **3.90** | **2.85** | **2.20** |

## Final decision

Approve a **one-way subprocess pilot with a manifest/adapter boundary**. Approve file IPC only as a fallback queue after strengthening its state model. Defer MCP pending an exact Windows compatibility pilot. Reject the custom bridge.

The most important architectural rule is not the transport: **one orchestrator owns the task, one worker owns the assigned files, and success is proven by validated artifacts rather than agent prose.**

