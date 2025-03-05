import asyncio
from typing import Dict, Optional
from uuid import uuid4

class BattleSessionManager:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self.lock = asyncio.Lock()

    async def create_session(self, challenger, challenged, chat_id):
        async with self.lock:
            session_id = str(uuid4())
            self.sessions[session_id] = {
                "id": session_id,
                "challenger": challenger,
                "challenged": challenged,
                "chat_id": chat_id,
                "message_id": None,
                "engine": None,
                "active": True
            }
            return session_id

    async def get_session(self, session_id) -> Optional[dict]:
        return self.sessions.get(session_id)

    async def end_session(self, session_id):
        async with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
