from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import Container
from src.api.api_router import api_router
from src.api.craft.craft_registry import get_craft_registry
from src.containers import create_container
from src.now_the_game.game.game_registry import get_game_registry
from src.now_the_game.telegram.telegram_registry import get_telegram_registry
from src.shared.config import Logger, shared_config

logger = Logger("main-app-component").logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up the application")
    logger.info(f"App environment: {shared_config.app_env}")
    logger.info(f"Debug mode: {shared_config.debug_mode}")
    logger.info(f"Event bus type: {shared_config.event_bus}")

    # --- Container Initialization ---
    logger.info("Initializing container")
    container: Container = create_container()
    app.state.container = container

    # --- Event Bus Initialization ---
    logger.info("Initializing event bus")
    event_bus_instance = container.event_bus()

    # --- Database Initialization ---
    logger.info("Initializing database")
    db_instance = container.db()
    try:
        # Metadata initialization
        await get_craft_registry()
        await get_telegram_registry()
        await get_game_registry()
        await db_instance.create_all()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e

    # --- Telegram Initialization ---
    telegram_object = container.telegram_object()
    try:
        await telegram_object.start()
    except Exception as e:
        logger.error(f"Error initializing telegram: {e}")
        raise e

    # --- Service Initialization ---
    try:
        logger.debug("Initializing services")
        # -- API Services --
        api_services = [
            container.elements_service(),
            container.recipes_service(),
        ]
        for service in api_services:
            event_bus_instance.register_subscribers_from(service)

        # -- Telegram Services --
        telegram_services = [
            container.chats_service(),
            container.memberships_service(),
            container.messages_service(),
            container.polls_service(),
            container.users_service(),
            container.elements_agent(),
        ]
        for service in telegram_services:
            event_bus_instance.register_subscribers_from(service)
        logger.debug("Services initialized")
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
