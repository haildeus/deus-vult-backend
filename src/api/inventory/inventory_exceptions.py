from src.shared.exceptions import BadRequestError


class BaseInventoryException(BadRequestError):
    pass


class InventoryNotEnoughItemsException(BaseInventoryException):
    pass
