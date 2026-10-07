from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class SessionManager:
    def __init__(self, max_history_per_session: int = 10):
        self.max_history = max_history_per_session
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Trim to sliding window
        if len(self._sessions[session_id]) > self.max_history * 2:
            self._sessions[session_id] = self._sessions[session_id][-self.max_history * 2:]

    def clear_history(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

session_manager = SessionManager()
