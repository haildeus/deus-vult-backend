from typing import cast

from sqlalchemy.exc import SQLAlchemyError

from src.api import logger
from src.api.craft.recipes.recipes_model import recipe_model
from src.api.craft.recipes.recipes_schemas import CreateRecipe, FetchRecipe, RecipeTable
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import RecipeTopics
from src.shared.events import Event
from src.shared.uow import current_uow


class RecipesService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = recipe_model

    @EventBus.subscribe(RecipeTopics.RECIPE_CREATE)
    async def on_create_recipe(self, event: Event) -> None:
        payload = cast(CreateRecipe, event.extract_payload(event, CreateRecipe))
        logger.debug(f"Recipe payload: {payload}")
        element_a_id = payload.element_a_id
        element_b_id = payload.element_b_id
        result_id = payload.result_id
        recipe = RecipeTable(
            element_a_id=element_a_id, element_b_id=element_b_id, result_id=result_id
        )
        logger.debug(f"Creating recipe: {element_a_id} + {element_b_id} = {result_id}")

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()

            try:
                await self.model.add(db, recipe, pass_checks=False)
            except SQLAlchemyError as e:
                logger.error(
                    f"SQLAlchemy: {element_a_id} + {element_b_id} = {result_id}: {e}"
                )
                raise e
            except Exception as e:
                logger.error(
                    f"Error: {element_a_id} + {element_b_id} = {result_id}: {e}"
                )
                raise e
        else:
            raise RuntimeError("No active UoW found during recipe creation")

    @EventBus.subscribe(RecipeTopics.RECIPE_FETCH)
    async def on_fetch_recipe(self, event: Event) -> list[RecipeTable]:
        payload = cast(FetchRecipe, event.extract_payload(event, FetchRecipe))
        logger.debug(f"Fetching recipe: {payload}")

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            recipes = await self.model.get(
                db,
                element_a_id=payload.element_a_id,
                element_b_id=payload.element_b_id,
                result_id=payload.result_id,
            )
            logger.debug(f"Fetched recipes: {recipes} (length: {len(recipes)})")

            return recipes
        else:
            raise RuntimeError("No active UoW found during recipe fetching")
