import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path

CODEX_EXECUTABLE = Path(
    os.environ.get(
        "CODEX_PATH",
        os.path.expanduser("~/.codex/.sandbox-bin/codex.exe"),
    )
)
CODEX_ENDPOINT = Path(__file__).parent / "CODEX_ENDPOINT"
COOLDOWN = float(os.environ.get("CODEX_COOLDOWN", "2.0"))
DEFAULT_SANDBOX = "danger-full-access"


def _resolve_codex() -> Path:
    if CODEX_EXECUTABLE.exists():
        return CODEX_EXECUTABLE
    which = shutil_which("codex") or shutil_which("codex.exe")
    if which:
        return Path(which)
    raise FileNotFoundError(
        f"Codex executable not found at {CODEX_EXECUTABLE} or on PATH"
    )


def shutil_which(name: str) -> str | None:
    for dir in os.environ.get("PATH", "").split(";"):
        candidate = Path(dir) / name
        if candidate.exists():
            return str(candidate.resolve())
    return None


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
    log_dir = CODEX_ENDPOINT / "responses"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"bridge_{entry['id']}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Thin wrapper around codex exec")
    parser.add_argument("task", nargs="?", help="Task prompt (omit to read from stdin)")
    parser.add_argument("--workdir", "-C", help="Working directory")
    parser.add_argument("--sandbox", "-s", default=DEFAULT_SANDBOX, help="Sandbox level (read-only, workspace-write, danger-full-access)")
    parser.add_argument("--dangerous", action="store_true", help="Shortcut for --sandbox danger-full-access")
    parser.add_argument("--timeout", "-t", type=int, default=120, help="Timeout in seconds")
    parser.add_argument("--no-ephemeral", action="store_true", help="Persist session")
    parser.add_argument("--json", action="store_true", help="Output result as JSON (to stdout)")
    args = parser.parse_args()

    task = args.task
    if not task:
        task = sys.stdin.read().strip()
    if not task:
        print("error: no task provided", file=sys.stderr)
        sys.exit(1)

    result = run_codex(
        task,
        workdir=args.workdir,
        sandbox=args.sandbox,
        timeout=args.timeout,
        ephemeral=not args.no_ephemeral,
    )

    entry_id = str(uuid.uuid4())[:8]
    result["id"] = entry_id
    result["task_preview"] = task[:200]
    audit_log(result)

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("stdout", ""))
        if result["status"] != "ok":
            print(f"[bridge] status={result['status']} exit={result['exit_code']} elapsed={result['elapsed']}s",
                  file=sys.stderr)
            if result.get("stderr"):
                print(f"[bridge] stderr: {result['stderr']}", file=sys.stderr)

    sys.exit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
