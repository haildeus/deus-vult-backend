import logging

from fastapi import APIRouter

from src.api.craft.craft_router import craft_router
from src.api.users.users_router import users_router

logger = logging.getLogger("deus-vult.api")

imported_routers = [craft_router, users_router]

api_router = APIRouter(prefix="/api")

for router in imported_routers:
    logger.debug("Including router: %s", router)
    api_router.include_router(router)


@api_router.get("/ping", tags=["Health Check"])
async def ping() -> dict[str, str]:
    """Health check endpoint for VMs"""
    return {"message": "pong"}
