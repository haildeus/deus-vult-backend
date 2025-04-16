from fastapi import HTTPException, status


class BadRequestError(HTTPException):
    def __init__(self, msg: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


class NotFoundError(HTTPException):
    def __init__(self, name: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=name.capitalize() + " not found"
        )
