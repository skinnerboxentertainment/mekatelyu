import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from CODEX_ENDPOINT import session_lib as sl
from CODEX_ENDPOINT.session_schema import (
    Session,
    SessionState,
    derive_display_fields,
)

BRIDGE_SCRIPT = PROJECT_ROOT / "codex_bridge.py"


def cmd_create(args):
    session_id = sl.new_session_id()
    now = sl.utcnow()
    session = {
        "schema_version": "2.0",
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "title": args.title,
        "description": args.description,
        "workdir": str(Path(args.workdir).resolve()) if args.workdir else str(Path.cwd()),
        "artifacts_root": f"tasks/{session_id}/artifacts",
        "references_root": None,
        "status": "active",
        "state": "awaiting_codex",
        "turn": 0,
        "revision": 1,
        "current_holder": "codex",
        "needs_input": False,
        "last_bridge_run_id": None,
        "parent_session_id": None,
        "completed_at": None,
        "cancelled_at": None,
        "conversation": [
            {
                "id": sl.bridge_run_id(),
                "turn": 0,
                "from": "opencode",
                "type": "instruction",
                "message": args.message or args.description,
                "artifacts": [],
                "timestamp": now,
                "bridge_run_id": None,
                "metadata": {},
            }
        ],
        "error": None,
        "config": {
            "sandbox": args.sandbox or "danger-full-access",
            "timeout": args.timeout or 300,
            "ephemeral": True,
            "cooldown": 2.0,
        },
    }

    spath = sl.session_path(session_id)
    sl.write_session_atomic(session, spath)

    print(f"Session created: {session_id}")
    print(f"  Title: {args.title}")
    print(f"  Path: {spath}")
    print(f"  Run 'python session_orchestrator.py next --session-id {session_id}' to start")


def cmd_next(args):
    session_id = args.session_id
    if not sl.validate_session_id(session_id):
        print(f"error: invalid session_id '{session_id}'", file=sys.stderr)
        sys.exit(1)

    spath = sl.session_path(session_id)
    if not spath.exists():
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    raw = sl.read_session(spath)
    if raw is None:
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        session = Session(**raw)
    except Exception as e:
        print(f"error: session validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    if session.state not in (SessionState.AWAITING_OPENCODE, SessionState.CREATING, SessionState.AWAITING_CODEX):
        print(f"error: session is in state '{session.state.value}', need 'awaiting_opencode', 'creating', or 'awaiting_codex'", file=sys.stderr)
        sys.exit(1)

    if args.message:
        now = sl.utcnow()
        new_turn = session.turn + 1
        new_entry = {
            "id": sl.bridge_run_id(),
            "turn": new_turn,
            "from": "opencode",
            "type": "instruction" if session.state != SessionState.AWAITING_OPENCODE else "review",
            "message": args.message,
            "artifacts": [],
            "timestamp": now,
            "bridge_run_id": None,
            "metadata": {},
        }
        session.conversation.append(new_entry)
        session.turn = new_turn
        session.revision += 1
        session.state = SessionState.AWAITING_CODEX
        session.updated_at = now
        derive_display_fields(session)

        sl.write_session_atomic(session.model_dump(mode="json", by_alias=True), spath)

    bridge_cmd = [
        sys.executable,
        str(BRIDGE_SCRIPT),
        "--session", session_id,
        "--json",
    ]
    if args.sandbox:
        bridge_cmd.extend(["--sandbox", args.sandbox])
    if args.timeout:
        bridge_cmd.extend(["--timeout", str(args.timeout)])

    print(f"Running session {session_id}...")
    sys.stdout.flush()

    result = subprocess.run(
        bridge_cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(json.dumps(output, indent=2, ensure_ascii=False))

    if output.get("status") != "ok":
        sys.exit(1)


def cmd_status(args):
    session_id = args.session_id
    spath = sl.session_path(session_id)
    if not spath.exists():
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    raw = sl.read_session(spath)
    if raw is None:
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    print(f"Session: {session_id}")
    print(f"  Title:      {raw.get('title', '?')}")
    print(f"  Status:     {raw.get('status', '?')}")
    print(f"  State:      {raw.get('state', '?')}")
    print(f"  Turn:       {raw.get('turn', '?')}")
    print(f"  Revision:   {raw.get('revision', '?')}")
    print(f"  Holder:     {raw.get('current_holder', '?')}")
    print(f"  Needs:      {raw.get('needs_input', '?')}")
    print(f"  Created:    {raw.get('created_at', '?')}")
    print(f"  Updated:    {raw.get('updated_at', '?')}")

    conv = raw.get("conversation", [])
    if conv:
        print(f"\n  Latest turn [{len(conv) - 1}]:")
        latest = conv[-1]
        print(f"    From:      {latest.get('from', '?')}")
        print(f"    Type:      {latest.get('type', '?')}")
        print(f"    Message:   {latest.get('message', '')[:200]}")
        arts = latest.get("artifacts", [])
        if arts:
            for a in arts:
                apath = a.get("path", a) if isinstance(a, dict) else a
                print(f"    Artifact:  {apath}")

    if raw.get("error"):
        print("\n  Error:")
        print(f"    Code:    {raw['error'].get('code', '?')}")
        print(f"    Message: {raw['error'].get('message', '')[:200]}")


def cmd_show(args):
    session_id = args.session_id
    spath = sl.session_path(session_id)
    if not spath.exists():
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    raw = sl.read_session(spath)
    print(json.dumps(raw, indent=2, ensure_ascii=False))


def cmd_cancel(args):
    session_id = args.session_id
    spath = sl.session_path(session_id)
    if not spath.exists():
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    raw = sl.read_session(spath)
    if raw is None:
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    if raw.get("status") in ("completed", "cancelled"):
        print(f"Session already in terminal state: {raw['status']}")
        return

    raw["state"] = "cancelled"
    raw["status"] = "cancelled"
    raw["cancelled_at"] = sl.utcnow()
    raw["updated_at"] = sl.utcnow()
    derive_display_fields_raw(raw)
    sl.write_session_atomic(raw, spath)
    print(f"Session {session_id} cancelled")


def cmd_retry(args):
    session_id = args.session_id
    spath = sl.session_path(session_id)
    if not spath.exists():
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    raw = sl.read_session(spath)
    if raw is None:
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    if raw.get("state") != "error":
        print(f"Session is in '{raw.get('state')}', not 'error'. Nothing to retry.", file=sys.stderr)
        sys.exit(1)

    now = sl.utcnow()
    new_turn = raw["turn"] + 1
    new_entry = {
        "id": sl.bridge_run_id(),
        "turn": new_turn,
        "from": "opencode",
        "type": "review",
        "message": args.message if args.message else f"Retry from previous error: {raw.get('error', {}).get('message', 'unknown')}",
        "artifacts": [],
        "timestamp": now,
        "bridge_run_id": None,
        "metadata": {},
    }
    raw.setdefault("conversation", []).append(new_entry)
    raw["turn"] = new_turn
    raw["revision"] = raw.get("revision", 0) + 1
    raw["state"] = "awaiting_codex"
    raw["status"] = "active"
    raw["error"] = None
    raw["updated_at"] = now
    derive_display_fields_raw(raw)
    sl.write_session_atomic(raw, spath)
    print(f"Session {session_id} retry prepared. Run 'next' to execute: python session_orchestrator.py next --session-id {session_id}")


def cmd_archive(args):
    session_id = args.session_id
    spath = sl.session_path(session_id)
    if not spath.exists():
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    raw = sl.read_session(spath)
    if raw is None:
        print(f"error: session '{session_id}' not found", file=sys.stderr)
        sys.exit(1)

    if raw.get("state") not in ("completed", "cancelled"):
        print(f"Session is in state '{raw.get('state')}', not terminal. Cancel or complete first.", file=sys.stderr)
        sys.exit(1)

    archive_path = sl.ARCHIVE_DIR / f"{session_id}.json"
    import shutil
    shutil.copy2(str(spath), str(archive_path))
    spath.unlink()
    print(f"Session {session_id} archived to {archive_path}")


def cmd_list(args):
    sessions = []
    for f in sl.SESSION_DIR.glob("*.json"):
        if f.stem in ("archive", "corrupt"):
            continue
        try:
            raw = sl.read_session(f)
            if raw:
                sessions.append(raw)
        except Exception:
            pass

    if args.status:
        sessions = [s for s in sessions if s.get("status") == args.status]

    if not sessions:
        print("No sessions found.")
        return

    for s in sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True):
        sid = s.get("session_id", "???")
        title = s.get("title", "?")
        state = s.get("state", "?")
        turn = s.get("turn", "?")
        print(f"  {sid}  {state:20s}  turn {turn:2d}  {title[:50]}")


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
    parser = argparse.ArgumentParser(description="CODEX_ENDPOINT Session Orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a new session")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--description", required=True)
    p_create.add_argument("--message", help="Initial instruction (defaults to description)")
    p_create.add_argument("--workdir")
    p_create.add_argument("--sandbox")
    p_create.add_argument("--timeout", type=int)

    p_next = sub.add_parser("next", help="Append instruction and invoke Codex")
    p_next.add_argument("--session-id", required=True)
    p_next.add_argument("--message")
    p_next.add_argument("--sandbox")
    p_next.add_argument("--timeout", type=int)

    p_status = sub.add_parser("status", help="Show session status")
    p_status.add_argument("--session-id", required=True)

    p_show = sub.add_parser("show", help="Full session dump")
    p_show.add_argument("--session-id", required=True)

    p_cancel = sub.add_parser("cancel", help="Cancel a session")
    p_cancel.add_argument("--session-id", required=True)

    p_retry = sub.add_parser("retry", help="Retry a failed session")
    p_retry.add_argument("--session-id", required=True)
    p_retry.add_argument("--message", help="Retry instruction")

    p_archive = sub.add_parser("archive", help="Archive a completed session")
    p_archive.add_argument("--session-id", required=True)

    p_list = sub.add_parser("list", help="List sessions")
    p_list.add_argument("--status", choices=["active", "completed", "cancelled", "error"], help="Filter by status")

    args = parser.parse_args()

    commands = {
        "create": cmd_create,
        "next": cmd_next,
        "status": cmd_status,
        "show": cmd_show,
        "cancel": cmd_cancel,
        "retry": cmd_retry,
        "archive": cmd_archive,
        "list": cmd_list,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
