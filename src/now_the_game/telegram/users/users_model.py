from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ... import logger
from ...core.base import BaseModel
from .users_schemas import UserBase


class UserModel(BaseModel[UserBase]):
    def __init__(self):
        super().__init__(UserBase)

    @overload
    async def get(self, session: AsyncSession, *, user_id: int) -> list[UserBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, username: str) -> list[UserBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, premium: bool = True
    ) -> list[UserBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        user_id: int | None = None,
        username: str | None = None,
        premium: bool | None = None,
    ) -> list[UserBase]:
        """Get a user by ID, username, or premium status"""
        if user_id:
            return await self.get_by_id(session, user_id)
        elif username:
            return await self.get_by_username(session, username)
        elif premium is not None:
            return await self.get_premium_users(session)
        else:
            return await self.get_all(session)

    async def get_premium_users(self, session: AsyncSession) -> list[UserBase]:
        """Get all premium users"""
        query = select(UserBase).where(UserBase.is_premium is True)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> list[UserBase]:
        """Get a user by username"""
        try:
            assert username
            assert isinstance(username, str)
            assert len(username) >= 3
        except AssertionError as e:
            logger.error(f"Error getting user by username: {e}")
            raise e
        query = select(UserBase).where(UserBase.username == username)
        result = await session.execute(query)
        return list(result.scalars().all())


user_model = UserModel()
