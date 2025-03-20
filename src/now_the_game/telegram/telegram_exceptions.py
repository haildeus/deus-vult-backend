class MissingCredentialsError(Exception):
    """Exception raised when required credentials are missing."""

    def __init__(self, message="Missing required credentials"):
        self.message = message
        super().__init__(self.message)
