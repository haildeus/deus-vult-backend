class InvalidInitData(Exception):
    """Exception raised when the init data is invalid."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
