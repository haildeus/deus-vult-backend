from src import BaseService, Event, event_bus
from src.api import logger, logger_wrapper
from src.api.craft.recipes.recipes_model import recipe_model
from src.api.craft.recipes.recipes_schemas import (
    CreateRecipePayload,
    FetchRecipePayload,
    FetchRecipeResponsePayload,
    RecipeTable,
    RecipeTopics,
)


class RecipesService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = recipe_model

    @event_bus.subscribe(RecipeTopics.RECIPE_CREATE.value)
    @logger_wrapper.log_debug
    async def on_create_recipe(self, event: Event) -> None:
        if not isinstance(event.payload, CreateRecipePayload):
            payload = CreateRecipePayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.debug(f"Creating recipe: {payload}")

        element_a_id = payload.element_a_id
        element_b_id = payload.element_b_id
        result_id = payload.result_id
        db = payload.db_session

        logger.debug(f"Creating recipe: {element_a_id} + {element_b_id} = {result_id}")

        recipe = RecipeTable(
            element_a_id=element_a_id, element_b_id=element_b_id, result_id=result_id
        )
        await self.model.add(db, recipe)

    @event_bus.subscribe(RecipeTopics.RECIPE_FETCH.value)
    @logger_wrapper.log_debug
    async def on_fetch_recipe(self, event: Event) -> FetchRecipeResponsePayload:
        if not isinstance(event.payload, FetchRecipePayload):
            payload = FetchRecipePayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.debug(f"Fetching recipe: {payload}")

        element_a_id = payload.element_a_id
        element_b_id = payload.element_b_id
        result_id = payload.result_id
        db = payload.db_session

        logger.debug(f"Fetching recipe: {element_a_id} + {element_b_id} = {result_id}")

        if element_a_id:
            result = await self.model.get(db, element_a_id=element_a_id)
        elif element_b_id:
            # TODO: Think about how to implement this
            raise NotImplementedError("Fetching by element_b_id is not implemented")
        elif result_id:
            result = await self.model.get(db, result_id=result_id)
        else:
            result = await self.model.get(db)

        logger.debug(f"Fetched recipes: {result}")

        return FetchRecipeResponsePayload(recipes=result)


recipes_service = RecipesService()
