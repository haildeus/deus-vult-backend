from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvloop
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import Container
from src.api.api_router import api_router
from src.api.craft.craft_registry import get_craft_registry
from src.containers import create_container
from src.now_the_game.telegram.telegram_registry import get_telegram_registry
from src.shared.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up the application")
    uvloop.install()

    # --- Container Initialization ---
    container: Container = create_container()
    app.state.container = container

    # --- Event Bus Initialization ---
    event_bus_instance = container.event_bus()

    # --- Database Initialization ---
    db_instance = container.db()
    try:
        # Metadata initialization
        get_craft_registry()
        get_telegram_registry()
        await db_instance.initialize()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e
    # --- Service Initialization ---
    try:
        subscriber_services = [
            container.elements_service(),
            container.recipes_service(),
        ]
        for service in subscriber_services:
            event_bus_instance.register_subscribers_from(service)
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        raise e

    logger.info("Application initialized")
    yield

    # Shutdown events
    logger.info("Shutting down the application")

    # --- Database Shutdown ---
    try:
        await db_instance.close()
    except Exception as e:
        logger.error(f"Error closing database: {e}")
        raise e

    logger.info("Application stopped")


app = FastAPI(lifespan=lifespan)

# That's for the cors plugin
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "ETag",
        "Cache-Control",
        "If-None-Match",
        "Vary",
        "CDN-Cache-Control",
    ],
)

app.include_router(api_router)
