from fastapi import APIRouter

from src.api import logger
from src.api.core.interfaces import SuccessResponse

recipes_router = APIRouter()


@recipes_router.get(
    "/recipes",
    name="Get all recipes",
    response_model=SuccessResponse,
    status_code=200,
)
async def get_recipe_all() -> SuccessResponse:
    """Get all recipes"""
    logger.debug("Getting all recipes")

    return SuccessResponse(message="Recipes fetched successfully", data=[])
