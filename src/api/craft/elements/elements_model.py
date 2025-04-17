import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.craft.elements.elements_schemas import ElementTable
from src.shared.base import BaseModel, EntityAlreadyExistsError, EntityNotFoundError
from src.shared.observability.traces import async_traced_function

logger = logging.getLogger("deus-vult.api.craft")


class ElementModel(BaseModel[ElementTable]):
    def __init__(self) -> None:
        super().__init__(ElementTable)

    @async_traced_function
    async def get(
        self,
        session: AsyncSession,
        *,
        element_id: int | list[int] | None = None,
        name: str | list[str] | None = None,
    ) -> list[ElementTable]:
        """Get an element by ID, name, or all elements"""
        if element_id:
            if isinstance(element_id, list):
                return await self.get_by_param_in_list(session, "object_id", element_id)
            else:
                return await self.get_by_id(session, element_id)
        elif name:
            if isinstance(name, list):
                return await self.get_by_param_in_list(session, "name", name)
            else:
                return await self.get_by_other_params(session, name=name)
        else:
            return_obj = await self.get_all(session)
            return return_obj

    @async_traced_function
    async def remove_secure(self, session: AsyncSession, name: str) -> bool:
        query = select(self.model_class).where(self.model_class.name == name)
        result = list((await session.execute(query)).scalars().all())
        try:
            assert len(result) == 1
        except AssertionError as e:
            raise EntityNotFoundError(entity_id=name) from e
        except Exception as e:
            logger.error("Error removing Element: %s", e)
            raise e

        await session.delete(result[0])
        return True

    @async_traced_function
    async def not_exists(self, session: AsyncSession, name: str) -> bool:
        query = select(self.model_class).where(self.model_class.name == name)
        result = list((await session.execute(query)).scalars().all())
        try:
            assert len(result) == 0
        except AssertionError as e:
            raise EntityAlreadyExistsError(
                entity=name, entity_type=self.model_class.__name__
            ) from e
        except Exception as e:
            logger.error("Error checking if Element exists: %s", e)
            raise e

        return len(result) == 0


element_model = ElementModel()
