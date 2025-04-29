import logging

from sqlmodel import select

from src.api.craft.elements.elements_constants import VOID
from src.api.craft.elements.elements_schemas import Element, ElementTable
from src.api.craft.recipes.recipes_schemas import RecipeTable
from src.shared.base import BaseService
from src.shared.observability.traces import async_traced_function
from src.shared.uow import UnitOfWork, current_uow

logger = logging.getLogger("deus-vult.api.craft")


class RecipesService(BaseService):
    def __init__(self, uow: UnitOfWork) -> None:
        super().__init__()
        self.uow = uow

    @async_traced_function
    async def save_new_recipe(
        self,
        element_a: ElementTable,
        element_b: ElementTable,
        new_element: Element | None,
    ) -> RecipeTable:
        async with self.uow.start() as uow:
            session = await uow.get_session()
            if new_element is not None:
                created_element = ElementTable.model_validate(new_element)
                session.add(created_element)
                logger.debug(
                    "Created new recipe for: %s + %s = %s",
                    element_a,
                    element_b,
                    created_element,
                )
            else:
                # We use the VOID element as a placeholder for impossible crafts.
                created_element = ElementTable.model_validate(VOID)
                logger.debug(
                    "Failed to create new recipe for %s + %s", element_a, element_b
                )

            new_recipe = RecipeTable(
                element_a_id=element_a.object_id,
                element_b_id=element_b.object_id,
                result_id=created_element.object_id,
                result=created_element,
            )
            new_recipe.update_resources_cost(element_a, element_b)
            session.add(new_recipe)

        return new_recipe

    @async_traced_function
    async def fetch_recipe(
        self,
        element_a_id: int,
        element_b_id: int,
    ) -> RecipeTable | None:

        active_uow = current_uow.get()
        session = await active_uow.get_session()

        stmt = select(RecipeTable).where(
            RecipeTable.element_a_id == element_a_id,
            RecipeTable.element_b_id == element_b_id,
        )
        result = (await session.execute(stmt)).scalars().one_or_none()

        return result
