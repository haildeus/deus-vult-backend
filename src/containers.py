import logging
import pkgutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dependency_injector import containers, providers
from pyrogram.client import Client

from src.agents.glif.glif_service import GlifConfig, GlifService
from src.api.craft.elements.elements_agent import ElementsAgent
from src.api.craft.elements.elements_service import ElementsService
from src.api.craft.progress.progress_service import ProgressService
from src.api.craft.recipes.recipes_service import RecipesService
from src.now_the_game.telegram.chats.chats_service import ChatsService
from src.now_the_game.telegram.client.client_config import TelegramConfig
from src.now_the_game.telegram.client.client_object import TelegramBot
from src.now_the_game.telegram.memberships.memberships_service import MembershipsService
from src.now_the_game.telegram.messages.messages_service import MessagesService
from src.now_the_game.telegram.polls.polls_service import PollsService
from src.now_the_game.telegram.users.users_service import UsersService
from src.shared.base import BaseService
from src.shared.base_llm import VertexConfig, VertexLLM
from src.shared.cache import get_disk_cache
from src.shared.config import PostgresConfig
from src.shared.database import Database
from src.shared.event_bus import EventBus
from src.shared.observability.utils import configure_logging
from src.shared.types import SessionFactory
from src.shared.uow import UnitOfWork

logger = logging.getLogger("deus-vult.containers")


class Container(containers.DeclarativeContainer):
    # --- DATABASE ---
    postgres_config = providers.Factory(
        PostgresConfig,
    )
    db = providers.Singleton(
        Database,
        db_config=postgres_config,
    )

    # -- Database Session --
    db_session_provider = providers.Factory[SessionFactory](
        lambda db_instance: db_instance.session,  # type: ignore
        db_instance=db,
    )
    # -- Unit of Work --
    uow_factory = providers.Factory(
        UnitOfWork,
        session_factory=db_session_provider,
    )

    # -- Disk Cache --
    disk_cache_instance = providers.Singleton(get_disk_cache)

    # -- Event Bus --
    event_bus = providers.Singleton(EventBus)

    # -- API Services --
    elements_service = providers.Singleton(ElementsService)
    recipes_service = providers.Singleton(RecipesService)
    progress_service = providers.Singleton(ProgressService)

    # -- Telegram --
    telegram_config = providers.Factory(TelegramConfig)
    telegram_object = providers.Singleton(TelegramBot, config=telegram_config)
    telegram_client = providers.Factory[Client](
        lambda telegram_bot: telegram_bot.get_client(),  # type: ignore
        telegram_bot=telegram_object,
    )

    # -- Telegram Services --
    chats_service = providers.Singleton(ChatsService)
    memberships_service = providers.Singleton(MembershipsService)
    messages_service = providers.Singleton(MessagesService)
    polls_service = providers.Singleton(PollsService)
    users_service = providers.Singleton(UsersService)

    # -- LLM Provider --
    model_config = providers.Factory(VertexConfig)
    model_object = providers.Singleton(VertexLLM, config=model_config)
    elements_agent = providers.Singleton(ElementsAgent, provider=model_object)

    # -- Glif --
    glif_config = providers.Factory(GlifConfig)
    glif_service = providers.Singleton(GlifService)

    # -- Observability --
    observability = providers.Factory(configure_logging)


def find_modules_in_packages(packages_paths: list[str]) -> list[str]:
    """
    Finds all module names within the specified package paths.

    Args:
        packages_paths: A list of dotted package paths

    Returns:
        A list of fully qualified module names found within those packages.
    """
    discovered_modules = set[str]()
    project_root = Path(__file__).parent.parent
    for package_path in packages_paths:
        try:
            package_parts = package_path.split(".")
            package_dir = project_root.joinpath(*package_parts)

            for _, name, ispkg in pkgutil.walk_packages(
                path=[str(package_dir)],
                prefix=package_path + ".",
            ):
                if not ispkg:
                    discovered_modules.add(name)

        except ModuleNotFoundError:
            logger.warning(
                "Warning: Package path %s not found or not a package.", package_path
            )
        except Exception as e:
            logger.warning(
                "Warning: Error scanning package %s: %s",
                package_path,
                e,
            )

    discovered_modules = list(discovered_modules)
    discovered_modules_len = len(discovered_modules)
    if discovered_modules_len == 0:
        logger.critical("No modules found for wiring in %s", project_root)
    else:
        logger.debug("Discovered modules for wiring: %s", discovered_modules_len)
    return discovered_modules


def create_container() -> Container:
    """Creates and wires the dependency injection container."""
    logger.debug("Creating dependency injection container")
    container = Container()

    packages_to_wire = [
        "src.agents",
        "src.api",
        "src.now_the_game",
        "src.shared",
    ]
    modules_to_wire = find_modules_in_packages(packages_to_wire)  # type: ignore
    modules_to_wire.append("app")
    container.wire(modules=modules_to_wire)

    logger.debug("Container wired")
    return container


async def init_service(container: Container, name: str) -> Any:
    """
    Initializes a service.
    """
    service_dict = {
        "db": container.db,
        "telegram_object": container.telegram_object,
        "disk_cache_instance": container.disk_cache_instance,
        "event_bus": container.event_bus,
    }
    try:
        logger.debug("Initializing service %s", name)
        service = service_dict[name]()
        logger.debug("Initialized service %s", name)
        return service
    except KeyError as e:
        raise ValueError("Service %s not found in container", name) from e
    except Exception as e:
        logger.exception("Error initializing service %s", name)
        raise e


async def init_service_and_register(
    service_factory: Callable[[], BaseService], event_bus: EventBus
) -> None:
    """
    Initializes a service and registers it with the event bus.

    Args:
        service_factory: A callable that returns a BaseService instance.
        event_bus: The event bus to register the service with.
    """
    service = service_factory()
    event_bus.register_subscribers_from(service)
    logger.debug("Initialized and registered %s", service.__class__.__name__)
