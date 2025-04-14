from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select

from src.api.craft.progress.progress_schemas import ProgressTable
from src.shared.base import BaseModel, EntityAlreadyExistsError
from src.shared.config import Logger

logger = Logger("progress_model").logger


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
    ) -> list[ProgressTable]:
        """Get a progress by user_id or chat_instance"""
        # All three parameters are provided
        if user_id and chat_instance and element_id:
            logger.debug(
                f"Fetching progress with all parameters: {user_id}, "
                + f"{chat_instance}, {element_id}"
            )
            return await self.get_by_other_params(
                session,
                user_id=user_id,
                chat_instance=chat_instance,
                element_id=element_id,
            )

        # Two parameters are provided
        elif user_id and chat_instance:
            logger.debug(
                f"Fetching progress with two parameters: {user_id}, {chat_instance}"
            )
            return await self.get_by_other_params(
                session, user_id=user_id, chat_instance=chat_instance
            )
        elif user_id and element_id:
            logger.debug(
                f"Fetching progress with two parameters: {user_id}, {element_id}"
            )
            return await self.get_by_other_params(
                session, user_id=user_id, element_id=element_id
            )
        elif chat_instance and element_id:
            logger.debug(
                f"Fetching progress with two parameters: {chat_instance}, {element_id}"
            )
            return await self.get_by_other_params(
                session, chat_instance=chat_instance, element_id=element_id
            )

        # One parameter is provided
        elif user_id:
            logger.debug(f"Fetching progress with one parameter: {user_id}")
            return await self.get_by_id(session, user_id)
        elif chat_instance:
            logger.debug(f"Fetching progress with one parameter: {chat_instance}")
            return await self.get_by_other_params(session, chat_instance=chat_instance)
        elif element_id:
            logger.debug(f"Fetching progress with one parameter: {element_id}")
            raise ValueError("Element ID is not enough to get a progress")
        else:
            logger.debug("Fetching all progress")
            return await self.get_all(session)

    async def not_exists(
        self,
        session: AsyncSession,
        user_id: int,
        result_id: int,
    ) -> bool:
        """Checks if a progress exists for the given user_id and result_id"""
        query = select(ProgressTable).where(
            ProgressTable.object_id == user_id,
            ProgressTable.element_id == result_id,
        )
        result = await session.execute(query)
        result = list(result.scalars().all())
        logger.debug(f"Progress result: {result}")
        try:
            assert len(result) == 0
        except AssertionError as e:
            raise EntityAlreadyExistsError(
                entity=user_id, entity_type=self.model_class.__name__
            ) from e
        except Exception as e:
            logger.error(f"Error checking if progress exists: {e}")
            raise e

        return True

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
