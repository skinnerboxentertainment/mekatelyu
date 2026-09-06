import json
import os
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

CODEX_ENDPOINT = Path(__file__).parent.resolve()
SESSION_DIR = CODEX_ENDPOINT / "sessions"
LOCK_DIR = CODEX_ENDPOINT / "locks"
ARCHIVE_DIR = SESSION_DIR / "archive"
CORRUPT_DIR = SESSION_DIR / "corrupt"
TASKS_DIR = CODEX_ENDPOINT / "tasks"

SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}
LOCK_TTL_GRACE = 60


def validate_session_id(session_id: str) -> bool:
    if not SESSION_ID_PATTERN.match(session_id):
        return False
    if session_id.upper() in WINDOWS_RESERVED:
        return False
    return True


def session_path(session_id: str) -> Path:
    return SESSION_DIR / f"{session_id}.json"


def is_path_contained(child: Path, parent: Path) -> bool:
    try:
        child_resolved = child.resolve()
        parent_resolved = parent.resolve()
        return parent_resolved in child_resolved.parents or child_resolved == parent_resolved
    except (OSError, RuntimeError):
        return False


def ensure_dirs():
    for d in [SESSION_DIR, LOCK_DIR, ARCHIVE_DIR, CORRUPT_DIR, TASKS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def read_session(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        corrupt_path = CORRUPT_DIR / f"{path.stem}.{int(time.time())}.json"
        try:
            import shutil
            shutil.copy2(str(path), str(corrupt_path))
        except OSError:
            pass
        bak = path.with_suffix(".bak")
        if bak.exists():
            try:
                with open(bak, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        raise SessionCorruptError(f"Cannot read {path}: {e}", corrupt_path=str(corrupt_path) if corrupt_path.exists() else None)


class SessionCorruptError(Exception):
    def __init__(self, message: str, corrupt_path: str | None = None):
        super().__init__(message)
        self.corrupt_path = corrupt_path


class AtomicWriteError(Exception):
    pass


def write_session_atomic(data: dict, path: Path):
    ensure_dirs()
    pid = os.getpid()
    tmp_path = path.with_name(f"{path.stem}.tmp.{pid}")
    bak_path = path.with_name(f"{path.stem}.bak")
    try:
        content = json.dumps(data, indent=2, ensure_ascii=False)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        with open(tmp_path, encoding="utf-8") as f:
            json.load(f)
        if path.exists():
            import shutil
            shutil.copy2(str(path), str(bak_path))
            _prune_backups(path, keep=5)
        os.replace(tmp_path, path)
    except (OSError, json.JSONDecodeError) as e:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise AtomicWriteError(f"Atomic write failed for {path}: {e}")


def _prune_backups(path: Path, keep: int = 5):
    pattern = f"{path.stem}.bak.*"
    backups = sorted(path.parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[keep:]:
        old.unlink(missing_ok=True)


def lock_path(session_id: str) -> Path:
    return LOCK_DIR / f"{session_id}.lock"


def acquire_lock(session_id: str, purpose: str = "bridge_spawn", timeout_sec: int = 300) -> bool:
    ensure_dirs()
    lpath = lock_path(session_id)
    expires_at = datetime.now(UTC).timestamp() + timeout_sec + LOCK_TTL_GRACE
    lock_data = {
        "session_id": session_id,
        "pid": os.getpid(),
        "hostname": os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME", "unknown"),
        "acquired_at": datetime.now(UTC).isoformat(),
        "expires_at": datetime.fromtimestamp(expires_at, tz=UTC).isoformat(),
        "purpose": purpose,
    }
    retry_delays = [0.1, 0.2, 0.4, 0.8, 1.5, 3.0]
    for delay in retry_delays:
        if lpath.exists():
            try:
                with open(lpath, encoding="utf-8") as f:
                    existing = json.load(f)
                exp = existing.get("expires_at", "")
                exp_ts = datetime.fromisoformat(exp).timestamp() if exp else 0
                if exp_ts > datetime.now(UTC).timestamp() + 30:
                    time.sleep(delay)
                    continue
            except (json.JSONDecodeError, OSError, ValueError):
                pass
        try:
            tmp = lpath.with_name(f"{lpath.stem}.tmp.{os.getpid()}")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(lock_data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, lpath)
            return True
        except OSError:
            time.sleep(delay)
    return False


def release_lock(session_id: str):
    lpath = lock_path(session_id)
    try:
        if lpath.exists():
            with open(lpath, encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("pid") == os.getpid():
                lpath.unlink()
    except (json.JSONDecodeError, OSError):
        lpath.unlink(missing_ok=True)


def new_session_id() -> str:
    return uuid.uuid4().hex[:8]


def bridge_run_id() -> str:
    return uuid.uuid4().hex[:8]


def task_artifact_dir(session_id: str) -> Path:
    return TASKS_DIR / session_id / "artifacts"


def task_log_dir(session_id: str) -> Path:
    return TASKS_DIR / session_id / "logs"


def task_references_dir(session_id: str) -> Path:
    return TASKS_DIR / session_id / "references"


def utcnow() -> str:
    return datetime.now(UTC).isoformat()
