import logging
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src import Container
from src.api.core.dependencies import get_user
from src.api.craft.elements.elements_schemas import CraftRequest, ElementResponse
from src.api.craft.elements.elements_service import ElementsService
from src.api.users.users_schemas import UserTable
from src.shared.observability.traces import async_traced_function

logger = logging.getLogger("deus-vult.api.craft")

craft_router = APIRouter(prefix="/craft")


@craft_router.post(
    "/elements/combine",
    name="Combining elements",
    tags=["Elements"],
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
