import logging
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import app as app
from src.api.craft.elements.elements_constants import STARTING_ELEMENTS
from src.api.users.users_schemas import UserPublic
from src.shared.config import shared_config

logger = logging.getLogger("tests")


@pytest_asyncio.fixture(scope="function", autouse=True)
async def startup_app() -> AsyncGenerator[Any]:
    shared_config.debug_mode = True
    shared_config.app_env = "test"
    async with LifespanManager(app, startup_timeout=60, shutdown_timeout=60) as manager:
        yield manager.app  # type: ignore


@pytest.mark.asyncio(loop_scope="function")
async def test_get_user() -> None:
    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test/api",
        headers={"x-user-id": "1234"},
    ) as ac:
        response = await ac.get("/users/me")

    assert response.status_code == 200

    user = UserPublic.model_validate(response.json())
    logger.info("Received user %s", user)
    assert user.object_id == 1234
    assert user.inventory is not None
    assert len(user.inventory.items) == 4

    user.inventory.items.sort(key=lambda x: x.sub_type_id)
    for start_element, item in zip(
        STARTING_ELEMENTS, user.inventory.items, strict=True
    ):
        assert item.element
        assert item.element.emoji == start_element.emoji
        assert item.element.name == start_element.name
