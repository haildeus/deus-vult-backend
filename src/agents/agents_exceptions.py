import logging

logger = logging.getLogger("deus-vult.agents")


class UnsupportedModelError(Exception):
    def __init__(self, model: str):
        logger.error("Unsupported model: %s", model)
        self.message = f"Unsupported model: {model}"
        super().__init__(self.message)
