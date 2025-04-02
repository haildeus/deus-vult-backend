from src.shared.logging import LoggerWrapper

logger_wrapper = LoggerWrapper("now-the-game")
logger = logger_wrapper.logger

__all__ = ["logger"]
