import logging
from typing import Annotated, cast

from fastapi import APIRouter, Depends

from src.api.core.dependencies import get_user
from src.api.users.users_schemas import UserPublic, UserTable
from src.shared.observability.traces import async_traced_function

logger = logging.getLogger("deus-vult.api.users")

users_router = APIRouter(prefix="/users")


@users_router.get(
    "/me",
    name="Get User's Info",
    tags=["Users"],
    response_model=UserPublic,
)
@async_traced_function
async def get_me(
    user: Annotated[UserTable, Depends(get_user)],
) -> UserPublic:
    return cast(UserPublic, user)
