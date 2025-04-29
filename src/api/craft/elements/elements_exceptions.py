from src.shared.exceptions import BadRequestError


class BaseCraftElementException(BadRequestError):
    pass


class NoRecipeExistsException(BaseCraftElementException):
    pass
