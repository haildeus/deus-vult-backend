from sqlalchemy.exc import SQLAlchemyError

from src.api import logger
from src.api.craft.recipes.recipes_model import recipe_model
from src.api.craft.recipes.recipes_schemas import (
    CreateRecipePayload,
    FetchRecipePayload,
    FetchRecipeResponsePayload,
    RecipeTable,
    RecipeTopics,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.events import Event
from src.shared.uow import current_uow


class RecipesService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = recipe_model

    @EventBus.subscribe(RecipeTopics.RECIPE_CREATE.value)
    async def on_create_recipe(self, event: Event) -> None:
        if not isinstance(event.payload, CreateRecipePayload):
            payload = CreateRecipePayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

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
                await self.model.add(db, recipe)
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

    @EventBus.subscribe(RecipeTopics.RECIPE_FETCH.value)
    async def on_fetch_recipe(self, event: Event) -> FetchRecipeResponsePayload:
        if not isinstance(event.payload, FetchRecipePayload):
            payload = FetchRecipePayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.debug(f"Fetching recipe: {payload}")

        element_a_id = payload.element_a_id
        element_b_id = payload.element_b_id
        result_id = payload.result_id
        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()

            try:
                result = await self.model.get(
                    db,
                    element_a_id=element_a_id,
                    element_b_id=element_b_id,
                    result_id=result_id,
                )
                logger.debug(f"Fetched recipes: {result} (length: {len(result)})")

                return FetchRecipeResponsePayload(recipes=result)
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy: {e}")
                raise e
            except Exception as e:
                logger.error(f"Error: {e}")
                raise e
        else:
            raise RuntimeError("No active UoW found during recipe fetching")
