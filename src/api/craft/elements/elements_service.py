import asyncio
import logging

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import select

from src.api.craft.elements.elements_agent import ElementsAgent
from src.api.craft.elements.elements_constants import INIT_ELEMENTS, VOID
from src.api.craft.elements.elements_exceptions import NoRecipeExistsException
from src.api.craft.elements.elements_schemas import (
    Element,
    ElementInput,
    ElementResponse,
    ElementTable,
)
from src.api.craft.progress.progress_service import ProgressService
from src.api.craft.recipes.recipes_schemas import RecipePublic
from src.api.craft.recipes.recipes_service import RecipesService
from src.api.inventory.inventory_schemas import InventoryItemTable
from src.api.users.users_schemas import UserTable
from src.shared.base import BaseService
from src.shared.observability.traces import async_traced_function
from src.shared.uow import UnitOfWork, current_uow

logger = logging.getLogger("deus-vult.api.craft")


class ElementsService(BaseService):
    def __init__(
        self,
        uow: UnitOfWork,
        progress_service: ProgressService,
        recipes_service: RecipesService,
        elements_agent: ElementsAgent,
    ):
        super().__init__()
        self.uow = uow
        self.progress_service = progress_service
        self.recipes_service = recipes_service
        self.elements_agent = elements_agent

    @async_traced_function
    async def init_elements(self) -> None:
        async with self.uow.start() as uow:
            session = await uow.get_session()

            for element in INIT_ELEMENTS:
                stmt = (
                    insert(ElementTable)
                    .values(**element.model_dump())
                    .on_conflict_do_nothing(index_elements=["object_id"])
                )
                await session.execute(stmt)

    @async_traced_function
    async def craft_from_recipe(
        self, user: UserTable, recipe_id: int
    ) -> ElementResponse:
        recipe = await self.recipes_service.get_recipe(recipe_id)
        if (
            recipe is None
            or recipe.result is None
            or not await self.progress_service.is_discovered_recipe(user, recipe)
        ):
            raise NoRecipeExistsException(f"Recipe with id {recipe_id} is not found")

        base_items = []
        for base_item_id, amount in recipe.resources_cost.items():
            base_items.append(
                InventoryItemTable(
                    type=InventoryItemTable.ItemType.ELEMENT,
                    sub_type_id=int(base_item_id),
                    amount=int(amount),
                ),
            )

        await user.inventory.remove_items(*base_items)
        await user.inventory.add_items(
            InventoryItemTable(
                type=InventoryItemTable.ItemType.ELEMENT,
                sub_type_id=recipe.result.object_id,
                amount=1,
            ),
        )

        return ElementResponse(
            object_id=recipe.result.object_id,
            name=recipe.result.name,
            emoji=recipe.result.emoji,
            recipe=RecipePublic.model_validate(recipe, from_attributes=True),
            is_first_discovered=False,
            is_new=False,
        )

    @async_traced_function
    async def combine_elements(
        self,
        user: UserTable,
        element_a_id: int,
        element_b_id: int,
    ) -> ElementResponse:
        assert element_a_id <= element_b_id
        uow = current_uow.get()
        session = await uow.get_session()

        await user.inventory.remove_items(
            InventoryItemTable(
                type=InventoryItemTable.ItemType.ELEMENT,
                sub_type_id=element_a_id,
                amount=1,
            ),
            InventoryItemTable(
                type=InventoryItemTable.ItemType.ELEMENT,
                sub_type_id=element_b_id,
                amount=1,
            ),
        )

        element_a, element_b = await asyncio.gather(
            session.get_one(ElementTable, element_a_id),
            session.get_one(ElementTable, element_b_id),
        )

        recipe = await self.recipes_service.fetch_recipe(element_a_id, element_b_id)

        if recipe is not None:
            is_first_discovered = await self.progress_service.discover_recipe(
                user, recipe
            )
            is_new = False
        else:
            is_first_discovered = True
            is_new = True

            ai_input = ElementInput(
                element_a=Element.model_validate(element_a, from_attributes=True),
                element_b=Element.model_validate(element_b, from_attributes=True),
            )

            # We retry 3 times looking for a unique new element.
            new_element = None
            retries = 3
            while retries > 0:
                potential_element = await self.elements_agent.combine_elements(ai_input)

                stmt = select(
                    select(ElementTable)
                    .where(ElementTable.name == potential_element.name)
                    .exists()
                )
                exits = (await session.execute(stmt)).scalar()

                if not exits:
                    new_element = potential_element
                    break

                retries -= 1

            # noinspection PyTypeChecker
            recipe = await self.recipes_service.save_new_recipe(
                element_a, element_b, new_element
            )

            if not new_element:
                raise NoRecipeExistsException("No recipe to combine.")

            await self.progress_service.discover_recipe(user, recipe)

        if recipe.result is None or recipe.result.object_id == VOID.object_id:
            raise NoRecipeExistsException("No recipe to combine.")

        await user.inventory.add_items(
            InventoryItemTable(
                type=InventoryItemTable.ItemType.ELEMENT,
                sub_type_id=recipe.result.object_id,
            )
        )

        return ElementResponse(
            object_id=recipe.result.object_id,
            name=recipe.result.name,
            emoji=recipe.result.emoji,
            recipe=RecipePublic.model_validate(recipe, from_attributes=True),
            is_first_discovered=is_first_discovered,
            is_new=is_new,
        )
