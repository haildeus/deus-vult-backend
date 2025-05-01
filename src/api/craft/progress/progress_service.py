import logging

from sqlmodel import col, select, update

from src.api.craft.progress.progress_schemas import (
    ProgressTable,
)
from src.api.craft.recipes.recipes_schemas import RecipeTable
from src.api.users.users_schemas import UserTable
from src.shared.base import BaseService
from src.shared.observability.traces import async_traced_function
from src.shared.uow import UnitOfWork, current_uow

logger = logging.getLogger("deus-vult.api.craft")


class ProgressService(BaseService):
    def __init__(self, uow: UnitOfWork) -> None:
        super().__init__()
        self.uow = uow

    @async_traced_function
    async def is_discovered_recipe(self, user: UserTable, recipe: RecipeTable) -> bool:
        uow = current_uow.get()
        session = await uow.get_session()

        stmt = select(
            select(ProgressTable)
            .where(
                ProgressTable.object_id == user.object_id,
                ProgressTable.recipe_id == recipe.object_id,
            )
            .exists()
        )
        return bool((await session.execute(stmt)).scalar())

    @async_traced_function
    async def discover_recipe(self, user: UserTable, recipe: RecipeTable) -> bool:
        uow = current_uow.get()
        session = await uow.get_session()

        exits = await self.is_discovered_recipe(user, recipe)
        if exits:
            return False

        session.add(
            ProgressTable(
                object_id=user.object_id,
                recipe_id=recipe.object_id,
            )
        )

        async with self.uow.start() as inner_uow:
            inner_session = await inner_uow.get_session()
            inner_stmt = (
                update(RecipeTable)
                .where(
                    col(RecipeTable.object_id) == recipe.object_id,
                )
                .values(discovered_count=RecipeTable.discovered_count + 1)
            )
            await inner_session.execute(inner_stmt)

        return True

    @async_traced_function
    async def get_open_recipies(self, user: UserTable) -> list[RecipeTable]:
        uow = current_uow.get()
        session = await uow.get_session()

        stmt = select(ProgressTable).where(
            ProgressTable.object_id == user.object_id,
        )
        result = (await session.execute(stmt)).scalars().all()
        return [progress.recipe for progress in result]
