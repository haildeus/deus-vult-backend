from typing import Any

from fastapi.responses import JSONResponse

from ... import Event


class ICraftEvent(Event):
    pass


class SuccessResponse(JSONResponse):
    def __init__(self, content: dict[str, Any] | None = None):
        response_content: dict[str, Any] = {"message": "Success"}
        if content:
            response_content["data"] = content

        super().__init__(content=response_content)
