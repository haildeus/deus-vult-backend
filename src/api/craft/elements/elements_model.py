from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api import logger
from src.api.craft.elements.elements_schemas import ElementTable
from src.shared.base import BaseModel, EntityAlreadyExistsError, EntityNotFoundError


class ElementModel(BaseModel[ElementTable]):
    def __init__(self):
        super().__init__(ElementTable)

    async def get(
        self,
        session: AsyncSession,
        *,
        element_id: int | None = None,
        name: str | list[str] | None = None,
    ) -> list[ElementTable]:
        """Get an element by ID, name, or all elements"""
        if element_id:
            return await self.get_by_id(session, element_id)
        elif name:
            if isinstance(name, list):
                return await self.get_by_param_in_list(session, "name", name)
            else:
                return await self.get_by_other_params(session, name=name)
        else:
            return_obj = await self.get_all(session)
            return return_obj

    async def remove_secure(self, session: AsyncSession, name: str) -> bool:
        query = select(self.model_class).where(self.model_class.name == name)
        result = await session.execute(query)
        result = list(result.scalars().all())
        try:
            assert len(result) == 1
        except AssertionError as e:
            raise EntityNotFoundError(entity_id=name) from e
        except Exception as e:
            logger.error(f"Error removing Element: {e}")
            raise e

        await session.delete(result[0])
        return True

    async def not_exists(self, session: AsyncSession, name: str) -> bool:
        query = select(self.model_class).where(self.model_class.name == name)
        result = await session.execute(query)
        result = list(result.scalars().all())
        try:
            assert len(result) == 0
        except AssertionError as e:
            raise EntityAlreadyExistsError(
                entity=name, entity_type=self.model_class.__name__
            ) from e
        except Exception as e:
            logger.error(f"Error checking if Element exists: {e}")
            raise e

        return len(result) == 0


element_model = ElementModel()
