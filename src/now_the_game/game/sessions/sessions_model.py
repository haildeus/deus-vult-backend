from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.now_the_game.game.sessions.sessions_schemas import SessionBase
from src.shared.base import BaseModel


class GameSessionModel(BaseModel[SessionBase]):
    def __init__(self) -> None:
        super().__init__(SessionBase)

    @overload
    async def get(self, session: AsyncSession) -> list[SessionBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int
    ) -> list[SessionBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, session_id: int
    ) -> list[SessionBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        chat_id: int | None = None,
        session_id: int | None = None,
    ) -> list[SessionBase]:
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

    @staticmethod
    async def get_for_chat_id(
        session: AsyncSession, chat_id: int
    ) -> list[SessionBase]:
        query = select(SessionBase).where(SessionBase.chat_id == chat_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_for_chat_id_and_session_id(
        session: AsyncSession, chat_id: int, session_id: int
    ) -> list[SessionBase]:
        query = select(SessionBase).where(
            SessionBase.chat_id == chat_id, SessionBase.object_id == session_id
        )
        result = await session.execute(query)
        return list(result.scalars().all())


session_model = GameSessionModel()
