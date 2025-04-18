import hashlib
import hmac
import logging

from dependency_injector.wiring import Provide, inject
from fastapi import HTTPException

from src import Container
from src.now_the_game.telegram.client.client_config import TelegramConfig
from src.shared.config import shared_config

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


# TODO: Decouple this part, implement event bus for communication
@inject
def validate_init_data(
    init_data: str | None = None,
) -> int:
    """
    Validates the data received from Telegram WebApp.

    Args:
        init_data: The data from Telegram.WebApp.initData field

    Returns:
        bool: True if the data is valid, False otherwise
    """
    if DEBUG_MODE and not init_data:
        return 714862471
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
