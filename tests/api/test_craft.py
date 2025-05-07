import logging
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import app as app
from src import Container
from src.api.craft.elements.elements_constants import STARTING_ELEMENTS
from src.api.craft.elements.elements_schemas import ElementTable
from src.api.users.users_schemas import UserPublic
from src.shared.config import shared_config

logger = logging.getLogger("tests")


@pytest_asyncio.fixture(scope="function", autouse=True)
async def startup_app() -> AsyncGenerator[Any]:
    shared_config.debug_mode = True
    shared_config.app_env = "test"
    async with LifespanManager(app, startup_timeout=60, shutdown_timeout=60) as manager:
        yield manager.app  # type: ignore


@pytest_asyncio.fixture(scope="function")
async def client(startup_app: Any) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test/api",
        headers={"x-user-id": "1234"},
    ) as client:
        yield client


@pytest.mark.asyncio(loop_scope="function")
async def test_get_user(client: AsyncClient) -> None:
    response = await client.get("/users/me")
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


@pytest.mark.asyncio(loop_scope="function")
async def test_save_empty_recipe(client: AsyncClient) -> None:
    container: Container = app.state.container

    await container.recipes_service().save_new_recipe(
        ElementTable(object_id=1),
        ElementTable(object_id=2),
        None,
    )

    response = await client.post(
        "/craft/elements/combine", json={"object_id_a": 1, "object_id_b": 2}
    )
    assert response.status_code == 404

    response = await client.post(
        "/craft/elements/combine", json={"object_id_a": 1, "object_id_b": 3}
    )
    assert response.status_code == 200
