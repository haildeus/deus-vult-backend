from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .characters_schemas import CharacterBase, LoreBase, PrimaryStatsBase


class CharacterModel(BaseModel[CharacterBase]):
    def __init__(self):
        super().__init__(CharacterBase)

    @overload
    async def get(self, session: AsyncSession) -> list[CharacterBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, character_id: int
    ) -> list[CharacterBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int
    ) -> list[CharacterBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, user_id: int
    ) -> list[CharacterBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int, user_id: int
    ) -> list[CharacterBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        character_id: int | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> list[CharacterBase]:
        if character_id:
            return await self.get_by_id(session, character_id)

        elif chat_id and user_id:
            return await self.get_for_chat_user_id(session, chat_id, user_id)
        elif chat_id:
            return await self.get_for_chat_id(session, chat_id)
        elif user_id:
            return await self.get_for_user_id(session, user_id)
        else:
            return await self.get_all(session)

    async def get_for_character_id(
        self, session: AsyncSession, character_id: int
    ) -> list[CharacterBase]:
        query = select(CharacterBase).where(CharacterBase.object_id == character_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_for_chat_id(
        self, session: AsyncSession, chat_id: int
    ) -> list[CharacterBase]:
        query = select(CharacterBase).where(CharacterBase.chat_id == chat_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_for_user_id(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> list[CharacterBase]:
        query = select(CharacterBase).where(CharacterBase.user_id == user_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_for_chat_user_id(
        self,
        session: AsyncSession,
        chat_id: int,
        user_id: int,
    ) -> list[CharacterBase]:
        query = select(CharacterBase).where(
            CharacterBase.chat_id == chat_id, CharacterBase.user_id == user_id
        )
        result = await session.execute(query)
        return list(result.scalars().all())


class LoreModel(BaseModel[LoreBase]):
    def __init__(self):
        super().__init__(LoreBase)

    @overload
    async def get(self, session: AsyncSession) -> list[LoreBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, lore_id: int) -> list[LoreBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, character_id: int
    ) -> list[LoreBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        character_id: int | None = None,
        lore_id: int | None = None,
    ) -> list[LoreBase]:
        if lore_id:
            return await self.get_by_id(session, lore_id)
        elif character_id:
            return await self.get_for_character_id(session, character_id)
        else:
            return await self.get_all(session)

    async def get_for_character_id(
        self, session: AsyncSession, character_id: int
    ) -> list[LoreBase]:
        query = select(LoreBase).where(LoreBase.character_id == character_id)
        result = await session.execute(query)
        return list(result.scalars().all())


class PrimaryStatsModel(BaseModel[PrimaryStatsBase]):
    def __init__(self):
        super().__init__(PrimaryStatsBase)

    @overload
    async def get(self, session: AsyncSession) -> list[PrimaryStatsBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, primary_stats_id: int
    ) -> list[PrimaryStatsBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, character_id: int
    ) -> list[PrimaryStatsBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        character_id: int | None = None,
        primary_stats_id: int | None = None,
    ) -> list[PrimaryStatsBase]:
        if primary_stats_id:
            return await self.get_by_id(session, primary_stats_id)
        elif character_id:
            return await self.get_for_character_id(session, character_id)
        else:
            return await self.get_all(session)

    async def get_for_character_id(
        self, session: AsyncSession, character_id: int
    ) -> list[PrimaryStatsBase]:
        query = select(PrimaryStatsBase).where(
            PrimaryStatsBase.character_id == character_id
        )
        result = await session.execute(query)
        return list(result.scalars().all())


character_model = CharacterModel()
lore_model = LoreModel()
primary_stats_model = PrimaryStatsModel()
