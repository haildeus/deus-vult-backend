from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession

from src.api import logger_wrapper
from src.api.craft.recipes.recipes_schemas import RecipeBase, RecipeTable
from src.shared.base import BaseModel


class RecipeModel(BaseModel[RecipeTable]):
    def __init__(self):
        super().__init__(RecipeTable)

    @overload
    async def get(self, session: AsyncSession) -> list[RecipeBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, element_a_id: int
    ) -> list[RecipeBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, element_a_id: int, element_b_id: int
    ) -> list[RecipeBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, result_id: int
    ) -> list[RecipeBase]: ...

    @logger_wrapper.log_debug
    async def get(
        self,
        session: AsyncSession,
        *,
        element_a_id: int | None = None,
        element_b_id: int | None = None,
        result_id: int | None = None,
    ) -> list[RecipeBase]:
        """Get a recipe by element_a_id, element_b_id, or result_id"""
        if element_a_id:
            return await self.get_by_other_params(session, element_a_id=element_a_id)
        elif element_b_id:
            return await self.get_by_other_params(session, element_b_id=element_b_id)
        elif result_id:
            return await self.get_by_other_params(session, result_id=result_id)
        else:
            return await self.get_all(session)


recipe_model = RecipeModel()
