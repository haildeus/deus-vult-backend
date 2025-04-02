from typing import Any

from pydantic import BaseModel

from src.shared.events import Event


class ICraftEvent(Event):
    pass


class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Any
