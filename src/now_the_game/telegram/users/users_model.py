from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .users_schemas import User


class UserModel(BaseModel[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> User | None:
        query = select(User).where(User.username == username)
        result = await session.exec(query)
        return result.scalar_one_or_none()


user_model = UserModel()
