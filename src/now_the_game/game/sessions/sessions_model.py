from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.now_the_game.game.sessions.sessions_schemas import GameSessionBase
from src.shared.base import BaseModel


class GameSessionModel(BaseModel[GameSessionBase]):
    def __init__(self):
        super().__init__(GameSessionBase)

    @overload
    async def get(self, session: AsyncSession) -> list[GameSessionBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int
    ) -> list[GameSessionBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, session_id: int
    ) -> list[GameSessionBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        chat_id: int | None = None,
        session_id: int | None = None,
    ) -> list[GameSessionBase]:
        if chat_id and session_id:
            return await self.get_for_chat_id_and_session_id(
                session, chat_id, session_id
            )
        elif chat_id:
            return await self.get_for_chat_id(session, chat_id)
        elif session_id:
            return await self.get_by_id(session, session_id)
        else:
            return await self.get_all(session)

    async def get_for_chat_id(
        self, session: AsyncSession, chat_id: int
    ) -> list[GameSessionBase]:
        query = select(GameSessionBase).where(GameSessionBase.chat_id == chat_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_for_chat_id_and_session_id(
        self, session: AsyncSession, chat_id: int, session_id: int
    ) -> list[GameSessionBase]:
        query = select(GameSessionBase).where(
            GameSessionBase.chat_id == chat_id, GameSessionBase.object_id == session_id
        )
        result = await session.execute(query)
        return list(result.scalars().all())


game_session_model = GameSessionModel()
