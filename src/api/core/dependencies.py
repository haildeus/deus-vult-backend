import contextlib
import hashlib
import hmac
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Header, HTTPException

from src import Container
from src.api.users.users_schemas import UserTable
from src.api.users.users_service import UsersService
from src.now_the_game.telegram.client.client_config import TelegramConfig
from src.shared.config import shared_config
from src.shared.uow import UnitOfWork

DEBUG_MODE = shared_config.debug_mode
logger = logging.getLogger("deus-vult.dependencies")


@inject
def get_bot_token(
    telegram_config: TelegramConfig = Provide[Container.telegram_config],
) -> str:
    """
    Get the bot token from the Telegram config.
    """
    return telegram_config.bot_token


def validate_init_data(
    x_user_id: Annotated[int | None, Header()],
    init_data: str | None = None,
) -> UserTable:
    """
    Validates the data received from Telegram WebApp.
    """
    if DEBUG_MODE and not init_data:
        return UserTable(
            object_id=x_user_id or 714862471,
            first_name="Chris",
            last_name="The Gigachad",
        )
    bot_token = get_bot_token()

    try:
        assert init_data
        assert bot_token
    except AssertionError as e:
        logger.error("Invariant violation: init_data or bot_token is not set")
        raise HTTPException(status_code=401, detail="Invalid init data") from e

    # Parse the query string into a dict
    data_dict: dict[str, str] = dict(
        pair.split("=", 1) for pair in init_data.split("&") if pair
    )

    # Check if we have the required hash field
    if "hash" not in data_dict or not data_dict["hash"]:
        raise HTTPException(status_code=401, detail="Invalid init data")

    received_hash = data_dict.pop("hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    check = computed_hash == received_hash
    if not check:
        raise HTTPException(status_code=401, detail="Invalid init data")

    # TODO: Implement the rest of the init data logic
    raise NotImplementedError


# FastAPI dependencies doesn't work for async generators with @inject
@contextlib.asynccontextmanager
@inject
async def _with_uow(
    uow: UnitOfWork = Provide[Container.uow_factory],
) -> AsyncGenerator[UnitOfWork]:
    async with uow.start() as uow:
        yield uow


async def with_uow() -> AsyncGenerator[UnitOfWork]:
    async with _with_uow() as uow:
        yield uow


# TODO: JWT auth
@inject
async def get_user(
    _: Annotated[UnitOfWork, Depends(with_uow)],
    user_data: Annotated[UserTable, Depends(validate_init_data)],
    users_service: Annotated[UsersService, Depends(Provide[Container.users_service])],
) -> UserTable:
    return await users_service.create_or_update(user_data)
