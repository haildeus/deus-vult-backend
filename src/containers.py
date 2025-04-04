import pkgutil
from pathlib import Path

from dependency_injector import containers, providers
from pyrogram.client import Client

from src.api.craft.elements.elements_service import ElementsService
from src.api.craft.recipes.recipes_service import RecipesService
from src.now_the_game.telegram.chats.chats_service import ChatsService
from src.now_the_game.telegram.client.client_config import TelegramConfig
from src.now_the_game.telegram.client.client_object import TelegramBot
from src.now_the_game.telegram.memberships.memberships_service import MembershipsService
from src.now_the_game.telegram.messages.messages_service import MessagesService
from src.now_the_game.telegram.polls.polls_service import PollsService
from src.now_the_game.telegram.users.users_service import UsersService
from src.shared.base_llm import VertexConfig, VertexLLM
from src.shared.config import PostgresConfig
from src.shared.database import Database
from src.shared.event_bus import EventBus
from src.shared.logging import logger
from src.shared.types import SessionFactory
from src.shared.uow import UnitOfWork


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
    # -- Event Bus --
    event_bus = providers.Singleton(EventBus)

    # -- API Services --
    elements_service = providers.Singleton(ElementsService)
    recipes_service = providers.Singleton(RecipesService)

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
    model = providers.Singleton(VertexLLM, config=model_config)


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
                f"Warning: Package path {package_path} not found or not a package."
            )
        except Exception as e:
            logger.warning(f"Warning: Error scanning package {package_path}: {e}")

    discovered_modules = list(discovered_modules)
    discovered_modules_len = len(discovered_modules)
    if discovered_modules_len == 0:
        logger.critical(f"No modules found for wiring in {project_root}")
    else:
        logger.debug(f"Discovered modules for wiring: {discovered_modules_len}")
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
    container.wire(modules=modules_to_wire)
    modules_to_wire.append("app")

    logger.debug("Container wired")
    return container
