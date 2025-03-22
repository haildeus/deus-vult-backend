from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .users_schemas import UserSchema


class UserModel(BaseModel[UserSchema]):
    def __init__(self):
        super().__init__(UserSchema)

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> UserSchema | None:
        query = select(UserSchema).where(UserSchema.username == username)
        result = await session.execute(query)
        return result.scalar_one_or_none()


user_model = UserModel()
