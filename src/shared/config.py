import logging
import os
import sys
from abc import ABC
from typing import Literal, TypeVar

import colorlog
from google.auth import default as google_default_credentials  # type: ignore
from google.auth.exceptions import DefaultCredentialsError  # type: ignore
from google.cloud import secretmanager  # type: ignore
from pydantic import Field, computed_field
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
HELPER FUNCTIONS
"""


def get_secret(
    project_id: str, secret_id: str, version_id: str = "latest"
) -> str | None:
    """Fetches a secret's value from Google Secret Manager."""
    try:
        _credentials, detected_project_id = google_default_credentials()  # type: ignore
        effective_project_id = project_id or detected_project_id  # type: ignore

        if not effective_project_id:
            logger.error(
                "Could not determine Google Cloud Project ID for Secret Manager."
            )
            return None

        client = secretmanager.SecretManagerServiceClient()
        name = (
            f"projects/{effective_project_id}/secrets/{secret_id}/versions/{version_id}"
        )
        response = client.access_secret_version(request={"name": name})  # type: ignore
        payload = response.payload.data.decode("UTF-8")
        logger.info(
            f"Successfully accessed secret: {secret_id} (version: {version_id})"
        )
        return payload
    except DefaultCredentialsError:  # type: ignore
        logger.error(
            f"Could not find credentials to access secret {secret_id}. "
            "Check 'Secret Manager Secret Accessor' role."
        )
        return None
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}", exc_info=True)
        return None


"""
SHARED CONFIG
"""


class SharedConfig(BaseConfig):
    app_env: Literal["local", "cloud"] = "local"
    stage: Literal["dev", "prod"] = "dev"
    event_bus: Literal["local"] = "local"
    debug_mode: bool = True

    log_level: int = logging.DEBUG if debug_mode else logging.INFO

    class Config(BaseConfig.Config):
        env_prefix = "GLOBAL_"

    @property
    def root_path(self) -> str:
        # Local dev
        if self.app_env == "local":
            return ""

        # Cloud dev
        if self.stage == "prod":
            return "https://api.haildeus.com"
        elif self.stage == "dev":
            return "https://dev.haildeus.com"
        else:
            raise ValueError(f"Invalid app environment: {self.app_env}")


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

    # Basic config
    user: str = Field("postgres", validation_alias="POSTGRES_USER")
    host: str = Field("localhost", validation_alias="POSTGRES_HOST")
    port: int = Field(5432, validation_alias="POSTGRES_PORT")
    db_name: str = Field("deus-vult", validation_alias="POSTGRES_DB_NAME")

    # For Google App Engine
    instance_connection_name: str | None = Field(
        None, validation_alias="INSTANCE_CONNECTION_NAME"
    )
    app_engine: Literal["google", "local"] = Field(
        "local", validation_alias="POSTGRES_APP_ENGINE"
    )
    password_secret_id: str | None = Field(
        None, validation_alias="DB_PASSWORD_SECRET_ID"
    )
    google_project_id: str | None = Field(None, validation_alias="GOOGLE_CLOUD_PROJECT")

    class Config(BaseConfig.Config):
        env_prefix = "POSTGRES_"

    @computed_field(return_type=str)
    @property
    def password(self) -> str:
        """Fetches the password from Secret Manager or raises an error."""
        if not self.password_secret_id:
            # Local dev as fallback
            local_pw = os.environ.get("POSTGRES_PASSWORD")
            if local_pw:
                logger.warning(
                    "Using POSTGRES_PASSWORD env var for local dev. "
                    "Set DB_PASSWORD_SECRET_ID for deployed environments."
                )
                return local_pw
            raise ValueError("DB_PASSWORD_SECRET_ID environment variable not set.")

        if not self.google_project_id:
            # Auto-detect project ID
            try:
                _creds, detected_project_id = google_default_credentials()  # type: ignore
                if detected_project_id:
                    self.google_project_id = detected_project_id
                else:
                    raise ValueError("Could not auto-detect Google Cloud Project ID.")
            except Exception as e:
                raise ValueError(
                    f"Failed to get Google Cloud Project ID for secret fetching: {e}"
                ) from e

        logger.debug(
            f"Attempting to fetch secret '{self.password_secret_id}' "
            f"from project '{self.google_project_id}'"  # type: ignore
        )
        fetched_password = get_secret(self.google_project_id, self.password_secret_id)  # type: ignore

        if fetched_password is None:
            # raise config error here
            raise ValueError(
                f"Failed to fetch database password from Secret Manager "
                f"(Secret ID: {self.password_secret_id}). Check logs and permissions."
            )

        return fetched_password

    def _build_sqlalchemy_url(self, use_placeholder_password: bool = False) -> URL:
        """Internal helper to construct the SQLAlchemy URL object."""

        password_to_use = "XXXXXX" if use_placeholder_password else self.password

        if self.app_engine == "google" and self.instance_connection_name:
            # App Engine Standard: Connect via Unix socket
            socket_dir = f"/cloudsql/{self.instance_connection_name}"
            if not use_placeholder_password:
                logger.debug(
                    f"App Engine. Configuring connection via Unix socket: {socket_dir}"
                )

            sqlalchemy_url = URL.create(
                drivername="postgresql+asyncpg",
                username=self.user,
                password=password_to_use,
                database=self.db_name,
                query={"host": socket_dir},  # Pass socket path via 'host' query arg
            )
        else:
            # Local Development or other environments: Connect via TCP/IP
            if not use_placeholder_password:
                logger.debug(f"Local. Using TCP: {self.host}:{self.port}")

            sqlalchemy_url = URL.create(
                drivername="postgresql+asyncpg",
                username=self.user,
                password=password_to_use,  # Use determined password
                host=self.host,
                port=self.port,
                database=self.db_name,
            )
        return sqlalchemy_url

    # --- Public Properties ---
    @property
    def db_url(self) -> str:
        """Generates the appropriate SQLAlchemy database URL with the real password."""
        url_obj = self._build_sqlalchemy_url(use_placeholder_password=False)
        return url_obj.render_as_string(hide_password=False)

    @property
    def safe_db_url(self) -> str:
        """Generates a database URL safe for logging (password hidden)."""
        url_obj = self._build_sqlalchemy_url(use_placeholder_password=True)
        return url_obj.render_as_string(hide_password=False)
