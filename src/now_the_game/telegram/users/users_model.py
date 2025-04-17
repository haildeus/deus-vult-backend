from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession

from src.now_the_game.telegram.users.users_schemas import UserBase, UserTable
from src.shared.base import BaseModel


class UserModel(BaseModel[UserTable]):
    def __init__(self) -> None:
        super().__init__(UserTable)

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
            return await self.get_by_other_params(session, username=username)
        elif premium is not None:
            return await self.get_by_other_params(session, is_premium=premium)
        else:
            return await self.get_all(session)


user_model = UserModel()
