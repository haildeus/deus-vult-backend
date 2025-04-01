from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src import Event, event_bus
from src.api import logger, logger_wrapper
from src.api.core.database import api_db
from src.api.core.dependencies import validate_init_data
from src.api.core.interfaces import SuccessResponse
from src.api.craft.recipes.recipes_schemas import CreateRecipe, RecipeTopics

recipes_router = APIRouter()


@recipes_router.get(
    "/recipes",
    name="Get recipes",
    response_model=SuccessResponse,
    status_code=200,
)
@logger_wrapper.log_debug
async def get_recipes(
    init_data: Annotated[dict[str, str] | None, Depends(validate_init_data)],
    element_a_id: int | None = Query(None, description="The ID of the element"),
    element_b_id: int | None = Query(None, description="The ID of the element"),
    result_id: int | None = Query(None, description="The ID of the element"),
) -> SuccessResponse:
    """Get recipes"""
    logger.debug("Getting recipes")

    async with api_db.session() as session:
        payload_example = {
            "element_a_id": element_a_id,
            "element_b_id": element_b_id,
            "result_id": result_id,
            "db_session": session,
        }
        event = Event.from_dict(RecipeTopics.RECIPE_FETCH.value, payload_example)
        response = await event_bus.request(event)
        logger.debug(f"Recipe response: {response.payload.recipes}")

    return SuccessResponse(
        message="Recipes fetched successfully", data=response.payload.recipes
    )


@recipes_router.post(
    "/recipes",
    name="Create a new recipe",
    response_model=SuccessResponse,
    status_code=201,
)
@logger_wrapper.log_debug
async def create_recipe(
    init_data: Annotated[dict[str, str] | None, Depends(validate_init_data)],
    recipe: CreateRecipe,
) -> SuccessResponse:
    """Create a new recipe"""
    logger.debug(f"Creating new recipe: {recipe}")

    async with api_db.session() as session:
        payload_example = {
            "element_a_id": recipe.element_a_id,
            "element_b_id": recipe.element_b_id,
            "result_id": recipe.result_id,
            "db_session": session,
        }
        event = Event.from_dict(RecipeTopics.RECIPE_CREATE.value, payload_example)
        await event_bus.publish_and_wait(event)
        await session.flush()
        logger.debug("Recipe created")

    return SuccessResponse(message="Recipe created", data={"message": "Recipe created"})
