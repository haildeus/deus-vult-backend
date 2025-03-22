class PyrogramConversionError(Exception):
    """Raised when a pyrogram message cannot be converted to a database entity"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
