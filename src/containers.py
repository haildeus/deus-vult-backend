import pkgutil
from pathlib import Path

from dependency_injector import containers, providers

from src.api.craft.elements.elements_service import ElementsService
from src.api.craft.recipes.recipes_service import RecipesService
from src.shared.config import PostgresConfig
from src.shared.database import Database
from src.shared.event_bus import EventBus
from src.shared.logging import logger
from src.shared.types import SessionFactory
from src.shared.uow import UnitOfWork


class Container(containers.DeclarativeContainer):
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

    # -- Services --
    elements_service = providers.Singleton(ElementsService)
    recipes_service = providers.Singleton(RecipesService)


def find_modules_in_packages(packages_paths: list[str]) -> list[str]:
    """
    Finds all module names within the specified package paths.

    Args:
        packages_paths: A list of dotted package paths

    Returns:
        A list of fully qualified module names found within those packages.
    """
    discovered_modules = set[str]()
    project_root = Path(__file__).parent.parent.parent
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

    logger.debug(f"Discovered modules for wiring: {len(list(discovered_modules))}")
    return list(discovered_modules)


def create_container() -> Container:
    """Creates and wires the dependency injection container."""
    logger.debug("Creating dependency injection container")
    container = Container()

    packages_to_wire = [
        "src.api",
        "src.now_the_game",
        "src.shared",
    ]
    modules_to_wire = find_modules_in_packages(packages_to_wire)  # type: ignore
    container.wire(modules=modules_to_wire)
    modules_to_wire.append("app")

    logger.debug("Container wired")
    return container
