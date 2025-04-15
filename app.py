import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvloop
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import Container
from src.api.api_router import api_router
from src.api.craft.craft_registry import get_craft_registry
from src.containers import create_container, init_service, init_service_and_register
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

    # --- Event Loop Initialization ---
    uvloop.install()

    # --- Container Initialization ---
    logger.info("Initializing container")
    container: Container = create_container()
    app.state.container = container

    key_service_init_tasks = [
        init_service(container, "db"),
        init_service(container, "telegram_object"),
        init_service(container, "event_bus"),
        init_service(container, "disk_cache_instance"),
    ]
    db_instance, telegram_object, event_bus_instance, _ = await asyncio.gather(
        *key_service_init_tasks
    )

    # --- Service Initialization ---
    try:
        logger.debug("Initializing services")
        services_to_initialize = [
            # -- API Services --
            container.elements_service,
            container.recipes_service,
            container.elements_agent,
            container.progress_service,
            # -- Telegram Services --
            container.chats_service,
            container.memberships_service,
            container.messages_service,
            container.polls_service,
            container.users_service,
        ]
        async_init_tasks = [
            init_service_and_register(service, event_bus_instance)
            for service in services_to_initialize
        ]

        async_service_start_tasks = [
            get_craft_registry(),
            get_telegram_registry(),
            get_game_registry(),
            db_instance.create_all(),
            telegram_object.start(),
        ]

        async_tasks = [
            *async_init_tasks,
            *async_service_start_tasks,
        ]

        await asyncio.gather(*async_tasks)

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


app = FastAPI(
    lifespan=lifespan,
    title="Telemetree API",
    description="Telemetree API endpoints.",
    version="1.0.0",
    root_path=shared_config.root_path,
)

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
