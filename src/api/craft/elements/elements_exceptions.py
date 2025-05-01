from fastapi import HTTPException, status


class BaseCraftElementException(HTTPException):
    def __init__(
        self, status_code: int = status.HTTP_400_BAD_REQUEST, msg: str | None = None
    ) -> None:
        super().__init__(status_code=status_code, detail=msg)


class NoRecipeExistsException(BaseCraftElementException):
    def __init__(self, msg: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, msg=msg)
