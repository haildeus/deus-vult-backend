import logging
import os
from typing import Literal, TypeVar

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
LOGGING
"""

logger = logging.getLogger("deus-vult.settings")

"""
ABSTRACT BASE CONFIG CLASSES
"""


class BaseAccess:
    """Base class for accessing secrets."""

    def _resolve_secret(
        self, local_secret: str, cloud_secret_id: str | None = None
    ) -> str:
        """Resolves a secret from Secret Manager or local environment."""
        return (
            local_secret
            if not cloud_secret_id
            else self._get_cloud_secret(self._get_google_project_id(), cloud_secret_id)
        )

    # --- Private Helper Methods ---
    def _get_google_project_id(self) -> str:
        """Returns the Google Cloud Project ID."""
        logger.debug("Getting Google Cloud Project ID")
        try:
            response = os.environ.get("BASE_GOOGLE_CLOUD_PROJECT")
            if not response:
                raise ValueError(
                    "BASE_GOOGLE_CLOUD_PROJECT environment variable not set."
                )
            return response
        except Exception as e:
            logger.error("Error getting Google Cloud Project ID: %s", e)
            raise e

    def _get_local_secret(self, env_var: str) -> str:
        """Fetches a secret's value from local environment."""
        logger.warning("Using %s env var for local dev.", env_var)
        local_secret = os.environ.get(env_var)
        if local_secret:
            return local_secret
        raise ValueError(f"{env_var} environment variable not set.")

    def _get_cloud_secret(
        self,
        project_id: str,
        secret_id: str,
        version_id: str = "latest",
    ) -> str:
        """Fetches a secret's value from Google Secret Manager."""
        logger.debug(
            "Attempting to fetch secret '%s' from project '%s'",
            secret_id,
            project_id,
        )
        try:
            _, detected_project_id = google_default_credentials()  # type: ignore
            effective_project_id = project_id or detected_project_id  # type: ignore

            if not effective_project_id:
                logger.error(
                    "Could not determine Google Cloud Project ID for Secret Manager."
                )
                raise ValueError(
                    "Could not determine Google Cloud Project ID for Secret Manager."
                )

            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{effective_project_id}/secrets/{secret_id}/versions/{version_id}"  # noqa: E501
            response = client.access_secret_version(request={"name": name})  # type: ignore
            payload = response.payload.data.decode("UTF-8")
            logger.info(
                "Successfully accessed secret: %s (version: %s)",
                secret_id,
                version_id,
            )
            return payload

        except DefaultCredentialsError as e:
            logger.error(
                "Could not find credentials to access secret %s. "
                "Check 'Secret Manager Secret Accessor' role.",
                secret_id,
            )
            raise e from e
        except Exception as e:
            logger.error("Error accessing secret %s: %s", secret_id, e, exc_info=True)
            raise e


class BaseConfig(BaseSettings, BaseAccess):
    """Base class for configuration settings across vertical slices"""

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
        logger.error("Error accessing secret %s: %s", secret_id, e, exc_info=True)
        return None


"""
SHARED CONFIG
"""


class SharedConfig(BaseConfig):
    app_env: Literal["local", "cloud", "test"] = "local"
    stage: Literal["dev", "prod"] = "dev"
    event_bus: Literal["local"] = "local"
    debug_mode: bool = True
    use_disk_cache: bool = True

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

    # --- Access ---

    # For local dev
    password_local: str = Field("", validation_alias="POSTGRES_PASSWORD_LOCAL")
    # For Google App Engine
    password_secret_id: str | None = Field(
        None, validation_alias="DB_PASSWORD_SECRET_ID"
    )
    instance_connection_name: str | None = Field(
        None, validation_alias="INSTANCE_CONNECTION_NAME"
    )
    app_engine: Literal["google", "local"] = Field(
        "local", validation_alias="POSTGRES_APP_ENGINE"
    )

    class Config(BaseConfig.Config):
        env_prefix = "POSTGRES_"

    @computed_field(return_type=str)  # type: ignore
    @property
    def password(self) -> str:
        """Fetches the password from Secret Manager or local environment."""
        return self._resolve_secret(self.password_local, self.password_secret_id)

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
                logger.debug("Local. Using TCP: %s:%s", self.host, self.port)

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


class ClickHouseConfig(BaseConfig):
    """ClickHouse configuration, required for observability."""

    # Basic config
    user: str = Field("default", validation_alias="CLICKHOUSE_USER")
    host: str = Field("ch.haildeus.com", validation_alias="CLICKHOUSE_HOST")
    port: int = Field(443, validation_alias="CLICKHOUSE_PORT")
    secure: bool = Field(True, validation_alias="CLICKHOUSE_SECURE")

    # constants
    http_thread_executor_size: int = Field(
        12, validation_alias="CLICKHOUSE_HTTP_THREAD_EXECUTOR_SIZE"
    )
    http_max_pool_size: int = Field(
        12, validation_alias="CLICKHOUSE_HTTP_MAX_POOL_SIZE"
    )
    http_num_pools: int = Field(4, validation_alias="CLICKHOUSE_HTTP_NUM_POOLS")

    # --- Access ---

    # For local dev
    password_local: str = Field("", validation_alias="CLICKHOUSE_PASSWORD_LOCAL")
    # For Google App Engine
    password_secret_id: str | None = Field(
        None, validation_alias="CLICKHOUSE_PASS_SECRET_ID"
    )

    class Config(BaseConfig.Config):
        env_prefix = "CLICKHOUSE_"

    @computed_field(return_type=str)  # type: ignore
    @property
    def password(self) -> str:
        """Fetches the password from Secret Manager or local environment."""
        return self._resolve_secret(self.password_local, self.password_secret_id)


# noinspection PyArgumentList
clickhouse_config = ClickHouseConfig()  # type: ignore
