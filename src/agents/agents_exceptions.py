from src.agents import logger


class UnsupportedModelError(Exception):
    def __init__(self, model: str):
        logger.error(f"Unsupported model: {model}")
        self.message = f"Unsupported model: {model}"
        super().__init__(self.message)
