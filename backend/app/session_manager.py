import threading
import time

class SessionState:
    def __init__(self):
        self.lock = threading.Lock()
        self.df_base = None
        self.df_ativo = None
        self.edicoes = {}
        self.analise_nome = None
        self.last_accessed = time.time()

# Dictionary to hold all sessions
_sessions = {}
_session_lock = threading.Lock()
SESSION_TTL = 2 * 3600  # 2 hours in seconds

def get_session(session_id: str) -> SessionState:
    with _session_lock:
        # Clean up expired sessions first
        now = time.time()
        expired = [sid for sid, state in _sessions.items() if now - state.last_accessed > SESSION_TTL]
        for sid in expired:
            del _sessions[sid]
            
        if session_id not in _sessions:
            _sessions[session_id] = SessionState()
        
        _sessions[session_id].last_accessed = time.time()
        return _sessions[session_id]
