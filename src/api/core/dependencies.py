import hashlib
import hmac

from src.api import logger
from src.api.core.config import api_config
from src.shared.config import shared_config

DEBUG_MODE = shared_config.debug_mode


# TODO: add auth_date check
def validate_init_data(init_data: str, debug_mode: bool = DEBUG_MODE) -> bool:
    """
    Validates the data received from Telegram WebApp.

    Args:
        init_data: The data from Telegram.WebApp.initData field

    Returns:
        bool: True if the data is valid, False otherwise
    """
    if debug_mode:
        return True

    try:
        assert init_data
        assert api_config.bot_token
    except AssertionError:
        logger.error("Invariant violation: init_data or bot_token is not set")
        return False

    # Parse the query string into a dict
    data_dict: dict[str, str] = dict(
        pair.split("=", 1) for pair in init_data.split("&") if pair
    )

    # Check if we have the required hash field
    if "hash" not in data_dict or not data_dict["hash"]:
        return False

    received_hash = data_dict.pop("hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    secret_key = hashlib.sha256(api_config.bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    return computed_hash == received_hash
