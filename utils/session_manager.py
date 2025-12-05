from typing import Dict, Any, Optional
from core.database import db


class SessionManager:
    @staticmethod
    async def save(user_id: int, mode: str, step: int = 0, data: dict = None):
        await db.save_session(user_id, mode, step, data)

    @staticmethod
    async def get(user_id: int) -> Optional[Dict[str, Any]]:
        return await db.get_session(user_id)

    @staticmethod
    async def clear(user_id: int):
        await db.clear_session(user_id)

    @staticmethod
    async def update_step(user_id: int, step: int):
        session = await db.get_session(user_id)
        if session:
            await db.save_session(
                user_id,
                session.get('mode', ''),
                step,
                session.get('data')
            )

    @staticmethod
    async def update_data(user_id: int, new_data: dict):
        session = await db.get_session(user_id)
        if session:
            current_data = session.get('data') or {}
            current_data.update(new_data)
            await db.save_session(
                user_id,
                session.get('mode', ''),
                session.get('step', 0),
                current_data
            )
        else:
            await db.save_session(user_id, '', 0, new_data)

    @staticmethod
    async def get_data(user_id: int, key: str, default=None):
        session = await db.get_session(user_id)
        if session and session.get('data'):
            return session['data'].get(key, default)
        return default
