import hashlib
import hmac

from fastapi import HTTPException

from src.api import logger
from src.api.core.config import api_config
from src.shared.config import shared_config

DEBUG_MODE = shared_config.debug_mode


def validate_init_data(init_data: str | None = None) -> int:
    """
    Validates the data received from Telegram WebApp.

    Args:
        init_data: The data from Telegram.WebApp.initData field

    Returns:
        bool: True if the data is valid, False otherwise
    """
    if DEBUG_MODE and not init_data:
        return 714862471

    try:
        assert init_data
        assert api_config.bot_token
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
    secret_key = hashlib.sha256(api_config.bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    check = computed_hash == received_hash
    if not check:
        raise HTTPException(status_code=401, detail="Invalid init data")

    # TODO: Implement the rest of the init data logic
    raise NotImplementedError
