from fastapi import APIRouter

from .. import logger
from .elements.elements_router import elements_router
from .recipes.recipes_router import recipes_router

imported_routers = [elements_router, recipes_router]

craft_router = APIRouter(prefix="/craft")

for router in imported_routers:
    logger.debug(f"Including router: {router}")
    craft_router.include_router(router)
