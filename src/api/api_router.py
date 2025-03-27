from fastapi import APIRouter

from . import logger
from .craft.craft_router import craft_router

imported_routers = [craft_router]

api_router = APIRouter(prefix="/api")

for router in imported_routers:
    logger.debug(f"Including router: {router}")
    api_router.include_router(router)


@api_router.get("/ping")
async def ping():
    """Health check endpoint for VMs"""
    return {"message": "pong"}
