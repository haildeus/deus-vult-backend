import logging
from fastapi import APIRouter

from src.api.craft.craft_router import craft_router

logger = logging.getLogger("deus-vult.api")

imported_routers = [craft_router]

api_router = APIRouter(prefix="/api")

for router in imported_routers:
    logger.debug("Including router: %s", router)
    api_router.include_router(router)


@api_router.get("/ping", tags=["Health Check"])
async def ping():
    """Health check endpoint for VMs"""
    return {"message": "pong"}
