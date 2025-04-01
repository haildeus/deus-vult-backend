from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src import BaseModel, EntityAlreadyExistsError, EntityNotFoundError
from src.api import logger, logger_wrapper
from src.api.craft.recipes.recipes_schemas import RecipeBase, RecipeTable


class RecipeModel(BaseModel[RecipeTable]):
    def __init__(self):
        super().__init__(RecipeTable)

    @overload
    async def get(self, session: AsyncSession) -> list[RecipeBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, first: int) -> list[RecipeBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, first: int, second: int
    ) -> list[RecipeBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, result: int) -> list[RecipeBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        first: int | None = None,
        second: int | None = None,
        result: int | None = None,
    ) -> list[RecipeBase]:
        """Get a recipe by first, second, or result"""
        if first:
            return await self.get_by_other_params(session, first=first)
        
