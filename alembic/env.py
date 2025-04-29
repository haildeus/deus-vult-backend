import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context
from src.api.craft.craft_registry import get_craft_registry
from src.now_the_game.game.game_registry import get_game_registry
from src.now_the_game.telegram.telegram_registry import get_telegram_registry
from src.shared.config import PostgresConfig

# --- Importing metadata ---
asyncio.run(get_craft_registry())
asyncio.run(get_game_registry())
asyncio.run(get_telegram_registry())


# this is the Alembic Config object, which provides
config = context.config

# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Set Target Metadata ---
target_metadata = SQLModel.metadata


def get_database_url() -> str:
    """Gets the database URL from the application's config."""
    try:
        pg_config = PostgresConfig()  # type: ignore
        sync_driver = "postgresql+psycopg2"
        async_driver = "postgresql+asyncpg"

        return pg_config.db_url.replace(async_driver, sync_driver)
    except Exception as e:
        print(f"Error getting database configuration: {e}")
        print("Ensure necessary environment variables for PostgresConfig are set.")
        raise


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    """
    url = get_database_url()  # Use our function
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get URL using our consistent method
    db_url = get_database_url()

    # Create a configuration dictionary using the URL
    connectable_config = config.get_section(config.config_ini_section) or {}
    connectable_config["sqlalchemy.url"] = db_url
    print(connectable_config)

    connectable = engine_from_config(
        connectable_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
