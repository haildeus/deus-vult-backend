from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select

from src.api.craft.progress.progress_schemas import ProgressBase, ProgressTable
from src.shared.base import BaseModel


class ProgressModel(BaseModel[ProgressTable]):
    def __init__(self):
        super().__init__(ProgressTable)

    async def get(
        self,
        session: AsyncSession,
        *,
        user_id: int | None = None,
        chat_instance: int | None = None,
        element_id: int | None = None,
    ) -> list[ProgressBase]:
        """Get a progress by user_id or chat_instance"""
        # All three parameters are provided
        if user_id and chat_instance and element_id:
            return await self.get_by_other_params(
                session,
                user_id=user_id,
                chat_instance=chat_instance,
                element_id=element_id,
            )

        # Two parameters are provided
        elif user_id and chat_instance:
            return await self.get_by_other_params(
                session, user_id=user_id, chat_instance=chat_instance
            )
        elif user_id and element_id:
            return await self.get_by_other_params(
                session, user_id=user_id, element_id=element_id
            )
        elif chat_instance and element_id:
            return await self.get_by_other_params(
                session, chat_instance=chat_instance, element_id=element_id
            )

        # One parameter is provided
        elif user_id:
            return await self.get_by_id(session, user_id)
        elif chat_instance:
            return await self.get_by_other_params(session, chat_instance=chat_instance)
        elif element_id:
            raise ValueError("Element ID is not enough to get a progress")
        else:
            return await self.get_all(session)

    async def check_access_internal(
        self, session: AsyncSession, user_id: int, element_a_id: int, element_b_id: int
    ) -> bool:
        """Internal helper to check progress within a session."""
        stmt = (
            select(ProgressTable.element_id)
            .where(ProgressTable.object_id == user_id)
            .where(
                or_(
                    ProgressTable.element_id == element_a_id,
                    ProgressTable.element_id == element_b_id,
                )
            )
        )
        result = await session.execute(stmt)
        found_elements = {row[0] for row in result.fetchall()}
        return element_a_id in found_elements and element_b_id in found_elements


progress_model = ProgressModel()
