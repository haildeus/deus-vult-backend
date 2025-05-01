import logging
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src import Container
from src.api.core.dependencies import get_user
from src.api.craft.elements.elements_schemas import (
    CraftFromRecipeRequest,
    CraftRequest,
    ElementResponse,
)
from src.api.craft.elements.elements_service import ElementsService
from src.api.craft.progress.progress_service import ProgressService
from src.api.craft.recipes.recipes_schemas import (
    RecipesListResponse,
    RecipeWithElementsPublic,
)
from src.api.users.users_schemas import UserTable
from src.shared.observability.traces import async_traced_function

logger = logging.getLogger("deus-vult.api.craft")

craft_router = APIRouter(prefix="/craft")


@craft_router.post(
    "/elements/combine",
    name="Combining elements",
    tags=["Elements"],
    response_model=ElementResponse,
)
@async_traced_function
@inject
async def combine_elements(
    user: Annotated[UserTable, Depends(get_user)],
    elements_service: Annotated[
        ElementsService, Depends(Provide[Container.elements_service])
    ],
    element_ids: CraftRequest,
) -> ElementResponse:
    """
    Combines two elements. Checks for existing recipes or generates a new one.
    """
    logger.debug(
        "Combining elements: %s + %s",
        element_ids.object_id_a,
        element_ids.object_id_b,
    )

    result = await elements_service.combine_elements(
        user,
        element_ids.object_id_a,
        element_ids.object_id_b,
    )

    logger.debug("Combined result: %s", result)
    return result


@craft_router.get(
    "/recipes/all",
    name="All open recipes by user",
    tags=["Elements"],
    response_model=RecipesListResponse,
)
@async_traced_function
@inject
async def open_recipes(
    user: Annotated[UserTable, Depends(get_user)],
    progress_service: Annotated[
        ProgressService, Depends(Provide[Container.progress_service])
    ],
) -> RecipesListResponse:
    recipes = await progress_service.get_open_recipies(user)
    return RecipesListResponse(
        recipes=[
            RecipeWithElementsPublic.model_validate(recipe, from_attributes=True)
            for recipe in recipes
        ],
    )


@craft_router.post(
    "/recipes/craft",
    name="Craft from recipe",
    tags=["Elements"],
    response_model=ElementResponse,
)
@async_traced_function
@inject
async def craft_from_recipe(
    user: Annotated[UserTable, Depends(get_user)],
    elements_service: Annotated[
        ElementsService, Depends(Provide[Container.elements_service])
    ],
    craft_request: CraftFromRecipeRequest,
) -> ElementResponse:
    return await elements_service.craft_from_recipe(user, craft_request.recipe_id)
