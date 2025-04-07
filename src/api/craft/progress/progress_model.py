from sqlalchemy.ext.asyncio import AsyncSession

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


progress_model = ProgressModel()
