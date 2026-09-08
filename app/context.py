from contextvars import ContextVar

session_id_var: ContextVar[str] = ContextVar("session_id", default=None)
