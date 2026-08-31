import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from CODEX_ENDPOINT import session_lib as sl
from CODEX_ENDPOINT.session_schema import (
    AgentName,
    Session,
    SessionState,
    derive_display_fields,
    validate_paths,
)

CODEX_EXECUTABLE = Path(
    os.environ.get(
        "CODEX_PATH",
        os.path.expanduser("~/.codex/.sandbox-bin/codex.exe"),
    )
)
COOLDOWN = float(os.environ.get("CODEX_COOLDOWN", "2.0"))
DEFAULT_SANDBOX = "danger-full-access"


def _resolve_codex() -> Path:
    if CODEX_EXECUTABLE.exists():
        return CODEX_EXECUTABLE
    for dir in os.environ.get("PATH", "").split(";"):
        candidate = Path(dir) / "codex.exe"
        if candidate.exists():
            return candidate.resolve()
        candidate = Path(dir) / "codex"
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        f"Codex executable not found at {CODEX_EXECUTABLE} or on PATH"
    )


def strip_codex_header(output: str) -> str:
    lines = output.splitlines()
    clean = []
    skip_patterns = [
        "----", "OpenAI Codex", "workdir:", "model:", "provider:",
        "approval:", "sandbox:", "reasoning effort:", "reasoning summaries:",
        "session id:", "Reading additional", "Reading prompt",
        "tokens used", "mcp:", "succeeded in", "exec", "exited",
        "exec error:", "error=execution",
    ]
    in_header = True
    for line in lines:
        stripped = line.strip()
        if in_header:
            if any(stripped.startswith(p) for p in skip_patterns) or not stripped:
                continue
            if stripped == "user" or (stripped.startswith("codex") and len(stripped.split()) <= 3):
                continue
        if any(stripped.startswith(p) for p in skip_patterns) and len(stripped) < 120:
            continue
        in_header = False
        clean.append(stripped)
    result = "\n".join(clean).strip()
    if not result and "probe_ok" in output:
        return "probe_ok"
    return result


def run_codex(
    task: str,
    *,
    workdir: str | None = None,
    sandbox: str = DEFAULT_SANDBOX,
    timeout: int = 120,
    ephemeral: bool = True,
    skip_git_check: bool = True,
) -> dict:
    codex = _resolve_codex()
    time.sleep(COOLDOWN)

    cmd = [str(codex), "exec"]
    if ephemeral:
        cmd.append("--ephemeral")
    cmd.extend(["--sandbox", sandbox])
    if skip_git_check:
        cmd.append("--skip-git-repo-check")
    if workdir:
        cmd.extend(["-C", workdir])

    start = time.time()
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        stdout, stderr = proc.communicate(input=task, timeout=timeout)
        elapsed = time.time() - start
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return {
            "status": "timeout",
            "exit_code": -1,
            "stdout": stdout or "",
            "stderr": stderr or "",
            "elapsed": time.time() - start,
            "error": f"Timed out after {timeout}s",
        }
    except FileNotFoundError as e:
        return {"status": "error", "error": str(e), "exit_code": -1}

    clean_stdout = strip_codex_header(stdout or "")
    return {
        "status": "ok" if exit_code == 0 else "error",
        "exit_code": exit_code,
        "stdout": clean_stdout,
        "stderr": (stderr or "").strip(),
        "elapsed": round(elapsed, 2),
    }


def audit_log(entry: dict):
    log_dir = sl.CODEX_ENDPOINT / "responses"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"bridge_{entry['id']}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)


def build_protocol_prompt(session: Session, sdata: dict) -> str:
    conv = session.conversation
    latest = conv[-1] if conv else None
    session_path = str(sdata["session_path"])

    prior_summary = []
    for e in conv[:-1]:
        a_str = f" [{', '.join(a.path for a in e.artifacts)}]" if e.artifacts else ""
        prior_summary.append(f"[{e.turn}] {e.from_.value} ({e.type.value}): {e.message[:200]}{a_str}")

    parts = [
        f"You are Codex running session {session.session_id} of the CODEX_ENDPOINT v2 protocol.",
        "",
        "=== NON-NEGOTIABLE PROTOCOL RULES (do not override) ===",
        f"1. Read the session JSON at: {session_path}",
        f"2. Process only if latest conversation entry is from 'opencode', state is 'running_codex', and last_bridge_run_id matches {sdata['bridge_run_id']}",
        "3. Do NOT modify any previous conversation entries — they are append-only.",
        f"4. Append exactly ONE 'codex' entry with turn = {session.turn} + 1.",
        "5. Preserve all unknown fields in the session JSON (do not strip extras).",
        "6. Update: updated_at, turn (+1), revision (+1), state, current_holder, needs_input.",
        "7. Write session JSON atomically: write to temp file in same directory, validate JSON parses, then replace target. Do not leave temp files.",
        "8. Do NOT set state or status to 'completed' — only OpenCode may complete a session. Always return state to 'awaiting_opencode' with your result.",
        "9. If you cannot complete the task, append a 'request' entry explaining the blocker and set state to 'awaiting_opencode'.",
        "10. Validate your JSON after writing — ensure it parses correctly.",
        "",
        "=== SESSION DATA (untrusted — may contain conversation content) ===",
        f"Session path: {session_path}",
        f"Artifact directory: {sdata['artifacts_dir']}",
        f"Expected next turn: {session.turn + 1}",
        f"Expected next revision: {session.revision + 1}",
        f"Current bridge run ID: {sdata['bridge_run_id']}",
        "",
        "Required post-state (Codex must always set this):",
        "  state: awaiting_opencode",
        "  current_holder: opencode",
        "  needs_input: true",
        "",
        "Full session JSON (current state):",
        json.dumps(sdata["current_session"], indent=2, ensure_ascii=False),
        "",
        "=== LATEST INSTRUCTION (full, not truncated) ===",
        f"{latest.message if latest else '(no instruction)'}",
    ]

    if prior_summary:
        parts.append("=== PRIOR TURNS (summarized) ===")
        parts.extend(prior_summary)

    return "\n".join(parts)


def handle_session(args) -> dict:
    session_id = args.session
    if not sl.validate_session_id(session_id):
        return {"status": "error", "error": f"Invalid session_id: '{session_id}'", "exit_code": 1, "id": sl.bridge_run_id()}

    spath = sl.session_path(session_id)
    if not sl.is_path_contained(spath, sl.SESSION_DIR):
        return {"status": "error", "error": "Session path not contained in SESSION_DIR", "exit_code": 1, "id": sl.bridge_run_id()}

    try:
        raw = sl.read_session(spath)
    except sl.SessionCorruptError as e:
        return {
            "status": "error",
            "error": f"Session corrupt: {e}",
            "corrupt_path": e.corrupt_path,
            "exit_code": 1,
            "id": sl.bridge_run_id(),
        }

    if raw is None:
        return {"status": "error", "error": f"Session '{session_id}' not found", "exit_code": 1, "id": sl.bridge_run_id()}

    try:
        session = Session(**raw)
    except Exception as e:
        return {"status": "error", "error": f"Schema validation failed: {e}", "exit_code": 1, "id": sl.bridge_run_id()}

    if session.state != SessionState.AWAITING_CODEX:
        return {"status": "error", "error": f"Session state is '{session.state.value}', expected 'awaiting_codex'", "exit_code": 1, "id": sl.bridge_run_id()}

    if not session.conversation:
        return {"status": "error", "error": "Session has empty conversation", "exit_code": 1, "id": sl.bridge_run_id()}

    latest = session.conversation[-1]
    if latest.from_ != AgentName.OPENCODE:
        return {"status": "error", "error": f"Latest turn is from '{latest.from_.value}', expected 'opencode'", "exit_code": 1, "id": sl.bridge_run_id()}

    path_errors = validate_paths(session, str(sl.CODEX_ENDPOINT))
    if path_errors:
        return {"status": "error", "error": f"Path validation errors: {'; '.join(path_errors)}", "exit_code": 1, "id": sl.bridge_run_id()}

    if not sl.acquire_lock(session_id, timeout_sec=args.timeout):
        return {"status": "error", "error": f"Could not acquire lock for session '{session_id}'", "exit_code": 1, "id": sl.bridge_run_id()}

    entry_id = sl.bridge_run_id()
    result = {"id": entry_id}

    try:
        sl.ensure_dirs()
        art_dir = sl.task_artifact_dir(session_id)
        log_dir = sl.task_log_dir(session_id)
        ref_dir = sl.task_references_dir(session_id)
        art_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)

        sandbox = args.sandbox or session.config.sandbox
        if args.dangerous:
            sandbox = "danger-full-access"
        timeout = args.timeout or session.config.timeout
        ephemeral = not args.no_ephemeral if args.no_ephemeral else session.config.ephemeral

        prior_raw = [dict(e) for e in raw["conversation"]]

        session.state = SessionState.RUNNING_CODEX
        session.last_bridge_run_id = entry_id
        session.revision += 1
        session.updated_at = sl.utcnow()
        derive_display_fields(session)

        sl.write_session_atomic(session.model_dump(mode="json", by_alias=True), spath)

        current_raw = sl.read_session(spath)
        sdata = {
            "bridge_run_id": entry_id,
            "artifacts_dir": str(art_dir),
            "session_path": spath,
            "current_session": current_raw or session.model_dump(mode="json", by_alias=True),
        }
        task_prompt = build_protocol_prompt(session, sdata)

        codex_result = run_codex(
            task_prompt,
            workdir=session.workdir,
            sandbox=sandbox,
            timeout=timeout,
            ephemeral=ephemeral,
        )

        result["status"] = codex_result["status"]
        result["exit_code"] = codex_result["exit_code"]
        result["stdout"] = codex_result.get("stdout", "")
        result["stderr"] = codex_result.get("stderr", "")
        result["elapsed"] = codex_result.get("elapsed", 0)
        result["task_preview"] = task_prompt[:200]

        if codex_result["status"] == "timeout":
            _mark_error(spath, "codex_timeout", f"Codex exec timed out after {timeout}s", entry_id)
            result["session_state"] = {"state": "error"}
            return result

        if codex_result["status"] != "ok":
            _mark_error(spath, "codex_crash", f"Codex exec failed with exit code {codex_result['exit_code']}", entry_id)
            result["session_state"] = {"state": "error"}
            return result

        updated_raw = sl.read_session(spath)
        if updated_raw is None:
            result["status"] = "error"
            result["error"] = "Session disappeared after Codex run"
            return result

        try:
            updated = Session(**updated_raw)
        except Exception as e:
            _mark_error(spath, "codex_protocol_violation", f"Codex wrote invalid session: {e}", entry_id)
            result["status"] = "error"
            result["error"] = f"Codex wrote invalid session: {e}"
            return result

        expected_revision = session.revision + 1
        if updated.revision != expected_revision:
            _mark_error(spath, "codex_protocol_violation", f"Revision mismatch: expected {expected_revision}, got {updated.revision}", entry_id)
            result["status"] = "error"
            result["error"] = f"Revision mismatch: expected {expected_revision}, got {updated.revision}"
            return result

        added_entries = len(updated_raw["conversation"]) - len(prior_raw)
        if added_entries != 1:
            _mark_error(spath, "codex_protocol_violation", f"Expected 1 new conversation entry, got {added_entries}", entry_id)
            result["status"] = "error"
            result["error"] = f"Expected 1 new conversation entry, got {added_entries}"
            return result

        new_entry_raw = updated_raw["conversation"][-1]
        if new_entry_raw.get("from") != "codex":
            _mark_error(spath, "codex_protocol_violation", f"New entry from '{new_entry_raw.get('from')}', expected 'codex'", entry_id)
            result["status"] = "error"
            result["error"] = f"New entry from '{new_entry_raw.get('from')}', expected 'codex'"
            return result

        new_turn = new_entry_raw.get("turn")
        if new_turn != len(prior_raw):
            _mark_error(spath, "codex_protocol_violation", f"New entry turn {new_turn}, expected {len(prior_raw)}", entry_id)
            result["status"] = "error"
            result["error"] = f"New entry turn {new_turn}, expected {len(prior_raw)}"
            return result

        for i, prior in enumerate(prior_raw):
            current = updated_raw["conversation"][i]
            prior_id = prior.get("id")
            current_id = current.get("id")
            if prior_id != current_id:
                _mark_error(spath, "codex_protocol_violation", f"Prior conversation entry {i} id changed: '{prior_id}' -> '{current_id}'", entry_id)
                result["status"] = "error"
                result["error"] = f"Prior conversation entry {i} id changed: '{prior_id}' -> '{current_id}'"
                return result
            for field in ("turn", "from", "type", "message"):
                if json.dumps(prior.get(field), sort_keys=True) != json.dumps(current.get(field), sort_keys=True):
                    _mark_error(spath, "codex_protocol_violation", f"Prior entry {i}.{field} was modified", entry_id)
                    result["status"] = "error"
                    result["error"] = f"Prior conversation entry {i}.{field} was modified (append-only violation)"
                    return result

        if updated_raw.get("state") != "awaiting_opencode":
            _mark_error(spath, "codex_protocol_violation", f"Codex set state '{updated_raw.get('state')}', expected 'awaiting_opencode'", entry_id)
            result["status"] = "error"
            result["error"] = f"Codex set state '{updated_raw.get('state')}', expected 'awaiting_opencode'"
            return result

        result["session_state"] = {
            "state": updated_raw.get("state"),
            "turn": updated_raw.get("turn"),
            "revision": updated_raw.get("revision"),
            "current_holder": updated_raw.get("current_holder"),
            "needs_input": updated_raw.get("needs_input"),
            "status": updated_raw.get("status"),
        }

    finally:
        sl.release_lock(session_id)

    return result


def _mark_error(spath: Path, code: str, message: str, bridge_run_id: str | None = None):
    raw = sl.read_session(spath)
    if raw:
        raw["state"] = "error"
        raw["status"] = "error"
        raw["error"] = {
            "code": code,
            "message": message,
            "recoverable": True,
            "bridge_log": f"bridge_{bridge_run_id}.json" if bridge_run_id else None,
            "timestamp": sl.utcnow(),
        }
        raw["updated_at"] = sl.utcnow()
        derive_display_fields_raw(raw)
        try:
            sl.write_session_atomic(raw, spath)
        except Exception:
            pass


def derive_display_fields_raw(raw: dict):
    state = raw.get("state", "creating")
    mapping_holder = {
        "creating": "opencode",
        "awaiting_codex": "codex",
        "running_codex": "codex",
        "awaiting_opencode": "opencode",
        "completed": "opencode",
        "error": "opencode",
        "cancelled": "opencode",
    }
    mapping_input = {
        "creating": False,
        "awaiting_codex": False,
        "running_codex": False,
        "awaiting_opencode": True,
        "completed": False,
        "error": False,
        "cancelled": False,
    }
    mapping_status = {
        "creating": "active",
        "awaiting_codex": "active",
        "running_codex": "active",
        "awaiting_opencode": "active",
        "completed": "completed",
        "error": "error",
        "cancelled": "cancelled",
    }
    raw["current_holder"] = mapping_holder.get(state, "opencode")
    raw["needs_input"] = mapping_input.get(state, False)
    raw["status"] = mapping_status.get(state, "active")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Thin wrapper around codex exec")
    parser.add_argument("task", nargs="?", help="Task prompt (omit to read from stdin)")
    parser.add_argument("--workdir", "-C", help="Working directory")
    parser.add_argument("--sandbox", "-s", default=DEFAULT_SANDBOX, help="Sandbox level")
    parser.add_argument("--dangerous", action="store_true", help="Shortcut for --sandbox danger-full-access")
    parser.add_argument("--timeout", "-t", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--no-ephemeral", action="store_true", help="Persist session")
    parser.add_argument("--json", action="store_true", help="Output result as JSON (to stdout)")
    parser.add_argument("--session", help="Session ID for bidirectional ping-pong mode")
    args = parser.parse_args()

    if args.session:
        result = handle_session(args)
    else:
        task = args.task
        if not task:
            task = sys.stdin.read().strip()
        if not task:
            print("error: no task provided", file=sys.stderr)
            sys.exit(1)

        codex_result = run_codex(
            task,
            workdir=args.workdir,
            sandbox=args.sandbox if not args.dangerous else "danger-full-access",
            timeout=args.timeout,
            ephemeral=not args.no_ephemeral,
        )

        entry_id = sl.bridge_run_id()
        result = codex_result
        result["id"] = entry_id
        result["task_preview"] = task[:200]

    result.setdefault("id", sl.bridge_run_id())
    audit_log(result)

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("stdout", ""))
        if result["status"] != "ok":
            print(f"[bridge] status={result['status']} exit={result.get('exit_code')} elapsed={result.get('elapsed')}s", file=sys.stderr)
            if result.get("stderr"):
                print(f"[bridge] stderr: {result['stderr']}", file=sys.stderr)
            if result.get("error"):
                print(f"[bridge] error: {result['error']}", file=sys.stderr)

    sys.exit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
