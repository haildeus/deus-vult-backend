import logging
import sys
from abc import ABC
from typing import Literal, TypeVar

import colorlog
from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL

"""
TYPE VARIABLES
"""

R = TypeVar("R")

"""
LOGGING CONSTANTS
"""

LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


"""
ABSTRACT BASE CONFIG CLASSES
"""


class BaseConfig(BaseSettings, ABC):
    """Abstract base class for configuration settings across vertical slices"""

    class Config:
        extra = "ignore"
        env_file = ".env"


"""
SHARED CONFIG
"""


class SharedConfig(BaseConfig):
    app_env: Literal["local", "cloud"] = "local"
    event_bus: Literal["local"] = "local"
    debug_mode: bool = True

    log_level: int = logging.DEBUG if debug_mode else logging.INFO

    class Config(BaseConfig.Config):
        env_prefix = "GLOBAL_"


shared_config = SharedConfig()


class Logger:
    def __init__(
        self,
        name: str = "shared-components",
        level: int = shared_config.log_level,
        log_format: str | None = None,
        date_format: str | None = None,
    ):
        """
        Initializes and configures a logger instance.

        Args:
            name: The name of the logger.
            level: The logging level (e.g., logging.DEBUG, logging.INFO).
            log_format: Optional custom log format string.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent duplicate handlers if this name was somehow configured before
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Console handler
        console_handler = colorlog.StreamHandler(sys.stdout)

        # Setup formatter
        if log_format is None:
            # Default detailed format good for debugging
            log_format = "%(log_color)s%(levelname)-8s%(reset)s | %(asctime)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"  # noqa: E501
        if date_format is None:
            date_format = "%Y-%m-%d %H:%M:%S"
        formatter = colorlog.ColoredFormatter(
            fmt=log_format,
            datefmt=date_format,
            reset=True,
            log_colors=LOG_COLORS,
            secondary_log_colors={},  # You can color specific parts of the message too
            style="%",  # Use %-style formatting
        )
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.debug(
            f"Logger '{name}' initialized with level {logging.getLevelName(level)}."
        )


logger = Logger("settings").logger


"""
DATABASE CONFIG
"""


class PostgresConfig(BaseConfig):
    """PostgreSQL configuration, handles App Engine Unix sockets."""

    user: str = Field("postgres", validation_alias="POSTGRES_USER")
    # For production, fetch password securely from Secret Manager
    password: str = Field("postgres", validation_alias="POSTGRES_PASSWORD")
    host: str = Field(
        "localhost", validation_alias="POSTGRES_HOST"
    )  # Used for local dev
    port: int = Field(5432, validation_alias="POSTGRES_PORT")  # Used for local dev
    db_name: str = Field("deus-vult", validation_alias="POSTGRES_DB_NAME")

    instance_connection_name: str | None = Field(
        None, validation_alias="POSTGRES_INSTANCE_CONNECTION_NAME"
    )
    app_engine: Literal["google", "local"] = Field(
        "local", validation_alias="POSTGRES_APP_ENGINE"
    )

    class Config(BaseConfig.Config):
        env_prefix = "POSTGRES_"

    @property
    def db_url(self) -> str:
        """Generates the appropriate SQLAlchemy database URL."""

        if self.app_engine == "google" and self.instance_connection_name:
            # App Engine Standard: Connect via Unix socket using asyncpg
            # The 'host' parameter in the query string points to the socket directory
            socket_dir = f"/cloudsql/{self.instance_connection_name}"
            logger.debug(
                f"Detected App Engine. Connecting via Unix socket: {socket_dir}"
            )
            sqlalchemy_url = URL.create(
                drivername="postgresql+asyncpg",
                username=self.user,
                password=self.password,  # Password still needed for DB auth
                database=self.db_name,
                query={
                    "host": socket_dir
                },  # Pass socket path via 'host' query arg for asyncpg
            )
        else:
            # Local Development or other environments: Connect via TCP/IP
            logger.debug(f"Not on App Engine. Using TCP: {self.host}:{self.port}")
            sqlalchemy_url = URL.create(
                drivername="postgresql+asyncpg",
                username=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.db_name,
            )
        return sqlalchemy_url.render_as_string(hide_password=False)

    @property
    def safe_db_url(self) -> str:
        """Generates a database URL safe for logging (password hidden)."""
        raw_url_str = self.db_url
        url_obj = URL.create(raw_url_str)
        return url_obj.render_as_string(hide_password=True)
