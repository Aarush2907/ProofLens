"""Events recorded while a research run is actually executing.

The log lives in this process. A reconnecting client reads it by event id.
Nothing here is invented by a timer.
"""

from contextvars import ContextVar
from datetime import datetime, timezone
from threading import Lock

_session: ContextVar[str] = ContextVar("prooflens_session", default="")


class ActivityLog:
    def __init__(self):
        self._lock = Lock()
        self._next_id = 0
        self._events: dict[str, list[dict]] = {}

    def record(
        self,
        session_id: str,
        kind: str,
        message: str,
        *,
        agent: str = "",
        detail: dict | None = None,
        terminal: bool = False,
    ) -> dict:
        with self._lock:
            self._next_id += 1
            event = {
                "id": self._next_id,
                "session_id": session_id,
                "kind": kind,
                "agent": agent,
                "message": message,
                "detail": detail or {},
                "at": datetime.now(timezone.utc).isoformat(),
                "terminal": terminal,
            }
            self._events.setdefault(session_id, []).append(event)
            return event

    def since(self, session_id: str, after_id: int) -> list[dict]:
        with self._lock:
            return [event for event in self._events.get(session_id, []) if event["id"] > after_id]


activity_log = ActivityLog()


def bind_session(session_id: str):
    return _session.set(session_id)


def reset_session(token) -> None:
    _session.reset(token)


def emit(
    kind: str,
    message: str,
    *,
    agent: str = "",
    detail: dict | None = None,
    terminal: bool = False,
    session_id: str | None = None,
) -> dict | None:
    sid = (session_id or _session.get() or "").strip()
    if not sid:
        return None
    return activity_log.record(
        sid,
        kind,
        message,
        agent=agent,
        detail=detail,
        terminal=terminal,
    )
