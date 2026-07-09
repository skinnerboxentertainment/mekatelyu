from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class SessionState(str, Enum):
    CREATING = "creating"
    AWAITING_CODEX = "awaiting_codex"
    RUNNING_CODEX = "running_codex"
    AWAITING_OPENCODE = "awaiting_opencode"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class AgentName(str, Enum):
    OPENCODE = "opencode"
    CODEX = "codex"


class EntryType(str, Enum):
    INSTRUCTION = "instruction"
    RESULT = "result"
    REVIEW = "review"
    REQUEST = "request"
    RESPONSE = "response"


STATUS_FROM_STATE = {
    SessionState.CREATING: SessionStatus.ACTIVE,
    SessionState.AWAITING_CODEX: SessionStatus.ACTIVE,
    SessionState.RUNNING_CODEX: SessionStatus.ACTIVE,
    SessionState.AWAITING_OPENCODE: SessionStatus.ACTIVE,
    SessionState.COMPLETED: SessionStatus.COMPLETED,
    SessionState.ERROR: SessionStatus.ERROR,
    SessionState.CANCELLED: SessionStatus.CANCELLED,
}

HOLDER_FROM_STATE = {
    SessionState.CREATING: AgentName.OPENCODE,
    SessionState.AWAITING_CODEX: AgentName.CODEX,
    SessionState.RUNNING_CODEX: AgentName.CODEX,
    SessionState.AWAITING_OPENCODE: AgentName.OPENCODE,
    SessionState.COMPLETED: AgentName.OPENCODE,
    SessionState.ERROR: AgentName.OPENCODE,
    SessionState.CANCELLED: AgentName.OPENCODE,
}

NEEDS_INPUT_FROM_STATE = {
    SessionState.CREATING: False,
    SessionState.AWAITING_CODEX: False,
    SessionState.RUNNING_CODEX: False,
    SessionState.AWAITING_OPENCODE: True,
    SessionState.COMPLETED: False,
    SessionState.ERROR: False,
    SessionState.CANCELLED: False,
}

ALLOWED_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.CREATING: {SessionState.AWAITING_CODEX},
    SessionState.AWAITING_CODEX: {SessionState.RUNNING_CODEX},
    SessionState.RUNNING_CODEX: {
        SessionState.AWAITING_OPENCODE,
        SessionState.ERROR,
        SessionState.CANCELLED,
    },
    SessionState.AWAITING_OPENCODE: {
        SessionState.AWAITING_CODEX,
        SessionState.COMPLETED,
        SessionState.CANCELLED,
    },
    SessionState.ERROR: {SessionState.AWAITING_CODEX, SessionState.CANCELLED},
    SessionState.COMPLETED: set(),
    SessionState.CANCELLED: set(),
}


class ArtifactRef(BaseModel):
    path: str
    hash: str | None = None
    mime: str | None = None


class ConversationEntry(BaseModel):
    model_config = {"extra": "allow", "populate_by_name": True}

    id: str
    turn: int
    from_: AgentName = Field(alias="from")
    type: EntryType
    message: str
    artifacts: list[ArtifactRef] = []
    timestamp: str
    bridge_run_id: str | None = None
    metadata: dict[str, Any] = {}


class ErrorInfo(BaseModel):
    code: str
    message: str
    recoverable: bool
    bridge_log: str | None = None
    stderr_log: str | None = None
    timestamp: str


class SessionConfig(BaseModel):
    sandbox: str = "danger-full-access"
    timeout: int = 300
    ephemeral: bool = True
    cooldown: float = 2.0


class Session(BaseModel):
    model_config = {"extra": "allow", "populate_by_name": True}

    schema_version: Literal["2.0"] = "2.0"
    session_id: str
    created_at: str
    updated_at: str
    title: str
    description: str
    workdir: str
    artifacts_root: str
    references_root: str | None = None
    status: SessionStatus
    state: SessionState
    turn: int
    revision: int
    current_holder: AgentName
    needs_input: bool
    last_bridge_run_id: str | None = None
    parent_session_id: str | None = None
    completed_at: str | None = None
    cancelled_at: str | None = None
    conversation: list[ConversationEntry] = []
    error: ErrorInfo | None = None
    config: SessionConfig = SessionConfig()

    @model_validator(mode="after")
    def check_derived_fields(self):
        expected_status = STATUS_FROM_STATE.get(self.state)
        if expected_status and self.status != expected_status:
            raise ValueError(f"status '{self.status}' inconsistent with state '{self.state}'; expected '{expected_status}'")

        expected_holder = HOLDER_FROM_STATE.get(self.state)
        if expected_holder and self.current_holder != expected_holder:
            raise ValueError(f"current_holder '{self.current_holder}' inconsistent with state '{self.state}'; expected '{expected_holder}'")

        expected_input = NEEDS_INPUT_FROM_STATE.get(self.state)
        if expected_input is not None and self.needs_input != expected_input:
            raise ValueError(f"needs_input '{self.needs_input}' inconsistent with state '{self.state}'; expected '{expected_input}'")

        if self.conversation:
            last_turn = self.conversation[-1].turn
            if self.turn != last_turn:
                raise ValueError(f"session turn {self.turn} != last conversation turn {last_turn}")

            for i, entry in enumerate(self.conversation):
                if entry.turn != i:
                    raise ValueError(f"conversation[{i}].turn is {entry.turn}, expected {i}")

        return self


def validate_transition(before: Session, after: Session) -> bool:
    allowed = ALLOWED_TRANSITIONS.get(before.state)
    if allowed is None:
        return False
    if after.state not in allowed:
        return False
    return True


def validate_paths(session: Session, endpoint_root: str) -> list[str]:
    errors = []
    root = endpoint_root
    if session.artifacts_root:
        art_path = os.path.join(root, session.artifacts_root)
        if not art_path.startswith(os.path.join(root, "tasks")):
            errors.append(f"artifacts_root '{session.artifacts_root}' not under tasks/")
    for entry in session.conversation:
        for art in entry.artifacts:
            resolved = os.path.normpath(os.path.join(root, art.path))
            allowed_roots = []
            if session.artifacts_root:
                allowed_roots.append(os.path.normpath(os.path.join(root, session.artifacts_root)))
            if session.references_root:
                allowed_roots.append(os.path.normpath(os.path.join(root, session.references_root)))
            if not any(resolved.startswith(a) for a in allowed_roots):
                errors.append(f"artifact path '{art.path}' not under allowed roots")
    return errors


def derive_state(session: Session) -> SessionState:
    return session.state


def derive_display_fields(session: Session):
    session.current_holder = HOLDER_FROM_STATE.get(session.state, session.current_holder)
    session.needs_input = NEEDS_INPUT_FROM_STATE.get(session.state, session.needs_input)
    session.status = STATUS_FROM_STATE.get(session.state, session.status)


import os
